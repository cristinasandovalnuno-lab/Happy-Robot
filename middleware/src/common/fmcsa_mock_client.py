"""Cliente FMCSA mock - mismo interfaz que FMCSAClient.verify_authority(),
sin red. Se mantiene como fallback documentado (FMCSA_MODE=mock) para el
manejo de fallos: si la API real de FMCSA está caída el día de una demo,
no bloquea el resto del flujo (ver "Tool/Systems Failure Handling" en el
prompt del agente). Confirmado que la API real SÍ funciona en producción
(ver TESTING.md), así que el default es "live"; el mock es solo para
contingencia, no la opción esperada.
"""

_MOCK_CARRIERS = {
    "872144": {
        "verified": True,
        "reason": "autoridad activa (MOCK)",
        "carrier": {"legalName": "Ouza Transportation Inc (MOCK)", "allowedToOperate": "Y", "mcNumber": "872144"},
    },
    "999999": {
        "verified": False,
        "reason": "MC number no encontrado en FMCSA (MOCK)",
        "carrier": None,
    },
}


class MockFMCSAClient:
    def __init__(self, *_, **__):
        pass

    def verify_authority(self, mc_number: str) -> dict:
        mc_number = str(mc_number).strip().upper().lstrip("MC").strip()
        result = _MOCK_CARRIERS.get(mc_number)
        if result is None:
            return {"verified": False, "reason": "MC number no encontrado en FMCSA (MOCK)", "carrier": None}
        return dict(result)
