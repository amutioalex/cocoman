"""Command-line logic and utilities.

This subpackage contains the command-line interface (CLI) components used to interact
with the regression orchestrator framework. It includes:

Modules:
    argp: Argument parser definition.
    commands: CLI command implementations.

Exports:
    CocoregmanArgParser: Custom argument parser for the CLI.
    cmd_list: Command for displaying runbook/testbench information.
    cmd_run: Command for executing regressions with filtering options.
"""

from cocoregman.cli.argp import CocoregmanArgParser
from cocoregman.cli.commands import cmd_list, cmd_run

__all__ = [
    "CocoregmanArgParser",
    "cmd_list",
    "cmd_run",
]
