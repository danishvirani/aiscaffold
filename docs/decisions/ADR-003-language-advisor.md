# ADR-003: the language advisor lives in the plugin, the data lives in the CLI

Date: 2026-06-07
Status: Accepted
Deciders: Danish Virani
Builds on: [ADR-002](ADR-002-multi-language.md)

## Context

ADR-002 made aiscaffold multi-language. That unlocked a capability the
single-language version couldn't have: helping an author *choose* the language,
not just scaffold one they already picked.

The motivating observation: coding assistants reach for TypeScript/Next.js by
default, regardless of whether the project wants it. A multi-language scaffolder
is the natural place to push back — "here's a tool that makes Go, Rust, or
Python a one-liner, and will tell you which one actually fits." So aiscaffold
should be able to answer "which `--lang` is best for the project I'm doing?"

This is **one feature among several**, not a new identity. aiscaffold is still a
scaffolder first; the advisor is a capability the multi-language design enables.

The design tension: a good recommendation requires reasoning about a *specific*
project. But the aiscaffold CLI is deliberately stdlib-only and dependency-free
(ADR-001 §3, carried into ADR-002) — it has no model to reason with, and pulling
one in would break the one-line, zero-dependency install that is the whole pitch.

## Decision

**Split the advisor across two layers:**

1. **Data in the CLI (dumb, deterministic, dependency-free).**
   `aiscaffold --compare` prints an opinionated decision matrix — per language:
   sweet spot, strengths, when to reach for something else, runtime deps, and the
   generated stack shape. `aiscaffold --compare --json` emits the same matrix as
   JSON for machine consumption. The data is a single source of truth in
   `src/aiscaffold/languages.py`. No project-specific reasoning, no network, no
   model — just curated, opinionated reference data.

2. **Reasoning in the plugin (where an LLM actually is).** aiscaffold ships its
   own Claude Code plugin at `plugins/aiscaffold/`, with an `/aiscaffold:pick`
   command. It instructs Claude to understand the project from context (asking a
   short clarifying round if needed), read the matrix via
   `aiscaffold --compare --json`, recommend one language with a rationale that
   cites *this* project's specifics, and then run `aiscaffold <name> --lang
   <choice>`. The intelligence rides on the surface that already has a model.

This mirrors the architecture's existing division of labor: the generated MCP
servers are dumb stdio loops, and intelligence lives in the agent that drives
them. The advisor follows the same shape — dumb data, smart driver.

### Why aiscaffold dogfoods its own plugin

Until now aiscaffold only *generated* Claude Code plugins; it didn't ship one.
Putting the advisor in `plugins/aiscaffold/` makes aiscaffold the first consumer
of the exact surface it sells. If the plugin/command shape is awkward to use, we
feel it ourselves first.

## Consequences

**Good:**

1. The wedge is intact — `pipx run aiscaffold` stays instant and dependency-free;
   no LLM dependency leaks into the CLI.
2. `--compare`/`--json` is independently useful: a human can read the matrix, and
   any tool (not just Claude) can consume the JSON.
3. aiscaffold dogfoods the plugin surface it generates.
4. The matrix is one curated data structure, testable in isolation, kept in
   lockstep with `scaffold.LANGUAGES` by a test — advice can never drift out of
   sync with what's actually scaffoldable.

**Bad — accepted:**

1. The recommendation quality depends on the driving model and the prompt in
   `pick.md`, which can rot as conventions change (the ADR-002 template-rot risk,
   now extended to the command prompt).
2. Two places to keep honest when adding a language: the template tree *and* the
   matrix entry. The lockstep test makes the second a hard failure, not a silent
   gap.
3. The opinion in the matrix is exactly that — opinionated. Reasonable people
   will disagree with a "reach for something else when" line. That's the point;
   bland advice helps no one. We revise the data as we learn.

## When this is wrong

- If the `--compare` data and the `/pick` prompt drift apart in practice, collapse
  them: have `pick.md` embed the guidance inline and drop the JSON dependency.
- If a future aiscaffold gains a legitimate reason to carry an LLM client (it
  won't lightly), the split could fold back into the CLI. Not anticipated.

## References

- ADR-001 §3 / ADR-002 §3 — the scaffolder stays stdlib-only Python. This ADR is
  a direct consequence: the advisor's reasoning *cannot* live in the CLI.
- `src/aiscaffold/languages.py` — the matrix data.
- `plugins/aiscaffold/commands/pick.md` — the advisor command.
