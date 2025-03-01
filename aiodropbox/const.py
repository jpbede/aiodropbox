"""Constants for aiodropbox."""

from enum import StrEnum

MAX_UPLOAD_CHUNK_SIZE = 150 * 1024 * 1024  # 150MB
DEFAULT_CHUNK_SIZE = 5 * 1024 * 1024  # 5MB

CONTENT_ENDPOINT = "https://content.dropboxapi.com/2/files"
BASE_ENDPOINT = "https://api.dropboxapi.com/2"


class ContentType(StrEnum):
    """Content types for Dropbox API."""

    JSON = "application/json"
    OCTET = "application/octet-stream"
