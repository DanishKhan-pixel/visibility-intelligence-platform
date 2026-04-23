from app.utils.json_parser import safe_json_parse


def test_safe_json_parse_strict():
    assert safe_json_parse('{"a":1}') == {"a": 1}


def test_safe_json_parse_extracts_array():
    txt = "blah\n[{\"query_text\":\"x\"}]\nblah"
    assert safe_json_parse(txt) == [{"query_text": "x"}]


def test_safe_json_parse_failure_returns_empty_list():
    assert safe_json_parse("not json") == []

