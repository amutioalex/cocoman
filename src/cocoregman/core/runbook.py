# pylint: disable=wrong-import-position, too-many-instance-attributes, import-error
"""Runbook and associated dataclasses declarations module."""

from dataclasses import dataclass, field
from os.path import expanduser, expandvars
from pathlib import Path
from typing import Any, Dict, List
from cocotb.runner import Simulator
from yaml import MarkedYAMLError, safe_load, YAMLError
from cocoregman.core.validation import (
    validate_paths,
    validate_runbook,
    validate_stages_args,
)
from cocoregman.errors import RbFileError, RbYAMLError


@dataclass
class Testbench:
    """Represent a runbook testbench configuration.

    Attributes:
        path: Absolute path to the directory containing the cocotb testbench module.
        srcs: List of source file indices used by the testbench.
        tb_top: Top-level Python module containing cocotb tests.
        rtl_top: Top-level RTL module name.
        hdl: Hardware description language.
        build_args: Build-stage arguments.
        test_args: Test-stage arguments.
        tags: List of optional tags for filtering/grouping testbenches.
    """

    path: Path = Path("")
    srcs: List[int] = field(default_factory=list)
    tb_top: str = ""
    rtl_top: str = ""
    hdl: str = ""
    build_args: Dict[str, Any] = field(default_factory=dict)
    test_args: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def __str__(self):
        """Return a string representation of the Testbench instance."""
        return (
            f"path: {self.path}\n"
            f"srcs: {', '.join(map(str, self.srcs))}\n"
            f"tb_top: {self.tb_top}\n"
            f"rtl_top: {self.rtl_top}\n"
            f"hdl: {self.hdl}\n"
            f"build_args: {self.build_args}\n"
            f"test_args: {self.test_args}\n"
            f"tags: {', '.join(self.tags)}\n"
        )


@dataclass
class Runbook:
    """Represent the full runbook metadata and configuration.

    Attributes:
        title: Descriptive title of the runbook.
        sim: Simulation tool name.
        srcs: Mapping from source indices to file paths.
        include: Directories to include in the Python path.
        build_args: Global build-stage arguments.
        test_args: Global test-stage arguments.
        tbs: Mapping from testbench names to Testbench instance.
    """

    title: str = ""
    sim: str = ""
    srcs: Dict[int, Path] = field(default_factory=dict)
    include: List[Path] = field(default_factory=list)
    build_args: Dict[str, Any] = field(default_factory=dict)
    test_args: Dict[str, Any] = field(default_factory=dict)
    tbs: Dict[str, Testbench] = field(default_factory=dict)

    def __str__(self):
        """Return a string representation of the Runbook instance."""
        out = (
            f"title: {self.title}\n"
            f"sim: {self.sim}\n"
            f"srcs: {self.srcs}\n"
            f"include: {', '.join(map(str, self.include))}\n"
            f"build_args: {self.build_args}\n"
            f"test_args: {self.test_args}\n"
            f"tbs:"
        )
        for name, tb in self.tbs.items():
            tb_str = "\n    ".join(str(tb).splitlines())
            out += f"\n  {name}\n    {tb_str}"
        return out

    def __contains__(self, name: str) -> bool:
        """Check whether the given name is a registered testbench."""
        return isinstance(name, str) and name in self.tbs

    @staticmethod
    def _expand_paths(file_path: Path, rb_dict: dict) -> dict:
        """Expand and normalize all paths and environment variables in the runbook.

        Args:
            file_path: Path to the source YAML file.
            rb_dict: A runbook-like dictionary.

        Returns:
            The provided runbook-like dictionary with the expanded paths.
        """

        def _get_abs_path(base: str, path: str) -> Path:
            """Convert a relative or env-based path to an absolute Path object.

            Args:
                base: Base path for resolving relative paths.
                path: Path string to resolve.

            Returns:
                Absoluted path computed from input.
            """
            expanded = Path(expandvars(expanduser(path)))
            return expanded if expanded.is_absolute() else Path(base) / expanded

        aux_rb = rb_dict.copy()

        aux_rb["include"] = [_get_abs_path(file_path, p) for p in aux_rb["include"]]
        aux_rb["srcs"] = {
            k: _get_abs_path(file_path, v) for k, v in aux_rb["srcs"].items()
        }

        for tb in aux_rb["tbs"].values():
            tb["path"] = _get_abs_path(file_path, tb["path"])
            for key in ("build_args", "test_args"):
                tb[key] = {
                    k: expandvars(expanduser(v)) if isinstance(v, str) else v
                    for k, v in tb[key].items()
                }

        general = aux_rb.get("general", aux_rb)
        for key in ("build_args", "test_args"):
            general[key] = {
                k: expandvars(expanduser(v)) if isinstance(v, str) else v
                for k, v in general[key].items()
            }

        return aux_rb

    @staticmethod
    def _parse_yaml(file_path: Path) -> dict:
        """Safely parse YAML file and apply default values to critical fields.

        Args:
            file_path: Path to a YAML file.

        Raises:
            es:
            RbFileError: If an error occurs while trying to read the file.
            RbYAMLError: If the YAML file is invalid or cannot be parsed.

        Returns:
            A YAML dictionary parsed from the provided file.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f_handler:
                rb_dict: dict = safe_load(f_handler)
        except OSError as exc:
            raise RbFileError(exc) from exc
        except (MarkedYAMLError, YAMLError) as exc:
            raise RbYAMLError(exc) from exc

        rb_dict.setdefault("srcs", {})
        rb_dict.setdefault("include", [])

        general_dict: dict = rb_dict.get("general", rb_dict)
        general_dict.setdefault("build_args", {})
        general_dict.setdefault("test_args", {})
        rb_dict.setdefault("tbs", {})
        for _, tb in rb_dict["tbs"].items():
            tb: dict
            tb.setdefault("srcs", [])
            tb.setdefault("build_args", {})
            tb.setdefault("test_args", {})
        return rb_dict

    @classmethod
    def load_from_yaml(cls, file_path: Path) -> "Runbook":
        """Load and validate a runbook YAML file into a Runbook instance.

        This method validates the YAML syntax, schema, and paths; normalizes paths; and
        instantiates a fully populated Runbook object.

        Args:
            file_path: Path to the YAML file to load.

        Raises:
            RbFileError: If the file cannot be read.
            RbYAMLError: If the YAML content is malformed.
            RbValidationError: If schema or file structure validation fails.

        Returns:
            Validated and instantiated Runbook object.
        """
        rb_dict = cls._parse_yaml(file_path)
        validate_runbook(rb_dict)

        rb_dict = cls._expand_paths(file_path.parent, rb_dict)
        validate_paths(rb_dict)

        general_dict: dict = rb_dict.get("general", rb_dict)
        validate_stages_args(general_dict["build_args"], Simulator.build)
        validate_stages_args(general_dict["test_args"], Simulator.test)

        for _, tb in rb_dict["tbs"].items():
            validate_stages_args(tb["build_args"], Simulator.build)
            validate_stages_args(tb["test_args"], Simulator.test)

        return Runbook(
            title=general_dict.get("title", ""),
            sim=general_dict["sim"],
            srcs=rb_dict["srcs"],
            include=rb_dict["include"],
            build_args=general_dict["build_args"],
            test_args=general_dict["test_args"],
            tbs={
                name: Testbench(
                    build_args=tb["build_args"],
                    hdl=tb["hdl"],
                    path=tb["path"],
                    rtl_top=tb["rtl_top"],
                    srcs=tb["srcs"],
                    tags=tb.get("tags", []),
                    tb_top=tb["tb_top"],
                    test_args=tb["test_args"],
                )
                for name, tb in rb_dict["tbs"].items()
            },
        )
