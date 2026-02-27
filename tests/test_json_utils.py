import pytest

from idea_refinery.utils import JSONParseError, parse_json


def test_parse_json_with_pure_json() -> None:
    data = parse_json('{"a": 1, "b": "x"}')
    assert isinstance(data, dict)
    assert data["a"] == 1


def test_parse_json_with_wrapped_content() -> None:
    text = "Result:\n```json\n{\"name\": \"demo\"}\n```"
    data = parse_json(text)
    assert isinstance(data, dict)
    assert data["name"] == "demo"


def test_parse_json_raises_on_invalid_text() -> None:
    with pytest.raises(JSONParseError):
        parse_json("this is not json")
