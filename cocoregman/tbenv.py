"""cocoman testbench environment configuration module.

This module provides functions for managing and importing cocotb testbenches within
the current Python runtime environment. It ensures that all provided Runbook paths are
included and that specific testbenches are accessible for analysis, simulation and
testing.
"""

from importlib.util import find_spec, module_from_spec
from sys import path as sys_path
from types import ModuleType
from cocoregman.datatypes import Testbench
from cocoregman.errors import TbEnvImportError
from cocoregman.runbook import Runbook


def load_includes(rbook: Runbook) -> None:
    """Add include directories from a Runbook to the Python module search path.

    This function ensures that all directories specified under the 'include' key of
    the provided Runbook are added to the system's Python path. This allows Python
    to locate and import modules defined within those directories during simulation.

    Args:
        rbook: Runbook object containing the 'include' paths to be loaded.
    """
    for path in rbook.include:
        if str(path) not in sys_path:
            sys_path.append(str(path))


def load_n_import_tb(tb_info: Testbench) -> ModuleType:
    """Dynamically import the top-level module of a specified Testbench.

    Given a Testbench object, this function temporarily adds the testbench's path
    to the Python module search path and imports the module specified by 'tb_top'.
    This allows the cocoman framework to access and interact with the desired
    testbench components.

    Args:
        tb_info: Testbench object containing metadata about the testbench to import.

    Raises:
        TbEnvImportError: If a testbench top module cannot be imported correctly, or if
            the module could not be found.

    Returns:
        The imported Python module representing the testbench.
    """
    for path in [tb_info.path, tb_info.path.parent]:
        if path not in sys_path:
            sys_path.insert(0, str(path))

    try:
        spec = find_spec(f"{tb_info.path.name}.{tb_info.tb_top}")
    except ValueError as excp:
        raise TbEnvImportError(0, excp) from excp
    if spec is None:
        raise TbEnvImportError(
            1,
            f"could not correctly import {tb_info.path.name}.{tb_info.tb_top}",
        )
    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    return module
