"""Scaffold orchestrator.

Merges the language-agnostic ``_shared`` template tree with the chosen
language's tree (``templates/<lang>/``), classifies each file by surface,
prunes surfaces the user turned off, renders the rest, and writes them into
the output directory. Stdlib-only.
"""

from pathlib import Path

from aiscaffold.render import (
    TEMPLATES_DIR,
    Context,
    render_conditionals,
    render_path,
    render_string,
)

# The language-agnostic tree, merged into every scaffold regardless of --lang.
SHARED_DIR_NAME = "_shared"

# Languages with a complete template tree under templates/<lang>/. Only list a
# language here once every surface it ships actually builds and runs — an
# advertised but half-built tree is worse than no tree. Node is next.
LANGUAGES = ("python", "go", "rust")

# Files that must keep their executable bit when written.
_EXECUTABLE = {"install.sh"}


def _strip_tmpl(name: str) -> str:
    return name[:-5] if name.endswith(".tmpl") else name


def classify_surface(rel_path: Path) -> str:
    """Return the surface a template file belongs to: core | plugin | skill | mcp.

    Language-agnostic: the MCP server is any file whose rendered stem is
    ``mcp`` (``mcp.py``, ``mcp.go``, ``mcp.rs``, ``mcp.js``) or that lives
    under an ``mcp`` directory.
    """
    parts = rel_path.parts
    if parts and parts[0] == "plugins":
        if "skills" in parts:
            return "skill"
        return "plugin"
    stem = Path(_strip_tmpl(rel_path.name)).stem
    if stem == "mcp" or "mcp" in parts:
        return "mcp"
    return "core"


def _included(surface: str, ctx: Context) -> bool:
    if surface == "mcp":
        return ctx.with_mcp
    if surface == "plugin":
        return ctx.with_plugin
    if surface == "skill":
        # The skill lives inside the plugin dir; no plugin means no host for it.
        return ctx.with_plugin and ctx.with_skill
    return True


def template_roots(lang: str, templates_dir: Path = TEMPLATES_DIR) -> list[Path]:
    """The ordered template roots for *lang*: shared first, language last.

    Later roots win on path collisions, so a language may override a shared
    file by shipping the same relative path.
    """
    return [templates_dir / SHARED_DIR_NAME, templates_dir / lang]


def iter_templates(roots):
    """Yield (relative_path, absolute_path) for every template file across
    *roots*. Later roots override earlier ones on identical relative paths."""
    if isinstance(roots, Path):
        roots = [roots]
    merged: dict[str, tuple[Path, Path]] = {}
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file():
                rel = path.relative_to(root)
                merged[str(rel)] = (rel, path)
    for rel, path in sorted(merged.values(), key=lambda item: str(item[0])):
        yield rel, path


def scaffold(ctx: Context, out_dir: Path, templates_dir: Path = TEMPLATES_DIR) -> list[Path]:
    """Render the scaffold into *out_dir*. Returns the list of files written
    (paths relative to out_dir)."""
    variables = ctx.as_dict()
    flags = ctx.flags()
    roots = template_roots(ctx.lang, templates_dir)
    written: list[Path] = []

    for rel_path, abs_path in iter_templates(roots):
        if not _included(classify_surface(rel_path), ctx):
            continue

        target_rel = render_path(rel_path, variables)
        target = out_dir / target_rel
        target.parent.mkdir(parents=True, exist_ok=True)

        text = render_conditionals(abs_path.read_text(encoding="utf-8"), flags)
        rendered = render_string(text, variables)
        target.write_text(rendered, encoding="utf-8")

        if target.name in _EXECUTABLE:
            target.chmod(0o755)

        written.append(target_rel)

    return written
