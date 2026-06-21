"""Cliente delgado para la QCMobile API de FMCSA - usado en el paso de
verificación de autoridad del carrier (paso 2 del proceso inbound).

Endpoint (FMCSA Developer docs, mobile.fmcsa.dot.gov):
  GET /qc/services/carriers/docket-number/{mcNumber}?webKey=<key>

Confirmado funcionando en producción (no desde redes residenciales - ver
notas en TESTING.md sobre el bloqueo de IP que afecta a conexiones desde
casa pero no a infraestructura cloud como AWS Lambda o AWS CloudShell).

Campos reales observados en la respuesta (no todos los que suele
documentarse genéricamente para esta API):
  allowedToOperate, commonAuthorityStatus, contractAuthorityStatus,
  brokerAuthorityStatus, statusCode, oosDate, legalName, dotNumber, etc.
NO existe un campo "outOfService" como tal - el indicador real de una
orden de out-of-service activa es oosDate (no nulo si está OOS).
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
import urllib.error

BASE_URL = "https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/"


class FMCSAError(Exception):
    pass


class FMCSAClient:
    def __init__(self, api_key: str, timeout: float = 8.0):
        self.api_key = api_key
        self.timeout = timeout

    def lookup_by_mc(self, mc_number: str) -> dict:
        mc_number = str(mc_number).strip().upper()
        if mc_number.startswith("MC"):
            mc_number = mc_number[2:].strip().lstrip("-").strip()

        url = f"{BASE_URL}{urllib.parse.quote(mc_number)}?webKey={urllib.parse.quote(self.api_key)}"

        # mobile.fmcsa.dot.gov está detrás de un WAF que bloquea con 403
        # el User-Agent por defecto de urllib ("Python-urllib/x.y"), incluso
        # con un webKey válido. Mandamos un UA y un Accept normales.
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; HappyRobotMiddleware/1.0)",
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = ""
            raise FMCSAError(f"FMCSA devolvió HTTP {exc.code}: {detail or '(sin cuerpo de respuesta)'}") from exc
        except urllib.error.URLError as exc:
            raise FMCSAError(f"no se pudo alcanzar la API de FMCSA: {exc.reason}") from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise FMCSAError("FMCSA devolvió una respuesta que no es JSON") from exc

        return payload

    @staticmethod
    def extract_carrier(payload: dict):
        """El endpoint docket-number envuelve los resultados en una lista
        'content' de objetos {"carrier": {...}}. Normalizamos a un único
        dict de carrier (o None si no hay resultados)."""
        content = payload.get("content")
        if not content:
            return None
        first = content[0] if isinstance(content, list) else content
        return first.get("carrier", first)

    def verify_authority(self, mc_number: str) -> dict:
        """Devuelve un resultado de verificación normalizado:
          {"verified": bool, "reason": str, "carrier": <dict crudo o None>}
        """
        payload = self.lookup_by_mc(mc_number)
        carrier = self.extract_carrier(payload)

        if carrier is None:
            return {"verified": False, "reason": "MC number no encontrado en FMCSA", "carrier": None}

        allowed = str(carrier.get("allowedToOperate", "")).upper() == "Y"
        has_active_oos_order = bool(carrier.get("oosDate"))

        if has_active_oos_order:
            return {"verified": False, "reason": "el carrier tiene una orden de out-of-service activa", "carrier": carrier}
        if not allowed:
            return {"verified": False, "reason": "el carrier no tiene autoridad activa para operar", "carrier": carrier}

        return {"verified": True, "reason": "autoridad activa", "carrier": carrier}
