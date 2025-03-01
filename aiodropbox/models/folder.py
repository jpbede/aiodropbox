"""Models for aiodropbox."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from mashumaro.mixins.orjson import DataClassORJSONMixin
from mashumaro.types import Discriminator


@dataclass(frozen=True, slots=True)
class BaseResponse[T](DataClassORJSONMixin):
    """Base response for Dropbox API."""

    cursor: str
    entries: list[
        Annotated[
            T, Discriminator(include_supertypes=True, variant_tagger_fn=lambda x: x.tag)
        ]
    ]


@dataclass(frozen=True, slots=True)
class FileMetadata(DataClassORJSONMixin):
    """Representation of a file metadata."""

    name: str
    path_lower: str
    path_display: str
    id: str
    client_modified: str
    server_modified: str
    rev: str
    size: int
    content_hash: str
    is_downloadable: bool

    tag: str = "file"


@dataclass(frozen=True, slots=True)
class DeleteResult(DataClassORJSONMixin):
    """Result of a delete operation."""

    metadata: FileMetadata
