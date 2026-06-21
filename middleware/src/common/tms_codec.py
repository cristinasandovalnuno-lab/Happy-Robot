"""Encode/decode a nivel de wire para el protocolo de líneas del Legacy TMS.

Spec: ASCII, terminado en \r\n, pares KEY:VALUE separados por '|'.
Este módulo no sabe nada de la semántica del TMS (comandos, significado de
los campos) - solo convierte dicts de Python en líneas de request y bytes
crudos en dicts / señales de fallo.
"""
from __future__ import annotations

MAX_FRAME_SIZE = 4096
TERMINATOR = "\r\n"


def encode_request(cmd: str, auth: str, fields: dict) -> bytes:
    """Construye la línea de request. CMD y AUTH siempre van primero, en
    ese orden, según el spec. Lanza ValueError si algún valor contiene un
    carácter prohibido (| o CRLF)."""
    parts = [f"CMD:{cmd}", f"AUTH:{auth}"]
    for key, value in fields.items():
        value = str(value)
        if "|" in value or "\r" in value or "\n" in value:
            raise ValueError(f"el campo {key!r} contiene un carácter prohibido (| o CRLF)")
        parts.append(f"{key.upper()}:{value}")

    line = "|".join(parts) + TERMINATOR
    encoded = line.encode("ascii")
    if len(encoded) > MAX_FRAME_SIZE:
        raise ValueError(f"el frame de request excede {MAX_FRAME_SIZE} bytes ({len(encoded)})")
    return encoded


def parse_line(line: str) -> dict:
    """Parsea una línea KEY:VALUE|KEY:VALUE... a un dict.

    Los valores se recortan por la derecha: los campos de ancho fijo se
    rellenan con espacios a la derecha según el spec, y recortar es el
    comportamiento documentado como seguro (NOTES en blanco colapsa a "").

    Algunas líneas de respuesta llevan un token "tag" inicial sin
    KEY:VALUE, antes de los pares normales - p.ej. la respuesta de
    DEBUG_ECHO es "ECHO|AUTH:OK|FIELDS_PARSED:3|MSG:HELLO" (igual que ERR
    antepone "ERR|" antes de CODE:/MSG:). Ese primer segmento se guarda
    bajo la clave "_TAG" en vez de lanzar error.

    Lanza ValueError si CUALQUIER OTRO segmento (no el primero) no es un
    par KEY:VALUE - esa sí es la señal real de la categoría de fallo
    'malformed response'.
    """
    fields = {}
    segments = line.split("|")
    for index, segment in enumerate(segments):
        if ":" not in segment:
            if index == 0 and len(segments) > 1:
                fields["_TAG"] = segment
                continue
            raise ValueError(f"segmento sin separador ':': {segment!r}")
        key, _, value = segment.partition(":")
        if not key:
            raise ValueError(f"clave vacía en segmento: {segment!r}")
        fields[key] = value.rstrip(" ")
    return fields


def is_error_line(line: str) -> bool:
    return line.startswith("ERR|") or line == "ERR"


def is_terminator_line(line: str) -> bool:
    return line == "END"
