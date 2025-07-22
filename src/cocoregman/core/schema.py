"""Schema definitions for validating a runbook YAML configuration."""

from typing import Any


def _get_tb_entry_schema() -> dict[str, Any]:
    """Return schema for a single testbench description entry."""
    return {
        "srcs": {
            "type": "list",
            "required": False,
            "empty": False,
            "schema": {"type": "integer"},
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
            "empty": False,
            "schema": {"type": "string"},
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


def _get_runbook_base_schema() -> dict[str, Any]:
    """Return base schema for the runbook (excluding general configuration)."""
    return {
        "srcs": {
            "type": "dict",
            "keysrules": {"type": "integer", "coerce": int},
            "valuesrules": {"type": "string", "empty": False},
            "required": False,
            "empty": False,
        },
        "tbs": {
            "type": "dict",
            "keysrules": {"type": "string"},
            "valuesrules": {
                "type": "dict",
                "schema": _get_tb_entry_schema(),
            },
        },
        "include": {
            "type": "list",
            "schema": {"type": "string"},
            "required": False,
            "empty": False,
        },
    }


def _get_general_section_schema() -> dict[str, Any]:
    """Return schema for the general configuration section of the runbook."""
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


def get_runbook_schema(separate_general: bool = False) -> dict[str, Any]:
    """Return the full runbook schema for validation.

    Args:
        separate_general: If True, the general config section will be nested under the
            `general` key. If False, general keys will be merged at the top level.

    Returns:
        A cerberus-compatible dictionary schema.
    """
    schema = _get_runbook_base_schema()
    general_schema = _get_general_section_schema()

    if separate_general:
        schema["general"] = {"type": "dict", "required": True, "schema": general_schema}
    else:
        schema.update(general_schema)

    return schema
