"""POST /loads/{load_id}/book
Body: {"mc_number": "872144", "agreed_rate": 2200}

LOAD_BOOK NO se reintenta automáticamente. Si el TMS falla a mitad de
request no podemos saber si la reserva ya se aplicó del lado del servidor
antes del fallo. Reintentar a ciegas arriesga: (a) enmascarar un fallo real
como ALREADY_BOOKED, o (b) duplicar el efecto de una reserva. En su lugar:

  1. Se intenta una sola vez.
  2. Ante un fallo transitorio (timeout/partial/malformed) devolvemos un
     502/503 y dejamos que el caller (el flujo del agente de voz) decida
     si reintentar, comunicando al carrier que su reserva está "pendiente
     de confirmación", no confirmada.
  3. Si un reintento posterior del caller devuelve ALREADY_BOOKED, lo
     tratamos como señal de éxito (este token ya tiene una reserva sobre
     este load) pero lo registramos distinto de un BOOKED limpio, porque
     no tenemos el BOOKING_REF original.

Esto es una decisión de diseño deliberada, no un descuido - documentarla
en el build description doc del challenge.
"""
import json

from common.config import get_tms_client
from common.http import response, error_response
from common.tms_faults import TMSError, TMSProtocolError


def handler(event, context):
    load_id = (event.get("pathParameters") or {}).get("load_id")
    if not load_id:
        return error_response(400, "load_id es requerido")

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return error_response(400, "el body debe ser JSON válido")

    mc_number = body.get("mc_number")
    agreed_rate = body.get("agreed_rate")
    if not mc_number or agreed_rate is None:
        return error_response(400, "mc_number y agreed_rate son requeridos")

    client = get_tms_client()
    try:
        record = client.load_book(load_id, mc_number, agreed_rate, retries=0)
    except TMSProtocolError as exc:
        if exc.code == "ALREADY_BOOKED":
            return response(200, {
                "load_id": load_id,
                "status": "ALREADY_BOOKED",
                "note": "este token ya tiene una reserva sobre este load",
            })
        status = {"UNKNOWN_LOAD": 404, "INVALID_RATE": 422, "MISSING_FIELD": 400}.get(exc.code, 502)
        return error_response(status, f"{exc.code}: {exc.message}")
    except TMSError as exc:
        return error_response(503, f"TMS no disponible, reserva no confirmada: {exc}")

    return response(200, record)
