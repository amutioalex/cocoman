# pylint: disable=import-error
"""Custom argument parser for the cocoman command-line interface (CLI)."""

from argparse import _SubParsersAction, ArgumentParser, ArgumentTypeError
from pathlib import Path
from re import compile as re_compile, error as ReError
from cocoregman import __version__


class CocomanArgParser(ArgumentParser):
    """Custom argument parser for the Cocoman CLI."""

    def __init__(self) -> None:
        """Initialize the custom argument parser and set up the CLI interface."""
        super().__init__()

        self._init_metadata()
        self._init_parser()

    # INITIALIZATION

    def _init_metadata(self) -> None:
        """Initialize parser metadata fields."""
        self.prog = "cmn"
        self.description = "Regression runner for cocotb-based verification workflows."
        self.epilog = "Support available on the GitHub repository."

    def _init_parser(self) -> None:
        """Initialize the argument parser with core arguments and subcommands."""
        self.allow_abbrev = False
        self.add_argument(
            "-V",
            "--version",
            action="version",
            version=__version__,
            help="print the cocoman version number and exit",
        )
        sub_p = self.add_subparsers(
            dest="command",
            metavar="<command>",
            parser_class=ArgumentParser,
            required=True,
        )
        self._config_list_subparser(sub_p)
        self._config_run_subparser(sub_p)

    # SUBPARSERS CONFIGURATION

    def _config_list_subparser(self, parser: _SubParsersAction) -> None:
        """Configure the 'list' subcommand for inspecting runbook contents."""
        list_p = parser.add_parser("list", help="display runbook information")
        list_p.add_argument(
            "runbook",
            default=Path("./"),
            nargs="?",
            metavar="<path>",
            type=Path,
            help="path to runbook or directory containing a '.cocoman' file",
        )
        list_p.add_argument(
            "-t",
            "--testbench",
            default=None,
            dest="testbench",
            nargs=1,
            metavar="<name>",
            type=str,
            help="testbench to inspect",
        )

    def _config_run_subparser(self, parser: _SubParsersAction) -> None:
        """Configure the 'run' subcommand for executing regressions."""
        run_p = parser.add_parser("run", help="run a cocoman regression")
        run_p.add_argument(
            "runbook",
            default=Path("./"),
            nargs="?",
            metavar="<path>",
            type=Path,
            help="path to runbook or directory containing a '.cocoman' file",
        )
        run_p.add_argument(
            "-d",
            "--dry",
            action="store_true",
            dest="dry",
            help="preview execution plan",
        )
        run_p.add_argument(
            "-t",
            "--testbench",
            default=[],
            dest="testbench",
            nargs="+",
            metavar="<name>",
            help="testbench(es) to run",
        )
        run_p.add_argument(
            "-n",
            "--ntimes",
            default=1,
            dest="ntimes",
            metavar="<int>",
            type=int,
            help="number of times each test should be executed",
        )
        run_p.add_argument(
            "-i",
            "--include-tests",
            default=[],
            dest="include_tests",
            metavar="<regex>",
            nargs="+",
            type=self._check_regex,
            help="select specific tests to include in the run",
        )
        run_p.add_argument(
            "-e",
            "--exclude-tests",
            default=[],
            dest="exclude_tests",
            metavar="<regex>",
            nargs="+",
            type=self._check_regex,
            help="select specific tests to exclude from the run",
        )
        run_p.add_argument(
            "-I",
            "--include-tags",
            default=[],
            dest="include_tags",
            metavar="<regex>",
            nargs="+",
            type=self._check_regex,
            help="select specific testbench tags to include in the run",
        )
        run_p.add_argument(
            "-E",
            "--exclude-tags",
            default=[],
            dest="exclude_tags",
            metavar="<regex>",
            nargs="+",
            type=self._check_regex,
            help="select specific testbench tags to exclude from the run",
        )

    # AUX

    @staticmethod
    def _check_regex(regex: str) -> str:
        """Validate a provided string as a compatible regular expression.

        Args:
            regex: Regular expression string.

        Returns:
            The validated regex string.

        Raises:
            ArgumentTypeError: If the regex is invalid or empty.
        """
        if not regex.strip():
            raise ArgumentTypeError("provided regular expression cannot be empty")
        try:
            re_compile(regex)
        except ReError as excp:
            raise ArgumentTypeError(
                f"'{regex}' is not a valid regular expression: {excp}"
            ) from excp
        return regex
