"""Additional package setup configuration."""

from pathlib import Path
from typing import TYPE_CHECKING

from git import Commit, Repo, Tag
from setuptools import setup


if TYPE_CHECKING:
    from setuptools_scm import ScmVersion


def calculate_version(scm_version: ScmVersion) -> str:
    """Calculate the package version number according to the semantic versioning rules.

    Args:
        scm_version: The setuptools_scm version object.

    Returns:
        Formatted package version.
    """
    if not scm_version:
        return "0.0.0.dev0"

    repo = Repo(Path(__file__).parent)
    if not repo.tags:
        return "0.0.0.dev0"

    latest_tag: Tag = repo.tags[-1]
    if latest_tag.is_detached:
        return latest_tag.name

    latest_cmmt: Commit = repo.active_branch.commit
    if latest_tag.commit == latest_cmmt:
        return latest_tag.name

    branch_cmmts = list(repo.iter_commits())
    ind_tag_cmmt = branch_cmmts.index(latest_tag.commit)
    ind_latest_cmmt = branch_cmmts.index(latest_cmmt)
    new_cmmts = branch_cmmts[ind_latest_cmmt:ind_tag_cmmt]
    not_only_fix = any(not c.message.casefold().startswith("fix:") for c in new_cmmts)
    version = latest_tag.name.split(".")
    bump_index = 1 if not_only_fix else 2
    version[bump_index] = str(int(version[bump_index]) + 1)
    version = ".".join(version)
    return f"{version}.dev{len(new_cmmts)}"


setup(use_scm_version={"version_scheme": calculate_version})
