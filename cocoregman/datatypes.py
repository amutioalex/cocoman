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


@dataclass
class Runbook:
    """Dataclass representing a complete cocotb Runbook configuration.

    Attributes:
        build_args: Global build-specific arguments for all cocotb testbenches.
        include: List of directories to be included in the Python path.
        sim: Simulation tool to be used.
        srcs: Mapping of source file indices to their absolute paths.
        tbs: Dictionary of testbench names mapped to Testbench objects.
        test_args: Global test-specific arguments for all cocotb testbenches.
    """

    build_args: Dict[str, Any] = field(default_factory=dict)
    include: List[Path] = field(default_factory=list)
    sim: str = ""
    srcs: Dict[int, Path] = field(default_factory=dict)
    tbs: Dict[str, Testbench] = field(default_factory=dict)
    test_args: Dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        """Return the current Runbook instance as a string."""
        pr_str = (
            f"sim: {self.sim}\n"
            f"srcs: {self.srcs}\n"
            f"include: {','.join(map(str, self.include))}\n"
            f"build_args: {self.build_args}\n"
            f"test_args: {self.test_args}\n"
            f"tbs:"
        )
        for tb_name, tb_info in self.tbs.items():
            tb_str = "\n    ".join(str(tb_info).splitlines())
            pr_str += f"\n  {tb_name}\n    {tb_str}"
        return pr_str

    def __contains__(self, name: str) -> bool:
        """Return True if the provided string parameter is the name of a testbench
        contained in the runbook's instance. Otherwise, return False."""
        if not isinstance(name, str):
            return NotImplemented
        return name in self.tbs
