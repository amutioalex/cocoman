"""Custom argument parser for the command-line interface."""

from argparse import ArgumentParser, ArgumentTypeError, _SubParsersAction
from importlib.metadata import version
from pathlib import Path
from re import compile as re_compile
from re import error as re_error


class CocoregmanArgParser(ArgumentParser):
    """Argument parser for the `cmn` CLI entrypoint."""

    def __init__(self) -> None:
        """Initialize the CLI parser with metadata and subcommands."""
        super().__init__()

        self._init_metadata()
        self._init_parser()

    def _init_metadata(self) -> None:
        """Set up program metadata."""
        self.prog = "cmn"
        self.description = "Regression runner for cocotb-based verification workflows."

    def _init_parser(self) -> None:
        """Initialize CLI arguments and subparsers."""
        self.allow_abbrev = False

        self.add_argument(
            "-V",
            "--version",
            action="version",
            version=version("cocoregman"),
            help="print the version number and exit",
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
            help="path to a runbook or directory containing a '.cocoman' file",
        )
        list_p.add_argument(
            "-t",
            "--testbench",
            default=None,
            dest="testbench",
            nargs=1,
            metavar="<name>",
            type=str,
            help="optional testbench name to inspect",
        )

    def _config_run_subparser(self, parser: _SubParsersAction) -> None:
        """Configure the 'run' subcommand for executing regressions."""
        run_p = parser.add_parser("run", help="run a regression")

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
            help="testbench(es) to include",
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
            help="regex pattern(s) to include specific test names",
        )
        run_p.add_argument(
            "-e",
            "--exclude-tests",
            default=[],
            dest="exclude_tests",
            metavar="<regex>",
            nargs="+",
            type=self._check_regex,
            help="regex pattern(s) to exclude specific test names",
        )
        run_p.add_argument(
            "-I",
            "--include-tags",
            default=[],
            dest="include_tags",
            metavar="<regex>",
            nargs="+",
            type=self._check_regex,
            help="regex pattern(s) to include specific testbench tags",
        )
        run_p.add_argument(
            "-E",
            "--exclude-tags",
            default=[],
            dest="exclude_tags",
            metavar="<regex>",
            nargs="+",
            type=self._check_regex,
            help="regex pattern(s) to exclude specific testbench tags",
        )

    @staticmethod
    def _check_regex(regex: str) -> str:
        """Validate a regular expression string.

        Args:
            regex: A string representing the regex pattern.

        Returns:
            The original string if it is a valid regex.

        Raises:
            ArgumentTypeError: If the regex is invalid or empty.
        """
        if not regex.strip():
            raise ArgumentTypeError("provided regular expression cannot be empty")

        try:
            re_compile(regex)
        except re_error as exc:
            raise ArgumentTypeError(f"Invalid regex '{regex}': {exc}") from exc

        return regex
