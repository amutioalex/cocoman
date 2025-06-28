"""cocoman command-line interface (CLI) entry point.

This module serves as the execution entry point for cocoman, a regression runner for
cocotb-based verification workflows. It handles command-line argument parsing, loads
the runbook, and dispatches execution to the appropriate commands.
"""

from argparse import ArgumentTypeError
from pathlib import Path
from cocoregman.cli.argp import CocomanArgParser
from cocoregman.cli.commands import cmd_list, cmd_run
from cocoregman.core.orchestrator import Filtering
from cocoregman.core.runbook import Runbook
from cocoregman.errors import CocomanError, RbError, TbEnvError


def _exec_thread() -> None:
    """Execute the main cocoman processing flow. Parses arguments, loads the runbook,
    and executes the requested command.

    Raises:
        ArgumentTypeError: If the path to the runbook does not point to an existent file.
        RbError: If an error is found while loading the runbook.
        CocomanError: If an error is found while running a command.
        TbEnvError: If an error is found while running a command.
    """
    cmn_p = CocomanArgParser()
    p_args = cmn_p.parse_args()

    # Obtain runbook
    rb_path: Path = p_args.runbook.resolve()
    rb_path = rb_path if rb_path.is_file() else rb_path / ".cocoman"
    if not rb_path.exists():
        raise ArgumentTypeError(
            f"provided runbook path is not an existing file '{str(rb_path)}'"
        )
    rbook = Runbook.load_from_yaml(rb_path)

    # Commands
    if p_args.command == "list":
        tb = None if not p_args.testbench else p_args.testbench[0]
        cmd_list(rbook, tb)

    elif p_args.command == "run":
        tb_names = list(rbook.tbs.keys()) if not p_args.testbench else p_args.testbench
        criteria = Filtering(
            tb_names,
            p_args.include_tests,
            p_args.exclude_tests,
            p_args.include_tags,
            p_args.exclude_tags,
        )
        cmd_run(rbook, criteria, p_args.ntimes, p_args.dry)


def main() -> None:
    """Main entry point for cocoman execution. Call '_exec_thread' to process commands
    and handle top-level exceptions.
    """
    try:
        _exec_thread()
    except (RbError, CocomanError, TbEnvError) as excp:
        print(excp)


if __name__ == "__main__":
    main()
