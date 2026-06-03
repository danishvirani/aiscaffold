"""Tests for the create-ai-cli scaffolder.

Covers the CLI surface, the render core (variables + conditionals), and the
scaffold orchestrator (full bundle + surface pruning), including a compile
check that every generated Python file is syntactically valid.
"""

import io
import py_compile
import shutil
import subprocess
from contextlib import redirect_stdout

import pytest

import create_ai_cli
from create_ai_cli import cli
from create_ai_cli.render import RenderError, render_conditionals, render_string


# --- CLI surface ---------------------------------------------------------


def test_version_constant():
    assert create_ai_cli.__version__ == "0.0.1"


def test_help_renders():
    parser = cli.build_parser()
    captured = io.StringIO()
    with redirect_stdout(captured):
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["--help"])
        assert exc.value.code == 0
    out = captured.getvalue()
    assert "create-ai-cli" in out
    assert "name" in out
    assert "--no-mcp" in out


def test_version_flag():
    captured = io.StringIO()
    with redirect_stdout(captured):
        with pytest.raises(SystemExit) as exc:
            cli.main(["--version"])
        assert exc.value.code == 0
    assert "create-ai-cli 0.0.1" in captured.getvalue()


def test_invalid_name_rejected(tmp_path):
    rc = cli.main(["bad name", "-o", str(tmp_path / "x"), "--yes"])
    assert rc == 2


def test_refuses_nonempty_output_dir(tmp_path):
    (tmp_path / "existing.txt").write_text("hi")
    rc = cli.main(["my-tool", "-o", str(tmp_path), "--yes"])
    assert rc == 1


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


def _scaffold(tmp_path, **flags):
    target = tmp_path / "out"
    args = ["my-tool", "-o", str(target), "--yes", "--commands", "scan"]
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
