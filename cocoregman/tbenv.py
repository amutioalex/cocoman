"""cocoman testbench environment configuration module.

This module provides functions for managing and importing cocotb testbenches within
the current Python runtime environment. It ensures that all provided Runbook paths are
included and that specific testbenches are accessible for analysis, simulation and
testing.
"""

from importlib.util import find_spec, module_from_spec
from sys import path as sys_path
from types import ModuleType
from cocoregman.runbook import Runbook, Testbench


class TbEnvError(Exception):
    """Base exception class for errors encountered during testbench environment
    configuration."""

    def __init__(self, err_prefix: str, tag_id: int, message: str) -> None:
        """Initialize a generic TbEnverror with a given message.

        Args:
            err_prefix: The sub-error prefix name.
            tag_id: The specific error tag number id.
            message: Description of the error.
        """
        super().__init__(message)
        self.prefix = err_prefix
        self.tag_id = tag_id
        self.message = message

    def __str__(self) -> str:
        """Return a string representation of the error.

        Returns:
            The error message.
        """
        return f"TE{self.prefix}-{self.tag_id}: {self.message}"


class TbEnvImportError(TbEnvError):
    """Raised when a import-related error occurs during testbench environment
    configuration."""

    def __init__(self, tag_id: int, message: str) -> None:
        """Initialize a TbEnvImportError with a prefixed message.

        Args:
            tag_id: The specific error tag number id.
            message: Description of the import-related error.
        """
        super().__init__("I", tag_id=tag_id, message=message)


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
        raise TbEnvImportError(0, excp)
    if spec is None:
        raise TbEnvImportError(
            1,
            f"could not correctly import {tb_info.path.name}.{tb_info.tb_top}",
        )
    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    return module
