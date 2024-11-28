"""Base classes for tools."""

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, fields, replace
from typing import Any, Dict, Optional
import asyncio
from anthropic.types.beta import BetaToolUnionParam


@dataclass(frozen=True)
class ToolResult:
    """Result of a tool execution"""
    output: Optional[str] = None
    error: Optional[str] = None
    base64_image: Optional[str] = None
    system: Optional[str] = None

    def __bool__(self):
        return any(getattr(self, field.name) for field in fields(self))

    def __add__(self, other: "ToolResult"):
        def combine_fields(
            field: Optional[str], 
            other_field: Optional[str], 
            concatenate: bool = True
        ):
            if field and other_field:
                if concatenate:
                    return field + other_field
                raise ValueError("Cannot combine tool results")
            return field or other_field

        return ToolResult(
            output=combine_fields(self.output, other.output),
            error=combine_fields(self.error, other.error),
            base64_image=combine_fields(self.base64_image, other.base64_image, False),
            system=combine_fields(self.system, other.system),
        )

    def replace(self, **kwargs):
        """Returns a new ToolResult with the given fields replaced."""
        return replace(self, **kwargs)


class CLIResult(ToolResult):
    """A ToolResult that represents CLI output."""


class ToolError(Exception):
    """Raised when a tool encounters an error."""
    def __init__(self, message: str):
        self.message = message


class ToolFailure(ToolResult):
    """A ToolResult that represents a failure."""


class BaseAnthropicTool(metaclass=ABCMeta):
    """Base class for Anthropic-defined tools."""

    def __init__(self):
        """Initialize the tool."""
        super().__init__()

    @abstractmethod
    async def __call__(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        ...

    @abstractmethod
    def to_params(self) -> BetaToolUnionParam:
        """Convert tool to API parameters."""
        raise NotImplementedError
