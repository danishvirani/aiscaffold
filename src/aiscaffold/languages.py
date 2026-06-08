"""The language decision matrix — aiscaffold's opinionated answer to "which
``--lang`` should I pick for this project?"

Stdlib-only and dependency-free, deliberately. This module ships only the
*data* and a couple of plain renderers. It does NOT reason about a specific
project — aiscaffold the CLI has no model to reason with, and we will not pull
one in (that would break the one-line, zero-dependency install).

The actual "best for the project you're doing" judgment lives one layer up, in
aiscaffold's own Claude Code plugin (``plugins/aiscaffold/commands/pick.md``):
Claude reads the real project context, consults this matrix via
``aiscaffold --compare --json``, recommends one language with a rationale, then
runs ``aiscaffold <name> --lang <choice>``. Dumb-but-dependency-free data here;
the intelligence rides in the plugin surface that actually has an LLM. See
``docs/decisions/ADR-003-language-advisor.md``.

Keep ``LANGUAGE_GUIDE`` ids in lockstep with ``scaffold.LANGUAGES`` — a test
asserts the two match so we never advertise advice for a language we cannot
actually scaffold (or vice versa).
"""

import json

# One entry per scaffoldable language. Ordered by how often it's the right
# default for a general AI-native CLI, most-common first.
LANGUAGE_GUIDE = (
    {
        "id": "python",
        "tagline": "The fastest path from idea to working tool.",
        "sweet_spot": (
            "Glue and automation, data/ML work, fast iteration, and anywhere "
            "contributors already expect `pip install`."
        ),
        "strengths": (
            "Ubiquitous runtime, almost certainly already installed",
            "Richest data / ML / scripting ecosystem",
            "Fastest language to write and change",
            "Generated stack is stdlib-only: argparse CLI + hand-rolled stdio MCP",
        ),
        "avoid_when": (
            "You need a single self-contained binary to hand someone",
            "CPU-bound hot loops dominate the workload",
            "Cold-start latency is critical (per-invocation interpreter startup)",
        ),
        "runtime_deps": "stdlib only",
        "bundle": "argparse CLI + hand-rolled stdio JSON-RPC MCP server",
    },
    {
        "id": "go",
        "tagline": "One static binary, fast, trivial to distribute.",
        "sweet_spot": (
            "Network services and daemons, CLIs you ship as a single static "
            "binary, and teams that want simple built-in concurrency."
        ),
        "strengths": (
            "Compiles to one static binary — copy it and run, no runtime",
            "Fast compiles and a fast runtime",
            "Excellent stdlib for networking and JSON",
            "Goroutines make concurrency straightforward",
        ),
        "avoid_when": (
            "Heavy numeric or ML work (ecosystem is thin there)",
            "You want a REPL-driven, prototype-first workflow",
            "The design leans hard on rich generic abstractions",
        ),
        "runtime_deps": "stdlib only",
        "bundle": "stdlib dispatch CLI + encoding/json stdio MCP server",
    },
    {
        "id": "rust",
        "tagline": "Maximum performance and correctness when both matter.",
        "sweet_spot": (
            "Performance- or correctness-critical tools: parsers, systems "
            "utilities, anything where speed and memory safety both matter."
        ),
        "strengths": (
            "Top-tier performance with no garbage collector",
            "Memory safety enforced at compile time, no runtime needed",
            "Compiles to a single binary",
            "Strong type system catches whole classes of bugs before they ship",
        ),
        "avoid_when": (
            "You need to prototype fast and change shape often",
            "Contributors aren't comfortable with Rust",
            "It's simple glue work — Rust is overkill there",
        ),
        "runtime_deps": "serde_json (MCP server only); zero deps with --no-mcp",
        "bundle": "std::env match-dispatch CLI + serde_json stdio MCP server",
    },
    {
        "id": "node",
        "tagline": "Zero-build JS for teams that already live in npm.",
        "sweet_spot": (
            "JavaScript/TypeScript shops, frontend-adjacent tooling, and quick "
            "scripts where your team is already at home in the Node ecosystem."
        ),
        "strengths": (
            "Ubiquitous runtime and a vast ecosystem when you want it",
            "Generated stack is plain ESM with no build step",
            "Zero dependencies — runtime and dev (built-in JSON + node:readline)",
            "Built-in `node --test` runner, nothing extra to install",
        ),
        "avoid_when": (
            "CPU-bound work where single-threaded JS is the bottleneck",
            "You want one distributable binary without extra packaging tooling",
            "You need strict static typing without adding a TypeScript toolchain",
        ),
        "runtime_deps": "zero deps (runtime and dev)",
        "bundle": "plain-ESM CLI + built-in JSON + node:readline stdio MCP server",
    },
)


def guide_ids() -> tuple[str, ...]:
    """The language ids covered by the guide, in display order."""
    return tuple(entry["id"] for entry in LANGUAGE_GUIDE)


def as_json() -> str:
    """The full matrix as pretty JSON — what the plugin's /pick command reads."""
    return json.dumps({"languages": list(LANGUAGE_GUIDE)}, indent=2)


def as_text() -> str:
    """A human-readable rendering of the matrix for the terminal."""
    lines: list[str] = []
    lines.append("aiscaffold — which --lang should I pick?")
    lines.append("")
    lines.append("All four emit the same four-surface bundle (CLI + Claude Code plugin +")
    lines.append("skill + stdio MCP server + brief). Pick by the project, not the habit —")
    lines.append("a coding assistant's default is not automatically the right call.")
    lines.append("")
    for entry in LANGUAGE_GUIDE:
        lines.append(f"── {entry['id']} — {entry['tagline']}")
        lines.append(f"   Best for: {entry['sweet_spot']}")
        lines.append("   Strengths:")
        for s in entry["strengths"]:
            lines.append(f"     • {s}")
        lines.append("   Reach for something else when:")
        for a in entry["avoid_when"]:
            lines.append(f"     • {a}")
        lines.append(f"   Runtime deps: {entry['runtime_deps']}")
        lines.append(f"   Generated stack: {entry['bundle']}")
        lines.append("")
    lines.append("Scaffold with:  aiscaffold <name> --lang <python|go|rust|node>")
    lines.append("Want a recommendation for your specific project? Use the /aiscaffold:pick")
    lines.append("slash command in Claude Code — it reasons over this matrix for you.")
    return "\n".join(lines)
