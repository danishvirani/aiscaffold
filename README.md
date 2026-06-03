# aiscaffold

> Bootstrap a full AI-native CLI stack in 30 seconds. One command, all four surfaces, no Node, no SDK.

Run it:

```bash
pipx run aiscaffold my-tool
```

Or curl-install the dev build:

```bash
curl -fsSL https://raw.githubusercontent.com/danishvirani/aiscaffold/main/install.sh | sh
```

No `pip install langchain pydantic typer rich`. No Node. No Docker. Python 3.10+ is all you need — and so is everything it generates.

## What it generates

Most authors cobble the AI-tooling stack together by hand: a CLI here, a Claude Code plugin there, an MCP server from a different generator, then wire them up. aiscaffold emits the whole bundle, already wired:

```
$ pipx run aiscaffold my-tool
✓ src/my_tool/cli.py            stdlib argparse CLI
✓ src/my_tool/mcp.py            stdio MCP server — no SDK dependency
✓ plugins/my-tool/             Claude Code plugin: slash commands + skill
✓ my-tool brief                one-line AI session bootstrap, pre-wired
✓ install.sh                   curl-installable
✓ .github/workflows/ci.yml     lint + test on Python 3.10 / 3.11 / 3.12

cd my-tool && ./install.sh
my-tool --help
```

30 seconds from "I have an idea" to "Claude Code can use my tool."

## The four surfaces (and the brief)

- **CLI** — a stdlib `argparse` binary with one working command. Add more by copying the pattern.
- **Claude Code plugin** — `plugins/<name>/` with a manifest, a slash command per CLI command, and an auto-loading skill.
- **MCP server** — `src/<name>/mcp.py`, a hand-rolled stdio JSON-RPC server. No SDK, no transitive deps.
- **brief command** — every scaffolded tool ships `<name> brief`, which prints a Markdown context block you paste at the start of an AI session. The pattern is the stickiness: every session starts faster.

Skip any surface with `--no-plugin`, `--no-mcp`, `--no-skill`. Interactive prompts and flag-based invocation both work.

## Why stdlib-only

The install command is the first thing a user experiences, and most AI tooling fails it on day one with a wall of `pip install`. aiscaffold installs with one shell line — and so does everything it generates. [ADR-001](docs/decisions/ADR-001-stdlib-only.md) explains the reasoning: zero runtime deps, any Python 3.10+ works, nothing to compile, nothing to audit.

The thesis, repeated everywhere: **AI tooling should install with one shell line, no Node.**

## Command surface

```bash
aiscaffold <name>              # scaffold the full bundle into ./<name>/
aiscaffold <name> --no-mcp     # skip a surface
aiscaffold --version
aiscaffold --help
```

## Status

v0.0 — scaffold. The CLI surface is wired; `aiscaffold <name>` exits 1 with a "v0.1 ships the real scaffolder" message. v0.1 ships the real thing: templates rendered into your chosen directory, all four surfaces wired up, the generated project's own CI green. See [`docs/roadmap.md`](docs/roadmap.md).

## License

MIT. See [LICENSE](LICENSE).

## Thanks

Built by [Danish Virani](https://github.com/danishvirani). The design inheritance is obvious: `create-react-app`, `create-vite`, Simon Willison's `llm`, Mitchell Hashimoto's writing on shipping tools where the install is a feature.
