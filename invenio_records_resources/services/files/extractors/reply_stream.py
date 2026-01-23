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
    """A seekable file-like object that precaches part of an underlying stream.
    """

    def __init__(self, underlying_stream, buffer_pos, file_size):
        """Initialize a ReplyStream with a cached header region."""
        self.underlying_stream = underlying_stream
        self.current_pos = 0
        self.file_size = file_size

        self.buffer_pos = buffer_pos
        self.buffer_size = file_size - buffer_pos
        self.buffer = self.read_buffer(buffer_pos=self.buffer_pos, size=self.buffer_size)
        self.underlying_stream.seek(0)


    def read_buffer(self, buffer_pos, size):

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
        size = len(b)
        if self.current_pos >= self.buffer_pos:
            position_inside_buffer = self.current_pos - self.buffer_pos
            data_to_copy = self.buffer[position_inside_buffer: min(size, self.buffer_size) + position_inside_buffer]
            b[:len(data_to_copy)] = data_to_copy
            read_byte_count = len(data_to_copy)
        else:
            read_byte_count = self.underlying_stream.readinto(b)
        self.current_pos += read_byte_count
        return read_byte_count

    def close(self):
        self.underlying_stream.close()




