# pylint: disable=import-error
"""Utility functions for validating runbooks, paths, arguments, ..."""

from inspect import getfullargspec
from os.path import expanduser, expandvars
from pathlib import Path
from typing import Any, Callable, Dict, List, Union
from cerberus import Validator
from cocoregman.core.schema import get_runbook_schema
from cocoregman.errors import RbValidationError


def validate_yaml_schema(yaml_dict: dict) -> None:
    """Validate YAML dictionary against the runbook schema.

    Args:
        yaml_dict: Parsed YAML contents to validate.

    Raises:
        RbValidationError: If the structure does not match the expected schema.
    """
    schema = get_runbook_schema("general" in yaml_dict)
    sch_valid = Validator()
    if not sch_valid.validate(yaml_dict, schema):
        raise RbValidationError(f"YAML schema validation failed\n{sch_valid.errors}")


def validate_paths(
    rb_dict: Dict[str, Union[str, int, List[int], Dict[str, Any]]],
    yaml_path: str,
) -> None:
    """Resolve and validate all filesystem paths in the runbook.

    Ensure all relevant paths (sources, testbenches, includes) are valid an exist. Also
    verifies that testbenches reference only registered source indices.

    Args:
        rb_dict: Validated runbook dictionary.
        yaml_path: Path to the runbook YAML file.

    Raises:
        RbValidationError: If paths are invalid, non-existent, or incorrectly
            referenced.
    """

    def get_abs_path(base: str, path: str) -> Path:
        """Convert a relative or env-based path to an absolute Path object.

        Args:
            base: Base path for resolving relative paths.
            path: The string to resolve.

        Returns:
            An absolute `Path` object.
        """
        aux_p = Path(expandvars(expanduser(path)))
        return aux_p if aux_p.is_absolute() else Path(base) / aux_p

    # SOURCE PATHS
    rb_dict["srcs"] = {
        k: get_abs_path(yaml_path, v) for k, v in rb_dict.get("srcs", {}).items()
    }

    # TESTBENCHES
    for tb in rb_dict["tbs"].values():
        tb["path"] = get_abs_path(yaml_path, tb["path"])
        tb["srcs"] = tb.get("srcs", [])
        for key in ("build_args", "test_args"):
            tb[key] = {
                k: expandvars(expanduser(v)) if isinstance(v, str) else v
                for k, v in tb.get(key, {}).items()
            }

    # INCLUDES
    rb_dict["include"] = [
        get_abs_path(yaml_path, p) for p in rb_dict.get("include", [])
    ]

    # BUILD AND TEST ARGS
    general = rb_dict.get("general", rb_dict)
    for key in ("build_args", "test_args"):
        general[key] = {
            k: expandvars(expanduser(v)) if isinstance(v, str) else v
            for k, v in general.get(key, {}).items()
        }

    # Check if the provided paths exist, and if they are correctly set
    all_src_ind = set(rb_dict["srcs"].keys())
    missing_paths = []
    unregistered = {}

    for _, p in rb_dict["srcs"].items():
        if not p.is_file():
            missing_paths.append(str(p))

    for ind, tb in rb_dict["tbs"].items():
        if not tb["path"].is_dir():
            missing_paths.append(str(tb["path"]))
        unreg = [i for i in tb["srcs"] if i not in all_src_ind]
        if unreg:
            unregistered[ind] = unreg

    for p in rb_dict.get("include", []):
        if not p.exists():
            missing_paths.append(str(p))

    if missing_paths:
        raise RbValidationError(f"Non-existent paths\n{missing_paths}")
    if unregistered:
        raise RbValidationError(f"Unregistered source indices:\n{unregistered}")


def validate_stages_args(args: Dict[str, Any], sim_method: Callable) -> None:
    """Validate that keys in args are valid for a given cocotb simulation stage.

    Ignore common internal arguments that are handled by cocoman itself.

    Args:
        args: Arguments to validate.
        sim_method: Simulation stage callable.

    Raises:
        RbValidationError: If an illegal argument key is detected.
    """
    ignored = {
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

    valid_args = [arg for arg in getfullargspec(sim_method).args if arg not in ignored]

    for key in args:
        if key not in valid_args:
            raise RbValidationError(
                f"Invalid key '{key}' in '{sim_method.__name__}' arguments. "
                f"Allowed: {valid_args}",
            )
