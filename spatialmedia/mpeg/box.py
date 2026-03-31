#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""MPEG processing classes.

Tool for loading mpeg4 files and manipulating atoms.
"""

import io
import struct

from spatialmedia.mpeg import constants

def load(fh, position, end):
    """Loads the box located at a position in a mp4 file.

    Args:
      fh: file handle, input file handle.
      position: int or None, current file position.

    Returns:
      box: box, box from loaded file location or None.
    """
    if position is None:
        position = fh.tell()

    fh.seek(position)
    header_size = 8
    size = struct.unpack(">I", fh.read(4))[0]
    name = fh.read(4)

    if size == 1:
        size = struct.unpack(">Q", fh.read(8))[0]
        header_size = 16

    if size < 8:
        print("Error, invalid size {} in {} at {}".format(size, name, position))
        return None

    if (position + size) > end:
        print("Error: Leaf box size exceeds bounds.")
        return None

    new_box = Box()
    new_box.name = name
    new_box.position = position
    new_box.header_size = header_size
    new_box.content_size = size - header_size
    new_box.contents = None

    return new_box


class Box(object):
    """MPEG4 box contents and behaviour true for all boxes."""

    def __init__(self):
        self.name = ""
        self.position = 0
        self.header_size = 0
        self.content_size = 0
        self.contents = None

    def content_start(self):
        return self.position + self.header_size

    def save(self, in_fh, out_fh, delta):
        """Save box contents prioritizing set contents.

        Args:
          in_fh: file handle, source to read box contents from.
          out_fh: file handle, destination for written box contents.
          delta: int, index update amount.
        """
        if self.header_size == 16:
            out_fh.write(struct.pack(">I", 1))
            out_fh.write(self.name)
            out_fh.write(struct.pack(">Q", self.size()))
        elif self.header_size == 8:
            out_fh.write(struct.pack(">I", self.size()))
            out_fh.write(self.name)

        if self.content_start():
            in_fh.seek(self.content_start())

        if self.name == constants.TAG_STCO:
            stco_copy(in_fh, out_fh, self, delta)
        elif self.name == constants.TAG_CO64:
            co64_copy(in_fh, out_fh, self, delta)
        elif self.contents:
            out_fh.write(self.contents)
        else:
            tag_copy(in_fh, out_fh, self.content_size)

    def set(self, new_contents):
        """Sets / overwrites the box contents."""
        self.contents = new_contents
        self.content_size = len(contents)

    def size(self):
        """Total size of a box.

        Returns:
          Int, total size in bytes of the box.
        """
        return self.header_size + self.content_size

    def print_structure(self, indent=""):
        """Prints the box structure."""
        size1 = self.header_size
        size2 = self.content_size
        print("{0} {1} [{2}, {3}]".format(indent, self.name, size1, size2))


def tag_copy(in_fh, out_fh, size):
    """Copies a block of data from in_fh to out_fh.

    Args:
      in_fh: file handle, source of uncached file contents.
      out_fh: file handle, destination for saved file.
      size: int, amount of data to copy.
    """

    # On 32-bit systems reading / writing is limited to 2GB chunks.
    # To prevent overflow, read/write 64 MB chunks.
    block_size = 64 * 1024 * 1024
    while (size > block_size):
        contents = in_fh.read(block_size)
        out_fh.write(contents)
        size = size - block_size

    contents = in_fh.read(size)
    out_fh.write(contents)


def index_copy(in_fh, out_fh, box, mode, mode_length, delta=0):
    """Update and copy index table for stco/co64 files.

    Args:
      in_fh: file handle, source to read index table from.
      out_fh: file handle, destination for index file.
      box: box, stco/co64 box to copy.
      mode: string, bit packing mode for index entries.
      mode_length: int, number of bytes for index entries.
      delta: int, offset change for index entries.
    """
    fh = in_fh
    if not box.contents:
        fh.seek(box.content_start())
    else:
        fh = io.BytesIO(box.contents)

    header = struct.unpack(">I", fh.read(4))[0]
    values = struct.unpack(">I", fh.read(4))[0]

    new_contents = []
    new_contents.append(struct.pack(">I", header))
    new_contents.append(struct.pack(">I", values))
    for i in range(values):
        content = fh.read(mode_length)
        content = struct.unpack(mode, content)[0] + delta
        new_contents.append(struct.pack(mode, content))
    out_fh.write(b"".join(new_contents))


def stco_copy(in_fh, out_fh, box, delta=0):
    """Copy for stco box.

    Args:
      in_fh: file handle, source to read index table from.
      out_fh: file handle, destination for index file.
      box: box, stco box to copy.
      delta: int, offset change for index entries.
    """
    index_copy(in_fh, out_fh, box, ">I", 4, delta)


def co64_copy(in_fh, out_fh, box, delta=0):
    """Copy for co64 box.

    Args:
      in_fh: file handle, source to read index table from.
      out_fh: file handle, destination for index file.
      box: box, co64 box to copy.
      delta: int, offset change for index entries.
    """
    index_copy(in_fh, out_fh, box, ">Q", 8, delta)
