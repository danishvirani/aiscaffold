# Contributing to aiscaffold

aiscaffold is opinionated by design: it scaffolds AI-native CLIs, and it
embodies what it promotes. Contributions are welcome but must respect the
constraints below.

## The three constraints (non-negotiable)

1. **Stdlib-only at runtime — for the scaffolder AND its output.** No `httpx`,
   `pydantic`, `rich`, `click`. `argparse` + `json` + `string.Template` +
   `urllib` + ANSI escapes is the toolbox. The tool that promotes zero-dep AI
   CLIs cannot itself drag in dependencies. See
   [ADR-001](docs/decisions/ADR-001-stdlib-only.md).
2. **The install command stays one shell line forever.** `pipx run aiscaffold`
   or `curl ... | sh`. No Node, no `pip install` + venv dance. Every PR is
   checked against this.
3. **The full bundle is the product.** aiscaffold emits CLI + Claude Code
   plugin + skill + MCP server + brief command together. A change that breaks
   the "one command, all four surfaces" demo doesn't ship.

## Setup

```bash
git clone git@github.com:danishvirani/aiscaffold.git ~/code/aiscaffold
cd ~/code/aiscaffold
./install.sh
pip install -e ".[dev]"
pytest tests/ -v
```

## Workflow

1. Branch from `main`. Naming: `feat-short-desc`, `fix-short-desc`, `docs-short-desc`.
2. Open the PR as a draft. Mark Ready when self-reviewed and CI is green.
3. Add tests for new behavior. Scaffolded output especially needs
   render-then-assert tests (generate into a tmp dir, assert the files exist
   and the generated CLI runs).
4. CI must pass on Python 3.10 / 3.11 / 3.12 across Ubuntu + macOS.

## What we won't merge

- New runtime dependencies (even small ones), in the scaffolder or its output
- Generated scaffolds that require a Node toolchain or an SDK install
- Framework-y abstractions (decorators-as-API, metaclasses, plugin systems)
- Templates that bake in domain-specific content — the output is empty
  scaffolding the user fills in, not a vertical starter kit
- Marketing-shaped commit messages ("revolutionary", "AI-powered", etc.)

## Code style

- `argparse`, not `click`
- `json.loads` + `dataclasses`, not `pydantic`
- `string.Template` / hand-rolled substitution, not `jinja2`
- `print` + ANSI escape constants, not `rich`
- Module-level functions before classes. Classes only when state is real.
- Match the existing patterns in `src/aiscaffold/cli.py`.

## Reporting bugs

Open an issue with: aiscaffold version (`aiscaffold --version`), Python
version, the command you ran, the output you got, the output you expected.
