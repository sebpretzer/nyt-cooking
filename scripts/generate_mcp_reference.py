#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13, <3.15"
# dependencies = [
#     "griffe>=2.3.2",
#     "nyt-cooking[mcp]",
#     "pygments>=2.21.0",
# ]
#
# [tool.uv]
# exclude-newer = "14 days"
#
# [tool.uv.sources]
# nyt-cooking = { path = "..", editable = true }
# ///

"""Script to generate the MCP reference page from the MCP server.

WARNING: This script was vibe coded with Claude Opus and is not held to the same
standards as the rest of the codebase. Please do not rely on the coding patterns here,
only on what it produces.

The page mirrors the mkdocstrings pages: symbol badges on headings and in the table
of contents, labels, a highlighted signature, `Parameters`, `Returns` and `Raises`
tables, collapsible JSON schemas and the collapsible source code, inside the same
`doc` blocks that mkdocstrings uses so the theme styles them the same. The page carries
its own styles for the `tool` and `server` symbol badges, as mkdocstrings ships
styles for its own symbol types.
"""

import argparse
import asyncio
import html
import inspect
import json
import typing
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.tools import FunctionTool
from griffe import (
    Docstring,
    DocstringSectionRaises,
    DocstringSectionReturns,
)
from mcp.types import Tool
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.python import PythonLexer

from nyt_cooking.mcp.server import mcp

DEFAULT_OUTPUT = Path("docs/reference/mcp.md")
ROOT = Path(__file__).resolve().parents[1]
SIGNATURE_WIDTH = 70
STYLE = """
:root,
[data-md-color-scheme="default"] {
  --doc-symbol-tool-fg-color: #1b7c83;
  --doc-symbol-server-fg-color: var(--doc-symbol-module-fg-color);
}

[data-md-color-scheme="slate"] {
  --doc-symbol-tool-fg-color: #56d4dd;
  --doc-symbol-server-fg-color: var(--doc-symbol-module-fg-color);
}

a code.doc-symbol-tool,
code.doc-symbol-tool {
  color: var(--doc-symbol-tool-fg-color);
}

.md-content code.doc-symbol-tool::after {
  content: "tool";
}

.md-sidebar code.doc-symbol-tool::after {
  content: "t";
}

a code.doc-symbol-server,
code.doc-symbol-server {
  color: var(--doc-symbol-server-fg-color);
}

.md-content code.doc-symbol-server::after {
  content: "server";
}

.md-sidebar code.doc-symbol-server::after {
  content: "srv";
}
"""


@dataclass
class ToolDoc:
    """Everything the page shows about one tool.

    Attributes:
        tool (Tool): The tool as MCP clients see it.
        returns (str): The identifier of the Python return type, for linking.
        returns_description (str): The description under `Returns:` in the docstring.
        raises (list[tuple[str, str]]): Each exception and description under
            `Raises:` in the docstring.
        source_path (str): The path of the function's file, from the repository root.
        source_start (int): The line number where the function's source starts.
        source (str): The function's source code.
    """

    tool: Tool
    returns: str
    returns_description: str
    raises: list[tuple[str, str]]
    source_path: str
    source_start: int
    source: str


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


def _field_type(schema: dict[str, Any]) -> str:
    """Describe a parameter's type, naming nested objects `object`.

    Args:
        schema (dict[str, Any]): The JSON schema of one parameter or field.

    Returns:
        str: The type, such as `string` or `object | null`.
    """
    if _object_schema(schema) is None:
        return _schema_type(schema)
    return "object | null" if "null" in _schema_type(schema) else "object"


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


def _row(cells: list[str]) -> str:
    """Join cells into a Markdown table row, leaving empty cells blank.

    Args:
        cells (list[str]): The cell contents, in column order.

    Returns:
        str: The table row.
    """
    return "|" + "|".join(f" {cell} " if cell else " " for cell in cells) + "|"


def _symbol(kind: str, *, toc: bool = False) -> str:
    """Render a symbol badge, as mkdocstrings puts before headings.

    Args:
        kind (str): The symbol type, `server` or `tool`.
        toc (bool): Whether the badge is for the table of contents.

    Returns:
        str: An empty `code` element that the stylesheet fills in.
    """
    place = "toc" if toc else "heading"
    return f'<code class="doc-symbol doc-symbol-{place} doc-symbol-{kind}"></code>'


def _heading(level: int, kind: str, name: str, labels: list[str]) -> str:
    """Render a heading with a symbol badge, labels and a matching TOC entry.

    Args:
        level (int): The heading level.
        kind (str): The symbol type, `server` or `tool`.
        name (str): The heading text, also used as its anchor.
        labels (list[str]): Labels shown after the name.

    Returns:
        str: The Markdown heading.
    """
    label_html = ""
    if labels:
        pills = "".join(
            f'<small class="doc doc-label doc-label-{label}">'
            f"<code>{label}</code></small>"
            for label in labels
        )
        label_html = f' <span class="doc doc-labels">{pills}</span>'
    toc_label = f"{_symbol(kind, toc=True)}&nbsp;{name}"
    return (
        f"{'#' * level} {_symbol(kind)} {name}{label_html} "
        f"{{ #{name} data-toc-label='{toc_label}' }}"
    )


def _labels(tool: Tool) -> list[str]:
    """List a tool's labels from its annotations.

    Args:
        tool (Tool): The tool as MCP clients see it.

    Returns:
        list[str]: `read-only`, `destructive` or `non-destructive`, then
            `idempotent` and `open-world` when set.
    """
    annotations = tool.annotations
    if annotations is None:
        return []
    labels = []
    if annotations.read_only_hint:
        labels.append("read-only")
    elif annotations.destructive_hint:
        labels.append("destructive")
    elif annotations.destructive_hint is False:
        labels.append("non-destructive")
    if annotations.idempotent_hint:
        labels.append("idempotent")
    if annotations.open_world_hint:
        labels.append("open-world")
    return labels


def _signature(doc: ToolDoc) -> str:
    """Render a highlighted signature, wrapped like mkdocstrings wraps long ones.

    Args:
        doc (ToolDoc): The tool to render.

    Returns:
        str: The signature block as HTML, with the return type linked.
    """
    schema = doc.tool.input_schema
    required = set(schema.get("required", []))
    params = []
    for name, field in schema.get("properties", {}).items():
        param = f"{name}: {_field_type(field)}"
        if name not in required and "default" in field:
            param += f" = {json.dumps(field['default'])}"
        params.append(param)
    return_name = doc.returns.rsplit(".", 1)[-1]
    one_line = f"{doc.tool.name}({', '.join(params)}) -> {return_name}"
    if len(one_line) <= SIGNATURE_WIDTH:
        text = one_line
    else:
        body = "".join(f"    {param},\n" for param in params)
        text = f"{doc.tool.name}(\n{body}) -> {return_name}"
    code = highlight(text, PythonLexer(), HtmlFormatter(nowrap=True)).rstrip("\n")
    linked = f'<autoref identifier="{doc.returns}" optional>{return_name}</autoref>'
    head, _, tail = code.rpartition(return_name)
    code = f"{head}{linked}{tail}"
    return (
        '<div class="doc-signature highlight"><pre><span></span>'
        f"<code>{code}\n</code></pre></div>"
    )


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
        if name in required:
            default = "*required*"
        elif "default" in field:
            default = _code_cell(json.dumps(field["default"]))
        else:
            default = ""
        rows.append(
            _row(
                [
                    f"`{path}`",
                    _code_cell(_field_type(field)),
                    _cell(field.get("description", "")),
                    default,
                ]
            ),
        )
        nested = _object_schema(field)
        if nested:
            rows.extend(_parameter_rows(nested, prefix=f"{path}."))
    return rows


def _section(title: str, header: list[str], rows: list[str]) -> list[str]:
    """Render a docstring-style section: a bold title and a table.

    Args:
        title (str): The section title, such as `Parameters`.
        header (list[str]): The table's column names.
        rows (list[str]): The table rows.

    Returns:
        list[str]: The section's Markdown lines.
    """
    return [
        f'<span class="doc-section-title">{title}:</span>',
        "",
        _row(header),
        _row(["---"] * len(header)),
        *rows,
        "",
    ]


def _schema_details(summary: str, schema: dict[str, Any]) -> list[str]:
    """Render a collapsible JSON schema, as mkdocstrings shows Pydantic schemas.

    Args:
        summary (str): The text of the collapsed toggle.
        schema (dict[str, Any]): The JSON schema.

    Returns:
        list[str]: The block's Markdown lines.
    """
    return [
        "<details markdown>",
        f"<summary>{summary}</summary>",
        "",
        "```json",
        json.dumps(schema, indent=2),
        "```",
        "",
        "</details>",
        "",
    ]


def _source_details(doc: ToolDoc) -> list[str]:
    """Render the collapsible source code, as mkdocstrings shows it.

    Args:
        doc (ToolDoc): The tool.

    Returns:
        list[str]: The block's Markdown lines.
    """
    return [
        '<details class="mkdocstrings-source" markdown>',
        f"<summary>Source code in <code>{doc.source_path}</code></summary>",
        "",
        f'```python linenums="{doc.source_start}"',
        doc.source.rstrip("\n"),
        "```",
        "",
        "</details>",
        "",
    ]


def _summary(description: str) -> str:
    """Take a description's first paragraph as a one-line summary.

    Args:
        description (str): The full description.

    Returns:
        str: The first paragraph, on one line.
    """
    return _cell(description.strip().split("\n\n", 1)[0])


def render(docs: list[ToolDoc]) -> str:
    """Render the MCP reference page.

    Args:
        docs (list[ToolDoc]): The tools, in the server's order.

    Returns:
        str: The page as Markdown.
    """
    lines = [
        "# MCP Tools",
        "",
        "<style>",
        STYLE.strip(),
        "</style>",
        "",
        '<div class="doc doc-object doc-server" markdown>',
        "",
        _heading(2, "server", mcp.name, []),
        "",
        '<div class="doc doc-contents first" markdown>',
        "",
    ]
    if mcp.instructions:
        lines += [" ".join(mcp.instructions.split()), ""]
    lines += _section(
        "Tools",
        ["Name", "Description"],
        [
            _row(
                [
                    f"[`{doc.tool.name}`](#{doc.tool.name})",
                    _summary(doc.tool.description or ""),
                ]
            )
            for doc in docs
        ],
    )
    for doc in docs:
        tool = doc.tool
        lines += [
            '<div class="doc doc-object doc-tool" markdown>',
            "",
            _heading(3, "tool", tool.name, _labels(tool)),
            "",
            '<div class="doc doc-contents" markdown>',
            "",
        ]
        lines += [_signature(doc), ""]
        lines += [(tool.description or "").strip(), ""]
        rows = _parameter_rows(tool.input_schema)
        if rows:
            lines += _section(
                "Parameters",
                ["Name", "Type", "Description", "Default"],
                rows,
            )
        return_name = doc.returns.rsplit(".", 1)[-1]
        lines += _section(
            "Returns",
            ["Type", "Description"],
            [
                _row(
                    [
                        f"[`{return_name}`][{doc.returns}]",
                        _cell(doc.returns_description),
                    ]
                )
            ],
        )
        if doc.raises:
            lines += _section(
                "Raises",
                ["Type", "Description"],
                [_row([f"`{name}`", _cell(text)]) for name, text in doc.raises],
            )
        lines += _schema_details("Show input schema:", tool.input_schema)
        if tool.output_schema:
            lines += _schema_details("Show output schema:", tool.output_schema)
        lines += _source_details(doc)
        lines += ["</div>", "", "</div>", ""]
    lines += ["</div>", "", "</div>", ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def _source(function: Callable[..., Any]) -> tuple[str, int, str]:
    """Find a function's source code.

    Args:
        function (Callable[..., Any]): The function.

    Returns:
        tuple[str, int, str]: The path of its file from the repository root, the
            line number where it starts, and its source code.
    """
    lines, start = inspect.getsourcelines(function)
    path = Path(inspect.getsourcefile(function) or "").resolve().relative_to(ROOT)
    return path.as_posix(), start, "".join(lines)


async def _tool_docs() -> list[ToolDoc]:
    """Collect each tool as MCP clients see it, with its function's docstring.

    Returns:
        list[ToolDoc]: The tools, in the server's order.

    Raises:
        TypeError: If a tool is not defined by a Python function.
    """
    async with Client(mcp) as client:
        tools = await client.list_tools()
    docs = []
    for tool in tools:
        function_tool = await mcp.get_tool(tool.name)
        if not isinstance(function_tool, FunctionTool):
            msg = f"Tool {tool.name!r} is not a function tool."
            raise TypeError(msg)
        return_type = typing.get_type_hints(function_tool.fn)["return"]
        sections = Docstring(function_tool.fn.__doc__ or "").parse("google")
        returns_description = ""
        raises: list[tuple[str, str]] = []
        for section in sections:
            if isinstance(section, DocstringSectionReturns):
                returns_description = section.value[0].description
            elif isinstance(section, DocstringSectionRaises):
                raises += [
                    (str(item.annotation), item.description) for item in section.value
                ]
        source_path, source_start, source = _source(function_tool.fn)
        docs.append(
            ToolDoc(
                tool=tool,
                returns=f"{return_type.__module__}.{return_type.__qualname__}",
                returns_description=returns_description,
                raises=raises,
                source_path=source_path,
                source_start=source_start,
                source=source,
            ),
        )
    return docs


def main() -> None:
    """Write the MCP reference page."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.write_text(render(asyncio.run(_tool_docs())))


if __name__ == "__main__":
    main()
