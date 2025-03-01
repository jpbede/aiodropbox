"""Base client for Dropbox API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from aiohttp import ClientResponse, ClientSession
from mashumaro.mixins.orjson import DataClassORJSONMixin
import orjson

from .const import ContentType
from .exceptions import DropboxBadInputError, DropboxError, DropboxTokenError

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine


async def _raise_for_dropbox_error(response: ClientResponse) -> None:
    """Raise an error for a response."""
    # no need to do anything if the request was successful
    if response.status == 200:
        return

    if response.status == 400:
        result = await response.text()
        raise DropboxBadInputError(result)

    # only decode JSON if the content type is JSON
    # otherwise we raise an error trying to decode a non JSON response
    if response.content_type == ContentType.JSON:
        json_result = await response.json(loads=orjson.loads)
        if json_result and "error" in json_result:
            summary = json_result["error_summary"]
            if response.status == 401:
                msg = f"Authentication error: {summary}"
                raise DropboxTokenError(msg)

            raise DropboxError(summary)

    result = await response.text()
    msg = f"Error with status code {response.status}: {result}"
    raise DropboxError(msg)


class _BaseClient:
    """Base client for Dropbox API."""

    _close_session: bool = False

    def __init__(
        self,
        *,
        access_token_callback: Callable[[], Coroutine[None, None, str]],
        session: ClientSession | None = None,
    ) -> None:
        """Create a new base client."""
        self._access_token_callback = access_token_callback
        if session is None:
            self._session = ClientSession()
            self._close_session = True
        else:
            self._session = session

    async def _raw_request(self, url: str, **kwargs: Any) -> ClientResponse:
        """Make a raw request and return the aiohttp client session."""
        if (access_token := await self._access_token_callback()) is None:
            msg = "Callback did not return an access token"
            raise DropboxTokenError(msg)

        headers = {"Authorization": f"Bearer {access_token}"}
        if "headers" in kwargs:
            kwheaders = kwargs.pop("headers")
            headers.update(kwheaders)

        if "Content-Type" not in headers:
            headers["Content-Type"] = ContentType.JSON

        resp = await self._session.post(url, headers=headers, **kwargs)
        await _raise_for_dropbox_error(resp)

        return resp

    async def _request[_T: DataClassORJSONMixin](
        self,
        cls: type[_T] | None,
        url: str,
        **kwargs: Any,
    ) -> _T | None:
        """Make a request."""
        response = await self._raw_request(url, **kwargs)
        if cls is None:
            return None

        result = await response.text()
        return cls.from_json(result)

    async def close(self) -> None:
        """Close."""
        if self._close_session:
            await self._session.close()

    async def __aenter__(self) -> Self:
        """Async enter."""
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit."""
        await self.close()
