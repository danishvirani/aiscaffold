# ADR-002: aiscaffold targets multiple languages

Date: 2026-06-04
Status: Accepted
Deciders: Danish Virani
Supersedes: [ADR-001](ADR-001-stdlib-only.md)

## Context

ADR-001 scoped aiscaffold to Python and made "stdlib-only, no Node" the *brand* — the wedge against Anthropic's SDK-first tooling. That wedge is sharp but narrow. The judgment call: a scaffolder that only emits Python is useful to Python authors and nobody else, and the AI-tooling audience writes Go, Rust, and TypeScript too. To be broadly useful, aiscaffold must emit the full four-surface bundle in the language the author already ships in.

This reverses ADR-001's central positioning. It was made deliberately, with the trade-off understood: we trade a defensible-but-narrow niche for breadth, and we take on the Yeoman risk (a too-general generator loses to sharply-opinionated ones). We accept that risk because the *opinion* is preserved at a different level — see below.

## Decision

**aiscaffold emits the full AI-native bundle (CLI + Claude Code plugin + skill + MCP server + brief) in multiple target languages, selected with `--lang`.** Python and Go ship first; Rust and Node follow. The architecture is built to add a language as a self-contained template tree, not a fork.

### What carries over from ADR-001 (the opinion, relocated)

The brand is no longer "stdlib-only Python." It is now, per language:

1. **One-line install.** Every generated project installs via `./install.sh` (and the curl path). Python writes a launcher; Go/Rust build a single binary; Node runs without a build step. The install command is still the first user experience and still the pitch.
2. **No MCP *SDK* in the generated server.** Every language's MCP server is a hand-rolled stdio JSON-RPC loop — readable, auditable, no protocol black box. The server uses that language's *de-facto-standard JSON library*: stdlib where one exists (`json`, `encoding/json`, JS `JSON`), and the universal community standard where it doesn't (Rust → `serde`/`serde_json`). The line we hold is "no MCP SDK," not "zero dependencies absolutely" — hand-rolling a JSON parser in Rust's std would be brittle make-work that serves no one. (Decided 2026-06-04 when adding the Rust target; the original draft of this ADR said "zero third-party deps," which over-reached.)
3. **The scaffolder itself stays stdlib-only Python.** aiscaffold is still `argparse` + a hand-rolled `{{var}}`/`{{#if}}` renderer + `pathlib`. Eating our own cooking on the *tool* costs nothing and keeps `pipx run aiscaffold` instant.

So the wedge moves from "one language, zero deps" to "any language, idiomatic, with a dependency-free MCP server and a one-line install."

## Architecture

- Templates live under `src/aiscaffold/templates/`:
  - `_shared/` — language-agnostic surfaces (LICENSE, the whole `plugins/` tree). The plugin manifest points its MCP server at `{"command": "<name>", "args": ["mcp"]}`, which is correct for every language because every generated CLI exposes an `mcp` subcommand.
  - `<lang>/` — one complete tree per language (source, build manifest, install.sh, CI, README, .gitignore, tests).
- The renderer is language-blind: `{{var}}` substitution + line-based `{{#if flag}}` conditional blocks (the conditional feature, added during v0.1, is what lets `--no-mcp` prune cleanly in any language — note ADR-001's claim that we prune only in Python code is itself out of date).
- The orchestrator merges `_shared` + `<lang>` (language wins on collision), classifies each file by surface (`core | plugin | skill | mcp`) using a language-agnostic rule (the MCP server is any file whose stem is `mcp` or that lives under an `mcp/` directory), prunes disabled surfaces, and renders the rest.
- `--lang` advertises only languages with a complete, verified tree. An unbuilt language is not a choice — argparse rejects it rather than emitting a broken shared-only scaffold.

## Consequences

**Good:**

1. Broadly useful: a Go author gets an idiomatic Go project, not a Python one they have to port.
2. The shared layer keeps the plugin/skill surfaces in one place — no 4× duplication, less template rot.
3. Each language's output runs its own CI green out of the box (build + lint/format + test), and that is enforced by aiscaffold's own test suite, which actually builds and runs the generated Go binary plus a live MCP roundtrip.

**Bad — accepted openly:**

1. **The Yeoman risk.** Generality can dilute the product. Mitigation: the opinion lives in the *output shape and the no-SDK MCP server*, not in language count. We are not a config-driven meta-generator; each language is a hand-tuned, idiomatic tree.
2. **N× template-rot surface.** Every language's MCP/plugin conventions can drift independently. The v0.3 `upgrade` story now matters more, and per-language CI in the scaffold's own pipeline is the early-warning system.
3. **Packaging footguns.** Deeper template trees with dot-directories (`.github/`, `.claude-plugin/`) exposed a real bug: setuptools' `**` globs skip dot-dirs, so the wheel silently dropped `plugin.json` and `ci.yml`. Fixed with explicit package-data patterns and a wheel-contents test. New languages must keep that test honest.
4. **No more "Python is all you need" one-liner.** The marketing simplifies less cleanly. The install-command pitch still holds per language.

## When this is wrong

- If usage shows the breadth isn't used — authors only ever pick one language — reconsider whether the maintenance cost of N trees is worth it, and consider retreating to the sharp single-language wedge.
- If Anthropic ships a one-shot full-bundle multi-language scaffolder, the coverage differentiator is gone; fall back to the opinionated "no-SDK, one-line-install" angle or kill.

## References

- ADR-001 — the original stdlib-only-Python decision this supersedes.
- The Yeoman lesson — too general loses, sharply opinionated wins. The opinion here is the output shape, not the language menu.
