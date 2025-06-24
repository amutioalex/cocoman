# pylint: disable=import-error
"""Utility functions for validating runbooks, filesystem paths, and simulation
arguments."""

from inspect import getfullargspec
from typing import Any, Callable, Dict, List, Union
from cerberus import Validator
from cocoregman.core.schema import get_runbook_schema
from cocoregman.errors import RbValidationError


def validate_runbook(rb_dict: dict) -> None:
    """Validate a runbook dictionary against the runbook schema.

    Args:
        rb_dict: Dictionary to validate.

    Raises:
        RbValidationError: If the structure does not match the expected schema.
    """
    schema = get_runbook_schema(separate_general="general" in rb_dict)
    validator = Validator()

    if not validator.validate(rb_dict, schema):
        raise RbValidationError(f"YAML schema validation failed:\n{validator.errors}")


def validate_paths(
    rb_dict: Dict[str, Union[str, int, List[int], Dict[str, Any]]],
) -> None:
    """Validate all file system paths defined in the runbook.

    This function assumes that the provided runbook dictionary contains all
    sections/keys listed in the schema, even if void.

    Args:
        rb_dict: Validated and complete dictionary.

    Raises:
        RbValidationError: If any path does not exist, or testbenches reference
        unregistered sources.
    """
    all_srcs = set(rb_dict["srcs"].keys())
    missing_paths: List[str] = []
    unregistered: Dict[str, List[int]] = {}

    for src_path in rb_dict["srcs"].values():
        if not src_path.is_file():
            missing_paths.append(str(src_path))

    for name, tb in rb_dict["tbs"].items():
        if not tb["path"].is_dir():
            missing_paths.append(str(tb["path"]))
        missing_indices = [i for i in tb.get("srcs", []) if i not in all_srcs]
        if missing_indices:
            unregistered[name] = missing_indices

    for inc_path in rb_dict["include"]:
        if not inc_path.exists():
            missing_paths.append(str(inc_path))

    if missing_paths:
        raise RbValidationError(f"Non-existent paths\n{missing_paths}")
    if unregistered:
        raise RbValidationError(f"Unregistered source indices:\n{unregistered}")


def validate_stages_args(args: Dict[str, Any], sim_method: Callable) -> None:
    """Validate that argument keys are accepted by the given simulation method.

    Ignores common internal arguments injected automatically by the cocoregman.

    Args:
        args: Dictionary of user-provided arguments.
        sim_method: Simulation method to validate arguments against.

    Raises:
        RbValidationError: If an unrecognized argument is provided.
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
