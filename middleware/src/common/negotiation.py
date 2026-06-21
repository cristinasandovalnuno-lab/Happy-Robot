"""Lógica pura de decisión de negociación - sin red, sin TMS, fácil de
testear (ver tests/test_negotiation.py). El handler de negotiate/app.py
se encarga de obtener max_rate del TMS y llamar a decide().

Reglas (challenge spec):
  - max_rate es el techo absoluto que la brokerage no excede - nunca se
    devuelve en el resultado, solo se usa internamente para calcular
    accept/counter/reject y el counter_offer.
  - Hasta 3 rondas. Si no hay acuerdo tras la ronda 3, se rechaza.

Estrategia de concesión: en vez de contraofertar siempre exactamente al
techo (lo cual también sería válido y más simple - "hold the line"), nos
acercamos gradualmente a max_rate en cada ronda para que la negociación
se sienta real, sin arriesgarnos nunca a superarlo. La ronda 3 es siempre
una oferta firme al 100% del techo.
"""
from decimal import Decimal, ROUND_HALF_UP

MAX_ROUNDS = 3

ROUND_CONCESSION = {1: Decimal("0.95"), 2: Decimal("0.98"), 3: Decimal("1.00")}


def _round_money(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_HALF_UP))


def decide(carrier_offer: Decimal, max_rate: Decimal, round_num: int) -> dict:
    """Devuelve uno de:
      {"decision": "accept"}
      {"decision": "counter", "counter_offer": <int>}
      {"decision": "reject"}

    max_rate NUNCA aparece en el dict devuelto.
    """
    if round_num < 1 or round_num > MAX_ROUNDS:
        return {"decision": "reject"}

    if carrier_offer <= max_rate:
        return {"decision": "accept"}

    if round_num >= MAX_ROUNDS:
        return {"decision": "reject"}

    concession = ROUND_CONCESSION.get(round_num, Decimal("1.00"))
    counter_offer = _round_money(max_rate * concession)
    # Nunca contraofertar por encima del techo, ni por encima de lo que el
    # carrier ya pidió.
    counter_offer = min(counter_offer, _round_money(max_rate), int(carrier_offer))

    return {"decision": "counter", "counter_offer": counter_offer}
