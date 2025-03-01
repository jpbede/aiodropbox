"""Module contains a class for computing the same hash that the Dropbox API.

Code from https://github.com/dropbox/dropbox-api-content-hasher/blob/master/python/dropbox_content_hasher.py
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hashlib import _Hash


class DropboxContentHasher:
    """Computes a hash using the same algorithm that the Dropbox API uses for the "content_hash" metadata field.

    The digest() method returns a raw binary representation of the hash.  The
    hexdigest() convenience method returns a hexadecimal-encoded version, which
    is what the "content_hash" metadata field uses.

    This class has the same interface as the hashers in the standard 'hashlib'
    package.

    Example:
        hasher = DropboxContentHasher()
        with open('some-file', 'rb') as f:
            while True:
                chunk = f.read(1024)  # or whatever chunk size you want
                if len(chunk) == 0:
                    break
                hasher.update(chunk)
        print(hasher.hexdigest())

    """

    BLOCK_SIZE = 4 * 1024 * 1024

    def __init__(self) -> None:
        """Construct a new Dropbox hasher instance."""
        self._overall_hasher: _Hash | None = hashlib.sha256()
        self._block_hasher: _Hash | None = hashlib.sha256()
        self._block_pos = 0

        self.digest_size = self._overall_hasher.digest_size

    def update(self, new_data: bytes) -> None:
        """Update the hash object with the bytes-like object."""
        if self._overall_hasher is None:
            msg = "can't use this object anymore; you already called digest()"
            raise AssertionError(msg)

        new_data_pos = 0
        while new_data_pos < len(new_data):
            if self._block_pos == self.BLOCK_SIZE:
                self._overall_hasher.update(self._block_hasher.digest())
                self._block_hasher = hashlib.sha256()
                self._block_pos = 0

            space_in_block = self.BLOCK_SIZE - self._block_pos
            part = new_data[new_data_pos : (new_data_pos + space_in_block)]
            self._block_hasher.update(part)

            self._block_pos += len(part)
            new_data_pos += len(part)

    def _finish(self) -> _Hash:
        """Finish intermediate block hasher and return the hash object for the entire file."""
        if self._overall_hasher is None:
            msg = "can't use this object anymore; you already called digest() or hexdigest()"
            raise AssertionError(msg)

        if self._block_pos > 0:
            self._overall_hasher.update(self._block_hasher.digest())
            self._block_hasher = None
        h = self._overall_hasher
        self._overall_hasher = None  # Make sure we can't use this object anymore.
        return h

    def digest(self) -> bytes:
        """Return the digest of the data passed to the update() method."""
        return self._finish().digest()

    def hexdigest(self) -> str:
        """Return a hexadecimal digest as a string."""
        return self._finish().hexdigest()
