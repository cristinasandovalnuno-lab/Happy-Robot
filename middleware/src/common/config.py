"""Lee la configuración (host/puerto/tokens) desde variables de entorno de
la Lambda. Nunca hardcodear secretos en este módulo - se inyectan vía
template.yaml -> Environment Variables.
"""
import os


def get_tms_client():
    from .tms_client import TMSClient
    return TMSClient(
        host=os.environ["TMS_HOST"],
        port=int(os.environ["TMS_PORT"]),
        auth_token=os.environ["TMS_AUTH_TOKEN"],
    )


def get_fmcsa_client():
    """FMCSA_MODE controla si se usa la API real o el cliente mock.
    Default "live": confirmado que la API real funciona en producción
    (AWS, no redes residenciales - ver TESTING.md). El mock queda como
    fallback documentado, no como default.
    """
    mode = os.environ.get("FMCSA_MODE", "live").strip().lower()
    if mode == "mock":
        from .fmcsa_mock_client import MockFMCSAClient
        return MockFMCSAClient()

    from .fmcsa_client import FMCSAClient
    return FMCSAClient(api_key=os.environ["FMCSA_API_KEY"])
