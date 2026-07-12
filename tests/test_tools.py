"""
tests/test_tools.py

Unit tests verifying JSON parse, repair, and input trim functions.
"""
"""
tests/test_tools.py
Unit tests for tools.py helper functions (_trim, _parse_json, _repair_json).
These test pure functions — no Gemini API calls.
"""

import sys
import os
import json

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import _trim, _parse_json, _repair_json


class TestTrim:
    def test_short_text_unchanged(self):
        assert _trim("hello", 100) == "hello"

    def test_exact_length_unchanged(self):
        text = "a" * 50
        assert _trim(text, 50) == text

    def test_long_text_truncated(self):
        text = "a" * 100
        result = _trim(text, 50)
        assert len(result) > 50  # includes truncation note
        assert result.startswith("a" * 50)
        assert "[...truncated" in result

    def test_empty_string(self):
        assert _trim("", 100) == ""


class TestParseJson:
    def test_valid_json(self):
        result = _parse_json('{"name": "Alice", "score": 85}')
        assert result["name"] == "Alice"
        assert result["score"] == 85

    def test_json_with_markdown_fences(self):
        raw = '```json\n{"key": "value"}\n```'
        result = _parse_json(raw)
        assert result["key"] == "value"

    def test_json_with_bare_fences(self):
        raw = '```\n{"key": "value"}\n```'
        result = _parse_json(raw)
        assert result["key"] == "value"

    def test_json_embedded_in_text(self):
        raw = 'Here is the result: {"score": 90} end of response'
        result = _parse_json(raw)
        assert result["score"] == 90

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Empty response"):
            _parse_json("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="Empty response"):
            _parse_json("   \n  ")

    def test_no_json_raises(self):
        with pytest.raises(ValueError, match="No JSON found"):
            _parse_json("This is just plain text without any braces")

    def test_nested_json(self):
        raw = json.dumps({"outer": {"inner": [1, 2, 3]}})
        result = _parse_json(raw)
        assert result["outer"]["inner"] == [1, 2, 3]


class TestRepairJson:
    def test_complete_json_unchanged(self):
        text = '{"key": "value"}'
        result = _repair_json(text)
        assert json.loads(result) == {"key": "value"}

    def test_repairs_unclosed_brace(self):
        text = '{"key": "value"'
        result = _repair_json(text)
        parsed = json.loads(result)
        assert parsed["key"] == "value"

    def test_repairs_unclosed_string(self):
        text = '{"key": "val'
        result = _repair_json(text)
        assert result.endswith("}")

    def test_repairs_unclosed_array(self):
        text = '{"items": [1, 2, 3'
        result = _repair_json(text)
        parsed = json.loads(result)
        assert parsed["items"] == [1, 2, 3]
