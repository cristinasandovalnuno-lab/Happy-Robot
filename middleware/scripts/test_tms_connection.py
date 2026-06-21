#!/usr/bin/env python3
"""Prueba de conectividad contra el Legacy TMS real - SIN AWS, SIN Lambda,
SIN HappyRobot. Solo Python estándar + el codec/cliente de src/common.

Uso:
    python scripts/test_tms_connection.py

Lee host/puerto/token de variables de entorno (ver .env.example). Si no
están seteadas, usa los valores que vinieron con el challenge como
default, solo para esta prueba rápida.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from common.tms_client import TMSClient  # noqa: E402
from common.tms_faults import TMSError  # noqa: E402

HOST = os.environ.get("TMS_HOST", "tramway.proxy.rlwy.net")
PORT = int(os.environ.get("TMS_PORT", "17159"))
TOKEN = os.environ.get("TMS_AUTH_TOKEN", "hr-fde-cristinasandoval-2026")


def main():
    client = TMSClient(host=HOST, port=PORT, auth_token=TOKEN)
    print(f"--> conectando a {HOST}:{PORT}")

    print("\n[1] DEBUG_ECHO (bypassa fault injection - confirma framing/auth)")
    try:
        echo = client.debug_echo("hello-from-test-script")
        print("    OK:", echo)
    except TMSError as exc:
        print("    FALLÓ:", exc)
        print("    Detente aquí - arregla auth/conectividad antes de probar comandos operacionales.")
        return

    print("\n[2] LOAD_QUERY (GA -> TX, dry van)")
    loads = []
    try:
        loads = client.load_query(
            {"ORIG_STATE": "GA", "DEST_STATE": "TX", "EQTYPE": "DRY_VAN"}, max_results=5
        )
        print(f"    OK: {len(loads)} load(s)")
        for load in loads:
            print(
                "     -",
                load.get("LOAD_ID"),
                load.get("ORIG_CITY", "").strip(),
                "->",
                load.get("DEST_CITY", "").strip(),
                "rate:", load.get("RATE"),
            )
    except TMSError as exc:
        print("    FALLÓ:", exc)

    if not loads:
        print("\nNo hay loads para continuar con LOAD_GET/LOAD_BOOK. Fin de la prueba.")
        return

    sample_id = loads[0]["LOAD_ID"]

    print(f"\n[3] LOAD_GET {sample_id}")
    try:
        record = client.load_get(sample_id)
        print("    OK:", record)
    except TMSError as exc:
        print("    FALLÓ:", exc)

    print(f"\n[4] LOAD_BOOK {sample_id} -- comentado a propósito, descomenta para reservar de verdad")
    # try:
    #     booking = client.load_book(sample_id, mc_num="872144", agreed_rate=2200)
    #     print("    OK:", booking)
    # except TMSError as exc:
    #     print("    FALLÓ:", exc)


if __name__ == "__main__":
    main()
