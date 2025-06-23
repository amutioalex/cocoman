# pylint: disable=wrong-import-position, too-many-instance-attributes, import-error
"""Runbook parsing and validation module.

This module provides tools to parse, validate, and convert runbook YAML files into
structured runbook objects. It ensures the correctness of paths, schema, and simulation
arguments required for regression management.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
from warnings import filterwarnings

# Suppress warning when importing from cocotb.runner
filterwarnings("ignore")

from cocotb.runner import Simulator

filterwarnings("default")

from yaml import MarkedYAMLError, safe_load, YAMLError
from cocoregman.core.validation import (
    validate_paths,
    validate_stages_args,
    validate_yaml_schema,
)
from cocoregman.errors import RbFileError, RbYAMLError


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
    """Dataclass representing a complete runbook configuration.

    Attributes:
        build_args: Global build-specific arguments for all cocotb testbenches.
        include: List of directories to be included in the Python path.
        sim: Simulation tool to be used.
        srcs: Mapping of source file indices to their absolute paths.
        tbs: Dictionary of testbench names mapped to Testbench objects.
        test_args: Global test-specific arguments for all cocotb testbenches.
        title: Runbook description title.
    """

    build_args: Dict[str, Any] = field(default_factory=dict)
    include: List[Path] = field(default_factory=list)
    sim: str = ""
    srcs: Dict[int, Path] = field(default_factory=dict)
    tbs: Dict[str, Testbench] = field(default_factory=dict)
    test_args: Dict[str, Any] = field(default_factory=dict)
    title: str = ""

    def __str__(self):
        """Return the current Runbook instance as a string."""
        out = (
            f"title: {self.title}\n"
            f"sim: {self.sim}\n"
            f"srcs: {self.srcs}\n"
            f"include: {','.join(map(str, self.include))}\n"
            f"build_args: {self.build_args}\n"
            f"test_args: {self.test_args}\n"
            f"tbs:"
        )
        for tb_name, tb_info in self.tbs.items():
            tb_str = "\n    ".join(str(tb_info).splitlines())
            out += f"\n  {tb_name}\n    {tb_str}"
        return out

    def __contains__(self, name: str) -> bool:
        """Return True if the provided string parameter is the name of a testbench
        contained in the runbook's instance. Otherwise, return False."""
        return isinstance(name, str) and name in self.tbs

    @classmethod
    def load_yaml(cls, file_path: Path) -> "Runbook":
        """Load and parse a cocotb runbook YAML file, returning a validated Runbook
        object.

        This function reads a YAML file, validates its schema, verifies all paths, and
        converts relative paths and environment variables to absolute paths. It then
        constructs a Runbook object if all validations succeed.

        Args:
            file_path: Path to the runbook YAML file to be loaded.

        Raises:
            RbFileError: If an error occurs while trying to read the file.
            RbYAMLError: If the YAML file is invalid or cannot be parsed.
            RbValidationError: If the file content fails schema or path validation.

        Returns:
            A fully validated and ready-to-use Runbook object.
        """
        # Load YAML contents
        try:
            with open(file_path, "r", encoding="utf-8") as f_handler:
                rb_dict = safe_load(f_handler)
        except OSError as excp:
            raise RbFileError(excp) from excp
        except (MarkedYAMLError, YAMLError) as excp:
            raise RbYAMLError(excp) from excp

        # Validate YAML schema and paths
        validate_yaml_schema(rb_dict)
        validate_paths(rb_dict=rb_dict, yaml_path=str(file_path.parent))

        rb_dict: dict
        general_dict = rb_dict.get("general", rb_dict)
        validate_stages_args(general_dict.get("test_args", {}), Simulator.test)
        validate_stages_args(general_dict.get("build_args", {}), Simulator.build)
        for _, tb_info in rb_dict["tbs"].items():
            validate_stages_args(tb_info.get("test_args", {}), Simulator.test)
            validate_stages_args(tb_info.get("build_args", {}), Simulator.build)

        return Runbook(
            title=general_dict.get("title", ""),
            sim=general_dict["sim"],
            srcs=rb_dict["srcs"],
            include=rb_dict.get("include", []),
            test_args=general_dict.get("test_args", {}),
            build_args=general_dict.get("build_args", {}),
            tbs={
                name: Testbench(
                    build_args=info.get("build_args", {}),
                    hdl=info["hdl"],
                    path=info["path"],
                    rtl_top=info["rtl_top"],
                    srcs=info["srcs"],
                    tags=info.get("tags", []),
                    tb_top=info["tb_top"],
                    test_args=info.get("test_args", {}),
                )
                for name, info in rb_dict["tbs"].items()
            },
        )
