# pylint: disable=wrong-import-position, import-error, too-many-locals
# pylint: disable=too-many-positional-arguments, too-many-arguments, too-many-statements
"""Commands module for the cocoman command-line interface (CLI)."""

from typing import Union

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from cocoregman.core.env import get_test_names, load_includes, load_n_import_tb
from cocoregman.core.orchestrator import Filtering, Orchestrator
from cocoregman.core.runbook import Runbook
from cocoregman.errors import CocomanNameError


def cmd_list(rbook: Runbook, tb_name: Union[str, None] = None) -> None:
    """Display a general overview or specific testbench of the provided runbook.

    Args:
        rbook: The main runbook object.
        tb_name: The name of the specific testbench to inspect, if any.

    Raises:
        CocomanNameError: If the testbench name is invalid.
        TbEnvImportError: If the top testbench module could not be imported.
    """

    def get_docstr(obj: object) -> str:
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
                f"'{tb_name}' not found\nAvailable: {', '.join(rbook.tbs)}"
            )
        load_includes(rbook)
        tb_info = rbook.tbs[tb_name]
        tb_pkg = load_n_import_tb(tb_info)
        tb_tests = get_test_names(tb_pkg)

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
        if rbook.title:
            console.print(f"[bold]{rbook.title}[/bold]")
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
    tb_names: list[str],
    ntimes: int,
    include_tests: list[str],
    exclude_tests: list[str],
    include_tags: list[str],
    exclude_tags: list[str],
) -> None:
    """Execute specified testbenches using the cocotb runner, applying include/exclude
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
    runner = Orchestrator()
    criteria = Filtering(
        tb_names, include_tests, exclude_tests, include_tags, exclude_tags
    )
    exec_plan = runner.build_plan(rbook, criteria)
    runner.regression_plan += exec_plan
    if dry:
        runner.print_regression(ntimes)
    else:
        runner.run_regression(ntimes)
