# pylint: disable=import-error
"""Runbook testbench execution orchestrator."""

from dataclasses import dataclass, field
from pathlib import Path
from re import fullmatch as re_fullmatch

from cocotb.runner import get_runner
from rich.console import Console

from cocoregman.core.env import get_test_names, load_includes, load_n_import_tb
from cocoregman.core.runbook import Runbook


def _match_regexs(text: str, regexs: list[str]) -> bool:
    """Check if a string fully matches any of the provided regex patterns.

    Args:
        text: The string to evaluate.
        regexs: A list of regex patterns.

    Returns:
        True if the string fully matches any of the regex patterns.
    """
    return any(re_fullmatch(rgx, text) for rgx in regexs)


@dataclass
class ExecutionPlan:
    """Represent a regression execution unit.

    Attributes:
        runbook: Original runbook containing the testbench.
        tb_name: The testbench title.
        tests: List of the tests to be executed.
    """

    runbook: Runbook = None
    tb_name: str = ""
    tests: list[str] = field(default_factory=list)


@dataclass
class Filtering:
    """Represent filter criteria for testbench and test selection.

    Attributes:
        tb_names: List of testbench titles to run.
        include_tests: Names of test cases to include.
        exclude_tests: Names of test cases to exclude.
        include_tags: Name of testbench tags to include.
        exclude_tags: Name of testbench tags to exclude.
    """

    tb_names: list[str] = field(default_factory=list)
    include_tests: list[str] = field(default_factory=list)
    exclude_tests: list[str] = field(default_factory=list)
    include_tags: list[str] = field(default_factory=list)
    exclude_tags: list[str] = field(default_factory=list)

    def get_valid(self, attr: str, dataset: list[str]) -> list[str]:
        """Filter dataset items based on tags or test name criteria.

        Args:
            attr: Either "tags" or "tests" to apply the correct filter group.
            dataset: The list of strings to be filtered.

        Returns:
            A filtered list of strings based on inclusion and exclusion rules.

        Raises:
            ValueError: If an unknown attribute is passed.
        """
        attr = attr.lower()
        if attr not in ["tags", "tests"]:
            raise ValueError(f"Unknown filter attribute: '{attr}'")

        inclusion = self.include_tags if attr == "tags" else self.include_tests
        exclusion = self.exclude_tags if attr == "tags" else self.exclude_tests

        valid = dataset
        if inclusion:
            valid = [i for i in valid if _match_regexs(i, inclusion)]
        if exclusion:
            valid = [i for i in valid if not _match_regexs(i, exclusion)]

        return valid


class Orchestrator:
    """Coordinator of filtering, planning, and execution of testbenches."""

    def __init__(self) -> None:
        """Initialize an empty orchestrator."""
        self.regression_plan: list[ExecutionPlan] = []

    @classmethod
    def build_plan(cls, rbook: Runbook, criteria: Filtering) -> list[ExecutionPlan]:
        """Build execution plans for testbenches matching filter criteria.

        Args:
            rbook: The runbook containing testbenches and configurations.
            criteria: Filtering rules to select testbenches/tests.

        Returns:
            A list of ExecutionPlan objects for testbenches and selected tests.
        """
        if not criteria.tb_names:
            valid_tbs = list(rbook.tbs.keys())
        else:
            valid_tbs = [t for t in criteria.tb_names if t in rbook]

        plans: list[ExecutionPlan] = []
        for name in valid_tbs:
            tb_info = rbook.tbs[name]
            if not criteria.get_valid("tags", tb_info.tags):
                continue
            plans.append(ExecutionPlan(rbook, name))
        if not plans:
            return []

        load_includes(rbook)
        for plan in plans:
            tb_pkg = load_n_import_tb(rbook.tbs[plan.tb_name])
            all_tests = get_test_names(tb_pkg)
            plan.tests = criteria.get_valid("tests", all_tests)

        return plans

    def run_regression(self, n_times: int) -> None:
        """Run all testbenches and tests in the regression plan.

        Args:
            n_times: How many times to repeat each test case.
        """
        if not self.regression_plan:
            return

        previous_rb: Runbook = None
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

            res_xml = t_args.get(
                "results_xml", Path(sim.build_dir, f"{plan.tb_name}_results.xml")
            )

            sim.test(
                hdl_toplevel=tb.rtl_top,
                hdl_toplevel_lang=tb.hdl,
                test_module=tb.tb_top,
                testcase=[i for i in plan.tests for _ in range(n_times)],
                results_xml=res_xml,
                **t_args,
            )

            previous_rb = rb

    def print_regression(self, n_times: int) -> None:
        """Display the regression plan and associated tests (dry-run).

        Args:
            n_times: How many times each test would be repeated.
        """
        console = Console()
        if not self.regression_plan:
            console.print("\n[bold]No testbenches to run[/bold]\n")
            return

        console.print("\n[bold]DRY RUN[/bold]\n")
        for plan in self.regression_plan:
            console.rule(f"[italic]{plan.tb_name}[/italic]", align="left")
            tests = [i for i in plan.tests for _ in range(n_times)]
            if not tests:
                console.print("    No tests to run\n")
                continue
            console.print(f"    {', '.join(tests)}\n")
