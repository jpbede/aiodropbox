"""Exceptions for aiodropbox."""


class DropboxError(Exception):
    """Generic error occurred in aiodropbox package."""


class DropboxTokenError(DropboxError):
    """Error occurred when there was an authentication/token error in aiodropbox package."""


class DropboxBadInputError(DropboxError):
    """Error occurred when there was a bad input error in aiodropbox package."""
