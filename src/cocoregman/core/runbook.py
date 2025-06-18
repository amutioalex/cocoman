# pylint: disable=wrong-import-position, too-many-instance-attributes
"""Runbook parsing and validation module.

This module provides tools to parse, validate, and convert runbook YAML files into
structured runbook objects. It ensures the correctness of paths, schema, and simulation
arguments required for regression management.
"""

from dataclasses import dataclass, field
from inspect import getfullargspec
from os.path import expanduser, expandvars
from pathlib import Path
from typing import Any, Callable, Dict, List, Union
from warnings import filterwarnings
from cerberus import Validator

# Suppress warning when importing from cocotb.runner
filterwarnings("ignore")

from cocotb.runner import Simulator

filterwarnings("default")

from yaml import MarkedYAMLError, safe_load, YAMLError
from cocoregman.core.datatypes import Testbench
from cocoregman.errors import RbFileError, RbValidationError, RbYAMLError


# SCHEMA DEFINITION #


def _get_base_sch() -> dict:
    """Return base schema used for runbook validation, excluding general section."""
    return {
        "srcs": {
            "type": "dict",
            "keysrules": {"type": "integer", "coerce": int},
            "valuesrules": {"type": "string", "empty": False},
            "empty": False,
            "required": False,
        },
        "tbs": {
            "type": "dict",
            "keysrules": {"type": "string"},
            "valuesrules": {
                "type": "dict",
                "schema": {
                    "srcs": {
                        "type": "list",
                        "required": False,
                        "schema": {"type": "integer"},
                        "empty": False,
                    },
                    "path": {"type": "string", "required": True, "empty": False},
                    "rtl_top": {"type": "string", "required": False, "empty": False},
                    "tb_top": {"type": "string", "required": True, "empty": False},
                    "hdl": {
                        "type": "string",
                        "allowed": ["verilog", "vhdl"],
                        "required": True,
                    },
                    "tags": {
                        "type": "list",
                        "required": False,
                        "schema": {"type": "string"},
                        "empty": False,
                    },
                    "build_args": {
                        "type": "dict",
                        "keysrules": {"type": "string", "empty": False},
                        "required": False,
                    },
                    "test_args": {
                        "type": "dict",
                        "keysrules": {"type": "string", "empty": False},
                        "required": False,
                    },
                },
            },
        },
        "include": {
            "type": "list",
            "schema": {"type": "string"},
            "required": False,
            "empty": False,
        },
    }


def _get_general_sch() -> dict:
    """Return schema for the 'general' section of the runbook."""
    return {
        "sim": {
            "type": "string",
            "allowed": [
                "icarus",
                "verilator",
                "vcs",
                "riviera",
                "questa",
                "activehdl",
                "modelsim",
                "ius",
                "xcelium",
                "ghdl",
                "nvc",
                "cvc",
            ],
            "required": True,
        },
        "title": {"type": "string", "required": False, "empty": False},
        "build_args": {
            "type": "dict",
            "keysrules": {"type": "string", "empty": False},
            "required": False,
        },
        "test_args": {
            "type": "dict",
            "keysrules": {"type": "string", "empty": False},
            "required": False,
        },
    }


# VALIDATION FUNCTIONS #


def _validate_yaml_schema(yaml_dict: dict) -> None:
    """Validate parsed YAML content against the runbook schema.

    Args:
        yaml_dict: The YAML dictionary to be validated.

    Raises:
        RbValidationError: If the provided YAML dictionary does not match the expected
            schema.
    """
    rb_schema = {**_get_base_sch()}

    gen_sch = _get_general_sch()
    if "general" in yaml_dict:
        rb_schema["general"] = {"type": "dict", "schema": gen_sch, "required": True}
    else:
        rb_schema.update(gen_sch)

    sch_valid = Validator()
    if not sch_valid.validate(yaml_dict, rb_schema):
        raise RbValidationError(0, f"YAML schema validation failed\n{sch_valid.errors}")


def _validate_paths(
    rb_dict: Dict[str, Union[str, int, List[int], Dict[str, Any]]],
    yaml_path: str,
) -> None:
    """Resolve and validate all file system paths in the runbook.

    Ensures that paths specified in the runbook are valid, absolute, and accessible.
    Additionally, checks for source files referenced by testbenches and whether they
    are registered under 'srcs'.

    Args:
        rb_dict: The runbook dictionary after YAML schema validation.
        yaml_path: Path to runbook YAML file.

    Raises:
        RbValidationError: If paths are non-existent, unresolved, or incorrectly
            referenced by testbenches.
    """

    def get_abs_path(base: str, path: str) -> Path:
        """Convert a relative or environment-based path to an absolute Path object.

        This function expands user, environment variables and resolves relative paths to
        absolute paths for consistent file system access. Relative paths are resolved to
        a provided base path.

        Args:
            base: Relative path root.
            path: The string representation of the path to be resolved.

        Returns:
            An absolute and resolved Path object.
        """
        aux_p = Path(expandvars(expanduser(path)))
        return aux_p if aux_p.is_absolute() else Path(base, str(aux_p))

    # SOURCE PATHS
    rb_dict["srcs"] = {
        k: get_abs_path(base=yaml_path, path=v)
        for k, v in rb_dict.get("srcs", {}).items()
    }

    # TESTBENCHES
    for tb_info in rb_dict["tbs"].values():
        tb_info["path"] = get_abs_path(base=yaml_path, path=tb_info["path"])
        tb_info["srcs"] = tb_info.get("srcs", [])
        for args_name in ["build_args", "test_args"]:
            tb_info[args_name] = {
                k: expandvars(expanduser(v)) if isinstance(v, str) else v
                for k, v in tb_info.get(args_name, {}).items()
            }

    # INCLUDES
    rb_dict["include"] = [
        get_abs_path(base=yaml_path, path=i) for i in rb_dict.get("include", [])
    ]

    # BUILD AND TEST ARGS
    base_dict = rb_dict.get("general", rb_dict)
    for args_name in ["build_args", "test_args"]:
        base_dict[args_name] = {
            k: expandvars(expanduser(v)) if isinstance(v, str) else v
            for k, v in base_dict.get(args_name, {}).items()
        }

    # Check if the provided paths exist, and if they are correctly set
    x_srcs = list(rb_dict["srcs"].keys())
    x_non_exist = []
    x_non_reg = {}
    for n, path in rb_dict["srcs"].items():
        if not path.is_file():
            x_non_exist.append(str(path))
    for n, tb in rb_dict["tbs"].items():
        if not tb["path"].is_dir():
            x_non_exist.append(str(tb["path"]))
        unreg = [i for i in tb["srcs"] if i not in x_srcs]
        if unreg:
            x_non_reg[n] = unreg
    for path in rb_dict.get("include", []):
        if not path.exists():
            x_non_exist.append(str(path))

    if x_non_exist:
        raise RbValidationError(1, f"Non-existent paths\n{x_non_exist}")
    if x_non_reg:
        raise RbValidationError(2, f"Unregistered source indices:\n{x_non_reg}")


def _validate_stages_args(args: Dict[str, Any], sim_method: Callable) -> None:
    """Validate that provided keys are legal arguments for a specific cocotb simulation
    stage.

    Some keys are excluded from the valid arguments of a stage given they are handled by
    the cocoman script itself, and user input could potentially disrupt execution flow.

    Args:
        args: The arguments dictionary.
        sim_method: The cocotb stage callable.

    Raises:
        RbValidationError: If the dictionary contains an illegal key.
    """
    valid_args = [a for a in getfullargspec(sim_method)[0] if a not in {
            "self",
            "verilog_sources",
            "vhdl_sources",
            "sources",
            "hdl_toplevel",
            "test_module",
            "hdl_toplevel_lang",
            "testcase",
            "always",
            "timescale",
        }
    ]
    for key in args:
        if key not in valid_args:
            raise RbValidationError(
                3,
                f"Invalid key '{key}' in '{sim_method.__name__}' arguments. "
                f"Allowed: {valid_args}",
            )


# CLASS DECLARATION #


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
            raise RbFileError(0, excp) from excp
        except (MarkedYAMLError, YAMLError) as excp:
            raise RbYAMLError(0, excp) from excp

        # Validate YAML schema and paths
        _validate_yaml_schema(rb_dict)
        _validate_paths(rb_dict=rb_dict, yaml_path=str(file_path.parent))

        rb_dict: dict
        general_dict = rb_dict.get("general", rb_dict)
        _validate_stages_args(general_dict.get("test_args", {}), Simulator.test)
        _validate_stages_args(general_dict.get("build_args", {}), Simulator.build)
        for _, tb_info in rb_dict["tbs"].items():
            _validate_stages_args(tb_info.get("test_args", {}), Simulator.test)
            _validate_stages_args(tb_info.get("build_args", {}), Simulator.build)

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
