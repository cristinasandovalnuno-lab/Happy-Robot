"""POST /carrier/verify
Body: {"mc_number": "872144"}

Verificación de autoridad FMCSA (paso 2 del proceso). Esta Lambda es
puramente un puente hacia la API de FMCSA - no escribe en ninguna
base de datos ni conoce Twin. Toda la captura de datos (tanto el
resultado normal de la llamada como las verificaciones fallidas)
vive 100% dentro del workflow de HappyRobot, vía nodos nativos
"Write to Twin", no en código de esta Lambda ni de ninguna otra.

El OTP tampoco lo maneja esta Lambda - eso lo hace un nodo "Read from
Twin" (consultando `carrier_roster` por el número de teléfono
registrado) + el envío de SMS nativo de la plataforma, dentro del
propio workflow.
"""
import json
import re

from common.config import get_fmcsa_client
from common.http import response, error_response
from common.fmcsa_client import FMCSAError


def _clean_mc_number(raw: str) -> str:
    """El agente de voz puede extraer el MC number con caracteres
    sueltos que el carrier dijo o que la transcripción metió de más
    (guiones, espacios, la palabra "MC"). FMCSA solo espera dígitos -
    nos quedamos solo con eso en vez de fallar."""
    return re.sub(r"\D", "", raw)


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return error_response(400, "el body debe ser JSON válido")

    mc_number = body.get("mc_number")
    if not mc_number:
        return error_response(400, "mc_number es requerido")

    mc_number = _clean_mc_number(str(mc_number))
    if not mc_number:
        return error_response(400, "mc_number debe contener al menos un dígito")

    client = get_fmcsa_client()
    try:
        result = client.verify_authority(mc_number)
    except FMCSAError as exc:
        return error_response(502, f"falló el lookup en FMCSA: {exc}")

    return response(200, result)
