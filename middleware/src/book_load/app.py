"""POST /loads/{load_id}/book
Body: {"mc_number": "872144", "agreed_rate": 2200}

LOAD_BOOK NO se reintenta automáticamente. Si el TMS falla a mitad de
request no podemos saber si la reserva ya se aplicó del lado del servidor
antes del fallo. Reintentar el BOOK a ciegas arriesga duplicar el efecto
de una reserva. En su lugar, ante un fallo transitorio:

  1. Se intenta el BOOK una sola vez.
  2. Si falla con un error transitorio (timeout/partial/malformed - no
     un error de protocolo claro), hacemos UNA lectura de solo consulta
     (LOAD_GET, que nunca muta nada) sobre el mismo load_id, para ver si
     la reserva se aplicó igualmente del lado del TMS antes de que la
     respuesta se cayera.
  3. Si esa lectura muestra el load ya no como OPEN y el MC number en el
     registro coincide con el de esta request, lo confirmamos como
     reservado con confianza (status BOOKED_CONFIRMED_VIA_READBACK).
  4. Si el load ya no está OPEN pero no podemos confirmar que el MC
     number coincide (el campo no viene en la respuesta de lectura, o es
     de otro carrier), NO afirmamos éxito a ciegas - devolvemos un status
     distinto (POSSIBLY_BOOKED_UNCONFIRMED) con el registro real adjunto,
     para que el agente no le confirme al carrier algo que no es seguro.
  5. Si la lectura de verificación también falla, o el load sigue OPEN,
     devolvemos el 503 original sin más - la reserva genuinamente no se
     pudo confirmar.

Esto es una decisión de diseño deliberada, no un descuido - documentada
en el build description doc del challenge.
"""
import json

from common.config import get_tms_client
from common.http import response, error_response
from common.tms_faults import TMSError, TMSProtocolError


def _try_confirm_via_readback(client, load_id, mc_number):
    """Best-effort, solo lectura. Devuelve un dict de respuesta si logra
    decir algo útil, o None si no puede confirmar nada (el caller debe
    caer entonces al 503 original)."""
    try:
        record = client.load_get(load_id)
    except (TMSError, TMSProtocolError):
        return None

    record.pop("MAX_BUY", None)
    status = record.get("STATUS", "")
    if status == "OPEN" or not status:
        return None

    record_mc = record.get("MC_NUM") or record.get("MC_NUMBER")
    if record_mc is not None and str(record_mc) == str(mc_number):
        return response(200, {
            "load_id": load_id,
            "status": "BOOKED_CONFIRMED_VIA_READBACK",
            "note": "el BOOK original devolvió un error transitorio, pero una lectura de verificación confirma que la reserva sí se aplicó con este mismo mc_number",
            "record": record,
        })

    return response(200, {
        "load_id": load_id,
        "status": "POSSIBLY_BOOKED_UNCONFIRMED",
        "note": "el load ya no aparece como OPEN, pero no se pudo confirmar que el mc_number coincide con esta request - no asumir que la reserva es de este carrier",
        "record": record,
    })


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
        confirmed = _try_confirm_via_readback(client, load_id, mc_number)
        if confirmed is not None:
            return confirmed
        return error_response(503, f"TMS no disponible, reserva no confirmada: {exc}")

    return response(200, record)