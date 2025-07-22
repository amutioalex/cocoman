"""Regression runner for cocotb-based verification workflows.

This package provides a command-line-driven framework for managing, filtering, and
executing simulation regressions using cocotb. It includes a modular core for testbench
orchestration and a CLI interface for ease of use.

Modules:
    core: Core logic including Runbook parser, orchestration, and environment handling.
    cli: Command-line interface for parsing arguments and executing commands.
    errors: Custom error types used across the application.

Exports:
    Filtering
    Orchestrator
    Runbook
    Testbench
"""

from cocoregman.core import Filtering, Orchestrator, Runbook, Testbench

__all__ = [
    "Filtering",
    "Orchestrator",
    "Runbook",
    "Testbench",
]
