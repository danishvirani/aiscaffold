# ADR-001: aiscaffold is stdlib-only (and so is everything it generates)

Date: 2026-06-03
Status: Accepted
Deciders: Danish Virani

## Context

aiscaffold is a scaffolder. A developer runs it once — `pipx run aiscaffold my-tool` — and it writes a full AI-native CLI stack to disk: a CLI binary, a Claude Code plugin, a stdio MCP server, an auto-loading skill, and a `brief` command. It runs on a developer's laptop, makes no network calls, and writes plain files.

There are two obvious dependency stacks, and the decision applies to **two layers**: the scaffolder itself, and the code it generates.

**Option A — pick reasonable libraries.** For the scaffolder: `jinja2` for templating, `click` or `typer` for the CLI, `rich` for output, `pydantic` for the config model. For the generated MCP server: the official MCP Python SDK or FastMCP. Roughly the default Python stack of 2026.

**Option B — Python standard library only, both layers.** Scaffolder: `argparse` + `string.Template` + `pathlib` + `shutil` + ANSI escapes. Generated MCP server: hand-rolled stdio JSON-RPC over `sys.stdin` / `sys.stdout` with `json`. Generated CLI: `argparse`.

The AI tooling space in 2026 favors Option A. The median install command for a competing tool — and for the scaffolds those tools generate — is a wall of `pip install` or a Node toolchain. I want aiscaffold to install with:

```
pipx run aiscaffold my-tool
```

and I want what it generates to install with:

```
curl -fsSL .../install.sh | sh
```

The install command is the first user experience, and most AI tooling fails it on day one.

## Decision

**Option B. Stdlib only at runtime, for the scaffolder AND its output. Zero runtime dependencies on both layers.**

Test/lint tooling (`pytest`, `ruff`) is fine — it never runs on a user's machine, and it never ships in a generated scaffold.

This is the wedge. Anthropic's tooling assumes the TS SDK or FastMCP — both carry runtime deps. A stdlib-only scaffolder that generates stdlib-only output is a *different design philosophy*: zero-deps, hostile to supply chain, friendly to restricted corporate environments. It is the niche Anthropic culturally will not occupy.

## Consequences

**Good:**

1. The pitch IS the install command, on both layers. `pipx run aiscaffold`, then `curl | sh` for the generated tool. One shell line each, forever.
2. The scaffolder is honest. A generator that drags in `jinja2` while preaching zero-deps is a lie users will catch.
3. The generated MCP server is a single readable file (~150 lines of stdio JSON-RPC), not an SDK black box. Authors learn the protocol instead of importing it.
4. Cold start is the interpreter's startup (~30ms). No import-time framework cost in the scaffolder or the scaffold.
5. Any Python 3.10+ works. No compiled extensions, no version-pinning hell, in either layer.
6. Forces design discipline. Want `jinja2`? `string.Template` covers `{{var}}` substitution in five lines. Want `pydantic`? `json.loads` + a `@dataclass`. Want `rich`? Define ANSI constants.

**Bad — accepted openly:**

1. `string.Template` is less powerful than `jinja2` — no loops, no conditionals in templates. We prune surfaces in Python code (skip a directory) rather than with template conditionals. Live with it.
2. The hand-rolled stdio MCP server is more verbose than `@mcp.tool()` decorators. That verbosity is the teaching value, and the price of the install command.
3. `argparse` error messages aren't as polished as `click`'s, in both the scaffolder and the generated CLI. Live with it.
4. Interactive prompts use `input()`, not a fancy TUI. Fine for name/description/commands.

## Alternatives considered

**"Stdlib scaffolder, but let the generated MCP server use the SDK."** Tempting — the SDK is the blessed path. Rejected: it breaks the curl-install promise for the *generated* tool, which is the whole brand. The generated tool's install story is the demo; an SDK dep there undoes the pitch. The hand-rolled stdio server is ~150 lines and stays.

**"One dep is fine — just `jinja2` for templating."** Rejected. Once one dep ships, the second is psychologically free — the line moves. `string.Template` plus Python-side directory pruning covers every case v0.1 needs. And `pip install jinja2` requires `pip` on the box, which philosophically defeats the curl-install pitch even where `pipx` technically works.

**"Vendor a templating lib into `_vendor/`."** Rejected — adds maintenance surface for a problem `string.Template` already solves.

**"Use `typer`/`click` for the scaffolder CLI."** Rejected. `argparse` is what we tell users to generate; the scaffolder must eat its own cooking.

## When this is wrong

This ADR is superseded if:

- The MCP protocol moves to a transport that can't reasonably be hand-rolled in stdlib (e.g. a binary framing that needs a compiled codec). Write ADR-00N to take a single justified dep — in the generated layer only, if possible.
- Template complexity genuinely outgrows `string.Template` (deeply conditional scaffolds). Revisit templating then, not preemptively.
- Performance becomes the user complaint. We add deps for correctness, not cosmetics.

## How we'll know this was right

- Within 3 months: at least one external user writes "I love that this just installs — and so does what it makes." That comment is the validation.
- Within 6 months: no runtime dependency added on either layer. If we did, this ADR is superseded by ADR-00N.

## References

- The `create-X` lineage (`create-react-app`, `create-vite`) — own the install command, own the first 30 seconds.
- Simon Willison's `llm` — stdlib-leaning discipline, closest spiritual predecessor.
- Mitchell Hashimoto on shipping tools — treat the install as a feature.
- The Python stdlib documentation, which is better than people remember.
