"""Models for aiodropbox."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Annotated, Union

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin
from mashumaro.types import Discriminator


@dataclass(frozen=True, slots=True)
class BaseResponse[T](DataClassORJSONMixin):

    cursor: str
    entries: List[
        Annotated[
            Union[FileMetadata], Discriminator(include_supertypes=True, variant_tagger_fn=lambda x: x.tag)
        ]
    ]

@dataclass(frozen=True, slots=True)
class FileMetadata(DataClassORJSONMixin):

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