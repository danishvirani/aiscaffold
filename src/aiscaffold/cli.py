"""aiscaffold entry point.

Scaffolds a full AI-native CLI stack (CLI + Claude Code plugin + skill + MCP
server + brief command) into a new directory. Stdlib-only. Interactive prompts
and flag-based invocation both work.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from aiscaffold import __version__
from aiscaffold.render import Context
from aiscaffold.scaffold import scaffold

_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9-]*$")


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _git_author() -> str:
    try:
        out = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        name = out.stdout.strip()
        if name:
            return name
    except (OSError, subprocess.SubprocessError):
        pass
    return "Your Name"


def _prompt(label: str, default: str) -> str:
    try:
        answer = input(f"{label} [{default}]: ").strip()
    except EOFError:
        return default
    return answer or default


def _interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _build_context(args: argparse.Namespace) -> Context:
    interactive = _interactive() and not args.yes

    description = args.description
    if description is None:
        description = (
            _prompt("Description", "An AI-native CLI.") if interactive else "An AI-native CLI."
        )

    if args.commands is not None:
        raw_commands = args.commands
    elif interactive:
        raw_commands = _prompt("Commands (comma-separated)", "hello")
    else:
        raw_commands = "hello"
    commands = [c.strip() for c in raw_commands.split(",") if c.strip()] or ["hello"]

    author = args.author or _git_author()

    return Context(
        name=args.name,
        description=description,
        commands=commands,
        license=args.license,
        author=author,
        with_plugin=not args.no_plugin,
        with_mcp=not args.no_mcp,
        with_skill=not args.no_skill,
    )


def cmd_scaffold(args: argparse.Namespace) -> int:
    if not _NAME_RE.match(args.name):
        _eprint(f"aiscaffold: invalid name {args.name!r}")
        _eprint("Names must start with a letter and contain only letters, digits, and dashes.")
        return 2

    out_dir = Path(args.output_dir) if args.output_dir else Path.cwd() / args.name
    if out_dir.exists() and any(out_dir.iterdir()):
        _eprint(f"aiscaffold: {out_dir} already exists and is not empty.")
        return 1

    ctx = _build_context(args)
    written = scaffold(ctx, out_dir)

    display = args.output_dir if args.output_dir else ctx.name
    print(f"✓ Scaffolded {ctx.name} — {len(written)} files in {display}/")
    print("")
    print("Next:")
    print(f"  cd {display}")
    print("  ./install.sh")
    print(f"  {ctx.name} {ctx.command}")
    print(f"  {ctx.name} brief")
    if ctx.with_plugin:
        print(f"  claude --plugin-dir ./plugins/{ctx.name}   # use the Claude Code plugin")
    if ctx.with_mcp:
        print(f'  {ctx.name} mcp   # stdio MCP server (command "{ctx.name}", args ["mcp"])')
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aiscaffold",
        description="Bootstrap a full AI-native CLI stack in 30s: "
        "stdlib CLI + Claude Code plugin + skill + MCP server + brief command.",
        epilog="Full docs at https://github.com/danishvirani/aiscaffold",
    )
    parser.add_argument("-V", "--version", action="version", version=f"aiscaffold {__version__}")
    parser.add_argument("name", help="Name of the AI-native CLI to scaffold (e.g. my-tool)")
    parser.add_argument(
        "-o", "--output-dir", default=None, help="Where to write (default: ./<name>)"
    )
    parser.add_argument("--description", default=None, help="One-line description")
    parser.add_argument(
        "--commands", default=None, help="Comma-separated command names (default: hello)"
    )
    parser.add_argument("--license", default="MIT", help="License (default: MIT)")
    parser.add_argument("--author", default=None, help="Author name (default: git user.name)")
    parser.add_argument("--no-plugin", action="store_true", help="Skip the Claude Code plugin")
    parser.add_argument("--no-mcp", action="store_true", help="Skip the MCP server")
    parser.add_argument("--no-skill", action="store_true", help="Skip the auto-loading skill")
    parser.add_argument("-y", "--yes", action="store_true", help="Accept defaults; never prompt")
    parser.set_defaults(func=cmd_scaffold)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
