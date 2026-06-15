"""The tool base class and registry behave as the agent loop expects."""

from __future__ import annotations

import pytest

from backend.app.tools.base import ToolRegistry
from backend.app.tools.examples.echo import EchoTool


def test_register_get_and_run():
    registry = ToolRegistry()
    registry.register(EchoTool())

    assert "echo" in registry
    assert len(registry) == 1
    assert registry.get("echo").run(message="hi there") == "hi there"


def test_spec_serializes_to_openai_tool():
    registry = ToolRegistry()
    registry.register(EchoTool())

    specs = registry.specs()
    assert len(specs) == 1
    openai_tool = specs[0].to_openai()
    assert openai_tool["type"] == "function"
    assert openai_tool["function"]["name"] == "echo"
    assert "message" in openai_tool["function"]["parameters"]["properties"]


def test_allowlist_restricts_specs():
    registry = ToolRegistry()
    registry.register(EchoTool())

    assert [s.name for s in registry.specs(allow=["echo"])] == ["echo"]
    assert registry.specs(allow=[]) == []


def test_duplicate_registration_raises():
    registry = ToolRegistry()
    registry.register(EchoTool())
    with pytest.raises(ValueError):
        registry.register(EchoTool())


def test_missing_tool_raises():
    registry = ToolRegistry()
    with pytest.raises(KeyError):
        registry.get("nope")
