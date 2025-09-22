"""Orchestration of testbench execution from a runbook."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Literal

from cocotb.runner import get_runner
from rich.console import Console

from cocoregman.core.env import get_test_names, load_includes, load_n_import_tb
from cocoregman.core.validation import match_globs, match_regexs

if TYPE_CHECKING:
    from cocoregman.core.runbook import Runbook


@dataclass
class ExecutionPlan:
    """Unit of regression execution.

    Attributes:
        runbook: Original runbook containing the testbench.
        tb_name: Testbench instance name.
        tests: List of the tests to be executed.
    """

    runbook: Runbook
    tb_name: str
    tests: list[str] = field(default_factory=list)


@dataclass
class Filtering:
    """Selection criteria for testbenches and tests.

    Attributes:
        tb_names: Testbench names to explicitly include.
        pattern_style: Pattern matching style (e.g. regex, glob)
        include_tests: Regexes to match which tests to include.
        exclude_tests: Regexes to match which tests to exclude.
        include_tags: Regexes to match which testbench tags to include.
        exclude_tags: Regexes to match which testbench tags to exclude.
    """

    tb_names: list[str] = field(default_factory=list)
    pattern_style: Literal["regex", "glob"] = "regex"
    include_tests: list[str] = field(default_factory=list)
    exclude_tests: list[str] = field(default_factory=list)
    include_tags: list[str] = field(default_factory=list)
    exclude_tags: list[str] = field(default_factory=list)

    def get_valid(self, attr: str, dataset: list[str]) -> list[str]:
        """Filter a list based on inclusion and exclusion regex rules.

        Args:
            attr: Either "tests" or "tags" (determines which filters to apply).
            dataset: The list of items (test names or tags) to be filtered.

        Returns:
            A filtered list matching the criteria.

        Raises:
            ValueError: If an invalid attribute is specified.
        """
        attr = attr.lower()
        if attr not in {"tags", "tests"}:
            raise ValueError(f"Unknown filter attribute: '{attr}'")

        include = self.include_tags if attr == "tags" else self.include_tests
        exclude = self.exclude_tags if attr == "tags" else self.exclude_tests

        results = dataset
        validator: Callable
        validator = match_regexs if self.pattern_style == "regex" else match_globs
        if include:
            results = [i for i in results if validator(i, include)]
        if exclude:
            results = [i for i in results if not validator(i, exclude)]

        return results


class Orchestrator:
    """Coordinator for filtering, planning, and simulation of testbenches."""

    def __init__(self) -> None:
        """Initialize a regression run orchestrator."""
        self.regression_plan: list[ExecutionPlan] = []

    @classmethod
    def build_plan(cls, rbook: Runbook, criteria: Filtering) -> list[ExecutionPlan]:
        """Generate test execution plans based on filtering rules.

        Args:
            rbook: Runbook object defining available testbenches and configuration.
            criteria: Filtering rules for testbenches and individual tests.

        Returns:
            A list of ExecutionPlan objects (one per testbench).
        """
        valid_tb_names = (
            list(rbook.tbs.keys())
            if not criteria.tb_names
            else [tb for tb in criteria.tb_names if tb in rbook]
        )

        plans: list[ExecutionPlan] = []
        for tb_name in valid_tb_names:
            tb = rbook.tbs[tb_name]
            if criteria.get_valid("tags", tb.tags):
                plans.append(ExecutionPlan(runbook=rbook, tb_name=tb_name))

        if not plans:
            return []

        load_includes(rbook)

        for plan in plans:
            tb_pkg = load_n_import_tb(rbook.tbs[plan.tb_name])
            all_tests = get_test_names(tb_pkg)
            plan.tests = criteria.get_valid("tests", all_tests)

        return plans

    def run_regression(self, n_times: int) -> None:
        """Execute all testbenches and test cases in the regression plan.

        Args:
            n_times: Number of repetitions per test case.
        """
        if not self.regression_plan:
            return

        previous_rb: Runbook | None = None
        sim = None

        for plan in self.regression_plan:
            rb = plan.runbook
            tb = rb.tbs[plan.tb_name]

            if rb != previous_rb:
                load_includes(rb)
                sim = get_runner(rb.sim)

            srcs = [p for i, p in rb.srcs.items() if i in tb.srcs]
            b_args = {**rb.build_args, **tb.build_args}
            t_args = {**rb.test_args, **tb.test_args}

            sim.build(sources=srcs, hdl_toplevel=tb.rtl_top, always=True, **b_args)

            result_xml = t_args.get(
                "results_xml", Path(sim.build_dir, f"{plan.tb_name}_results.xml")
            )

            sim.test(
                hdl_toplevel=tb.rtl_top,
                hdl_toplevel_lang=tb.hdl,
                test_module=tb.tb_top,
                testcase=[t for t in plan.tests for _ in range(n_times)],
                results_xml=result_xml,
                **t_args,
            )

            previous_rb = rb

    def print_regression(self, n_times: int) -> None:
        """Print regression plan (dry run).

        Args:
            n_times: Number of times each test would run.
        """
        console = Console()
        if not self.regression_plan:
            console.print("\n[bold]No testbenches to run[/bold]\n")
            return

        console.print("\n[bold]DRY RUN[/bold]\n")
        for plan in self.regression_plan:
            console.rule(f"[italic]{plan.tb_name}[/italic]", align="left")
            tests = [t for t in plan.tests for _ in range(n_times)]
            if tests:
                console.print(f"    {', '.join(tests)}\n")
            else:
                console.print("    No tests to run\n")
