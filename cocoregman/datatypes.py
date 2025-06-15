# pylint: disable=too-many-instance-attributes
"""Centralized data structures for cocoman internals."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class Testbench:
    """Dataclass representing a single Runbook Testbench.

    Attributes:
        build_args: Dictionary of build-specific arguments for the cocotb testbench.
        hdl: Hardware description language used.
        path: Absolute path to the directory containing the cocotb testbench module.
        rtl_top: Top-level RTL module name to be simulated.
        srcs: List of integers representing source file indices in the Runbook.
        tags: List of strings of testbench tags for grouping and filtering.
        tb_top: Top-level Python module containing cocotb tests.
        test_args: Dictionary of test-specific arguments for the cocotb testbench.
    """

    build_args: Dict[str, Any] = field(default_factory=dict)
    hdl: str = ""
    path: Path = Path("")
    rtl_top: str = ""
    srcs: List[int] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    tb_top: str = ""
    test_args: Dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        """Return the current Testbench instance as a string."""
        return (
            f"tags: {','.join(self.tags)}\n"
            f"hdl: {self.hdl}\n"
            f"rtl_top: {self.rtl_top}\n"
            f"path: {self.path}\n"
            f"tb_top: {self.tb_top}\n"
            f"srcs: {','.join(map(str, self.srcs))}\n"
            f"build_args: {self.build_args}\n"
            f"test_args: {self.test_args}\n"
        )
