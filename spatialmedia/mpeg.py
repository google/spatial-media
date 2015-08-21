#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 Google Inc. All rights reserved.
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

import StringIO
import struct

TRAK_TYPE_VIDE = "vide"

# Leaf types.
TAG_STCO = "stco"
TAG_CO64 = "co64"
TAG_FREE = "free"
TAG_MDAT = "mdat"
TAG_XML = "xml "
TAG_HDLR = "hdlr"
TAG_FTYP = "ftyp"

# Container types.
TAG_MOOV = "moov"
TAG_UDTA = "udta"
TAG_META = "meta"
TAG_TRAK = "trak"
TAG_MDIA = "mdia"
TAG_MINF = "minf"
TAG_STBL = "stbl"
TAG_UUID = "uuid"

containers = [TAG_MOOV, TAG_UDTA, TAG_TRAK,
              TAG_MDIA, TAG_MINF, TAG_STBL]


class box:
    """MPEG4 box contents and behaviour true for all boxes."""

    def __init__(self):
        self.name = ""
        self.position = 0
        self.header_size = 0
        self.content_size = 0
        self.contents = None

    def content_start(self):
        return self.position + self.header_size

    @staticmethod
    def load(fh, position=None, end=None):
        """Loads the box located at a position in a mp4 file.

        Args:
          fh: file handle, input file handle.
          position: int or None, current file position.

        Returns:
          box: box, box from loaded file location or None.
        """
        if (position is None):
            position = fh.tell()

        fh.seek(position)
        header_size = 8
        size = struct.unpack(">I", fh.read(4))[0]
        name = fh.read(4)

        if (name in containers):
            return container_box.load(fh, position, end)

        if (size == 1):
            size = struct.unpack(">Q", fh.read(8))[0]
            header_size = 16

        if (size < 8):
            print "Error, invalid size in ", name, " at ", position
            return None

        if (position + size > end):
            print ("Error: Leaf box size exceeds bounds.")
            return None

        new_box = box()
        new_box.name = name
        new_box.position = position
        new_box.header_size = header_size
        new_box.content_size = size - header_size
        new_box.contents = None

        return new_box

    @staticmethod
    def load_multiple(fh, position=None, end=None):
        loaded = list()
        while (position < end):
            new_box = box.load(fh, position, end)
            if (new_box is None):
                print ("Error, failed to load box.")
                return None
            loaded.append(new_box)
            position = new_box.position + new_box.size()

        return loaded

    def save(self, in_fh, out_fh, delta):
        """Save box contents prioritizing set contents and specialized
        behaviour for stco/co64 boxes.

        Args:
          in_fh: file handle, source to read box contents from.
          out_fh: file handle, destination for written box contents.
          delta: int, index update amount.
        """
        if (self.header_size == 16):
            out_fh.write(struct.pack(">I", 1))
            out_fh.write(self.name)
            out_fh.write(struct.pack(">Q", self.size()))
        elif(self.header_size == 8):
            out_fh.write(struct.pack(">I", self.size()))
            out_fh.write(self.name)

        if self.content_start():
            in_fh.seek(self.content_start())

        if (self.name == TAG_STCO):
            stco_copy(in_fh, out_fh, self, delta)
        elif (self.name == TAG_CO64):
            co64_copy(in_fh, out_fh, self, delta)
        elif (self.contents is not None):
            out_fh.write(self.contents)
        else:
            tag_copy(in_fh, out_fh, self.content_size)

    def set(self, new_contents):
        """Sets the box contents. This can be used to change a box's
        contents"""
        contents = new_contents
        content_size = len(contents)

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
        print indent, self.name, " [", size1, ", ", size2, " ]"


class container_box(box):
    """MPEG4 container box contents / behaviour."""

    def __init__(self):
        self.name = ""
        self.position = 0
        self.header_size = 0
        self.content_size = 0
        self.contents = list()

    @staticmethod
    def load(fh, position=None, end=None):
        if (position is None):
            position = fh.tell()

        fh.seek(position)
        header_size = 8
        size = struct.unpack(">I", fh.read(4))[0]
        name = fh.read(4)

        assert(name in containers)

        if (size == 1):
            size = struct.unpack(">Q", fh.read(8))[0]
            header_size = 16

        if (size < 8):
            print "Error, invalid size in ", name, " at ", position
            return None

        if (position + size > end):
            print ("Error: Container box size exceeds bounds.")
            return None

        new_box = container_box()
        new_box.name = name
        new_box.position = position
        new_box.header_size = header_size
        new_box.content_size = size - header_size
        new_box.contents = box.load_multiple(
            fh, position + header_size, position + size)

        if (new_box.contents is None):
            return None

        return new_box

    def resize(self):
        """Recomputes the box size and recurses on contents."""
        self.content_size = 0
        for element in self.contents:
            if isinstance(element, container_box):
                element.resize()
            self.content_size += element.size()

    def print_structure(self, indent=""):
        """Prints the box structure and recurses on contents."""
        size1 = self.header_size
        size2 = self.content_size
        print indent, self.name, " [", size1, ", ", size2, " ]"

        size = len(self.contents)
        this_indent = indent
        for i in range(size):
            next_indent = indent

            next_indent = next_indent.replace("├", "│")
            next_indent = next_indent.replace("└", " ")
            next_indent = next_indent.replace("─", " ")

            if i == (size - 1):
                next_indent = next_indent + " └──"
            else:
                next_indent = next_indent + " ├──"

            element = self.contents[i]
            element.print_structure(next_indent)

    def remove(self, tag):
        """Removes a tag recursively from all containers."""
        new_contents = []
        self.content_size = 0
        for element in self.contents:
            if not (element.name == tag):
                new_contents.append(element)
                if isinstance(element, container_box):
                    element.remove(tag)
                self.content_size += element.size()
        self.contents = new_contents

    def add(self, element):
        """Adds an element, merging with containers of the same type.

        Returns:
          Int, increased size of container.
        """
        for content in self.contents:
            if (content.name == element.name):
                if (isinstance(content, container_leaf)):
                    return content.merge(element)
                print "Error, cannot merge leafs."
                return False

        self.contents.append(element)
        return True

    def merge(self, element):
        """Merges structure with container.

        Returns:
          Int, increased size of container.
        """
        assert(self.name == element.name)
        assert(isinstance(element, container_box))
        for sub_element in element.contents:
            if not self.add(sub_element):
                return False

        return True

    def save(self, in_fh, out_fh, delta):
        """Saves box structure to out_fh reading uncached content from
        in_fh.

        Args:
          in_fh: file handle, source of uncached file contents.
          out_fh: file_hande, destination for saved file.
          delta: int, file change size for updating stco and co64 files.
        """
        if (self.header_size == 16):
            out_fh.write(struct.pack(">I", 1))
            out_fh.write(self.name)
            out_fh.write(struct.pack(">Q", self.size()))
        elif(self.header_size == 8):
            out_fh.write(struct.pack(">I", self.size()))
            out_fh.write(self.name)

        for element in self.contents:
            element.save(in_fh, out_fh, delta)


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
      mode_length: int, number of bytes for index entires.
      delta: int, offset change for index entries.
    """
    fh = in_fh
    if not box.contents:
        fh.seek(box.content_start())
    else:
        fh = StringIO.StringIO(box.contents)

    header = struct.unpack(">I", fh.read(4))[0]
    values = struct.unpack(">I", fh.read(4))[0]

    new_contents = []
    new_contents.append(struct.pack(">I", header))
    new_contents.append(struct.pack(">I", values))
    for i in range(values):
        content = fh.read(mode_length)
        content = struct.unpack(mode, content)[0] + delta
        new_contents.append(struct.pack(mode, content))
    out_fh.write("".join(new_contents))


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


class mpeg4(container_box):
    """Specialized behaviour for the root mpeg4 container"""

    def __init__(self):
        self.contents = list()
        self.content_size = 0
        self.header_size = 0
        self.moov_box = None
        self.free_box = None
        self.first_mdat_box = None
        self.ftyp_box = None
        self.first_mdat_position = None

    @staticmethod
    def load(fh):
        """Load the mpeg4 file structure of a file.

        Args:
          fh: file handle, input file handle.
          position: int, current file position.
          size: int, maximum size. This is used to ensure correct box sizes.

        return:
          mpeg4, the loaded mpeg4 structure.
        """

        fh.seek(0, 2)
        size = fh.tell()
        contents = box.load_multiple(fh, 0, size)

        if (contents is None):
            print "Error, failed to load .mp4 file."
            return None

        if (len(contents) == 0):
            print ("Error, no boxes found.")
            return None

        loaded_mpeg4 = mpeg4()
        loaded_mpeg4.contents = contents

        for element in loaded_mpeg4.contents:
            if (element.name == "moov"):
                loaded_mpeg4.moov_box = element
            if (element.name == "free"):
                loaded_mpeg4.free_box = element
            if (element.name == "mdat"
                    and loaded_mpeg4.first_mdat_box is None):
                loaded_mpeg4.first_mdat_box = element
            if (element.name == "ftyp"):
                loaded_mpeg4.ftyp_box = element

        if (loaded_mpeg4.moov_box is None):
            print ("Error, file does not contain moov box.")
            return None

        if (loaded_mpeg4.first_mdat_box is None):
            print ("Error, file does not contain mdat box.")
            return None

        loaded_mpeg4.first_mdat_position = \
            loaded_mpeg4.first_mdat_box.position
        loaded_mpeg4.first_mdat_position += \
            loaded_mpeg4.first_mdat_box.header_size

        loaded_mpeg4.content_size = 0
        for element in loaded_mpeg4.contents:
            loaded_mpeg4.content_size += element.size()

        return loaded_mpeg4

    def merge(self, element):
        """Mpeg4 containers do not support merging."""
        print "Cannot merge mpeg4 files"
        exit(0)

    def print_structure(self):
        """Print mpeg4 file structure recursively."""
        print "mpeg4 [", self.content_size, "]"

        size = len(self.contents)
        for i in range(size):
            next_indent = " ├──"
            if i == (size - 1):
                next_indent = " └──"

            self.contents[i].print_structure(next_indent)

    def save(self, in_fh, out_fh):
        """Save mpeg4 filecontent to file.

        Args:
          in_fh: file handle, source file handle for uncached contents.
          out_fh: file handle, destination file hand for saved file.
        """
        self.resize()
        new_position = 0
        for element in self.contents:
            if element.name == TAG_MDAT:
                new_position += element.header_size
                break
            new_position += element.size()
        delta = new_position - self.first_mdat_position

        for element in self.contents:
            element.save(in_fh, out_fh, delta)
