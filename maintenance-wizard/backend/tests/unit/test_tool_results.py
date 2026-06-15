"""ToolResult envelope, SourceRef factories, and DataTool error handling."""

from __future__ import annotations

from typing import Any, ClassVar

import pytest

from backend.app.tools.results import (
    DataTool,
    ExpectedToolError,
    SourceRef,
    ToolResult,
)

_EMPTY_PARAMS = {"type": "object", "properties": {}, "additionalProperties": False}


class _OkTool(DataTool):
    name: ClassVar[str] = "ok_tool"
    description: ClassVar[str] = "ok"
    parameters: ClassVar[dict[str, Any]] = _EMPTY_PARAMS

    def execute(self, **_: Any) -> ToolResult:
        return ToolResult(tool=self.name, data={"x": 1},
                          sources=[SourceRef.record(table="t", id="1")])


class _ExpectedFailTool(DataTool):
    name: ClassVar[str] = "fail_tool"
    description: ClassVar[str] = "fail"
    parameters: ClassVar[dict[str, Any]] = _EMPTY_PARAMS

    def execute(self, **_: Any) -> ToolResult:
        raise ExpectedToolError("not found")


class _CrashTool(DataTool):
    name: ClassVar[str] = "crash_tool"
    description: ClassVar[str] = "crash"
    parameters: ClassVar[dict[str, Any]] = _EMPTY_PARAMS

    def execute(self, **_: Any) -> ToolResult:
        raise ValueError("unexpected")


def test_ok_result_serializes_to_clean_dict():
    out = _OkTool().run()
    assert out["ok"] is True
    assert out["tool"] == "ok_tool"
    assert out["data"] == {"x": 1}
    assert out["sources"][0]["kind"] == "record"
    assert out["sources"][0]["table"] == "t"
    assert "error" not in out  # exclude_none drops it


def test_expected_error_becomes_ok_false():
    out = _ExpectedFailTool().run()
    assert out["ok"] is False
    assert out["error"] == "not found"
    assert out["tool"] == "fail_tool"


def test_unexpected_exception_propagates_to_loop():
    with pytest.raises(ValueError):
        _CrashTool().run()


def test_sourceref_factories():
    doc = SourceRef.document(doc_id="m", source="s.md", section="Sec", score=1.2)
    assert doc.kind == "document" and doc.section == "Sec"
    sensor = SourceRef.sensor(source="f.parquet", equipment_id="E", window={"n": 1}, n_samples=1)
    assert sensor.kind == "sensor"
    comp = SourceRef.computation(method="m", detail="d")
    assert comp.kind == "computation"
