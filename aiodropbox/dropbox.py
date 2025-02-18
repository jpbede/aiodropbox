"""Dropbox client implementation."""
from dataclasses import dataclass
from typing import Callable, Coroutine, Any, Self, AsyncIterator

import orjson
from aiohttp import ClientSession

from aiodropbox.const import MAX_UPLOAD_CHUNK_SIZE, CONTENT_ENDPOINT, BASE_ENDPOINT
from aiodropbox.exceptions import DropboxAuthError
from aiodropbox.hasher import DropboxContentHasher
from aiodropbox.models import BaseResponse
from aiohttp import ClientResponse, StreamReader

@dataclass
class Dropbox:

    access_token_callback: Callable[[], Coroutine[None, None, str]] | None = None
    session: ClientSession | None = None

    _close_session: bool = False

    async def _raw_request(self, method: str, url: str, **kwargs: Any) -> ClientResponse:
        """Make a request."""
        if self.access_token_callback is None:
            raise DropboxAuthError("No access token available")

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        access_token = await self.access_token_callback()
        headers = {"Authorization": f"Bearer {access_token}"}
        if "headers" in kwargs:
            kwheaders = kwargs.pop("headers")
            headers.update(kwheaders)

        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        resp = await self.session.request(method, url, headers=headers, **kwargs)

        resp.raise_for_status()
        return resp

    async def _request(self, method: str, url: str, **kwargs: Any) -> str:
        """Make a request."""
        response = await self._raw_request(method, url, **kwargs)
        return await response.text()

    async def list_folder(self, path: str | None = None) -> BaseResponse[dict]:
        """List a folder."""
        result = await self._request("POST", f"{BASE_ENDPOINT}/files/list_folder", json={"path": path or ""})
        return BaseResponse.from_json(result)

    async def delete_file(self, path: str):
        """Delete a file."""
        await self._request("POST", f"{BASE_ENDPOINT}/files/delete_v2", json={"path": path})

    async def download_file(self, path: str) -> StreamReader:
        """Download a file."""
        response = await self._raw_request(
            "POST",
            f"{CONTENT_ENDPOINT}/download",
            headers={
                "Dropbox-API-Arg": orjson.dumps({"path": path}).decode(),
                "Content-Type": "application/octet-stream",
            }
        )

        result = response.headers.get("Dropbox-API-Result")
        if result is None:
            raise ValueError("Missing Dropbox-API-Result header")

        return response.content


    async def close(self):
        """Close"""
        if self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Self:
        """Async enter."""
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit."""
        await self.close()