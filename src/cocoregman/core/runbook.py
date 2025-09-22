"""Runbook and associated dataclasses used to configure regression runs."""

from dataclasses import dataclass, field
from os.path import expanduser, expandvars
from pathlib import Path
from typing import Any

from cocotb.runner import Simulator
from yaml import MarkedYAMLError, YAMLError, safe_load

from cocoregman.core.validation import (
    validate_paths,
    validate_runbook,
    validate_stages_args,
)
from cocoregman.errors import RbFileError, RbYAMLError


@dataclass
class Testbench:
    """Testbench defined in a runbook.

    Attributes:
        path: Path to the testbench directory.
        srcs: List of source file indices used by this testbench.
        tb_top: Python module containing the cocotb tests.
        rtl_top: Top-level RTL module name.
        hdl: HDL type (e.g., 'verilog', 'vhdl').
        build_args: Arguments for the build stage.
        test_args: Arguments for the test stage.
        tags: Optional labels for filtering or categorizing testbenches.
    """

    path: Path = Path()
    srcs: list[int] = field(default_factory=list)
    tb_top: str = ""
    rtl_top: str = ""
    hdl: str = ""
    build_args: dict[str, Any] = field(default_factory=dict)
    test_args: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def __str__(self) -> str:
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
    """Complete runbook configuration.

    Attributes:
        title: Title or label for the runbook session.
        sim: Name of the simulator to use.
        srcs: Map of source file indices to absolute Paths.
        include: Additional paths to include.
        build_args: Global build-stage arguments.
        test_args: Global test-stage arguments.
        tbs: Dictionary of testbench names to Testbench instances.
    """

    title: str = ""
    sim: str = ""
    srcs: dict[int, Path] = field(default_factory=dict)
    include: list[Path] = field(default_factory=list)
    build_args: dict[str, Any] = field(default_factory=dict)
    test_args: dict[str, Any] = field(default_factory=dict)
    tbs: dict[str, Testbench] = field(default_factory=dict)

    def __str__(self) -> str:
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
            tb_lines = "\n    ".join(str(tb).splitlines())
            out += f"\n  {name}\n    {tb_lines}"
        return out

    def __contains__(self, name: str) -> bool:
        """Check whether a testbench with the given name exists."""
        return isinstance(name, str) and name in self.tbs

    @staticmethod
    def _expand_paths(file_path: Path, rb_dict: dict) -> dict:
        """Expand user and environment variables in paths and normalize them.

        Args:
            file_path: Path to the YAML runbook file.
            rb_dict: Parsed dictionary from the runbook YAML.

        Returns:
            Runbook dictionary with expanded paths.
        """

        def _get_abs_path(base: str, path: str) -> Path:
            """Convert a relative or env-based path to an absolute Path object.

            Args:
                base: Base path for resolving relative paths.
                path: Path string to resolve.

            Returns:
                Absoluted path computed from input.
            """
            expanded = Path(expandvars(path)).expanduser()
            return expanded if expanded.is_absolute() else Path(base) / expanded

        base_path = file_path
        aux_rb = rb_dict.copy()

        aux_rb["include"] = [
            _get_abs_path(base_path, p) for p in aux_rb.get("include", [])
        ]
        aux_rb["srcs"] = {
            k: _get_abs_path(base_path, v) for k, v in aux_rb.get("srcs", {}).items()
        }

        for tb in aux_rb.get("tbs", {}).values():
            tb["path"] = _get_abs_path(base_path, tb["path"])
            for key in ("build_args", "test_args"):
                tb[key] = {
                    k: expandvars(expanduser(v)) if isinstance(v, str) else v
                    for k, v in tb.get(key, {}).items()
                }

        general = aux_rb.get("general", aux_rb)
        for key in ("build_args", "test_args"):
            general[key] = {
                k: expandvars(expanduser(v)) if isinstance(v, str) else v
                for k, v in general.get(key, {}).items()
            }

        return aux_rb

    @staticmethod
    def _parse_yaml(file_path: Path) -> dict:
        """Parse a runbook YAML file safely and ensure default structures.

        Args:
            file_path: Path to the YAML file.

        Raises:
            RbFileError: If file cannot be read.
            RbYAMLError: If the YAML is malformed.

        Returns:
            Parsed runbook dictionary.
        """
        try:
            with file_path.open("r", encoding="utf-8") as f:
                rb_dict: dict = safe_load(f)
        except OSError as exc:
            raise RbFileError(exc) from exc
        except (MarkedYAMLError, YAMLError) as exc:
            raise RbYAMLError(exc) from exc

        rb_dict.setdefault("srcs", {})
        rb_dict.setdefault("include", [])
        rb_dict.setdefault("tbs", {})

        general: dict = rb_dict.get("general", rb_dict)
        general.setdefault("build_args", {})
        general.setdefault("test_args", {})

        for tb in rb_dict["tbs"].values():
            tb.setdefault("srcs", [])
            tb.setdefault("build_args", {})
            tb.setdefault("test_args", {})

        return rb_dict

    @classmethod
    def load_from_yaml(cls, file_path: Path) -> "Runbook":
        """Load, normalize, validate, and instantiate a Runbook from a YAML file.

        Args:
            file_path: Path to the runbook YAML file.

        Raises:
            RbFileError: File read failure.
            RbYAMLError: YAML parsing failure.
            RbValidationError: Schema or file structure violation.

        Returns:
            Fully initialized Runbook instance.
        """
        rb_dict = cls._parse_yaml(file_path)
        validate_runbook(rb_dict)

        rb_dict = cls._expand_paths(file_path.parent, rb_dict)
        validate_paths(rb_dict)

        general: dict = rb_dict.get("general", rb_dict)
        validate_stages_args(general["build_args"], Simulator.build)
        validate_stages_args(general["test_args"], Simulator.test)

        for tb in rb_dict["tbs"].values():
            validate_stages_args(tb["build_args"], Simulator.build)
            validate_stages_args(tb["test_args"], Simulator.test)

        return Runbook(
            title=general.get("title", ""),
            sim=general["sim"],
            srcs=rb_dict["srcs"],
            include=rb_dict["include"],
            build_args=general["build_args"],
            test_args=general["test_args"],
            tbs={
                name: Testbench(
                    path=tb["path"],
                    srcs=tb["srcs"],
                    tb_top=tb["tb_top"],
                    rtl_top=tb["rtl_top"],
                    hdl=tb["hdl"],
                    build_args=tb["build_args"],
                    test_args=tb["test_args"],
                    tags=tb.get("tags", []),
                )
                for name, tb in rb_dict["tbs"].items()
            },
        )
