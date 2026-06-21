"""GET /loads/{load_id}

Devuelve el registro completo del load. max_rate (expuesto como MAX_BUY en
algunos tokens) se elimina antes de que la respuesta salga de esta
función - el agente que habla con el carrier nunca debe verlo, ni directa
ni indirectamente.
"""
from common.config import get_tms_client
from common.http import response, error_response
from common.tms_faults import TMSError, TMSProtocolError


def handler(event, context):
    load_id = (event.get("pathParameters") or {}).get("load_id")
    if not load_id:
        return error_response(400, "load_id es requerido")

    client = get_tms_client()
    try:
        record = client.load_get(load_id)
    except TMSProtocolError as exc:
        status = 404 if exc.code == "UNKNOWN_LOAD" else 502
        return error_response(status, f"{exc.code}: {exc.message}")
    except TMSError as exc:
        return error_response(503, f"TMS no disponible: {exc}")

    record.pop("MAX_BUY", None)
    return response(200, record)
