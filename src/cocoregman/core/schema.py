"""Schema definitions for validating a runbook dictionary."""

from typing import Any, Dict


def _get_tb_entry_schema() -> Dict[str, Any]:
    """Return schema for a single testbench entry."""
    return {
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
    }


def _get_runbook_base_sch() -> Dict[str, Any]:
    """Return base schema for the runbook, excluding the general section."""
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


def _get_general_section_sch() -> Dict[str, Any]:
    """Return schema for the general section of the runbook."""
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


def get_runbook_schema(separate_general: bool = False) -> Dict[str, Any]:
    """Return the runbook schema.

    Args:
        separate_general: If True, the general section will be nested under a
            top-level general dictionary key. If False, its keys will be merged at
            the top level of the schema.

    Returns:
        A dictionary representing the runbook schema.
    """
    rb_sch = {**_get_runbook_base_sch()}
    gen_sect_sch = _get_general_section_sch()

    if separate_general:
        rb_sch["general"] = {"type": "dict", "schema": gen_sect_sch, "required": True}
    else:
        rb_sch.update(gen_sect_sch)
    return rb_sch
