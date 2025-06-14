# pylint: disable=wrong-import-position, too-many-instance-attributes
"""Runbook parsing and validation module for the cocoman framework.

This module provides utilities to parse, validate, and convert runbook YAML files
into structured Runbook objects. It ensures the correctness of YAML content, paths,
and data references necessary for cocotb testbench management.
"""

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
from cocoregman.datatypes import Runbook, Testbench
from cocoregman.errors import RbFileError, RbValidationError, RbYAMLError

# SCHEMA VALIDATION #


def _get_base_sch() -> dict:
    """Return the common cerberus schema for runbook objects. This schema definition is
    shared in runbook with or without the 'general' section implemented."""
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
    """Return the cerberus schema for runbook 'general' section properties. To be used
    in the top level, or in a separated section."""
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


def _validate_yaml_schema(yaml_dict: dict) -> None:
    """Validate the structure of a YAML dictionary against the cocoman Runbook schema.

    Uses 'cerberus' to verify that the provided YAML dictionary adheres to the expected
    schema structure, including valid keys, value types, and allowed options.

    Args:
        yaml_dict: The YAML dictionary to be validated.

    Raises:
        RbValidationError: If the provided YAML dictionary does not match the expected
            schema.
    """
    base_sch = _get_base_sch()
    gen_sch = _get_general_sch()

    if "general" in yaml_dict:
        rb_schema = {
            **base_sch,
            "general": {"type": "dict", "schema": gen_sch, "required": True},
        }
    else:
        rb_schema = {**base_sch, **gen_sch}

    sch_valid = Validator()
    if sch_valid.validate(yaml_dict, rb_schema) is False:
        raise RbValidationError(
            0,
            f"schema validation of parsed YAML failed\n{sch_valid.errors}",
        )


# RUNBOOK PROPERTIES VALIDATION #


def _validate_paths(
    rb_dict: Dict[str, Union[str, int, List[int], Dict[str, Any]]],
    yaml_path: str,
) -> None:
    """Resolve and validate all paths in the runbook dictionary.

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
        if aux_p.is_absolute():
            return aux_p
        return Path(base, str(aux_p))

    # SOURCE PATHS
    rb_srcs = rb_dict.get("srcs", {})
    rb_dict["srcs"] = {
        k: get_abs_path(base=yaml_path, path=v) for k, v in rb_srcs.items()
    }

    # TESTBENCHES
    for tb_info in rb_dict["tbs"].values():
        # TB PATH
        tb_info["path"] = get_abs_path(base=yaml_path, path=tb_info["path"])
        # BUILD AND TEST ARGS
        for args_name in ["build_args", "test_args"]:
            tb_info[args_name] = {
                k: (expandvars(expanduser(v)) if isinstance(v, str) else v)
                for k, v in rb_dict.get(args_name, {}).items()
            }
        # SOURCES
        tb_info["srcs"] = tb_info.get("srcs", [])

    # INCLUDES
    rb_dict["include"] = [
        get_abs_path(base=yaml_path, path=i) for i in rb_dict.get("include", [])
    ]

    # BUILD AND TEST ARGS
    for args_name in ["build_args", "test_args"]:
        base_dict = rb_dict if not "general" in rb_dict else rb_dict["general"]
        base_dict[args_name] = {
            k: (expandvars(expanduser(v)) if isinstance(v, str) else v)
            for k, v in base_dict.get(args_name, {}).items()
        }

    # Check if the provided paths exist, and if they are correctly set
    x_srcs, x_non_exist, x_non_reg = [], [], {}
    for n, path in rb_dict["srcs"].items():
        x_srcs.append(n)
        if not path.is_file():
            x_non_exist.append(str(path))
    for n, tb in rb_dict["tbs"].items():
        if not tb["path"].is_dir():
            x_non_exist.append(str(tb["path"]))
        aux = [i for i in tb["srcs"] if i not in x_srcs]
        if aux:
            x_non_reg[n] = aux
    for path in rb_dict.get("include", []):
        if not path.exists():
            x_non_exist.append(str(path))
    if x_non_exist:
        raise RbValidationError(
            1,
            f"non-existent paths found in provided runbook\n{x_non_exist}",
        )
    if x_non_reg:
        raise RbValidationError(
            2,
            f"non-registered source paths found in provided runbook\n{x_non_reg}",
        )


def validate_stages_args(args: Dict[str, Any], sim_method: Callable) -> None:
    """Validate the keys of a dictionary containing arguments for a cocotb simulation
    stage.

    Some keys are excluded from the valid arguments of a stage given they are handled by
    the cocoman script itself, and user input could potentially disrupt execution flow.

    Args:
        args: The arguments dictionary.
        sim_method: The cocotb stage callable.

    Raises:
        RbValidationError: If the dictionary contains an illegal key.
    """
    valid_args = getfullargspec(sim_method)[0]
    excl_args = [
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
    ]
    valid_args = [a for a in valid_args if a not in excl_args]
    for key in args.keys():
        if key not in valid_args:
            raise RbValidationError(
                3,
                f"Invalid key '{key}' in '{sim_method.__name__}' arguments. "
                f"valid arguments: {valid_args}",
            )


def load_runbook(file_path: Path) -> Runbook:
    """Load and parse a cocotb runbook YAML file, returning a validated Runbook object.

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
    rb_dict: dict
    _validate_yaml_schema(rb_dict)
    _validate_paths(rb_dict=rb_dict, yaml_path=str(file_path.parent))
    base_dict = rb_dict if not "general" in rb_dict else rb_dict["general"]
    validate_stages_args(base_dict.get("test_args", {}), Simulator.test)
    validate_stages_args(base_dict.get("build_args", {}), Simulator.build)
    for _, tb_info in rb_dict["tbs"].items():
        validate_stages_args(tb_info.get("test_args", {}), Simulator.test)
        validate_stages_args(tb_info.get("build_args", {}), Simulator.build)

    # Build Runbook and Testbench objects
    rbook = Runbook(
        sim=base_dict["sim"],
        srcs=rb_dict["srcs"],
        include=rb_dict.get("include", []),
        test_args=base_dict.get("test_args", {}),
        build_args=base_dict.get("build_args", {}),
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

    return rbook
