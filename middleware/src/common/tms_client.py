"""Cliente TCP para el Legacy TMS.

Implementa:
  - una conexión nueva por request (el spec dice que la reutilización de
    conexión no está soportada)
  - timeout de lectura explícito -> TMSTimeoutFault
  - detección explícita del fallo 'partial response' (el socket se cierra
    antes de END/ERR) -> TMSPartialResponseFault
  - detección explícita de líneas mal formadas -> TMSMalformedResponseFault
  - cierre proactivo en cuanto se ve END/ERR, así nunca dependemos de (ni
    esperamos) el comportamiento de 'delayed termination' del servidor
  - un wrapper de reintentos fino para las tres categorías de fallo que son
    seguras de reintentar a ciegas en comandos de solo lectura

Deliberadamente NO reintenta LOAD_BOOK por defecto - ver book_load/app.py
para la justificación.
"""
from __future__ import annotations

import socket
import time
from dataclasses import dataclass

from .tms_codec import encode_request, parse_line, is_error_line, is_terminator_line
from .tms_faults import (
    TMSConnectionError,
    TMSTimeoutFault,
    TMSPartialResponseFault,
    TMSMalformedResponseFault,
    TMSProtocolError,
)


@dataclass
class TMSResponse:
    records: list  # list[dict] - 0+ para LOAD_QUERY, exactamente 1 para LOAD_GET/LOAD_BOOK/DEBUG_ECHO


@dataclass
class TMSClient:
    host: str
    port: int
    auth_token: str
    connect_timeout: float = 5.0
    read_timeout: float = 10.0  # bien por debajo del idle timeout de 30s del servidor

    def _send_and_receive(self, cmd: str, fields: dict) -> TMSResponse:
        request = encode_request(cmd, self.auth_token, fields)

        try:
            sock = socket.create_connection((self.host, self.port), timeout=self.connect_timeout)
        except OSError as exc:
            raise TMSConnectionError(f"no se pudo conectar a {self.host}:{self.port}: {exc}") from exc

        records: list = []
        buffer = ""
        try:
            sock.settimeout(self.read_timeout)
            sock.sendall(request)

            while True:
                try:
                    chunk = sock.recv(4096)
                except socket.timeout as exc:
                    raise TMSTimeoutFault(
                        f"sin datos en {self.read_timeout}s esperando respuesta de {cmd}"
                    ) from exc

                if chunk == b"":
                    # El servidor cerró la conexión. Si todavía no vimos
                    # END ni ERR, esto es el fallo 'partial response'.
                    raise TMSPartialResponseFault(
                        f"conexión cerrada a mitad de respuesta para {cmd}; buffer hasta ahora: {buffer!r}"
                    )

                buffer += chunk.decode("ascii", errors="strict")

                while "\r\n" in buffer:
                    line, buffer = buffer.split("\r\n", 1)

                    if is_error_line(line):
                        try:
                            err_fields = parse_line(line[len("ERR|"):]) if line.startswith("ERR|") else {}
                        except ValueError as exc:
                            raise TMSMalformedResponseFault(f"línea ERR mal formada: {line!r}") from exc
                        raise TMSProtocolError(
                            code=err_fields.get("CODE", "UNKNOWN"),
                            message=err_fields.get("MSG", ""),
                        )

                    if is_terminator_line(line):
                        # Éxito. Dejamos de leer ya mismo - esto es lo que
                        # nos protege de 'delayed termination': no
                        # esperamos a que el servidor cierre por su cuenta.
                        return TMSResponse(records=records)

                    try:
                        records.append(parse_line(line))
                    except ValueError as exc:
                        raise TMSMalformedResponseFault(f"línea de registro mal formada: {line!r}") from exc
        finally:
            try:
                sock.close()
            except OSError:
                pass

    def call(self, cmd: str, fields: dict, *, retries: int = 0, backoff: float = 0.5) -> TMSResponse:
        """Envía un request, reintentando opcionalmente fallos transitorios.

        retries=0 significa sin reintento (usado por defecto en LOAD_BOOK).
        Cada reintento abre una conexión nueva, según el spec.
        """
        attempt = 0
        while True:
            try:
                return self._send_and_receive(cmd, fields)
            except (TMSTimeoutFault, TMSPartialResponseFault, TMSMalformedResponseFault):
                attempt += 1
                if attempt > retries:
                    raise
                time.sleep(backoff * attempt)

    # Wrappers de conveniencia -----------------------------------------

    def load_query(self, filters: dict, max_results=None, retries: int = 2) -> list:
        fields = dict(filters)
        if max_results is not None:
            fields["MAX_RESULTS"] = max_results
        return self.call("LOAD_QUERY", fields, retries=retries).records

    def load_get(self, load_id: str, retries: int = 2) -> dict:
        resp = self.call("LOAD_GET", {"LOAD_ID": load_id}, retries=retries)
        return resp.records[0] if resp.records else {}

    def load_book(self, load_id: str, mc_num: str, agreed_rate, retries: int = 0) -> dict:
        resp = self.call(
            "LOAD_BOOK",
            {"LOAD_ID": load_id, "MC_NUM": mc_num, "AGREED_RATE": agreed_rate},
            retries=retries,
        )
        return resp.records[0] if resp.records else {}

    def debug_echo(self, msg: str) -> dict:
        # Bypassa fault injection según el spec - útil para confirmar
        # framing/auth sin la inestabilidad del path operacional.
        resp = self.call("DEBUG_ECHO", {"MSG": msg}, retries=0)
        return resp.records[0] if resp.records else {}
