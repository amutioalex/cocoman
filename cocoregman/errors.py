"""Custom exception classes definitions."""


# COMMAND LINE #


class CocomanError(Exception):
    """Base exception class for errors encountered during command-line processing."""

    def __init__(self, err_prefix: str, tag_id: int, message: str) -> None:
        """Initialize a generic CocomanError with a given message.

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
        return f"CM{self.prefix}-{self.tag_id}: {self.message}"


class CocomanNameError(CocomanError):
    """Raised when an unrecognized testbench or test name is found."""

    def __init__(self, tag_id: int, message: str) -> None:
        """Initialize a CocomanNameError with a prefixed message.

        Args:
            tag_id: The specific error tag number id.
            message: Description of the naming-related error.
        """
        super().__init__("N", tag_id=tag_id, message=message)


# RUNBOOK #


class RbError(Exception):
    """Base exception class for errors encountered during runbook processing."""

    def __init__(self, err_prefix: str, tag_id: int, message: str) -> None:
        """Initialize a generic RbError with a given message.

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
        return f"RB{self.prefix}-{self.tag_id}: {self.message}"


class RbFileError(RbError):
    """Raised when a file-related error occurs while loading the runbook."""

    def __init__(self, tag_id: int, message: str) -> None:
        """Initialize a RbFileError with a prefixed message.

        Args:
            tag_id: The specific error tag number id.
            message: Description of the file-related error.
        """
        super().__init__(err_prefix="F", tag_id=tag_id, message=message)


class RbValidationError(RbError):
    """Raised when a runbook fails validation due to schema or path issues."""

    def __init__(self, tag_id: int, message: str) -> None:
        """Initialize a RbValidationError with a prefixed message.

        Args:
            tag_id: The specific error tag number id.
            message: Description of the validation-related error.
        """
        super().__init__(err_prefix="V", tag_id=tag_id, message=message)


class RbYAMLError(RbError):
    """Raised when a YAML-specific error occurs during runbook parsing."""

    def __init__(self, tag_id: int, message: str) -> None:
        """Initialize a RbYAMLError with a prefixed message.

        Args:
            tag_id: The specific error tag number id.
            message: Description of the YAML-related error.
        """
        super().__init__(err_prefix="Y", tag_id=tag_id, message=message)


# TBENV #


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
