"""Template rendering core.

Stdlib-only. Variables are written as ``{{name}}`` in template files and in
template *path* segments. We deliberately use ``{{var}}`` rather than
``string.Template``'s ``$var`` (which collides with shell ``$`` in install.sh)
or ``str.format``'s ``{}`` (which collides with Python f-strings and dict
literals in the generated code).

A template file ends in ``.tmpl``; the suffix is stripped on output. Path
segments may also contain variables, e.g. ``src/{{package}}/cli.py.tmpl``
renders to ``src/my_tool/cli.py``.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"

_VAR = re.compile(r"\{\{\s*(\w+)\s*\}\}")
_IF_OPEN = re.compile(r"^\s*\{\{#if (\w+)\}\}\s*$")
_IF_CLOSE = re.compile(r"^\s*\{\{/if\}\}\s*$")


class RenderError(Exception):
    """Raised when a template references an unknown variable or has an
    unbalanced conditional block."""


@dataclass
class Context:
    """The substitution variables for one scaffold."""

    name: str
    description: str = "An AI-native CLI."
    commands: list[str] = field(default_factory=lambda: ["hello"])
    license: str = "MIT"
    author: str = "Your Name"
    year: int = 2026
    with_plugin: bool = True
    with_mcp: bool = True
    with_skill: bool = True

    @property
    def package(self) -> str:
        """Python package name: kebab-case name with dashes as underscores."""
        return self.name.replace("-", "_")

    @property
    def command(self) -> str:
        """The first (primary) command — used where a single example is needed."""
        return self.commands[0]

    def flags(self) -> dict[str, bool]:
        return {
            "with_plugin": self.with_plugin,
            "with_mcp": self.with_mcp,
            "with_skill": self.with_plugin and self.with_skill,
        }

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "package": self.package,
            "description": self.description,
            "command": self.command,
            "commands": ",".join(self.commands),
            "license": self.license,
            "author": self.author,
            "year": str(self.year),
        }


def render_conditionals(text: str, flags: dict[str, bool]) -> str:
    """Resolve ``{{#if flag}} ... {{/if}}`` blocks.

    A marker must occupy its own line. The block's contents survive only when
    every enclosing flag is true; marker lines are always removed. Supports
    nesting. An unknown flag or an unbalanced block raises ``RenderError``.
    """
    out: list[str] = []
    stack: list[bool] = []
    for line in text.splitlines(keepends=True):
        open_match = _IF_OPEN.match(line)
        if open_match:
            flag = open_match.group(1)
            if flag not in flags:
                raise RenderError(f"unknown conditional flag: {flag}")
            stack.append(flags[flag])
            continue
        if _IF_CLOSE.match(line):
            if not stack:
                raise RenderError("{{/if}} without matching {{#if}}")
            stack.pop()
            continue
        if all(stack):
            out.append(line)
    if stack:
        raise RenderError("unterminated {{#if}} block")
    return "".join(out)


def render_string(text: str, variables: dict[str, str]) -> str:
    """Substitute every ``{{var}}`` in *text*. Unknown variables raise."""

    def _sub(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables:
            raise RenderError(f"unknown template variable: {{{{{key}}}}}")
        return variables[key]

    return _VAR.sub(_sub, text)


def render_path(rel_path: Path, variables: dict[str, str]) -> Path:
    """Substitute variables in each path segment and strip a trailing .tmpl."""
    parts = [render_string(part, variables) for part in rel_path.parts]
    rendered = Path(*parts)
    if rendered.suffix == ".tmpl":
        rendered = rendered.with_suffix("")
    return rendered
