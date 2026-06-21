"""POST /loads/search
Body: {"origin_state": "GA", "destination_state": "TX", "equipment_type": "DRY_VAN", "max_results": 5}

El TMS exige al menos un filtro además de CMD/AUTH. Mapeamos un set
pequeño de nombres "amigables" a los nombres de campo del wire; extender
según se necesite.

NORMALIZACIÓN: el agente de voz puede mandar "origin_state" con un
nombre de ciudad completo ("New Orleans") en vez de una abreviatura de
2 letras ("LA"), o "equipment_type" con espacios/minúsculas ("Dry
Van"). Este handler normaliza ambos casos antes de mandar el filtro al
TMS, en vez de fallar silenciosamente con 0 resultados.

max_rate / MAX_BUY se elimina de cada registro antes de que salga de esta
función - nunca debe llegar al agente que habla con el carrier.
"""
import json
import re

from common.config import get_tms_client
from common.http import response, error_response
from common.tms_faults import TMSError, TMSProtocolError

FIELD_MAP = {
    "origin_city": "ORIG_CITY",
    "origin_state": "ORIG_STATE",
    "origin_zip": "ORIG_ZIP",
    "destination_city": "DEST_CITY",
    "destination_state": "DEST_STATE",
    "destination_zip": "DEST_ZIP",
    "equipment_type": "EQTYPE",
    "pickup_date": "PICKUP_DT",
}

# Sinónimos habituales que el agente de voz puede transcribir -> código
# canónico que usa el TMS. Ampliar esta lista si aparecen nuevos casos.
EQUIPMENT_SYNONYMS = {
    "dry van": "DRY_VAN",
    "dryvan": "DRY_VAN",
    "van": "DRY_VAN",
    "reefer": "REEFER",
    "refrigerated": "REEFER",
    "refrigerator": "REEFER",
    "flatbed": "FLATBED",
    "flat bed": "FLATBED",
}

_STATE_RE = re.compile(r"^[A-Za-z]{2}$")


def _normalize_state_or_city(field_prefix: str, value: str) -> dict:
    """Decide si `value` parece una abreviatura de estado (2 letras) o un
    nombre de ciudad, y devuelve {wire_key: value} apuntando al campo
    correcto (*_STATE o *_CITY)."""
    cleaned = value.strip()
    if _STATE_RE.match(cleaned):
        return {f"{field_prefix}_STATE": cleaned.upper()}
    return {f"{field_prefix}_CITY": cleaned}


def _normalize_equipment(value: str) -> str:
    key = value.strip().lower()
    return EQUIPMENT_SYNONYMS.get(key, value.strip().upper().replace(" ", "_"))


def _to_wire_filters(body: dict) -> dict:
    filters = {}

    origin = body.get("origin_city") or body.get("origin_state")
    if origin:
        filters.update(_normalize_state_or_city("ORIG", origin))

    destination = body.get("destination_city") or body.get("destination_state")
    if destination:
        filters.update(_normalize_state_or_city("DEST", destination))

    if body.get("origin_zip"):
        filters["ORIG_ZIP"] = body["origin_zip"]
    if body.get("destination_zip"):
        filters["DEST_ZIP"] = body["destination_zip"]
    if body.get("equipment_type"):
        filters["EQTYPE"] = _normalize_equipment(body["equipment_type"])
    if body.get("pickup_date"):
        filters["PICKUP_DT"] = body["pickup_date"]

    return filters


def _strip_sensitive(record: dict) -> dict:
    record.pop("MAX_BUY", None)
    return record


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return error_response(400, "el body debe ser JSON válido")

    filters = _to_wire_filters(body)
    if not filters:
        return error_response(
            400,
            "se requiere al menos un filtro (origin, destination, equipment, pickup date)",
        )

    client = get_tms_client()
    try:
        records = client.load_query(filters, max_results=body.get("max_results"))
    except TMSProtocolError as exc:
        return error_response(502, f"el TMS rechazó el request: {exc.code} {exc.message}")
    except TMSError as exc:
        return error_response(503, f"TMS no disponible: {exc}")

    return response(200, {"loads": [_strip_sensitive(r) for r in records]})
