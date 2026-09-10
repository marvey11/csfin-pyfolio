class RepositoryCorruptedError(Exception):
    """
    This exception is used to indicate that a repository's underlying JSON file is
    corrupted and cannot be loaded or processed.
    """

    pass


class InsufficientSharesError(Exception):
    """Raised when a sale exceeds the active FIFO lots."""
