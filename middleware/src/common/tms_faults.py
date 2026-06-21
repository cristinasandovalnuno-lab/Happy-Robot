"""Excepciones que mapean 1:1 con las categorías de fallo descritas en el
protocolo del Legacy TMS. Separar esto de tms_client.py hace que el resto
del código (handlers de Lambda) pueda razonar sobre fallos sin conocer
nada del wire protocol.
"""


class TMSError(Exception):
    """Clase base para todo error relacionado con el TMS."""


class TMSProtocolError(TMSError):
    """El servidor devolvió un ERR bien formado (AUTH_FAILED, UNKNOWN_LOAD, etc.)."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class TMSTimeoutFault(TMSError):
    """No llegó ningún byte antes del timeout configurado.
    Corresponde a la categoría 'Timeout' del spec."""


class TMSPartialResponseFault(TMSError):
    """La conexión se cerró antes de ver un terminador END o ERR.
    Corresponde a la categoría 'Partial response' del spec."""


class TMSMalformedResponseFault(TMSError):
    """Una línea no se pudo parsear como pares KEY:VALUE, o violó las
    reglas de framing. Corresponde a la categoría 'Malformed response'."""


class TMSConnectionError(TMSError):
    """No se pudo abrir la conexión TCP en absoluto (DNS, conexión rechazada, etc.)."""
