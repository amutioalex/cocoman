"""Regression orchestration logic and utilities.

This subpackage contains the essential components required to load, filter, import, and
execute testbenches defined in runbooks.

Modules:
    env: Utilities to import testbenches and discover cocotb tests.
    runbook: Data models for representing runbooks and testbenches.
    orchestrator: Build execution plans and manage test regression flows.

Exports:
    ExecutionPlan: Data model representing a testbench execution unit.
    Filtering: Selection criteria for testbenches/tests.
    Orchestrator: Main entry point for orchestrating regressions.
    Runbook: Structure representing a test execution configuration file.
    Testbench: Metadata model for individual testbenches.
    get_test_names: Retrieve cocotb test function names.
    load_includes: Add include paths to Python sys.path.
    load_n_import_tb: Dynamically import a testbench module.
"""

from cocoregman.core.env import get_test_names, load_includes, load_n_import_tb
from cocoregman.core.orchestrator import ExecutionPlan, Filtering, Orchestrator
from cocoregman.core.runbook import Runbook, Testbench

__all__ = [
    "ExecutionPlan",
    "Filtering",
    "Orchestrator",
    "Runbook",
    "Testbench",
    "get_test_names",
    "load_includes",
    "load_n_import_tb",
]
