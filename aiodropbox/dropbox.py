"""Dropbox client implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import orjson

from .base import _BaseClient
from .const import (
    BASE_ENDPOINT,
    CONTENT_ENDPOINT,
    DEFAULT_CHUNK_SIZE,
    MAX_UPLOAD_CHUNK_SIZE,
    ContentType,
)
from .exceptions import DropboxBadInputError, DropboxError
from .models.account import FullAccount, SpaceUsage
from .models.folder import BaseResponse, DeleteResult, FileMetadata
from .upload_session import UploadSession

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from aiohttp import StreamReader


class Dropbox(_BaseClient):
    """Dropbox client implementation."""

    async def current_account(self) -> FullAccount | None:
        """Get the current account."""
        return await self._request(
            FullAccount, f"{BASE_ENDPOINT}/users/get_current_account", data="null"
        )

    async def space_usage(self) -> SpaceUsage | None:
        """Get the space usage."""
        return await self._request(
            SpaceUsage, f"{BASE_ENDPOINT}/users/get_space_usage", data="null"
        )

    async def list_folder(
        self, path: str | None = None
    ) -> BaseResponse[FileMetadata] | None:
        """List a folder."""
        return await self._request(
            BaseResponse[FileMetadata],
            f"{BASE_ENDPOINT}/files/list_folder",
            json={"path": path or ""},
        )

    async def delete_file(self, path: str) -> DeleteResult | None:
        """Delete a file."""
        return await self._request(
            DeleteResult, f"{BASE_ENDPOINT}/files/delete_v2", json={"path": path}
        )

    async def download_file(self, path: str) -> StreamReader:
        """Download a file."""
        response = await self._raw_request(
            f"{CONTENT_ENDPOINT}/download",
            headers={
                "Dropbox-API-Arg": orjson.dumps({"path": path}).decode(),
                "Content-Type": ContentType.OCTET,
            },
        )

        result = response.headers.get("Dropbox-API-Result")
        if result is None:
            msg = "Missing Dropbox-API-Result header"
            raise DropboxError(msg)

        return response.content

    async def upload_file(
        self,
        path: str,
        stream: AsyncIterator[bytes],
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:
        """Upload a file using an upload session."""
        if chunk_size > MAX_UPLOAD_CHUNK_SIZE:
            msg = "Chunk size must be less than 150MB"
            raise DropboxError(msg)

        if not path.startswith("/"):
            msg = "Path must start with /"
            raise DropboxBadInputError(msg)

        async with UploadSession(
            access_token_callback=self._access_token_callback,
            session=self._session,
            stream=stream,
        ) as session:
            await session.upload(path, chunk_size)
