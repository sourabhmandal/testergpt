# Global Exceptions for the project

class BaseError(Exception):
    """Base class for all exceptions raised by the project."""
    pass

class DatabaseError(BaseError):
    """Exception raised for database-related errors."""
    pass

class GitHubAPIError(BaseError):
    """Exception raised for GitHub API errors."""
    pass
