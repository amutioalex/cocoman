"""cocoman command-line interface (CLI) entry point.

This module serves as the execution entry point for cocoman, a regression runner for
cocotb-based verification workflows. It handles command-line argument parsing, loads
the runbook, and dispatches execution to the appropriate commands.
"""

from argparse import ArgumentTypeError
from pathlib import Path
from cocoregman.cli.argp import CocomanArgParser
from cocoregman.cli.commands import cmd_list, cmd_list_testbench, cmd_run
from cocoregman.errors import CocomanError, RbError, TbEnvError
from cocoregman.runbook import Runbook


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
    if rb_path.is_dir():
        rb_path = rb_path / ".cocoman"
    if not rb_path.is_file():
        raise ArgumentTypeError(
            0, f"provided runbook path is not a file '{str(rb_path)}'"
        )
    try:
        rbook = Runbook.load_yaml(rb_path)
    except RbError as excp:
        raise excp

    # Commands
    if p_args.command == "list":
        if not p_args.testbench:
            cmd_list(rbook)
        else:
            try:
                cmd_list_testbench(rbook=rbook, tb_name=p_args.testbench[0])
            except (CocomanError, TbEnvError) as excp:
                raise excp

    elif p_args.command == "run":
        tb_names = list(rbook.tbs.keys()) if not p_args.testbench else p_args.testbench
        try:
            cmd_run(
                rbook=rbook,
                dry=p_args.dry,
                tb_names=tb_names,
                ntimes=p_args.ntimes,
                include_tests=p_args.include_tests,
                exclude_tests=p_args.exclude_tests,
                include_tags=p_args.include_tags,
                exclude_tags=p_args.exclude_tags,
            )
        except (CocomanError, TbEnvError) as excp:
            raise excp


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
