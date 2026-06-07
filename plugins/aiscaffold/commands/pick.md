---
description: Recommend the best language for an AI-native CLI, then scaffold it
---

The user wants to build a tool (a CLI, an MCP server, a Claude Code plugin — or
all of them at once). Your job: recommend the language that actually fits *this*
project, then scaffold it with aiscaffold. Do **not** default to TypeScript or
Next.js out of habit — that reflex is exactly what this command exists to
counter. Pick by the work, not the habit.

## 1. Understand the project

Use what the user told you in `$ARGUMENTS` plus the surrounding conversation and
repo. If you don't yet know these, ask briefly (one short round, not an
interrogation):

- What does the tool *do*? (glue/automation, a network service, a parser, a
  systems utility, frontend-adjacent tooling, data/ML work…)
- How will it be distributed? (a `pip install`, a single static binary, an npm
  package, run from source…)
- Who maintains it, and what are they fluent in?
- Any hard constraints — performance, cold-start latency, zero-dependency
  install, an existing ecosystem the team already lives in?

## 2. Consult the decision matrix

Run this and read the result — it is aiscaffold's opinionated, dependency-free
matrix of each language's sweet spot, strengths, and when to avoid it:

```bash
aiscaffold --compare --json
```

(If the `aiscaffold` command isn't on PATH, fall back to
`pipx run aiscaffold --compare --json`.)

## 3. Recommend — with a real rationale

Map the project to the matrix and recommend **one** of `python`, `go`, `rust`,
`node`. Give a 2–4 sentence rationale that references *this* project's specifics
and the matrix's "best for" / "avoid when" lines — not generic language
trivia. If it's genuinely a close call between two, say so and name the
tie-breaker. Be honest when the popular default is the wrong fit here.

## 4. Scaffold it

Confirm the choice with the user, then scaffold (all four surfaces by default):

```bash
aiscaffold <name> --lang <choice>
```

Pass through anything else they specified — `--description`, `--commands`,
`--no-mcp`, `--no-plugin`, `--no-skill`, `-o <dir>`. Then summarize what was
generated and the next steps it printed (`cd`, `./install.sh`, run the command,
`<name> brief`).
