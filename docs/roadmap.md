# aiscaffold — build roadmap

Date: 2026-06-03
Status: v0.1.0 (released) — all four language targets complete

Engineering plan, not a marketing roadmap. Each version is a real, shippable artifact a stranger can install and use. Ship when the DoD line below is true.

---

## v0.0 — scaffold (current)

**What works:**
- `aiscaffold --help` renders, shows the `name` positional and `--no-plugin` / `--no-mcp` / `--no-skill` flags
- `aiscaffold --version` prints `aiscaffold 0.0.1`
- `aiscaffold <name>` exits 1 with "scaffolder not yet implemented" + roadmap pointer
- `pip install -e ".[dev]"` works
- `./install.sh` writes a launcher at `~/.local/bin/aiscaffold`
- CI passes: ruff lint + ruff format + pytest on Python 3.10 / 3.11 / 3.12 across Ubuntu + macOS

**What does NOT work yet:**
- No templates are rendered — there is no `src/aiscaffold/templates/` yet
- No file is written to disk; the scaffolder is a stub

**DoD:** ✅ shipped.

---

## v0.1 — the real scaffolder

The first version someone can actually use. One command produces a working four-surface AI CLI.

> **Update (2026-06-04): multi-language.** Per [ADR-002](decisions/ADR-002-multi-language.md), aiscaffold now targets multiple languages via `--lang`, superseding the stdlib-only-Python wedge of ADR-001. Architecture: `templates/_shared/` (language-agnostic plugin + skill + LICENSE) merged with `templates/<lang>/` per-language trees. **All four target languages — Python, Go, Rust, and Node — are complete and verified end-to-end** (each builds/checks, lints, tests + a live MCP stdio roundtrip; wheel packaging verified incl. dot-dir files). Rust uses `serde_json` for its MCP server (no MCP SDK), per [ADR-002](decisions/ADR-002-multi-language.md), gated behind `--no-mcp` (zero deps without the server); Node is plain ESM with no build step and zero dependencies (runtime *and* dev — built-in `JSON` + `node:readline` + the `node --test` runner). `--lang` advertises only languages with a complete tree.

**DoD:** `pipx run aiscaffold my-tool` produces a working CLI + Claude Code plugin + MCP server + skill + brief + install.sh + CI, wired up, in the chosen language. 60 seconds from invocation to "Claude can use my tool." Final acceptance: `pipx run aiscaffold redink` reproduces redink's v0.0 shape (Python).

### Architecture

- Templates in `src/aiscaffold/templates/` as plain files, shipped as package data.
- Stdlib rendering: `string.Template` or hand-rolled `{{var}}` substitution. No `jinja2`.
- A renderer that walks the template tree, substitutes variables, and writes into the chosen output dir.
- All four surfaces by default; `--no-plugin`, `--no-mcp`, `--no-skill` prune the tree.
- Interactive prompts and flag-based invocation both supported.

### Commits in order

1. **Template-rendering core** — `string.Template`-based renderer + a variable context (`name`, `package` (underscored), `description`, `commands`, `license`, `year`, `author`). Render a tree from `templates/` into an output dir, skipping pruned surfaces. Tests render into a tmp dir and assert file existence + substitution.
2. **CLI template** — `templates/src/{{package}}/cli.py.tmpl` — argparse CLI with one working command + a pre-wired `brief` subcommand that prints a Markdown context block.
3. **MCP server template** — `templates/src/{{package}}/mcp.py.tmpl` — hand-rolled stdio JSON-RPC, ~150 lines, stdlib only. Exposes one tool that calls the same code path as the CLI command.
4. **Plugin templates** — `.claude-plugin/plugin.json`, `commands/<cmd>.md` per command, generated from the commands list.
5. **Skill template** — `skills/{{name}}-bootstrap/SKILL.md`, an auto-loading skill that references `<name> brief`.
6. **Project-meta templates** — `install.sh`, `pyproject.toml`, `.github/workflows/ci.yml`, `README.md`, `.gitignore`, `LICENSE` (MIT), `tests/test_smoke.py`.
7. **Interactive mode** — when invoked with just a name (or no name), prompt for description, commands, license. Flag-based path stays for scripting.
8. **Post-scaffold output** — print the one-line install instruction, the "add to Claude Code" instruction (symlink to `~/.claude/plugins/`), and the "use as MCP server" instruction.
9. **Dogfood test** — `aiscaffold redink` in CI, asserting the output matches redink's v0.0 file shape.

**README diff when v0.1 ships:** drop "scaffold" framing, add a sub-30-second screencast gif, bump version.

---

## v0.1.x — the language advisor (shipped)

> **Added 2026-06-07.** Once aiscaffold went multi-language ([ADR-002](decisions/ADR-002-multi-language.md)), it could do something a single-language scaffolder can't: help the author *choose*. Coding assistants reach for TypeScript/Next.js by reflex; a multi-language scaffolder is the natural place to push back. This is **one feature among several**, not a new identity — aiscaffold is a scaffolder first.

**What shipped:**
- `aiscaffold --compare` — an opinionated, dependency-free decision matrix (per language: sweet spot, strengths, when to avoid, runtime deps, generated stack shape). `--compare --json` emits it machine-readably. Single source of truth in [`src/aiscaffold/languages.py`](../src/aiscaffold/languages.py), kept in lockstep with `scaffold.LANGUAGES` by a test.
- aiscaffold's **own Claude Code plugin** at `plugins/aiscaffold/` with an `/aiscaffold:pick` command — reads the project context, consults the matrix via `aiscaffold --compare --json`, recommends one language with a rationale, then scaffolds it. aiscaffold now dogfoods the exact plugin surface it generates.

**Design split (see [ADR-003](decisions/ADR-003-language-advisor.md)):** the *data* lives in the dependency-free CLI; the *reasoning* lives in the plugin layer that actually has a model. The CLI never gains an LLM dependency — the one-line, zero-dependency install is preserved.

---

## v0.2 — polish + the things that make it stick

**DoD:**
1. Generated tools pass their own CI on first push (the scaffold's CI is green out of the box).
2. `aiscaffold` supports adding a command to an existing scaffold without re-running the whole generator.

**Commits:**
1. **`aiscaffold add-command <cmd>`** — append a command to an existing scaffold: CLI subcommand stub, plugin command markdown, MCP tool entry.
2. **Richer brief template** — the generated `brief` emits project structure, command list, and a "how to extend" section, not just a stub.
3. **`uvx` parity** — verify and document `uvx aiscaffold` alongside `pipx run`.
4. **Screencast + landing** — sub-30-second demo gif in the README; a single-page landing.
5. **Template lint** — a CI job that scaffolds, then runs the generated project's own ruff + pytest, catching template rot.

---

## v0.3 — the upgrade story (template rot is the silent killer)

Template rot kills scaffolders in 2-3 quarters: plugin manifest schema, MCP APIs, and Claude Code conventions change quarterly. A scaffolder that emits stale templates becomes worse than nothing.

**DoD:**
- `aiscaffold upgrade` diffs a user's existing scaffold against the current templates and applies non-conflicting updates, flagging conflicts for manual resolution.
- Templates pin against a specific Claude Code / MCP convention version recorded in the generated manifest.

**Commits:**
1. **Version-stamp generated scaffolds** — record the aiscaffold version + template version in the generated `pyproject.toml` / manifest.
2. **`aiscaffold upgrade` core** — three-way diff (original template, current template, user's file); clean-apply the non-conflicting hunks.
3. **Conflict reporting** — list files needing manual merge, with the template diff inline.
4. **`docs/upgrading.md`** — the upgrade workflow, documented.

---

## Beyond v0.3 (radar, not committed)

- **More languages** — a Go single-binary backend option; deferred because Node/TS is already well-served by Anthropic's tooling and Python stdlib is the wedge.
- **Marketplace submission flow** — generate the marketplace manifest + a `submit` helper.
- **Hooks + agents surfaces** — extend beyond the four core surfaces once they're rock-solid.
- **PyPI publish of the scaffold** — `pipx run` stays canonical; `pipx install aiscaffold` as fallback.

## What would make us slow down or pivot

- **Anthropic ships a one-shot full-bundle scaffolder** (`claude plugin create --full`). Coverage differentiator gone — pivot to the opinionated stdlib-only minimalist alternative, or kill. Yeoman's lesson: too general loses, sharply opinionated wins.
- **The audience is shallower than it looks.** Most authors ship one thing. If usage caps low, treat this as a credibility play — the name and demo are the win.
- **Template rot outruns the upgrade story.** If templates fall behind faster than `upgrade` can keep up, the tool dies. Prioritize v0.3.
