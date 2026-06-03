# create-ai-cli — strategy

Date: 2026-06-03
Status: pre-v0.1
Audience: me (Danish). Forward to teammates if helpful.

This is the "why create-ai-cli exists, why this shape" doc. Build sequence is in [roadmap.md](roadmap.md). The single biggest engineering decision is in [decisions/ADR-001-stdlib-only.md](decisions/ADR-001-stdlib-only.md).

---

## The call

The AI-native CLI stack has converged on four surfaces that ship together: a CLI binary, a Claude Code plugin (slash commands + skill), an MCP server, and a session-bootstrap `brief` command. Authors build all four by hand, every time, copy-pasting boilerplate across surfaces that don't quite line up.

**create-ai-cli is a one-shot scaffolder that emits all four surfaces, already wired, stdlib-only, curl-installable. One command, 30 seconds, a distributable AI tool.**

The MCP ecosystem grew 232% in six months (425 → 1,412 servers, ~300 new/month); the community catalog lists 6,700+ skills and 11,200+ MCP servers. That's a lot of authors doing the same setup work, repeatedly. The gap is specific: **no existing scaffolder bundles all four surfaces with a working curl-install.** Each existing tool owns one slice.

### Why not the adjacent shapes

- **MCP-server-only scaffolders** (`mcp-framework`, `create-mcp`, the deprecated `@modelcontextprotocol/create-server`) — one surface, Node-heavy. Don't emit a CLI, a plugin, or an install path.
- **Plugin-only scaffolders** (`claude plugin init`, `ivan-magda/claude-code-plugin-template`) — plugin shell only. No CLI binary, no MCP, no install.sh.
- **Anthropic's guided scaffolders** (`/plugin-dev:create-plugin`, `mcp-server-dev`) — comprehensive but chat-driven multi-phase workflows, not one-shot CLIs. They assume the TS SDK or FastMCP. No curl-install, no brief command.
- **Yeoman-style general generators** — lost precisely by being too general. The winning shape is a sharply-opinionated `create-X`, not a meta-framework.

### Why create-ai-cli survives

- It owns the **full bundle**. Every competitor picks one surface; the wired-together four-surface output is genuinely greenfield.
- The demo is **shorter than the official path**. `pipx run create-ai-cli my-tool` finishes in ~30s with a publishable tool. Anthropic's `/plugin-dev:create-plugin` is a multi-minute interactive chat.
- The **stdlib-only / curl-install / no-Node** wedge is one Anthropic culturally won't take — their tooling is SDK-first (TS SDK, FastMCP). We occupy the minimalist niche: zero deps, hostile to supply chain, friendly to restricted corp envs.
- NDA-clean: this is meta-tooling about tool authoring. It never touches any domain — the output is empty scaffolding the user fills in.

---

## The opinion (the brand)

The brand IS the opinion. Repeat verbatim — README, ADRs, commit messages, any future writing.

- **AI tooling should install with one shell line, no Node.** The install command is the first user experience, and most AI tooling fails it on day one.
- **The scaffolder embodies what it promotes.** create-ai-cli is stdlib-only, so its output is stdlib-only. A generator that drags in deps while preaching zero-deps is a lie.
- **The full bundle, or it's just another single-surface scaffolder.** CLI + plugin + skill + MCP + brief ship together. That bundle is the only thing that beats the official tools.
- **The brief command is the stickiness.** Every scaffolded tool gets `<name> brief` — a Markdown context block for AI session bootstrap. The scaffold is a one-time thrill; the brief pattern pays off every session.
- **Empty scaffolds, not vertical starter kits.** We generate structure, not domain logic. No opinions baked into the templates beyond "this is how the surfaces wire together."

### Anti-positioning — what we will NOT do

- No Node. No `npx` for v0.1 — being Python-first reinforces the stdlib-only angle.
- No runtime dependencies, in the scaffolder or its output.
- No domain-flavored templates. The output is generic.
- No "AI-powered" / "revolutionary" copy. We sound like the engineer who shipped this three times and got tired of the boilerplate.
- No hosted service, no telemetry, no account.

### Reference engineers (study their posture, not their content)

- **The `create-X` lineage** — `create-react-app`, `create-vite`, `create-t3-app`. Own a `create-X` name, own the first 30 seconds. The brand IS the install command.
- **Simon Willison** — `llm`, `files-to-prompt`: stdlib-leaning discipline, ship + explain + move on.
- **Mitchell Hashimoto** — ship what works, treat the install as a feature.

---

## v0.1 scope summary

**DoD:** `pipx run create-ai-cli my-tool` produces a working CLI + Claude Code plugin + MCP server + skill + brief + install.sh + CI, wired up. 60 seconds from invocation to "Claude can use my tool."

**Architecture:**
- Templates live in `src/create_ai_cli/templates/` as plain files.
- Rendering via stdlib `string.Template` or hand-rolled `{{var}}` substitution — no `jinja2`.
- Render into the user's chosen output directory.
- All four surfaces by default; `--no-plugin`, `--no-mcp`, `--no-skill` to skip pieces.
- Interactive prompts (tool name, one-line description, commands, license) and flag-based (`--commands list,scan --license MIT --no-mcp`) both work. Defaults: stdlib Python, all surfaces on, MIT.

**What gets emitted (v0.1):**
- `src/<name>/cli.py` — argparse CLI with one working command + a pre-wired `brief` subcommand
- `src/<name>/mcp.py` — stdio MCP server, single file, stdlib JSON over stdin/stdout
- `bin/<name>` — launcher shim
- `plugins/<name>/.claude-plugin/plugin.json`
- `plugins/<name>/commands/<cmd>.md` per command
- `plugins/<name>/skills/<name>-bootstrap/SKILL.md` — auto-loading skill referencing `<name> brief`
- `install.sh`, `pyproject.toml`, `.github/workflows/ci.yml`, `README.md`

**Out of scope for v0.1:** Go/Node backends, multiple commands generated up front (start with one, document how to add more), Docker, npm/PyPI publishing of the scaffold, marketplace submission, hooks, agents. Each is a later skill expansion.

---

## Dogfooding (the v0.1 acceptance test)

[redink](https://github.com/danishvirani/redink) is a sister project built on this exact pattern. Its v0.0 shape — README, LICENSE, pyproject, `src/<name>/cli.py`, install.sh, CI, tests, docs — is the reference the scaffolder must reproduce.

**Final v0.1 acceptance test:** `pipx run create-ai-cli redink` should produce output matching redink's v0.0 scaffold shape. If it does, the scaffolder is correct. (This means matching the shape — not rewriting redink, which is built by other sessions.)

---

## The window

Anthropic ships scaffolders aggressively, and `plugin-dev` will absorb adjacent capability quarterly. **Kill condition:** if Anthropic ships a one-shot `claude plugin create --full` that emits CLI + MCP + skill + install.sh before this lands, the coverage differentiator is gone — pivot to "the opinionated stdlib-only minimalist alternative" or kill. Until then the niche is open, and the 18-month window is real. Ship fast, claim the name, build the demo.

This is a credibility play as much as a usage play. Most plugin authors ship one thing and don't return; realistic v0.1 audience is ~3-5K repeat authors. The name and the demo matter more than the install count.
