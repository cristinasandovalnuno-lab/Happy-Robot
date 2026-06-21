"""POST /negotiate
Body: {"load_id": "LD0000045821", "carrier_offer": 2300, "round": 1}

Decide si aceptar, contraofertar o rechazar la oferta del carrier para un
load, sin revelar nunca max_rate (campo MAX_BUY del TMS) al caller. La
decisión vive enteramente en el servidor - el agente de voz solo ve
"accept" / "counter" + counter_offer / "reject", nunca la cifra del techo
en sí. Ver common/negotiation.py para la lógica de decisión pura.

Si este token/load no expone MAX_BUY, fallamos de forma segura (422) en
vez de aceptar a ciegas - nunca "fail open" en algo que controla cuánto
paga la brokerage.
"""
import json
from decimal import Decimal, InvalidOperation

from common.config import get_tms_client
from common.http import response, error_response
from common.tms_faults import TMSError, TMSProtocolError
from common.negotiation import decide


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return error_response(400, "el body debe ser JSON válido")

    load_id = body.get("load_id")
    carrier_offer = body.get("carrier_offer")
    round_num = body.get("round")

    if not load_id or carrier_offer is None or round_num is None:
        return error_response(400, "load_id, carrier_offer y round son requeridos")

    try:
        round_num = int(round_num)
        carrier_offer = Decimal(str(carrier_offer))
    except (ValueError, TypeError, InvalidOperation):
        return error_response(400, "round debe ser entero y carrier_offer numérico")

    client = get_tms_client()
    try:
        record = client.load_get(load_id)
    except TMSProtocolError as exc:
        status = 404 if exc.code == "UNKNOWN_LOAD" else 502
        return error_response(status, f"{exc.code}: {exc.message}")
    except TMSError as exc:
        return error_response(503, f"TMS no disponible: {exc}")

    max_buy_raw = record.get("MAX_BUY")
    if not max_buy_raw:
        return error_response(
            422,
            "no se puede evaluar la oferta: este token no expone max_rate para este load",
        )

    result = decide(carrier_offer, Decimal(max_buy_raw), round_num)
    return response(200, result)
