# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CESNET i.a.l.e.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""A seekable file-like object that merges a cached header with an underlying stream."""

import os
from io import RawIOBase


class ReplyStream(RawIOBase):
    """A seekable, read-only file-like wrapper that serves bytes from two sources.

    1) An *underlying* (usually non-seek-friendly or expensive) stream.
    2) A *pre-cached* region loaded into memory up front.

    The cached region starts at ``buffer_pos`` and extends to EOF (size
    ``file_size - buffer_pos``). Reads that fall within this region are served
    from memory; reads before ``buffer_pos`` are delegated to the underlying
    stream.

    This is useful when you need random access semantics (seek/tell) but can
    afford to prefetch a known portion of the stream (e.g., a header, trailer, footer,
    index, or any region you expect to reread frequently).
    """

    def __init__(self, underlying_stream, buffer_pos, file_size):
        """Initialize the ReplyStream and pre-cache the header region.

        Args:
            underlying_stream:
                A binary stream supporting ``readinto()`` and ``seek()``.
            buffer_pos:
                Absolute byte offset where the in-memory cached region begins.
                Bytes in the range ``[buffer_pos, file_size)`` are cached.
            file_size:
                Total size of the logical file/stream in bytes. This is used to
                compute cache size and to support ``SEEK_END``.

        Notes:
            - This implementation eagerly reads the entire cached region
              (from ``buffer_pos`` to EOF) into memory.
            - After caching, the underlying stream is rewound to position 0.
        """
        self.underlying_stream = underlying_stream
        self.current_pos = 0
        self.file_size = file_size

        self.buffer_pos = buffer_pos
        self.buffer_size = file_size - buffer_pos
        self.buffer = self.read_buffer(
            buffer_pos=self.buffer_pos, size=self.buffer_size
        )
        self.underlying_stream.seek(0)

    def read_buffer(self, buffer_pos, size):
        """Read exactly ``size`` bytes from the underlying stream into memory.

        This helper seeks the underlying stream to ``buffer_pos`` and performs
        repeated ``readinto()`` calls until the requested number of bytes are
        read. If the underlying stream reaches EOF (or makes no progress)
        before reading ``size`` bytes, an ``EOFError`` is raised.

        Args:
            buffer_pos: Absolute byte offset to start reading from.
            size: Number of bytes to read.

        Returns:
            A ``bytes`` object of length ``size``.

        Raises:
            EOFError: If fewer than ``size`` bytes are available.
        """
        self.underlying_stream.seek(buffer_pos)
        buffer = bytearray(size)
        view = memoryview(buffer)
        got = 0
        while got < size:
            m = self.underlying_stream.readinto(view[got:])
            if not m:  # 0 or None => EOF / no progress
                raise EOFError(f"expected {size} bytes, got {got}")
            got += m
        return bytes(buffer)

    def seekable(self):
        """Return whether the stream is seekable."""
        return True

    def readable(self):
        """Return whether the stream is readable."""
        return True

    def writable(self):
        """Return whether the stream is writable."""
        return False

    def seek(self, offset, whence=os.SEEK_SET):
        """Seek to a position in the stream.

        Use cache when seeking within the cached header region, otherwise seek in the underlying stream.
        """
        if whence == os.SEEK_SET:
            self.current_pos = offset
        elif whence == os.SEEK_CUR:
            self.current_pos = self.current_pos + offset
        elif whence == os.SEEK_END:
            self.current_pos = self.file_size + offset
        else:
            raise ValueError("Invalid value for 'whence'.")

        # Only seek in the underlying stream if we're reading outside the cached header region
        if self.current_pos < self.buffer_pos:
            # Before the cached region - seek in underlying stream
            self.underlying_stream.seek(self.current_pos, os.SEEK_SET)

        return self.current_pos

    def tell(self):
        """Return the current position in the stream."""
        return self.current_pos

    def readinto(self, b):
        """Read bytes into a pre-allocated, writable buffer.

        This is the core I/O method required by ``RawIOBase``. It fills ``b`` with
        up to ``len(b)`` bytes from the current position and advances the position
        by the number of bytes read.

        Behavior:
            - If ``current_pos`` is within the cached region, copy from ``self.buffer``.
            - Otherwise, delegate to ``underlying_stream.readinto()``.

        Args:
            b: A writable, buffer-protocol object (e.g., ``bytearray`` or memoryview).

        Returns:
            The number of bytes read (0 indicates EOF for typical streams).

        Notes:
            The cached region copy uses slicing on the cached bytes. The end index
            is clamped to the cached region length.
        """
        size = len(b)
        if self.current_pos >= self.buffer_pos:
            position_inside_buffer = self.current_pos - self.buffer_pos
            data_to_copy = self.buffer[
                position_inside_buffer : min(size, self.buffer_size)
                + position_inside_buffer
            ]
            b[: len(data_to_copy)] = data_to_copy
            read_byte_count = len(data_to_copy)
        else:
            read_byte_count = self.underlying_stream.readinto(b)
        self.current_pos += read_byte_count
        return read_byte_count

    def close(self):
        """Close the ReplyStream and its underlying stream."""
        self.underlying_stream.close()
