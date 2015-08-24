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

"""MPEG4 processing classes.

Tool for loading mpeg4 files and manipulating boxes.
"""

from spatialmedia.mpeg import box
from spatialmedia.mpeg import constants
from spatialmedia.mpeg import container


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
    contents = container.load_multiple(fh, 0, size)

    if not contents:
        print "Error, failed to load .mp4 file."
        return None
    elif len(contents) == 0:
        print ("Error, no boxes found.")
        return None

    loaded_mpeg4 = Mpeg4Container()
    loaded_mpeg4.contents = contents

    for element in loaded_mpeg4.contents:
        if (element.name == "moov"):
            loaded_mpeg4.moov_box = element
        if (element.name == "free"):
            loaded_mpeg4.free_box = element
        if (element.name == "mdat"
                and not loaded_mpeg4.first_mdat_box):
            loaded_mpeg4.first_mdat_box = element
        if (element.name == "ftyp"):
            loaded_mpeg4.ftyp_box = element

    if not loaded_mpeg4.moov_box:
        print ("Error, file does not contain moov box.")
        return None

    if not loaded_mpeg4.first_mdat_box:
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


class Mpeg4Container(container.Container):
    """Specialized behaviour for the root mpeg4 container."""

    def __init__(self):
        self.contents = list()
        self.content_size = 0
        self.header_size = 0
        self.moov_box = None
        self.free_box = None
        self.first_mdat_box = None
        self.ftyp_box = None
        self.first_mdat_position = None

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
            if element.name == constants.TAG_MDAT:
                new_position += element.header_size
                break
            new_position += element.size()
        delta = new_position - self.first_mdat_position

        for element in self.contents:
            element.save(in_fh, out_fh, delta)
