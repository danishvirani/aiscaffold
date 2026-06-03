"""create-ai-cli entry point.

v0.0: the CLI surface is wired but the scaffolder is a stub. Invoking
`create-ai-cli <name>` exits 1 with a "v0.1 ships the real scaffolder"
message. v0.1 renders the full bundle (CLI + plugin + skill + MCP +
brief + install.sh + CI). See docs/roadmap.md.
"""

import argparse
import sys

from create_ai_cli import __version__


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def cmd_scaffold(args: argparse.Namespace) -> int:
    _eprint(f"create-ai-cli: scaffolder not yet implemented (would generate: {args.name})")
    _eprint("v0.1 ships the real scaffolder: CLI + Claude Code plugin + skill + MCP + brief.")
    _eprint("See docs/roadmap.md for the build sequence.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="create-ai-cli",
        description="Bootstrap a full AI-native CLI stack in 30s: "
        "stdlib CLI + Claude Code plugin + skill + MCP server + brief command.",
        epilog="Full docs at https://github.com/danishvirani/create-ai-cli",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"create-ai-cli {__version__}",
    )
    parser.add_argument(
        "name",
        help="Name of the AI-native CLI to scaffold (e.g. my-tool)",
    )
    parser.add_argument(
        "--no-plugin",
        action="store_true",
        help="Skip the Claude Code plugin surface (v0.1)",
    )
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help="Skip the MCP server surface (v0.1)",
    )
    parser.add_argument(
        "--no-skill",
        action="store_true",
        help="Skip the auto-loading skill surface (v0.1)",
    )
    parser.set_defaults(func=cmd_scaffold)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
