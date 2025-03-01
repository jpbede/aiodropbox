"""Module for upload session API calls."""

from collections.abc import AsyncIterator, Callable, Coroutine
import logging
from typing import Self

from aiohttp import ClientSession
import orjson

from .base import _BaseClient
from .const import CONTENT_ENDPOINT, ContentType
from .exceptions import DropboxError
from .hasher import DropboxContentHasher
from .models.folder import FileMetadata

_LOGGER = logging.getLogger(__name__)


class UploadSession(_BaseClient):
    """Upload session start response."""

    _offset = 0
    _path: str
    _session_id: str
    _started = False

    def __init__(
        self,
        *,
        stream: AsyncIterator[bytes],
        access_token_callback: Callable[[], Coroutine[None, None, str]],
        session: ClientSession | None = None,
    ) -> None:
        """Initialize the upload session."""
        super().__init__(access_token_callback=access_token_callback, session=session)

        self._stream = stream

    async def start(self) -> None:
        """Start an upload session."""
        first_chunk = await anext(self._stream)
        hasher = DropboxContentHasher()
        hasher.update(first_chunk)

        result = await self._raw_request(
            f"{CONTENT_ENDPOINT}/upload_session/start",
            headers={
                "Dropbox-API-Arg": orjson.dumps(
                    {
                        "close": False,
                        "content_hash": hasher.hexdigest(),
                    }
                ).decode(),
                "Content-Type": ContentType.OCTET,
            },
            data=first_chunk,
        )
        resp = await result.json(loads=orjson.loads)

        if "session_id" not in resp:
            msg = "Failed to start upload session: %s"
            raise DropboxError(msg, resp)

        _LOGGER.debug("Started upload session %s", resp["session_id"])

        self._session_id = resp["session_id"]
        self._offset += len(first_chunk)

    async def upload(self, path: str, chunk_size: int) -> None:
        """Upload the file."""
        self._path = path

        buffer = b""
        async for chunk in self._stream:
            buffer += chunk
            if len(buffer) >= chunk_size:
                await self._upload_chunk(buffer[:chunk_size])
                buffer = buffer[chunk_size:]
                self._offset += chunk_size

    async def finish(self) -> FileMetadata | None:
        """Finish an upload session."""
        result = await self._request(
            FileMetadata,
            f"{CONTENT_ENDPOINT}/upload_session/finish",
            headers={
                "Dropbox-API-Arg": orjson.dumps(
                    {
                        "cursor": {
                            "offset": self._offset,
                            "session_id": self._session_id,
                        },
                        "commit": {
                            "path": self._path,
                            "mute": True,
                        },
                    }
                ).decode(),
                "Content-Type": ContentType.OCTET,
            },
            data=b"",
        )

        _LOGGER.debug("Finished upload session %s", self._session_id)

        return result

    async def _upload_chunk(self, chunk: bytes) -> bool:
        """Upload a chunk of a file."""
        hasher = DropboxContentHasher()
        hasher.update(chunk)

        response = await self._raw_request(
            f"{CONTENT_ENDPOINT}/upload_session/append_v2",
            headers={
                "Dropbox-API-Arg": orjson.dumps(
                    {
                        "close": False,
                        "cursor": {
                            "offset": self._offset,
                            "session_id": self._session_id,
                        },
                        "content_hash": hasher.hexdigest(),
                    }
                ).decode(),
                "Content-Type": ContentType.OCTET,
            },
            data=chunk,
        )

        _LOGGER.debug("Uploaded chunk at offset %s", self._offset)

        return response.status == 200

    async def __aenter__(self) -> Self:
        """Async context manager enter."""
        await self.start()
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async context manager exit."""
        await self.finish()
