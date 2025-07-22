"""Command-line interface (CLI) entry point."""

from argparse import ArgumentTypeError
from typing import TYPE_CHECKING

from cocoregman.cli import CocomanArgParser, cmd_list, cmd_run
from cocoregman.core import Filtering, Runbook
from cocoregman.errors import CocomanError, RbError, TbEnvError

if TYPE_CHECKING:
    from argparse import Namespace
    from pathlib import Path


def _exec_thread() -> None:
    """Execute the main CLI processing flow.

    Parse arguments, validate the runbook path, load the runbook, and dispatch execution
    to the appropriate command.

    Raises:
        ArgumentTypeError: If the runbook path is invalid or does not exist.
        RbError: If an error occurs during runbook loading.
        CocomanError: If a CLI or testbench-related error occurs.
        TbEnvError: If an error occurs while importing a testbench module.
    """
    cmn_p = CocomanArgParser()
    args: Namespace = cmn_p.parse_args()

    # Obtain runbook
    rb_path: Path = args.runbook.resolve()
    rb_file = rb_path if rb_path.is_file() else rb_path / ".cocoman"
    if not rb_file.exists():
        raise ArgumentTypeError(f"Runbook file not found: '{rb_file}'")

    rbook = Runbook.load_from_yaml(rb_file)

    # Commands
    if args.command == "list":
        tb = args.testbench[0] if args.testbench else None
        cmd_list(rbook, tb)

    elif args.command == "run":
        selected = args.testbench or list(rbook.tbs)
        criteria = Filtering(
            tb_names=selected,
            include_tests=args.include_tests,
            exclude_tests=args.exclude_tests,
            include_tags=args.include_tags,
            exclude_tags=args.exclude_tags,
        )
        cmd_run(rbook, criteria, ntimes=args.ntimes, dry=args.dry)


def main() -> None:
    """Entry point for the CLI tool."""
    try:
        _exec_thread()
    except (RbError, CocomanError, TbEnvError) as exc:
        print(f"[cocoman error] {exc}")


if __name__ == "__main__":
    main()
