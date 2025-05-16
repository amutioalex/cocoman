"""cocoman argument parser module.

This module provides the command-line interface (CLI) for the cocoman tool, including
argument parsing and command handling.
"""

from argparse import ArgumentParser
from pathlib import Path
import re
from types import ModuleType
from typing import Any, Dict, List
from warnings import filterwarnings
from cocotb.decorators import test as cctb_test

# Suppress warning when importing from cocotb.runner
filterwarnings("ignore")
from cocotb.runner import get_runner
filterwarnings("default")

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from cocoregman import __version__
from cocoregman.runbook import Runbook
from cocoregman.tbenv import load_includes, load_n_import_tb, TbEnvImportError


# EXCEPTIONS #


class CocomanError(Exception):
    """Base exception class for errors encountered during command-line processing."""

    def __init__(self, err_prefix: str, tag_id: int, message: str) -> None:
        """Initialize a generic CocomanError with a given message.

        Args:
            err_prefix: The sub-error prefix name.
            tag_id: The specific error tag number id.
            message: Description of the error.
        """
        super().__init__(message)
        self.prefix = err_prefix
        self.tag_id = tag_id
        self.message = message

    def __str__(self) -> str:
        """Return a string representation of the error.

        Returns:
            The error message.
        """
        return f"CM{self.prefix}-{self.tag_id}: {self.message}"


class CocomanNameError(CocomanError):
    """Raised when an unrecognized testbench or test name is found."""

    def __init__(self, tag_id: int, message: str) -> None:
        """Initialize a CocomanNameError with a prefixed message.

        Args:
            tag_id: The specific error tag number id.
            message: Description of the naming-related error.
        """
        super().__init__("N", tag_id=tag_id, message=message)


class CocomanArgError(CocomanError):
    """Raised when an command-line argument is not an expected type or value."""

    def __init__(self, tag_id: int, message: str) -> None:
        """Initialize a CocomanArgError with a prefixed message.

        Args:
            tag_id: The specific error tag number id.
            message: Description of the naming-related error.
        """
        super().__init__("A", tag_id=tag_id, message=message)


# BUILDER #


def get_cmn_parser() -> ArgumentParser:
    """Create and configure the main ArgumentParser for cocoman.

    Returns:
        Configured parser instance.
    """
    base_p = ArgumentParser(
        "cmn",
        description="Regression runner for cocotb-based verification",
    )
    base_p.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
        help="show current cocoman version",
    )
    sub_p = base_p.add_subparsers(dest="command", metavar="COMMAND", required=True)
    list_p = sub_p.add_parser("list", help="display runbook information")
    list_p.add_argument(
        "runbook",
        action="store",
        default="./",
        nargs="?",
        metavar="RUNBOOK",
        type=Path,
        help="path to runbook file or directory containing a '.cocoman' runbook file",
    )
    list_p.add_argument(
        "-t",
        "--testbench",
        action="store",
        default=None,
        nargs=1,
        metavar="TBNAME",
        required=False,
        help="specify testbench name to inspect",
    )
    run_p = sub_p.add_parser("run", help="run a cocotb testbench")
    run_p.add_argument(
        "runbook",
        action="store",
        default="./",
        nargs="?",
        metavar="RUNBOOK",
        type=Path,
        help="path to runbook file or directory containing a '.cocoman' runbook file",
    )
    run_p.add_argument(
        "-d",
        "--dry",
        action="store_true",
        dest="dry",
        required=False,
        help="preview execution plan without simulating",
    )
    run_p.add_argument(
        "-t",
        "--testbench",
        action="store",
        default=[],
        nargs="+",
        metavar="TBNAME",
        required=False,
        help="specify testbench(es) to run",
    )
    run_p.add_argument(
        "-n",
        "--ntimes",
        action="store",
        default=[1],
        dest="ntimes",
        nargs=1,
        required=False,
        type=int,
        help="number of times each test should be executed",
    )
    run_p.add_argument(
        "-i",
        "--include-tests",
        action="store",
        default=[],
        dest="include_tests",
        metavar="TSTNAME",
        nargs="+",
        required=False,
        type=_check_regex,
        help="select specific tests to include in the run",
    )
    run_p.add_argument(
        "-e",
        "--exclude-tests",
        action="store",
        default=[],
        dest="exclude_tests",
        metavar="TSTNAME",
        nargs="+",
        required=False,
        type=_check_regex,
        help="select specific tests to exclude from the run",
    )
    run_p.add_argument(
        "-I",
        "--include-tags",
        action="store",
        default=[],
        dest="include_tags",
        metavar="TAGNAME",
        nargs="+",
        required=False,
        type=_check_regex,
        help="select specific testbench tags to include in the run",
    )
    run_p.add_argument(
        "-E",
        "--exclude-tags",
        action="store",
        default=[],
        dest="exclude_tags",
        metavar="TAGNAME",
        nargs="+",
        required=False,
        type=_check_regex,
        help="select specific testbench tags to exclude from the run",
    )
    return base_p


# AUXILIARY FUNCTIONS #


def _check_regex(regex: str) -> str:
    """Check if a provided string is a valid regular expression that can be compiled and
    used to perform pattern matching.

    Args:
        regex: The string that contains the regular expression.

    Returns:
        The regex string.

    Raises:
        CocomanArgError: If the provided string does not contain a valid regex.
    """
    if not regex.strip():
        raise CocomanArgError(0, "provided regular expression cannot be void")
    try:
        re.compile(regex)
    except re.error as excp:
        raise CocomanArgError(1, f"'{regex}' is not a valid regular expression: {excp}")
    return regex


def _check_testbench_name(rbook: Runbook, tb_name: str) -> None:
    """Check if a testbench name exists in the provided Runbook.

    Args:
        rbook: The Runbook to inspect.
        tb_name: The testbench name to check.

    Raises:
        CocomanNameError: If the testbench name is not found in the Runbook.
    """
    if tb_name not in rbook.tbs:
        valid_tbs = ", ".join(rbook.tbs.keys())
        raise CocomanNameError(
            0, f"testbench  '{tb_name}' not found\navailable: {valid_tbs}"
        )


def _get_test_names(tb_pkg: ModuleType) -> List[str]:
    """Retrieve test names from a testbench module.

    Args:
        tb_pkg: The Python module to inspect.

    Returns:
        A list of test names identified within the module.
    """
    return [
        name for name in dir(tb_pkg) if isinstance(getattr(tb_pkg, name), cctb_test)
    ]


def _str_in_regex_list(text: str, regexs: List[str]) -> bool:
    """Check if a provided string matches fully any of the valid regular expressions of
    a given list.

    Args:
        text: The string to check.
        regexs: The list of valid regular expressions.

    Returns:
        True if the string matches any of the regex in the list, otherwise False.
    """
    return any(re.fullmatch(rgx, text) for rgx in regexs)


# COMMANDS #


def cmd_list(rbook: Runbook) -> None:
    """Display a general overview of the provided Runbook and its testbenches.

    Args:
        rbook: The Runbook object to display information from.
    """
    property_c, value_c, accent_c = "bold cornflower_blue", "white", "light_sea_green"
    console = Console()

    # RUNBOOK CONFIGURATION #
    console.print()
    rb_table = Table(
        box=box.SIMPLE,
        show_header=False,
        title="RUNBOOK CONFIGURATION",
        title_justify="left",
        title_style="u bold",
    )
    rb_table.add_column(style=property_c)
    rb_table.add_column(style=value_c)
    rb_table.add_row("Simulator", rbook.sim, end_section=True)

    if rbook.srcs:
        src_table = Table(show_header=False)
        src_table.add_column(style=accent_c)
        src_table.add_column(style=value_c)
        for index, path in rbook.srcs.items():
            src_table.add_row(str(index), str(path))
        rb_table.add_row("Sources", src_table, end_section=True)

    if rbook.include:
        rb_table.add_row(
            "Include", "\n".join(map(str, rbook.include)), end_section=True
        )
    console.print(rb_table, justify="left")

    # TESTBENCHES #
    console.print()
    tb_table = Table(
        box=box.SIMPLE,
        header_style="italic",
        show_header=True,
        title="TESTBENCHES",
        title_justify="left",
        title_style="u bold",
    )
    tb_table.add_column(header="Name", style=property_c)
    tb_table.add_column(header="RTL Top", style=value_c)
    tb_table.add_column(header="TB Top", style=value_c)
    tb_table.add_column(header="Sources", style=accent_c)

    for tb_name, tb_info in rbook.tbs.items():
        tb_table.add_row(
            tb_name,
            tb_info.rtl_top,
            tb_info.tb_top,
            ", ".join(map(str, tb_info.srcs)),
        )

    console.print(tb_table, justify="left")
    console.print()


def cmd_list_testbench(rbook: Runbook, tb_name: str) -> None:
    """Display detailed information about a specific testbench within a Runbook.

    Args:
        rbook: The Runbook containing the testbenches.
        tb_name: The name of the testbench to inspect.

    Raises:
        CocomanNameError: If the testbench name is invalid.
        TbEnvImportError: If the top testbench module could not be imported.
    """
    try:
        _check_testbench_name(rbook=rbook, tb_name=tb_name)
        load_includes(rbook)
        tb_info = rbook.tbs[tb_name]
        tb_pkg = load_n_import_tb(tb_info)
        tb_tests = _get_test_names(tb_pkg)
    except (CocomanNameError, TbEnvImportError) as excp:
        raise excp

    property_c, value_c, accent_c = "bold cornflower_blue", "white", "light_sea_green"
    console = Console()

    def get_docstr(obj: Any) -> str:
        """Safely return the docstring of an object.

        Args:
            obj: Any Python object to extract the docstring from.

        Returns:
            The object's docstring if it exists, otherwise an empty string.
        """
        return obj.__doc__ if obj.__doc__ else ""

    # Main Table
    console.print()
    tb_table = Table(
        box=box.SIMPLE,
        show_header=False,
        title=tb_name.upper(),
        title_justify="left",
        title_style="u bold",
    )
    tb_table.add_column(style=property_c)
    tb_table.add_column(style=value_c)

    # Description
    tb_table.add_row(
        "Description",
        Markdown(get_docstr(tb_pkg), style=f"{value_c} italic dim"),
        end_section=True,
    )

    # Module Information
    mod_table = Table(box=box.SIMPLE, header_style="italic", show_header=True)
    mod_table.add_column("TB Top", style=value_c)
    mod_table.add_column("RTL Top", style=value_c)
    mod_table.add_column("HDL", style=value_c)
    mod_table.add_row(tb_info.tb_top, tb_info.rtl_top, tb_info.hdl)
    tb_table.add_row("Module", mod_table, end_section=True)

    # Path
    tb_table.add_row("Path", str(tb_info.path), end_section=True)

    # Tests
    tst_table = Table(show_header=False)
    tst_table.add_column(style=accent_c)
    tst_table.add_column(style=value_c)

    for tst in tb_tests:
        tst_func = getattr(tb_pkg, tst)
        tst_table.add_row(
            tst, Markdown(get_docstr(tst_func), style=f"{value_c} italic dim")
        )

    tb_table.add_row("Tests", tst_table, end_section=True)

    # Display
    console.print(tb_table, justify="left")
    console.print()


def cmd_run(
    rbook: Runbook,
    dry: bool,
    tb_names: List[str],
    ntimes: int,
    include_tests: List[str],
    exclude_tests: List[str],
    include_tags: List[str],
    exclude_tags: List[str],
) -> None:
    """
    Execute specified testbenches using the cocotb runner, applying include/exclude
    filters.

    Args:
        rbook: The Runbook containing testbench definitions and configuration.
        dry: Preview execution plan without simulating.
        tb_names: List of testbench names to execute.
        ntimes: Number of times each test case should be executed.
        include_tests: Names of test cases to include (if specified).
        exclude_tests: Names of test cases to exclude (if specified).
        include_tags: Name of testbench tags to include (if specified).
        exclude_tags: Name of testbench tags to exclude (if specified).

    Raises:
        CocomanNameError: If any of the testbench names is not registered in the
        runbook.
        TbEnvImportError: If the testbench module could not be imported properly.
    """
    load_includes(rbook)
    sim = get_runner(rbook.sim)
    console = Console()

    for name in tb_names:
        try:
            _check_testbench_name(rbook=rbook, tb_name=name)
        except CocomanNameError as excp:
            raise excp
        tb_info = rbook.tbs[name]

        try:
            tb_pkg = load_n_import_tb(tb_info)
        except TbEnvImportError as excp:
            raise excp

        # Filter testbench by tags
        tb_valid = True
        if include_tags:
            if not any(_str_in_regex_list(i, include_tags) for i in tb_info.tags):
                tb_valid = False
        if exclude_tags:
            if any(_str_in_regex_list(i, exclude_tags) for i in tb_info.tags):
                tb_valid = False
        if not tb_valid:
            continue

        # Filter test names
        tstcases = _get_test_names(tb_pkg)
        if include_tests:
            tstcases = [i for i in tstcases if _str_in_regex_list(i, include_tests)]
        if exclude_tests:
            tstcases = [i for i in tstcases if _str_in_regex_list(i, exclude_tests)]
        tstcases = [i for i in tstcases for _ in range(ntimes)]
        if not tstcases:
            continue

        if dry:
            console.print(Markdown(f"**{name}**: {', '.join(tstcases)}"))
            continue

        srcs = [p for i, p in rbook.srcs.items() if i in tb_info.srcs]

        b_args: Dict[str, Any] = rbook.build_args.copy()
        b_args.update(tb_info.build_args)
        t_args: Dict[str, Any] = rbook.test_args.copy()
        t_args.update(tb_info.test_args)

        sim.build(
            sources=srcs,
            hdl_toplevel=tb_info.rtl_top,
            always=True,
            **b_args,
        )

        if "results_xml" not in t_args:
            res_xml = Path(sim.build_dir, f"{name}_results.xml")
        else:
            res_xml = t_args["results_xml"]
        sim.test(
            hdl_toplevel=tb_info.rtl_top,
            hdl_toplevel_lang=tb_info.hdl,
            test_module=tb_info.tb_top,
            testcase=tstcases,
            results_xml=res_xml,
            **t_args,
        )
