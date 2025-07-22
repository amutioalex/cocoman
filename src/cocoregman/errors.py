"""Custom exception classes definitions."""

# COMMAND LINE #


class CocoregmanError(Exception):
    """Base exception class for errors encountered during command-line processing."""


class CocoregmanNameError(CocoregmanError):
    """Raised when an unrecognized testbench or test name is found."""


# RUNBOOK #


class RbError(Exception):
    """Base exception class for errors encountered during runbook processing."""


class RbFileError(RbError):
    """Raised when a file-related error occurs while loading the runbook."""


class RbValidationError(RbError):
    """Raised when a runbook fails validation due to schema or path issues."""


class RbYAMLError(RbError):
    """Raised when a YAML-specific error occurs during runbook parsing."""


# TBENV #


class TbEnvError(Exception):
    """Base exception class for errors encountered during environemnt configuration."""


class TbEnvImportError(TbEnvError):
    """Raised when a import-related error occurs during environment configuration."""
