import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from common.tms_codec import encode_request, parse_line, is_error_line, is_terminator_line


def test_encode_request_basic():
    raw = encode_request("LOAD_QUERY", "t-9c3a", {"ORIG_STATE": "GA", "MAX_RESULTS": 5})
    assert raw == b"CMD:LOAD_QUERY|AUTH:t-9c3a|ORIG_STATE:GA|MAX_RESULTS:5\r\n"


def test_encode_request_rejects_pipe():
    with pytest.raises(ValueError):
        encode_request("LOAD_QUERY", "t-9c3a", {"ORIG_CITY": "Atlanta|Fake"})


def test_parse_line_strips_padding():
    fields = parse_line("ORIG_CITY:Atlanta                       |ORIG_STATE:GA")
    assert fields["ORIG_CITY"] == "Atlanta"
    assert fields["ORIG_STATE"] == "GA"


def test_parse_line_blank_notes_collapses_to_empty():
    fields = parse_line("NOTES:" + " " * 40)
    assert fields["NOTES"] == ""


def test_parse_line_rejects_missing_colon():
    with pytest.raises(ValueError):
        parse_line("ORIG_CITY-Atlanta")


def test_parse_line_tolerates_leading_tag_token():
    # Respuesta real de DEBUG_ECHO (TRANSCRIPT 1 del manual del protocolo)
    fields = parse_line("ECHO|AUTH:OK|FIELDS_PARSED:3|MSG:HELLO")
    assert fields["_TAG"] == "ECHO"
    assert fields["AUTH"] == "OK"
    assert fields["FIELDS_PARSED"] == "3"
    assert fields["MSG"] == "HELLO"


def test_parse_line_still_rejects_malformed_non_leading_segment():
    # El tag inicial se tolera, pero un segmento roto más adelante sigue
    # siendo una señal real de 'malformed response'.
    with pytest.raises(ValueError):
        parse_line("ECHO|AUTH:OK|BROKEN_SEGMENT|MSG:HELLO")


def test_is_error_and_terminator_lines():
    assert is_error_line("ERR|CODE:AUTH_FAILED|MSG:invalid")
    assert not is_error_line("LOAD_ID:LD1|STATUS:OPEN")
    assert is_terminator_line("END")
    assert not is_terminator_line("ENDX")
