# pylint: disable=wrong-import-position, import-error, too-many-locals
# pylint: disable=too-many-positional-arguments, too-many-arguments, too-many-statements
"""Commands module for the cocoman command-line interface (CLI)."""

from pathlib import Path
from re import fullmatch as re_fullmatch
from types import ModuleType
from typing import Any, Dict, List, Union
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
from cocoregman.errors import CocomanNameError
from cocoregman.runbook import Runbook
from cocoregman.tbenv import load_includes, load_n_import_tb


# AUX #


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


def str_in_regex_list(text: str, regexs: List[str]) -> bool:
    """Check if a provided string matches fully any of the valid regular expressions of
    a given list.

    Args:
        text: The string to check.
        regexs: The list of valid regular expressions.

    Returns:
        True if the string matches any of the regex in the list, otherwise False.
    """
    return any(re_fullmatch(rgx, text) for rgx in regexs)


# COMMANDS #


def cmd_list(rbook: Runbook, tb_name: Union[str, None] = None) -> None:
    """Display a general overview or specific testbench of the provided runbook.

    Args:
        rbook: The main runbook object.
        tb_name: The name of the specific testbench to inspect, if any.

    Raises:
        CocomanNameError: If the testbench name is invalid.
        TbEnvImportError: If the top testbench module could not be imported.
    """

    def get_docstr(obj: Any) -> str:
        """Safely return the docstring of an object.

        Args:
            obj: Any Python object to extract the docstring from.

        Returns:
            The object's docstring if it exists, otherwise an empty string.
        """
        return obj.__doc__ if obj.__doc__ else ""

    property_c, value_c, accent_c = "bold cornflower_blue", "white", "light_sea_green"
    console = Console()

    main_table = Table(
        box=box.SIMPLE,
        show_header=False,
        title_justify="left",
        title_style="u bold",
    )
    main_table.add_column(style=property_c)
    main_table.add_column(style=value_c)

    # LIST TESTBENCH
    if tb_name:
        if tb_name not in rbook:
            raise CocomanNameError(
                0, f"'{tb_name}' not found\nAvailable: {', '.join(rbook.tbs)}"
            )
        load_includes(rbook)
        tb_info = rbook.tbs[tb_name]
        tb_pkg = load_n_import_tb(tb_info)
        tb_tests = _get_test_names(tb_pkg)

        main_table.title = tb_name.upper()

        # Description
        main_table.add_row(
            "Description",
            Markdown(get_docstr(tb_pkg), style=f"{value_c} italic dim"),
            end_section=True,
        )

        # Module Info
        aux_table = Table(box=box.SIMPLE, header_style="italic", show_header=True)
        aux_table.add_column("TB Top", style=value_c)
        aux_table.add_column("RTL Top", style=value_c)
        aux_table.add_column("HDL", style=value_c)
        aux_table.add_row(tb_info.tb_top, tb_info.rtl_top, tb_info.hdl)
        main_table.add_row("Module", aux_table, end_section=True)

        # Path
        main_table.add_row("Path", str(tb_info.path), end_section=True)

        # Tests
        aux_table = Table(show_header=False)
        aux_table.add_column(style=accent_c)
        aux_table.add_column(style=value_c)
        for tst in tb_tests:
            tst_func = getattr(tb_pkg, tst)
            aux_table.add_row(
                tst, Markdown(get_docstr(tst_func), style=f"{value_c} italic dim")
            )
        main_table.add_row("Tests", aux_table, end_section=True)

    # LIST RUNBOOK OVERVIEW
    else:
        main_table.title = "RUNBOOK CONFIGURATION"
        main_table.add_row("Simulator", rbook.sim, end_section=True)

        if rbook.srcs:
            aux_table = Table(show_header=False)
            aux_table.add_column(style=accent_c)
            aux_table.add_column(style=value_c)
            for index, path in rbook.srcs.items():
                aux_table.add_row(str(index), str(path))
            main_table.add_row("Sources", aux_table, end_section=True)

        if rbook.include:
            main_table.add_row(
                "Include", "\n".join(map(str, rbook.include)), end_section=True
            )

        console.print()
        console.print(main_table, justify="left")
        console.print()

        main_table = Table(
            box=box.SIMPLE,
            header_style="italic",
            show_header=True,
            title="TESTBENCHES",
            title_justify="left",
            title_style="u bold",
        )
        main_table.add_column(header="Name", style=property_c)
        main_table.add_column(header="RTL Top", style=value_c)
        main_table.add_column(header="TB Top", style=value_c)
        main_table.add_column(header="Sources", style=accent_c)

        for name, tb_info in rbook.tbs.items():
            main_table.add_row(
                name,
                tb_info.rtl_top,
                tb_info.tb_top,
                ", ".join(map(str, tb_info.srcs)),
            )

    console.print()
    console.print(main_table, justify="left")
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
        if name not in rbook:
            raise CocomanNameError(
                0,
                f"'{name}' not found\navailable tbs: {', '.join(rbook.tbs.keys())}",
            )
        tb_info = rbook.tbs[name]
        tb_pkg = load_n_import_tb(tb_info)

        # Filter testbench by tags
        if include_tags and not any(
            str_in_regex_list(i, include_tags) for i in tb_info.tags
        ):
            continue
        if exclude_tags and any(
            str_in_regex_list(i, include_tags) for i in tb_info.tags
        ):
            continue

        # Filter test names
        tstcases = _get_test_names(tb_pkg)
        if include_tests:
            tstcases = [i for i in tstcases if str_in_regex_list(i, include_tests)]
        if exclude_tests:
            tstcases = [i for i in tstcases if str_in_regex_list(i, exclude_tests)]
        tstcases = [i for i in tstcases for _ in range(ntimes)]
        if not tstcases:
            continue

        if dry:
            console.print(f"[bold]{name}[/bold]")
            for tst in tstcases:
                console.print(f" • {tst}")
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

        res_xml = t_args.get("results_xml", Path(sim.build_dir, f"{name}_results.xml"))

        sim.test(
            hdl_toplevel=tb_info.rtl_top,
            hdl_toplevel_lang=tb_info.hdl,
            test_module=tb_info.tb_top,
            testcase=tstcases,
            results_xml=res_xml,
            **t_args,
        )
