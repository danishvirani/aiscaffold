# aiscaffold

> Bootstrap a full AI-native CLI stack in 30 seconds — in the language you ship in. One command, all four surfaces, already wired.

Run it:

```bash
pipx run aiscaffold my-tool              # Python (default)
pipx run aiscaffold my-tool --lang go    # Go
pipx run aiscaffold my-tool --lang rust  # Rust
pipx run aiscaffold my-tool --lang node  # Node (plain JS)
```

Or curl-install the dev build:

```bash
curl -fsSL https://raw.githubusercontent.com/danishvirani/aiscaffold/main/install.sh | sh
```

## What it generates

Most authors cobble the AI-tooling stack together by hand: a CLI here, a Claude Code plugin there, an MCP server from a different generator, then wire them up. aiscaffold emits the whole bundle, already wired, for your target language:

```
$ pipx run aiscaffold my-tool --lang go
✓ cmd/my-tool/main.go          stdlib Go CLI
✓ internal/mcp/mcp.go          stdio MCP server — encoding/json, no SDK
✓ plugins/my-tool/             Claude Code plugin: slash commands + skill
✓ my-tool brief                one-line AI session bootstrap, pre-wired
✓ install.sh                   builds + installs a single static binary
✓ .github/workflows/ci.yml     vet + gofmt + test on Go 1.21 / 1.22

cd my-tool && ./install.sh
my-tool --help
```

30 seconds from "I have an idea" to "Claude Code can use my tool."

## Languages

| `--lang` | CLI | MCP server | Dependencies |
|----------|-----|------------|--------------|
| `python` (default) | `argparse` | hand-rolled stdio JSON-RPC | stdlib only |
| `go` | stdlib `flag`-free dispatch | `encoding/json` stdio JSON-RPC | stdlib only |
| `rust` | `std::env` match dispatch | hand-rolled stdio JSON-RPC | `serde_json` (MCP only) |
| `node` | plain ESM, no build step | built-in `JSON` + `node:readline` | zero deps (runtime *and* dev) |

Each language emits a complete, idiomatic project that builds, tests, lints, and runs its own CI green out of the box. The Claude Code plugin and bootstrap skill are language-agnostic and shared across every target.

## Not sure which language? Ask first.

Coding assistants reach for TypeScript/Next.js by reflex, whatever the project is. aiscaffold makes Go, Rust, or Python a one-liner — and helps you pick the one that actually fits, instead of defaulting on autopilot.

```bash
aiscaffold --compare          # opinionated decision matrix: each language's
                              # sweet spot, strengths, and when to avoid it
aiscaffold --compare --json   # same matrix, machine-readable
```

For a recommendation tailored to *your* project, aiscaffold ships its own Claude Code plugin with an `/aiscaffold:pick` command: it reads your project context, consults the matrix, recommends one language with a real rationale, then scaffolds it. The decision data stays in the dependency-free CLI; the reasoning rides in the plugin layer that actually has a model — see [ADR-003](docs/decisions/ADR-003-language-advisor.md).

## The four surfaces (and the brief)

- **CLI** — a native binary for the chosen language with one working command. Add more by copying the pattern.
- **Claude Code plugin** — `plugins/<name>/` with a manifest, a slash command per CLI command, and an auto-loading skill. The plugin's MCP entry points at `<name> mcp`, so it works identically regardless of language.
- **MCP server** — a hand-rolled stdio JSON-RPC server with no MCP SDK. It uses each language's de-facto-standard JSON library (stdlib `json` / `encoding/json` where one exists; `serde_json` for Rust). Run it with `<name> mcp`.
- **brief command** — every scaffolded tool ships `<name> brief`, which prints a Markdown context block you paste at the start of an AI session. The pattern is the stickiness: every session starts faster.

Skip any surface with `--no-plugin`, `--no-mcp`, `--no-skill`. Interactive prompts and flag-based invocation both work.

## Why one-line install

The install command is the first thing a user experiences, and most AI tooling fails it on day one with a wall of dependencies. aiscaffold installs with one shell line — and so does everything it generates, in every language. The generated MCP servers carry no SDK dependency, so there's nothing extra to audit. See [`docs/decisions/`](docs/decisions/) for the design record, including the multi-language decision ([ADR-002](docs/decisions/ADR-002-multi-language.md)) that superseded the original stdlib-only-Python wedge.

## Command surface

```bash
aiscaffold <name>                  # scaffold the full Python bundle into ./<name>/
aiscaffold <name> --lang go        # scaffold a Go bundle
aiscaffold <name> --no-mcp         # skip a surface
aiscaffold --compare               # which --lang fits my project?
aiscaffold --version
aiscaffold --help
```

## Status

**v0.1.0** — the real scaffolder. Renders all four surfaces into your chosen directory, wired up, with the generated project's own CI green. All four target languages — **Python, Go, Rust, and Node** — are complete and verified end-to-end (build/check + lint + test + a live MCP stdio roundtrip). See [`docs/roadmap.md`](docs/roadmap.md).

## License

MIT. See [LICENSE](LICENSE).

## Thanks

Built by [Danish Virani](https://github.com/danishvirani). The design inheritance is obvious: `create-react-app`, `create-vite`, Simon Willison's `llm`, Mitchell Hashimoto's writing on shipping tools where the install is a feature.
