#! /usr/bin/env uv run python

"""Script to generate the MCP reference page from the MCP server."""

import argparse
import asyncio
import html
import json
import typing
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.tools import FunctionTool
from mcp.types import Tool

from nyt_cooking.mcp.server import mcp

DEFAULT_OUTPUT = Path("docs/reference/mcp.md")


def _schema_type(schema: dict[str, Any]) -> str:
    """Describe a JSON schema's type in a few words, such as `integer | null`.

    Args:
        schema (dict[str, Any]): The JSON schema of one parameter or field.

    Returns:
        str: The type, joining the options of an `anyOf` with `|`.
    """
    if "anyOf" in schema:
        return " | ".join(_schema_type(option) for option in schema["anyOf"])
    if "enum" in schema:
        return " | ".join(f'"{value}"' for value in schema["enum"])
    if schema.get("type") == "array":
        return f"array of {_schema_type(schema.get('items', {}))}"
    return str(schema.get("type", "any"))


def _object_schema(schema: dict[str, Any]) -> dict[str, Any] | None:
    """Find the object schema in a parameter, including an optional one.

    Args:
        schema (dict[str, Any]): The JSON schema of one parameter or field.

    Returns:
        dict[str, Any] | None: The object schema, or `None` if the parameter is not
            an object.
    """
    if schema.get("type") == "object" and "properties" in schema:
        return schema
    for option in schema.get("anyOf", []):
        if option.get("type") == "object" and "properties" in option:
            return option
    return None


def _cell(text: str) -> str:
    """Make text safe for a single Markdown table cell.

    Args:
        text (str): The text to put in the cell.

    Returns:
        str: The text on one line, with pipes escaped.
    """
    return " ".join(text.split()).replace("|", "\\|")


def _code_cell(text: str) -> str:
    """Format text as inline code that is safe in a Markdown table cell.

    Escaping a pipe with a backslash leaves the backslash visible inside a code
    span, so the code is written as HTML with the pipe as an entity.

    Args:
        text (str): The text to show as code.

    Returns:
        str: An HTML `code` element on one line.
    """
    escaped = html.escape(" ".join(text.split())).replace("|", "&#124;")
    return f"<code>{escaped}</code>"


def _parameter_rows(schema: dict[str, Any], prefix: str = "") -> list[str]:
    """Build one table row per parameter, and per field of object parameters.

    Args:
        schema (dict[str, Any]): A JSON object schema, such as a tool's input schema.
        prefix (str): The dotted path of the parent parameter, for nested fields.

    Returns:
        list[str]: The Markdown table rows, in schema order.
    """
    rows = []
    required = set(schema.get("required", []))
    for name, field in schema.get("properties", {}).items():
        path = f"{prefix}{name}"
        nested = _object_schema(field)
        field_type = "object" if nested else _schema_type(field)
        if nested and "null" in _schema_type(field):
            field_type = "object | null"
        default = _code_cell(json.dumps(field["default"])) if "default" in field else ""
        cells = [
            f"`{path}`",
            _code_cell(field_type),
            "yes" if name in required else "no",
            default,
            _cell(field.get("description", "")),
        ]
        rows.append(
            "|" + "|".join(f" {cell} " if cell else " " for cell in cells) + "|"
        )
        if nested:
            rows.extend(_parameter_rows(nested, prefix=f"{path}."))
    return rows


def _behavior(tool: Tool) -> str:
    """Summarize a tool's annotations as whether and how it changes data.

    Args:
        tool (Tool): The tool as MCP clients see it.

    Returns:
        str: `Read-only`, `Destructive` or `Non-destructive`.
    """
    annotations = tool.annotations
    if annotations is None:
        return "Unspecified"
    if annotations.read_only_hint:
        return "Read-only"
    if annotations.destructive_hint:
        return "Destructive"
    return "Non-destructive"


def _returns(name: str) -> str:
    """Link a tool's return type to its page in the API reference.

    Args:
        name (str): The tool name, which is also its function's name.

    Returns:
        str: A Markdown cross-reference to the return type.

    Raises:
        TypeError: If the tool is not defined by a Python function.
    """
    tool = asyncio.run(mcp.get_tool(name))
    if not isinstance(tool, FunctionTool):
        msg = f"Tool {name!r} is not a function tool."
        raise TypeError(msg)
    return_type = typing.get_type_hints(tool.fn)["return"]
    identifier = f"{return_type.__module__}.{return_type.__qualname__}"
    return f"[`{return_type.__qualname__}`][{identifier}]"


def render(tools: list[Tool]) -> str:
    """Render the MCP reference page.

    Args:
        tools (list[Tool]): The tools as MCP clients see them.

    Returns:
        str: The page as Markdown.
    """
    lines = ["# MCP Tools", ""]
    lines += [
        "| Tool | Name | Behavior |",
        "| --- | --- | --- |",
    ]
    lines += [
        f"| [{tool.title}](#{tool.name}) | `{tool.name}` | {_behavior(tool)} |"
        for tool in tools
    ]
    for tool in tools:
        lines += ["", f"## {tool.title} {{ #{tool.name} }}", ""]
        lines += [f"`{tool.name}` · {_behavior(tool)}", ""]
        lines += [(tool.description or "").strip(), ""]
        rows = _parameter_rows(tool.input_schema)
        if rows:
            lines += [
                "**Parameters**",
                "",
                "| Name | Type | Required | Default | Description |",
                "| --- | --- | --- | --- | --- |",
                *rows,
                "",
            ]
        lines += ["**Returns**", "", _returns(tool.name)]
    return "\n".join(lines) + "\n"


async def _list_tools() -> list[Tool]:
    """List the server's tools through an in-memory MCP client.

    Returns:
        list[Tool]: The tools exactly as MCP clients see them.
    """
    async with Client(mcp) as client:
        return await client.list_tools()


def main() -> None:
    """Write the MCP reference page."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.write_text(render(asyncio.run(_list_tools())))


if __name__ == "__main__":
    main()
