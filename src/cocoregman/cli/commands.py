"""Command implementations for the command-line interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from cocoregman.core import (
    Filtering,
    Orchestrator,
    get_test_names,
    load_includes,
    load_n_import_tb,
)
from cocoregman.errors import CocoregmanNameError

if TYPE_CHECKING:
    from cocoregman.core import Runbook


def cmd_list(rbook: Runbook, tb_name: str | None = None) -> None:
    """Display an overview of the runbook or details for a specific testbench.

    Args:
        rbook: The runbook object containing configuration and testbenches.
        tb_name: Optional name of a specific testbench to inspect.

    Raises:
        CocoregmanNameError: If the provided testbench name is not in the runbook.
        TbEnvImportError: If the testbench module cannot be imported.
    """

    def _get_docstr(obj: object) -> str:
        """Safely return the docstring of an object.

        Args:
            obj: Any Python object to extract the docstring from.

        Returns:
            The object's docstring if it exists, otherwise an empty string.
        """
        return obj.__doc__ if obj.__doc__ else ""

    console = Console()
    property_c, value_c, accent_c = "bold cornflower_blue", "white", "light_sea_green"

    # SINGLE TESTBENCH
    if tb_name:
        if tb_name not in rbook:
            available = ", ".join(rbook.tbs)
            raise CocoregmanNameError(f"'{tb_name}' not found.\nAvailable: {available}")

        load_includes(rbook)
        tb_info = rbook.tbs[tb_name]
        tb_pkg = load_n_import_tb(tb_info)
        tb_tests = get_test_names(tb_pkg)

        table = Table(
            box=box.SIMPLE,
            show_header=False,
            title=tb_name.upper(),
            title_justify="left",
            title_style="u bold",
        )
        table.add_column(style=property_c)
        table.add_column(style=value_c)

        # Description
        table.add_row(
            "Description",
            Markdown(_get_docstr(tb_pkg), style=f"{value_c} italic dim"),
            end_section=True,
        )

        # Module Info
        aux_table = Table(box=box.SIMPLE, header_style="italic", show_header=True)
        aux_table.add_column("TB Top", style=value_c)
        aux_table.add_column("RTL Top", style=value_c)
        aux_table.add_column("HDL", style=value_c)
        aux_table.add_row(tb_info.tb_top, tb_info.rtl_top, tb_info.hdl)
        table.add_row("Module", aux_table, end_section=True)

        # Path
        table.add_row("Path", str(tb_info.path), end_section=True)

        # Tests
        aux_table = Table(show_header=False)
        aux_table.add_column(style=accent_c)
        aux_table.add_column(style=value_c)
        for name in tb_tests:
            tst_func = getattr(tb_pkg, name)
            aux_table.add_row(
                name, Markdown(_get_docstr(tst_func), style=f"{value_c} italic dim")
            )
        table.add_row("Tests", aux_table, end_section=True)

        console.print()
        console.print(table, justify="left")
        console.print()
        return

    # FULL RUNBOOK
    table = Table(
        box=box.SIMPLE,
        show_header=False,
        title="RUNBOOK CONFIGURATION",
        title_justify="left",
        title_style="u bold",
    )
    table.add_column(style=property_c)
    table.add_column(style=value_c)

    table.add_row("Simulator", rbook.sim, end_section=True)

    if rbook.srcs:
        aux_table = Table(show_header=False)
        aux_table.add_column(style=accent_c)
        aux_table.add_column(style=value_c)
        for index, path in rbook.srcs.items():
            aux_table.add_row(str(index), str(path))
        table.add_row("Sources", aux_table, end_section=True)

    if rbook.include:
        table.add_row("Include", "\n".join(map(str, rbook.include)), end_section=True)

    console.print()
    if rbook.title:
        console.print(f"[bold]{rbook.title}[/bold]")
    console.print()
    console.print(table, justify="left")
    console.print()

    table = Table(
        box=box.SIMPLE,
        header_style="italic",
        show_header=True,
        title="TESTBENCHES",
        title_justify="left",
        title_style="u bold",
    )
    table.add_column(header="Name", style=property_c)
    table.add_column(header="RTL Top", style=value_c)
    table.add_column(header="TB Top", style=value_c)
    table.add_column(header="Sources", style=accent_c)

    for name, tb_info in rbook.tbs.items():
        table.add_row(
            name,
            tb_info.rtl_top,
            tb_info.tb_top,
            ", ".join(map(str, tb_info.srcs)),
        )

    console.print()
    console.print(table, justify="left")
    console.print()


def cmd_run(rbook: Runbook, criteria: Filtering, ntimes: int, dry: bool) -> None:
    """Run test regressions from the provided runbook using selection criteria.

    Args:
        rbook: The runbook with all testbench configurations.
        criteria: Filters for which tests or testbenches to run.
        ntimes: Number of times each test should run.
        dry: If True, only display the regression plan without executing.

    Raises:
        TbEnvImportError: If testbench environment import fails.
    """
    runner = Orchestrator()
    exec_plan = runner.build_plan(rbook, criteria)
    runner.regression_plan += exec_plan

    if dry:
        runner.print_regression(ntimes)
    else:
        runner.run_regression(ntimes)
