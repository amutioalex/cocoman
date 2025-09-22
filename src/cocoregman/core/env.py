"""Testbench environment setup and dynamic importing for regression runs."""

from importlib.util import find_spec, module_from_spec
from sys import path as sys_path
from types import ModuleType

from cocotb.decorators import test as cctb_test

from cocoregman.core.runbook import Runbook, Testbench
from cocoregman.errors import TbEnvImportError


def get_test_names(tb_pkg: ModuleType) -> list[str]:
    """Return all cocotb test function names from a testbench module.

    Args:
        tb_pkg: Imported Python module representing the testbench.

    Returns:
        A list of function names decorated with @cocotb.test.
    """
    return [
        name for name in dir(tb_pkg) if isinstance(getattr(tb_pkg, name), cctb_test)
    ]


def load_includes(rbook: Runbook) -> None:
    """Append include paths from a runbook to the Python import path.

    Args:
        rbook: A Runbook object with include directories to add to sys.path.
    """
    for path in rbook.include:
        path_str = str(path)
        if path_str not in sys_path:
            sys_path.append(path_str)


def load_n_import_tb(tb_info: Testbench) -> ModuleType:
    """Dynamically import a testbench module from its directory.

    Args:
        tb_info: Testbench object.

    Raises:
        TbEnvImportError: If the testbench module cannot be found or loaded.

    Returns:
        The imported module object representing the testbench.
    """
    for path in [tb_info.path, tb_info.path.parent]:
        path_str = str(path)
        if path_str not in sys_path:
            sys_path.insert(0, path_str)

    try:
        mod_path = f"{tb_info.path.name}.{tb_info.tb_top}"
        spec = find_spec(mod_path)
    except ValueError as exc:
        raise TbEnvImportError(exc) from exc

    if spec is None:
        raise TbEnvImportError(f"Could not import testbench module '{mod_path}'")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
