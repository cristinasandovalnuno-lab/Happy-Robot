"""GET /metrics

Lee la tabla `calls_log` de Twin (vía su gateway REST) y devuelve
métricas agregadas en el formato que espera el dashboard externo
(React/Vite). Adaptado de la lógica de agregación de un proyecto de
referencia para este mismo tipo de reto, pero leyendo de Twin en vez
de S3.

Autenticación contra Twin: el gateway de Twin NO acepta el
HR_APP_SERVICE_KEY directamente - hay que mintear un JWT corto contra
HR_PLATFORM_URL primero (POST /api/apps/auth/service-token con el
service key como Bearer), y usar ESE JWT (no el service key) como
Bearer token contra el gateway de Twin, junto con x-org-id (el UUID
de la org, no el slug legible). El token se cachea a nivel de
contenedor Lambda (reusado entre invocaciones mientras el contenedor
siga caliente) y se renueva 30s antes de expirar.

Esquema real de columnas en `calls_log`:
  call_id, mc_number, carrier_name, load_id, origin_city, origin_state,
  destination_city, destination_state, outcome, agreed_price,
  carrier_sentiment, negotiation_rounds, logged_at, carrier_phone,
  loadboard_rate

IMPORTANTE sobre loadboard_rate vs max_rate: loadboard_rate es el rate
PÚBLICO que ya se le muestra al carrier en cada load (lo que devuelve
RATE en search_loads) - es seguro tenerlo en este pipeline porque el
agente ya lo conoce y lo dice en voz alta de forma rutinaria. max_rate
(el techo interno real) NUNCA debe entrar en este pipeline ni en
ningún dato que pase por el contexto del agente - ver el build
description doc, sección 4, para la razón completa. Las métricas de
"savings" de aquí miden el rendimiento de negociación contra el precio
público, no contra el margen interno real - es una limitación
consciente, no un descuido.

total_minutes sigue en 0 - no hay duration_minutes en este esquema.
"""
import json
import os
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta

from common.http import response, error_response

HR_PLATFORM_URL = os.environ["HR_PLATFORM_URL"].rstrip("/")
HR_APP_SERVICE_KEY = os.environ["HR_APP_SERVICE_KEY"]
TWIN_GATEWAY_URL = os.environ["TWIN_GATEWAY_URL"].rstrip("/")
TWIN_ORG_ID = os.environ["TWIN_ORG_ID"]  # UUID de la org, no el slug

# Cache a nivel de contenedor Lambda - se reutiliza entre invocaciones
# mientras el contenedor siga caliente (igual que el ejemplo del skill).
_token_cache = {"token": None, "exp_ms": 0}


def _mint_service_token():
    req = urllib.request.Request(
        f"{HR_PLATFORM_URL}/api/apps/auth/service-token",
        method="POST",
        headers={"Authorization": f"Bearer {HR_APP_SERVICE_KEY}"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read())
    exp_ms = datetime.fromisoformat(
        body["expiresAt"].replace("Z", "+00:00")
    ).timestamp() * 1000
    _token_cache.update(token=body["token"], exp_ms=exp_ms)
    return body["token"]


def _get_token():
    now_ms = time.time() * 1000
    if _token_cache["token"] and _token_cache["exp_ms"] - 30_000 > now_ms:
        return _token_cache["token"]
    return _mint_service_token()


def _fetch_calls_log():
    token = _get_token()
    url = f"{TWIN_GATEWAY_URL}/calls_log?select=*&order=logged_at.desc&limit=1000"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "x-org-id": TWIN_ORG_ID,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _lane(origin_city, origin_state, destination_city, destination_state):
    origin = ", ".join(p for p in [origin_city, origin_state] if p)
    destination = ", ".join(p for p in [destination_city, destination_state] if p)
    if not origin or not destination:
        return None, origin, destination
    return f"{origin} → {destination}", origin, destination


def _date_key(ts):
    if not ts:
        return "unknown"
    return str(ts)[:10]


def _to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compute_metrics(logs):
    total = len(logs)
    if total == 0:
        return _empty_metrics()

    outcome_counts = defaultdict(int)
    sentiment_counts = defaultdict(int)
    sentiment_by_outcome = defaultdict(lambda: defaultdict(int))
    lane_counts = defaultdict(int)
    booked_route_counts = defaultdict(int)
    neg_rounds = []
    date_counts = defaultdict(int)
    date_outcome_counts = defaultdict(lambda: defaultdict(int))
    recent_bookings = []

    negotiation_details = []
    discounts = []
    cost_by_date = defaultdict(float)
    savings_by_date = defaultdict(float)
    total_savings = 0.0
    cost_wtd = 0.0

    today = datetime.utcnow().date()
    week_start_str = (today - timedelta(days=today.weekday())).isoformat()

    funnel_authorized = 0
    funnel_matched = 0

    for log in logs:
        outcome = log.get("outcome") or "unknown"
        outcome_counts[outcome] += 1

        sentiment = log.get("carrier_sentiment") or "unknown"
        sentiment_counts[sentiment] += 1
        sentiment_by_outcome[outcome][sentiment] += 1

        if outcome != "rejected":
            funnel_authorized += 1
        if outcome not in ("rejected", "no_match"):
            funnel_matched += 1

        lane, origin, destination = _lane(
            log.get("origin_city"), log.get("origin_state"),
            log.get("destination_city"), log.get("destination_state"),
        )
        if lane:
            lane_counts[lane] += 1

        date_key = _date_key(log.get("logged_at"))

        if outcome == "booked":
            if lane:
                booked_route_counts[(origin, destination)] += 1
            recent_bookings.append({
                "timestamp": log.get("logged_at") or "",
                "carrier_name": log.get("carrier_name") or "Unknown",
                "load_id": log.get("load_id") or "",
                "origin": origin,
                "destination": destination,
                "agreed_price": log.get("agreed_price"),
                "negotiation_rounds": log.get("negotiation_rounds") or 0,
            })

            agreed = _to_float(log.get("agreed_price"))
            loadboard = _to_float(log.get("loadboard_rate"))

            if agreed is not None:
                cost_by_date[date_key] += agreed
                if date_key >= week_start_str:
                    cost_wtd += agreed

            if agreed is not None and loadboard is not None and loadboard > 0:
                negotiation_details.append({
                    "loadboard_rate": round(loadboard, 2),
                    "agreed_price": round(agreed, 2),
                })
                discount = (1 - agreed / loadboard) * 100
                discounts.append(discount)
                if loadboard > agreed:
                    saving = loadboard - agreed
                    total_savings += saving
                    savings_by_date[date_key] += saving

        rounds = log.get("negotiation_rounds") or 0
        if rounds:
            neg_rounds.append(rounds)

        date_counts[date_key] += 1
        date_outcome_counts[date_key][outcome] += 1

    booked = outcome_counts.get("booked", 0)
    booking_rate = (booked / total * 100) if total else 0.0

    call_funnel = [
        {"stage": "Incoming", "count": total},
        {"stage": "Authorized", "count": funnel_authorized},
        {"stage": "Matched", "count": funnel_matched},
        {"stage": "Booked", "count": booked},
    ]

    top_lanes = sorted(lane_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_lanes_list = [{"lane": lane, "count": count} for lane, count in top_lanes]

    all_outcomes = sorted(outcome_counts.keys())
    call_volume_list = []
    for d in sorted(date_counts.keys()):
        entry = {"date": d, "count": date_counts[d]}
        for oc in all_outcomes:
            entry[oc] = date_outcome_counts.get(d, {}).get(oc, 0)
        call_volume_list.append(entry)

    booked_routes_list = [
        {"origin": o, "destination": d, "count": c}
        for (o, d), c in sorted(booked_route_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    recent_bookings.sort(key=lambda x: x["timestamp"], reverse=True)

    cost_over_time_list = [
        {"date": d, "cost": round(c, 2)} for d, c in sorted(cost_by_date.items())
    ]

    cumulative = 0.0
    savings_over_time_list = []
    for d in sorted(savings_by_date.keys()):
        cumulative += savings_by_date[d]
        savings_over_time_list.append({"date": d, "savings": round(cumulative, 2)})

    return {
        "total_calls": total,
        "total_bookings": booked,
        "total_minutes": 0.0,
        "total_savings": round(total_savings, 2),
        "cost_wtd": round(cost_wtd, 2),
        "calls_by_outcome": dict(outcome_counts),
        "booking_rate": round(booking_rate, 1),
        "avg_negotiation_rounds": round(sum(neg_rounds) / len(neg_rounds), 1) if neg_rounds else 0.0,
        "avg_discount_pct": round(sum(discounts) / len(discounts), 1) if discounts else 0.0,
        "sentiment_distribution": dict(sentiment_counts),
        "sentiment_by_outcome": {k: dict(v) for k, v in sentiment_by_outcome.items()},
        "call_funnel": call_funnel,
        "negotiation_details": negotiation_details,
        "top_lanes": top_lanes_list,
        "loads_utilization": {"total_loads": 0, "booked": booked},
        "call_volume_over_time": call_volume_list,
        "savings_over_time": savings_over_time_list,
        "cost_over_time": cost_over_time_list,
        "booked_routes": booked_routes_list,
        "recent_bookings": recent_bookings[:20],
    }


def _empty_metrics():
    return {
        "total_calls": 0, "total_bookings": 0, "total_minutes": 0.0,
        "total_savings": 0.0, "cost_wtd": 0.0, "calls_by_outcome": {},
        "booking_rate": 0.0, "avg_negotiation_rounds": 0.0, "avg_discount_pct": 0.0,
        "sentiment_distribution": {}, "sentiment_by_outcome": {}, "call_funnel": [],
        "negotiation_details": [], "top_lanes": [],
        "loads_utilization": {"total_loads": 0, "booked": 0},
        "call_volume_over_time": [], "savings_over_time": [], "cost_over_time": [],
        "booked_routes": [], "recent_bookings": [],
    }


def handler(event, context):
    try:
        logs = _fetch_calls_log()
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError) as exc:
        return error_response(502, f"no se pudo leer calls_log de Twin: {exc}")

    return response(200, _compute_metrics(logs))