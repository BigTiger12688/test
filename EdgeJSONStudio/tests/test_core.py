"""核心模块单元测试样例。"""
from __future__ import annotations

from pathlib import Path

import pytest

from core import converter, diff, parser, query


def test_parse_standard(tmp_path):
    path = tmp_path / "data.json"
    path.write_text('{"a": 1, "b": 2}', encoding="utf-8")
    data, log = parser.parse_json_stream(path, strict=True)
    assert data["a"] == 1
    assert "标准" in log[0]


def test_diff_change():
    result = diff.diff({"a": 1}, {"a": 2})
    assert result[0].change_type == "change"
    assert result[0].value_b == 2


def test_jsonpath_query():
    data = {"items": [{"value": 1}, {"value": 2}]}
    try:
        values = query.query_jsonpath(data, "$.items[*].value")
    except RuntimeError as exc:
        pytest.skip(str(exc))
    else:
        assert values == [1, 2]


def test_converter_base64_roundtrip():
    text = "EdgeJSON"
    encoded = converter.base64_encode(text)
    decoded = converter.base64_decode(encoded)
    assert decoded == text
