#!/usr/bin/env python3
"""Prueba de la API key de FMCSA - SIN AWS, SIN Lambda.

Uso:
    python scripts/test_fmcsa_key.py [MC_NUMBER]

Confirmado (ver TESTING.md) que la API real de FMCSA funciona desde
infraestructura cloud (AWS) pero da 403 desde muchas redes residenciales
- si corres este script desde tu propia red y te da 403, no es
necesariamente un problema de la key, puede ser tu IP. FMCSA_MODE=mock
usa el cliente simulado en su lugar.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

API_KEY = os.environ.get("FMCSA_API_KEY", "cdc33e44d693a3a58451898d4ec9df862c65b954")
MODE = os.environ.get("FMCSA_MODE", "live").strip().lower()


def main():
    mc_number = sys.argv[1] if len(sys.argv) > 1 else "872144"

    if MODE == "mock":
        from common.fmcsa_mock_client import MockFMCSAClient
        client = MockFMCSAClient()
        print(f"--> (MOCK) buscando MC {mc_number}")
        result = client.verify_authority(mc_number)
    else:
        from common.fmcsa_client import FMCSAClient, FMCSAError
        client = FMCSAClient(api_key=API_KEY)
        print(f"--> buscando MC {mc_number}")
        try:
            result = client.verify_authority(mc_number)
        except FMCSAError as exc:
            print("FALLÓ:", exc)
            print("\nSi esto falla desde tu red local pero funcionó en AWS CloudShell,")
            print("es muy probablemente un bloqueo de IP residencial, no la key.")
            print("Para seguir trabajando sin depender de eso:")
            print("  $env:FMCSA_MODE = 'mock'  (PowerShell)  /  export FMCSA_MODE=mock  (bash)")
            return

    print("verified:", result["verified"])
    print("reason:", result["reason"])
    if result["carrier"]:
        c = result["carrier"]
        print("legalName:", c.get("legalName"))
        print("allowedToOperate:", c.get("allowedToOperate"))
        print("oosDate:", c.get("oosDate"))


if __name__ == "__main__":
    main()
