"""Utility functions for validating runbook input structures and file paths."""

from __future__ import annotations

from fnmatch import fnmatch
from inspect import getfullargspec
from re import compile as re_compile
from re import error as re_error
from re import fullmatch as re_fullmatch
from typing import TYPE_CHECKING, Any, Callable
from warnings import warn

from cerberus import Validator

from cocoregman.core.schema import get_runbook_schema
from cocoregman.errors import RbValidationError

if TYPE_CHECKING:
    from pathlib import Path


def match_globs(text: str, globs: list[str]) -> bool:
    """Check if a string fully matches any of the provided glob patterns.

    Args:
        text: The string to evaluate.
        globs: A list of glob patterns.

    Returns:
        True if the string fully matches any of the glob patterns.
    """
    return any(fnmatch(text, pattern) for pattern in globs)


def match_regexs(text: str, regexs: list[str]) -> bool:
    """Check if a string fully matches any of the provided regex patterns.

    Args:
        text: The string to evaluate.
        regexs: A list of regex patterns.

    Returns:
        True if the string fully matches any of the regex patterns.
    """
    return any(re_fullmatch(pattern, text) for pattern in regexs)


def validate_regexs(*patterns: list[str] | None) -> tuple[str, str] | None:
    """Validate all strings contained in a list as valid regex patterns.

    Args:
        patterns: A list containing regex patterns

    Raises:
        ValueError: If one of the string is not valid.
    """
    try:
        for collection in patterns:
            for p in collection:
                re_compile(p)
    except re_error as exc:
        return (p, exc.msg)
    return None


def validate_runbook(rb_dict: dict) -> None:
    """Validate the structure of a runbook dictionary.

    Args:
        rb_dict: Dictionary parsed from a runbook YAML file.

    Raises:
        RbValidationError: If the dictionary doesn't conform to the expected schema.
    """
    if "general" not in rb_dict:
        warn(
            "[Future Deprecation] Runbook structure without 'general' section.",
            UserWarning,
            stacklevel=2,
        )

    schema = get_runbook_schema(separate_general="general" in rb_dict)
    validator = Validator()

    if not validator.validate(rb_dict, schema):
        raise RbValidationError(f"YAML schema validation failed:\n{validator.errors}")


def validate_paths(rb_dict: dict[str, str | int | list[int] | list[str | Any]]) -> None:
    """Validate all paths and source references in a runbook dictionary.

    This function assumes that the provided runbook dictionary contains all
    sections/keys listed in the schema, even if void.

    Args:
        rb_dict: A validated runbook dictionary.

    Raises:
        RbValidationError: If any path is missing or source index is unregistered
    """
    all_srcs = set(rb_dict.get("srcs", {}).keys())
    unregistered: dict[str, list[int]] = {}
    missing_paths: list[Path]

    missing_paths = [p for p in rb_dict.get("srcs", {}).values() if not p.is_file()]

    for name, tb in rb_dict.get("tbs", {}).items():
        tb_path: Path = tb["path"]
        if not tb_path.is_dir():
            missing_paths.append(tb["path"])

        missing_indices = [i for i in tb.get("srcs", []) if i not in all_srcs]
        if missing_indices:
            unregistered[name] = missing_indices

    missing_paths.extend([p for p in rb_dict.get("include", []) if not p.exists()])

    if missing_paths:
        raise RbValidationError(f"Non-existent paths\n{missing_paths}")
    if unregistered:
        raise RbValidationError(f"Unregistered source indices:\n{unregistered}")


def validate_stages_args(args: dict[str, Any], sim_method: Callable) -> None:
    """Validate user-provided simulation stage arguments.

    Ignores common internal arguments injected automatically by the orchestrator.

    Args:
        args: Argument dictionary for a simulation stage (build/test).
        sim_method: Method/function of the simulation stage.

    Raises:
        RbValidationError: If any user argument is not accepted by the method.
    """
    ignored = {
        "always",
        "hdl_toplevel",
        "hdl_toplevel_lang",
        "self",
        "sources",
        "testcase",
        "test_module",
        "timescale",
        "verilog_sources",
        "vhdl_sources",
    }

    valid_args = [arg for arg in getfullargspec(sim_method).args if arg not in ignored]

    invalid_keys = [key for key in args if key not in valid_args]
    if invalid_keys:
        raise RbValidationError(
            f"Invalid argument(s) for '{sim_method.__name__}': {invalid_keys}. "
            f"Allowed: {valid_args}"
        )
