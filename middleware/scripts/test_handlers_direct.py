#!/usr/bin/env python3
"""Invoca los handlers de Lambda directamente, como funciones de Python
normales - SIN Docker, SIN SAM local, SIN AWS. Útil para iterar rápido;
no es 100% fiel al runtime real de Lambda (eso lo da `sam local invoke`),
pero para nuestro código (puro stdlib, sin dependencias) es equivalente.

Uso (con tus variables de entorno de TMS ya seteadas):

    python scripts/test_handlers_direct.py

"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import verify_carrier.app as verify_carrier_app
import search_loads.app as search_loads_app
import get_load.app as get_load_app
import book_load.app as book_load_app
import negotiate.app as negotiate_app


def load_event(name):
    with open(ROOT / "events" / name, encoding="utf-8") as f:
        return json.load(f)


def run(label, handler, event_file):
    print(f"\n== {label} ==")
    event = load_event(event_file)
    result = handler(event, None)
    print("status:", result["statusCode"])
    print("body:", json.loads(result["body"]))


if __name__ == "__main__":
    run("verify_carrier", verify_carrier_app.handler, "verify_carrier_event.json")
    run("search_loads", search_loads_app.handler, "search_loads_event.json")
    run("get_load", get_load_app.handler, "get_load_event.json")
    run("book_load", book_load_app.handler, "book_load_event.json")
    run("negotiate", negotiate_app.handler, "negotiate_event.json")
