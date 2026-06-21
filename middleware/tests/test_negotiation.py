import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from common.negotiation import decide


def test_accept_when_offer_at_or_below_max_rate():
    assert decide(Decimal("1900"), Decimal("1950"), 1) == {"decision": "accept"}
    assert decide(Decimal("1950"), Decimal("1950"), 1) == {"decision": "accept"}


def test_counter_never_exceeds_max_rate():
    result = decide(Decimal("3000"), Decimal("1950"), 1)
    assert result["decision"] == "counter"
    assert result["counter_offer"] <= 1950


def test_round_3_rejects_if_still_above_ceiling():
    result = decide(Decimal("2100"), Decimal("1950"), 3)
    assert result == {"decision": "reject"}


def test_round_3_accepts_if_offer_at_ceiling():
    result = decide(Decimal("1950"), Decimal("1950"), 3)
    assert result == {"decision": "accept"}


def test_concession_increases_toward_ceiling_across_rounds():
    max_rate = Decimal("2000")
    offer = Decimal("5000")  # muy por encima, fuerza counter en rondas 1 y 2
    r1 = decide(offer, max_rate, 1)
    r2 = decide(offer, max_rate, 2)
    assert r1["decision"] == "counter" and r2["decision"] == "counter"
    assert r1["counter_offer"] < r2["counter_offer"] <= 2000


def test_invalid_round_rejects():
    assert decide(Decimal("1000"), Decimal("1950"), 4) == {"decision": "reject"}
    assert decide(Decimal("1000"), Decimal("1950"), 0) == {"decision": "reject"}


def test_max_rate_never_leaks_into_result():
    cases = [
        decide(Decimal("1900"), Decimal("1950"), 1),
        decide(Decimal("3000"), Decimal("1950"), 1),
        decide(Decimal("2100"), Decimal("1950"), 3),
    ]
    for result in cases:
        assert "max_rate" not in result
        assert "1950" not in json.dumps(result)
