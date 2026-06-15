"""The ``Tool`` base class and the ``ToolRegistry``.

A tool declares its name, description, and a JSON Schema for its arguments, and
implements ``run``. The registry holds tools and can emit their specs -- with an
optional allowlist, which is how each specialist agent later restricts itself to
just the tools it is permitted to call.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from backend.app.llm.messages import ToolSpec


class Tool(ABC):
    """Base class for a callable, schema-described tool."""

    name: ClassVar[str]
    description: ClassVar[str]
    parameters: ClassVar[dict[str, Any]]

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """Execute the tool with keyword arguments parsed from the model call."""

    def spec(self) -> ToolSpec:
        """Return the advertisement the model sees for this tool."""

        return ToolSpec(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )


class ToolRegistry:
    """An ordered collection of tools, keyed by name."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name!r} is already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Tool {name!r} is not registered.")
        return self._tools[name]

    def names(self) -> list[str]:
        return list(self._tools)

    def specs(self, allow: list[str] | None = None) -> list[ToolSpec]:
        """Return tool specs, optionally restricted to an allowlist of names."""

        if allow is None:
            return [tool.spec() for tool in self._tools.values()]
        return [self._tools[name].spec() for name in allow]

    def __contains__(self, name: object) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
