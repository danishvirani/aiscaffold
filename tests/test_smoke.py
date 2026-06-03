"""Smoke tests for the v0.0 scaffold.

These pass before any real scaffolding logic exists. They verify:
- The package imports
- argparse renders --help correctly
- `--version` works
- The scaffold stub exits non-zero with a clear "not yet implemented" message
- No-args errors cleanly
"""

import io
from contextlib import redirect_stderr, redirect_stdout

import pytest

import create_ai_cli
from create_ai_cli import cli


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
    assert "--no-plugin" in out
    assert "--no-mcp" in out
    assert "--no-skill" in out


def test_version_flag_prints_and_exits_zero():
    captured = io.StringIO()
    with redirect_stdout(captured):
        with pytest.raises(SystemExit) as exc:
            cli.main(["--version"])
        assert exc.value.code == 0
    assert "create-ai-cli 0.0.1" in captured.getvalue()


def test_scaffold_stub_returns_nonzero_and_explains():
    captured = io.StringIO()
    with redirect_stderr(captured):
        rc = cli.main(["my-tool"])
    assert rc == 1
    err = captured.getvalue()
    assert "not yet implemented" in err
    assert "roadmap" in err.lower()


def test_scaffold_echoes_name():
    captured = io.StringIO()
    with redirect_stderr(captured):
        rc = cli.main(["my-tool"])
    assert rc == 1
    assert "my-tool" in captured.getvalue()


def test_skip_flags_accepted():
    captured = io.StringIO()
    with redirect_stderr(captured):
        rc = cli.main(["my-tool", "--no-plugin", "--no-mcp", "--no-skill"])
    assert rc == 1
    assert "my-tool" in captured.getvalue()


def test_no_args_errors_cleanly():
    captured = io.StringIO()
    with redirect_stderr(captured):
        with pytest.raises(SystemExit) as exc:
            cli.main([])
        assert exc.value.code != 0
