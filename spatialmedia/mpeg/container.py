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

Functions for loading MPEG files and manipulating boxes.
"""

import struct

from spatialmedia.mpeg import box
from spatialmedia.mpeg import constants
from spatialmedia.mpeg import sa3d

def load(fh, position, end):
    if position is None:
        position = fh.tell()

    fh.seek(position)
    header_size = 8
    size = struct.unpack(">I", fh.read(4))[0]
    name = fh.read(4)

    is_box = name not in constants.CONTAINERS_LIST
    # Handle the mp4a decompressor setting (wave -> mp4a).
    if name == constants.TAG_MP4A and size == 12:
        is_box = True
    if is_box:
        if name == constants.TAG_SA3D:
            return sa3d.load(fh, position, end)
        return box.load(fh, position, end)

    if size == 1:
        size = struct.unpack(">Q", fh.read(8))[0]
        header_size = 16

    if size < 8:
        print("Error, invalid size", size, "in", name, "at", position)
        return None

    if (position + size) > end:
        print("Error: Container box size exceeds bounds.")
        return None

    padding = 0
    if name == constants.TAG_STSD:
        padding = 8
    if name in constants.SOUND_SAMPLE_DESCRIPTIONS:
        current_pos = fh.tell()
        fh.seek(current_pos + 8)
        sample_description_version = struct.unpack(">h", fh.read(2))[0]
        fh.seek(current_pos)

        if sample_description_version == 0:
            padding = 28
        elif sample_description_version == 1:
            padding = 28 + 16
        elif sample_description_version == 2:
            padding = 64
        else:
            print("Unsupported sample description version:",
                  sample_description_version)

    new_box = Container()
    new_box.name = name
    new_box.position = position
    new_box.header_size = header_size
    new_box.content_size = size - header_size
    new_box.padding = padding
    new_box.contents = load_multiple(
        fh, position + header_size + padding, position + size)

    if new_box.contents is None:
        return None

    return new_box


def load_multiple(fh, position=None, end=None):
    loaded = list()
    while (position + 4 < end):
        new_box = load(fh, position, end)
        if new_box is None:
            print("Error, failed to load box.")
            return None
        loaded.append(new_box)
        position = new_box.position + new_box.size()

    return loaded


class Container(box.Box):
    """MPEG4 container box contents / behaviour."""

    def __init__(self, padding=0):
        self.name = ""
        self.position = 0
        self.header_size = 0
        self.content_size = 0
        self.contents = list()
        self.padding = padding

    def resize(self):
        """Recomputes the box size and recurses on contents."""
        self.content_size = self.padding
        for element in self.contents:
            if isinstance(element, Container):
                element.resize()
            self.content_size += element.size()

    def print_structure(self, indent=""):
        """Prints the box structure and recurses on contents."""
        size1 = self.header_size
        size2 = self.content_size
        print("{0} {1} [{2}, {3}]".format(indent, self.name, size1, size2))

        size = len(self.contents)
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
            if element.name != tag:
                new_contents.append(element)
                if isinstance(element, Container):
                    element.remove(tag)
                self.content_size += element.size()
        self.contents = new_contents

    def add(self, element):
        """Adds an element, merging with containers of the same type.

        Returns:
          Int, increased size of container.
        """
        for content in self.contents:
            if content.name == element.name:
                if isinstance(content, container_leaf):
                    return content.merge(element)
                print("Error, cannot merge leafs.")
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
        """Saves box to out_fh reading uncached content from in_fh.

        Args:
          in_fh: file handle, source of uncached file contents.
          out_fh: file_hande, destination for saved file.
          delta: int, file change size for updating stco and co64 files.
        """
        if self.header_size == 16:
            out_fh.write(struct.pack(">I", 1))
            out_fh.write(self.name)
            out_fh.write(struct.pack(">Q", self.size()))
        elif self.header_size == 8:
            out_fh.write(struct.pack(">I", self.size()))
            out_fh.write(self.name)

        if self.padding > 0:
            in_fh.seek(self.content_start())
            box.tag_copy(in_fh, out_fh, self.padding)

        for element in self.contents:
            element.save(in_fh, out_fh, delta)
