"""Exceptions for aiodropbox."""

class DropboxError(Exception):
    """Generic error occurred in aiodropbox package."""

class DropboxAuthError(DropboxError):
    """Error occurred when there was an authentication error in aiodropbox package."""