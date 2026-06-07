"""Tests for the aiscaffold scaffolder.

Covers the CLI surface, the render core (variables + conditionals), and the
scaffold orchestrator across every supported language (full bundle + surface
pruning). For Python it compiles the output; for Go, Rust, and Node it actually
builds/checks, lints, tests, runs the CLI, and exercises a live MCP stdio
roundtrip.
"""

import io
import json
import os
import py_compile
import shutil
import subprocess
from contextlib import redirect_stdout
from pathlib import Path

import pytest

import aiscaffold
from aiscaffold import cli, languages
from aiscaffold.render import (
    TEMPLATES_DIR,
    Context,
    RenderError,
    render_conditionals,
    render_string,
)
from aiscaffold.scaffold import LANGUAGES, template_roots

_REPO_ROOT = Path(aiscaffold.__file__).parents[2]


# --- CLI surface ---------------------------------------------------------


def test_version_constant():
    assert aiscaffold.__version__ == "0.1.0"


def test_help_renders():
    parser = cli.build_parser()
    captured = io.StringIO()
    with redirect_stdout(captured):
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["--help"])
        assert exc.value.code == 0
    out = captured.getvalue()
    assert "aiscaffold" in out
    assert "name" in out
    assert "--no-mcp" in out
    assert "--lang" in out


def test_version_flag():
    captured = io.StringIO()
    with redirect_stdout(captured):
        with pytest.raises(SystemExit) as exc:
            cli.main(["--version"])
        assert exc.value.code == 0
    assert "aiscaffold 0.1.0" in captured.getvalue()


def test_invalid_name_rejected(tmp_path):
    rc = cli.main(["bad name", "-o", str(tmp_path / "x"), "--yes"])
    assert rc == 2


def test_refuses_nonempty_output_dir(tmp_path):
    (tmp_path / "existing.txt").write_text("hi")
    rc = cli.main(["my-tool", "-o", str(tmp_path), "--yes"])
    assert rc == 1


# --- language advisor (--compare + dogfood plugin) -----------------------


def _run_capture(argv):
    """Run cli.main(argv), returning (exit_code, stdout)."""
    captured = io.StringIO()
    with redirect_stdout(captured):
        rc = cli.main(argv)
    return rc, captured.getvalue()


def test_compare_text_covers_every_language():
    rc, out = _run_capture(["--compare"])
    assert rc == 0
    for lang in LANGUAGES:
        assert lang in out
    # It should actually advise, not just list — sanity-check the framing line.
    assert "which --lang" in out


def test_compare_does_not_require_a_name():
    # --compare short-circuits before the name requirement.
    rc, _ = _run_capture(["--compare"])
    assert rc == 0


def test_compare_json_is_valid_and_complete():
    rc, out = _run_capture(["--compare", "--json"])
    assert rc == 0
    data = json.loads(out)
    entries = data["languages"]
    assert {e["id"] for e in entries} == set(LANGUAGES)
    required = {"id", "tagline", "sweet_spot", "strengths", "avoid_when", "runtime_deps", "bundle"}
    for e in entries:
        assert required <= set(e), f"{e['id']} missing keys: {required - set(e)}"
        assert e["strengths"] and e["avoid_when"]


def test_guide_stays_in_lockstep_with_scaffold_languages():
    # Advice must never drift from what's actually scaffoldable, in either
    # direction: every advertised --lang has a guide entry and vice versa.
    assert set(languages.guide_ids()) == set(LANGUAGES)


def test_dogfood_plugin_manifest_is_valid():
    manifest = _REPO_ROOT / "plugins/aiscaffold/.claude-plugin/plugin.json"
    assert manifest.exists(), "aiscaffold should ship its own Claude Code plugin"
    data = json.loads(manifest.read_text())
    assert data["name"] == "aiscaffold"


def test_dogfood_pick_command_wires_to_compare():
    pick = _REPO_ROOT / "plugins/aiscaffold/commands/pick.md"
    assert pick.exists(), "the /aiscaffold:pick advisor command should exist"
    body = pick.read_text()
    # The command's whole design is: read the matrix, then scaffold.
    assert "aiscaffold --compare --json" in body
    assert "--lang" in body


# --- render core ---------------------------------------------------------


def test_render_string_substitutes():
    assert render_string("hi {{name}}", {"name": "bob"}) == "hi bob"


def test_render_string_unknown_var_raises():
    with pytest.raises(RenderError):
        render_string("{{nope}}", {"name": "bob"})


def test_render_string_leaves_single_braces():
    # f-strings / JSON braces / GitHub Actions ${{ }} must survive untouched.
    text = 'f"{x}" and ${{ matrix.os }}'
    assert render_string(text, {}) == text


def test_render_conditionals_keeps_and_drops():
    text = "a\n{{#if on}}\nkept\n{{/if}}\n{{#if off}}\ndropped\n{{/if}}\nb\n"
    out = render_conditionals(text, {"on": True, "off": False})
    assert "kept" in out
    assert "dropped" not in out
    assert out.startswith("a\n")
    assert out.endswith("b\n")


def test_render_conditionals_unbalanced_raises():
    with pytest.raises(RenderError):
        render_conditionals("{{#if on}}\nx\n", {"on": True})


# --- scaffold orchestrator ----------------------------------------------


def _scaffold(tmp_path, lang="python", **flags):
    target = tmp_path / "out"
    args = ["my-tool", "-o", str(target), "--yes", "--commands", "scan", "--lang", lang]
    for f in flags.get("disable", []):
        args.append(f)
    rc = cli.main(args)
    assert rc == 0
    return target


def _assert_python_compiles(root):
    for py_file in root.rglob("*.py"):
        py_compile.compile(str(py_file), doraise=True)


def test_full_bundle(tmp_path):
    out = _scaffold(tmp_path)
    assert (out / "pyproject.toml").exists()
    assert (out / "README.md").exists()
    assert (out / "LICENSE").exists()
    assert (out / ".gitignore").exists()
    assert (out / "install.sh").exists()
    assert (out / ".github/workflows/ci.yml").exists()
    assert (out / "src/my_tool/cli.py").exists()
    assert (out / "src/my_tool/mcp.py").exists()
    assert (out / "src/my_tool/__init__.py").exists()
    assert (out / "tests/test_smoke.py").exists()
    assert (out / "plugins/my-tool/.claude-plugin/plugin.json").exists()
    assert (out / "plugins/my-tool/commands/scan.md").exists()
    assert (out / "plugins/my-tool/skills/my-tool-bootstrap/SKILL.md").exists()
    _assert_python_compiles(out)


def test_install_sh_is_executable(tmp_path):
    out = _scaffold(tmp_path)
    import os

    assert os.access(out / "install.sh", os.X_OK)


def test_substitution_applied(tmp_path):
    out = _scaffold(tmp_path)
    cli_src = (out / "src/my_tool/cli.py").read_text()
    assert "{{" not in cli_src
    assert "def cmd_scan" in cli_src
    assert 'prog="my-tool"' in cli_src


def test_no_mcp_prunes_server_and_references(tmp_path):
    out = _scaffold(tmp_path, disable=["--no-mcp"])
    assert not (out / "src/my_tool/mcp.py").exists()
    cli_src = (out / "src/my_tool/cli.py").read_text()
    assert "cmd_mcp" not in cli_src
    assert "mcp.py" not in cli_src
    _assert_python_compiles(out)


def test_no_plugin_prunes_plugin_dir(tmp_path):
    out = _scaffold(tmp_path, disable=["--no-plugin"])
    assert not (out / "plugins").exists()


def test_no_skill_keeps_plugin_drops_skill(tmp_path):
    out = _scaffold(tmp_path, disable=["--no-skill"])
    assert (out / "plugins/my-tool/.claude-plugin/plugin.json").exists()
    assert not (out / "plugins/my-tool/skills").exists()


@pytest.mark.skipif(shutil.which("ruff") is None, reason="ruff not installed")
def test_generated_project_is_ruff_clean(tmp_path):
    # The generated project's own CI runs these; template edits must keep the
    # rendered output format-stable regardless of name length.
    out = _scaffold(tmp_path)
    targets = [str(out / "src"), str(out / "tests")]
    for cmd in (["ruff", "check", *targets], ["ruff", "format", "--check", *targets]):
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"{cmd}\n{result.stdout}\n{result.stderr}"


def test_generated_mcp_handles_initialize(tmp_path):
    out = _scaffold(tmp_path)
    import importlib.util

    spec = importlib.util.spec_from_file_location("gen_mcp", out / "src/my_tool/mcp.py")
    module = importlib.util.module_from_spec(spec)
    # mcp.py imports `from my_tool import __version__`; make that resolve.
    import sys

    sys.path.insert(0, str(out / "src"))
    try:
        spec.loader.exec_module(module)
        resp = module.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        assert resp["result"]["serverInfo"]["name"] == "my-tool"
    finally:
        sys.path.remove(str(out / "src"))


# --- multi-language plumbing ---------------------------------------------


def test_context_carries_lang():
    assert Context(name="x").as_dict()["lang"] == "python"
    assert Context(name="x", lang="go").as_dict()["lang"] == "go"


def test_advertised_languages_have_template_trees():
    # Never advertise a --lang choice without a real tree behind it.
    for lang in LANGUAGES:
        assert (TEMPLATES_DIR / lang).is_dir(), f"advertised lang {lang!r} has no templates/"


def test_shared_tree_merges_into_every_language():
    # The plugin/skill surfaces live only in _shared; each language inherits them.
    for lang in LANGUAGES:
        roots = template_roots(lang)
        assert roots[0].name == "_shared"
        assert roots[1].name == lang


def test_rejects_unimplemented_language(tmp_path):
    # argparse choices guard: an unbuilt language exits 2 (argparse raises
    # SystemExit) rather than emitting a broken shared-only scaffold.
    with pytest.raises(SystemExit) as exc:
        cli.main(["my-tool", "-o", str(tmp_path / "x"), "--yes", "--lang", "cobol"])
    assert exc.value.code == 2


def test_no_conditional_markers_leak_in_any_language(tmp_path):
    # The renderer's {{#if}}/{{/if}} conditionals are line-based: a marker must
    # own its line. An inline marker is silently left as literal text (it lands
    # in a comment, so the toolchain never complains) — this guard catches that
    # for every language, in both the full bundle and the --no-mcp variant.
    # NB: GitHub Actions ${{ ... }} is legal output, so we only forbid the
    # conditional markers themselves, not all double-braces.
    for lang in LANGUAGES:
        for tag, disable in (("full", []), ("nomcp", ["--no-mcp"])):
            target = tmp_path / f"{lang}-{tag}"
            args = ["my-tool", "-o", str(target), "--yes", "--lang", lang, *disable]
            assert cli.main(args) == 0
            for path in target.rglob("*"):
                if not path.is_file():
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                assert "{{#if" not in text, f"leftover {{#if}} in {lang} {path}"
                assert "{{/if}}" not in text, f"leftover {{/if}} in {lang} {path}"


# --- Go end-to-end (skipped when the toolchain is absent) ----------------

_GO = shutil.which("go")


def _go_env():
    # GOTOOLCHAIN=local keeps `go` from trying to fetch a toolchain offline.
    return {**os.environ, "GOTOOLCHAIN": "local"}


@pytest.mark.skipif(_GO is None, reason="go not installed")
def test_go_full_bundle_builds_vets_tests(tmp_path):
    out = _scaffold(tmp_path, lang="go")
    assert (out / "go.mod").exists()
    assert (out / "cmd/my-tool/main.go").exists()
    assert (out / "internal/mcp/mcp.go").exists()
    assert (out / "README.md").exists()
    assert (out / "install.sh").exists()
    assert (out / ".github/workflows/ci.yml").exists()
    # Shared surfaces come along for the ride.
    assert (out / "LICENSE").exists()
    assert (out / "plugins/my-tool/.claude-plugin/plugin.json").exists()
    assert (out / "plugins/my-tool/commands/scan.md").exists()

    fmt = subprocess.run(["gofmt", "-l", "."], cwd=out, capture_output=True, text=True)
    assert fmt.stdout.strip() == "", f"gofmt flagged:\n{fmt.stdout}"
    for cmd in (["go", "vet", "./..."], ["go", "build", "./..."], ["go", "test", "./..."]):
        r = subprocess.run(cmd, cwd=out, capture_output=True, text=True, env=_go_env())
        assert r.returncode == 0, f"{cmd}\n{r.stdout}\n{r.stderr}"


@pytest.mark.skipif(_GO is None, reason="go not installed")
def test_go_binary_runs_cli_and_mcp(tmp_path):
    out = _scaffold(tmp_path, lang="go")
    binary = tmp_path / "my-tool-bin"
    build = subprocess.run(
        ["go", "build", "-o", str(binary), "./cmd/my-tool"],
        cwd=out,
        capture_output=True,
        text=True,
        env=_go_env(),
    )
    assert build.returncode == 0, build.stderr

    ran = subprocess.run([str(binary), "scan"], capture_output=True, text=True)
    assert ran.returncode == 0 and ran.stdout.strip()

    brief = subprocess.run([str(binary), "brief"], capture_output=True, text=True)
    assert "my-tool" in brief.stdout

    mcp = subprocess.run(
        [str(binary), "mcp"],
        input='{"jsonrpc": "2.0", "id": 1, "method": "initialize"}\n',
        capture_output=True,
        text=True,
    )
    assert '"serverInfo"' in mcp.stdout
    assert "my-tool" in mcp.stdout


@pytest.mark.skipif(_GO is None, reason="go not installed")
def test_go_no_mcp_prunes_and_still_builds(tmp_path):
    out = _scaffold(tmp_path, lang="go", disable=["--no-mcp"])
    assert not (out / "internal/mcp/mcp.go").exists()
    main_src = (out / "cmd/my-tool/main.go").read_text()
    assert "internal/mcp" not in main_src
    assert "mcp.Serve" not in main_src
    r = subprocess.run(
        ["go", "build", "./..."], cwd=out, capture_output=True, text=True, env=_go_env()
    )
    assert r.returncode == 0, r.stderr


# --- Rust end-to-end (skipped when the toolchain is absent) --------------

_CARGO = shutil.which("cargo")


@pytest.mark.skipif(_CARGO is None, reason="cargo not installed")
def test_rust_full_bundle_fmt_builds_tests(tmp_path):
    out = _scaffold(tmp_path, lang="rust")
    assert (out / "Cargo.toml").exists()
    assert (out / "src/main.rs").exists()
    assert (out / "src/mcp.rs").exists()
    assert (out / "README.md").exists()
    assert (out / "install.sh").exists()
    assert (out / ".github/workflows/ci.yml").exists()
    # Shared surfaces come along for the ride.
    assert (out / "LICENSE").exists()
    assert (out / "plugins/my-tool/.claude-plugin/plugin.json").exists()
    assert (out / "plugins/my-tool/commands/scan.md").exists()
    # serde_json is declared only when the MCP server is present.
    assert "serde_json" in (out / "Cargo.toml").read_text()

    fmt = subprocess.run(["cargo", "fmt", "--check"], cwd=out, capture_output=True, text=True)
    assert fmt.returncode == 0, f"cargo fmt flagged:\n{fmt.stdout}\n{fmt.stderr}"
    for cmd in (["cargo", "build"], ["cargo", "test"]):
        r = subprocess.run(cmd, cwd=out, capture_output=True, text=True)
        assert r.returncode == 0, f"{cmd}\n{r.stdout}\n{r.stderr}"


@pytest.mark.skipif(_CARGO is None, reason="cargo not installed")
def test_rust_binary_runs_cli_and_mcp(tmp_path):
    out = _scaffold(tmp_path, lang="rust")
    build = subprocess.run(["cargo", "build", "--release"], cwd=out, capture_output=True, text=True)
    assert build.returncode == 0, build.stderr
    binary = out / "target/release/my-tool"

    ran = subprocess.run([str(binary), "scan"], capture_output=True, text=True)
    assert ran.returncode == 0 and ran.stdout.strip()

    brief = subprocess.run([str(binary), "brief"], capture_output=True, text=True)
    assert "my-tool" in brief.stdout

    mcp = subprocess.run(
        [str(binary), "mcp"],
        input='{"jsonrpc": "2.0", "id": 1, "method": "initialize"}\n',
        capture_output=True,
        text=True,
    )
    assert '"serverInfo"' in mcp.stdout
    assert "my-tool" in mcp.stdout


@pytest.mark.skipif(_CARGO is None, reason="cargo not installed")
def test_rust_no_mcp_prunes_and_still_builds(tmp_path):
    out = _scaffold(tmp_path, lang="rust", disable=["--no-mcp"])
    assert not (out / "src/mcp.rs").exists()
    main_src = (out / "src/main.rs").read_text()
    assert "mod mcp" not in main_src
    assert "mcp::serve" not in main_src
    # No MCP server means no JSON dependency at all — back to zero deps.
    assert "serde_json" not in (out / "Cargo.toml").read_text()
    r = subprocess.run(["cargo", "build"], cwd=out, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


# --- Node end-to-end (skipped when the toolchain is absent) --------------

_NODE = shutil.which("node")


@pytest.mark.skipif(_NODE is None, reason="node not installed")
def test_node_full_bundle_checks_and_tests(tmp_path):
    out = _scaffold(tmp_path, lang="node")
    assert (out / "package.json").exists()
    assert (out / "src/cli.js").exists()
    assert (out / "src/mcp.js").exists()
    assert (out / "test/cli.test.js").exists()
    assert (out / "test/mcp/roundtrip.test.js").exists()
    assert (out / "README.md").exists()
    assert (out / "install.sh").exists()
    assert (out / ".github/workflows/ci.yml").exists()
    # Shared surfaces come along for the ride.
    assert (out / "LICENSE").exists()
    assert (out / "plugins/my-tool/.claude-plugin/plugin.json").exists()
    assert (out / "plugins/my-tool/commands/scan.md").exists()
    # Zero dependencies — no dependencies block in package.json.
    assert "dependencies" not in (out / "package.json").read_text()

    for src in ("src/cli.js", "src/mcp.js"):
        r = subprocess.run(["node", "--check", src], cwd=out, capture_output=True, text=True)
        assert r.returncode == 0, f"node --check {src}\n{r.stderr}"
    t = subprocess.run(["node", "--test"], cwd=out, capture_output=True, text=True)
    assert t.returncode == 0, f"{t.stdout}\n{t.stderr}"


@pytest.mark.skipif(_NODE is None, reason="node not installed")
def test_node_runs_cli_and_mcp(tmp_path):
    out = _scaffold(tmp_path, lang="node")
    cli_js = str(out / "src/cli.js")

    ran = subprocess.run(["node", cli_js, "scan"], capture_output=True, text=True)
    assert ran.returncode == 0 and ran.stdout.strip()

    brief = subprocess.run(["node", cli_js, "brief"], capture_output=True, text=True)
    assert "my-tool" in brief.stdout

    mcp = subprocess.run(
        ["node", cli_js, "mcp"],
        input='{"jsonrpc": "2.0", "id": 1, "method": "initialize"}\n',
        capture_output=True,
        text=True,
    )
    assert '"serverInfo"' in mcp.stdout
    assert "my-tool" in mcp.stdout


@pytest.mark.skipif(_NODE is None, reason="node not installed")
def test_node_no_mcp_prunes_and_still_checks(tmp_path):
    out = _scaffold(tmp_path, lang="node", disable=["--no-mcp"])
    assert not (out / "src/mcp.js").exists()
    assert not (out / "test/mcp").exists()
    cli_src = (out / "src/cli.js").read_text()
    assert "mcp.js" not in cli_src
    r = subprocess.run(["node", "--check", "src/cli.js"], cwd=out, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    t = subprocess.run(["node", "--test"], cwd=out, capture_output=True, text=True)
    assert t.returncode == 0, f"{t.stdout}\n{t.stderr}"
