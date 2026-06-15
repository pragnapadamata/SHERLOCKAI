"""A trivial echo tool: the smallest possible proof that tool-calling works."""

from __future__ import annotations

from typing import Any, ClassVar

from backend.app.tools.base import Tool


class EchoTool(Tool):
    """Return the provided message verbatim."""

    name: ClassVar[str] = "echo"
    description: ClassVar[str] = (
        "Echo back the provided message verbatim. Used to verify the "
        "tool-calling loop end to end."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The message to echo back.",
            }
        },
        "required": ["message"],
        "additionalProperties": False,
    }

    def run(self, message: str, **_: Any) -> str:
        return message
