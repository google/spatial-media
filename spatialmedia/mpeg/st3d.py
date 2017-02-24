#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017 Vimeo. All rights reserved.
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

"""MPEG st3d box processing classes.

Enables the injection of an st3d MPEG-4. The st3d box specification
conforms to that outlined in docs/spherical-video-v2-rfc.md
"""

import struct

from spatialmedia.mpeg import box
from spatialmedia.mpeg import constants


def load(fh, position=None, end=None):
    """ Loads the st3d box located at position in an mp4 file.

    Args:
      fh: file handle, input file handle.
      position: int or None, current file position.

    Returns:
      new_box: box, st3d box loaded from the file location or None.
    """
    if position is None:
        position = fh.tell()

    fh.seek(position)
    new_box = st3dBox()
    new_box.position = position
    size = struct.unpack(">I", fh.read(4))[0]
    name = fh.read(4)

    if (name != constants.TAG_ST3D):
        print "Error: box is not an st3d box."
        return None

    if (position + size > end):
        print "Error: st3d box size exceeds bounds."
        return None

    new_box.content_size = size - new_box.header_size
    new_box.version = struct.unpack(">I", fh.read(4))[0]
    new_box.stereo_mode = struct.unpack(">B", fh.read(1))[0]
    return new_box


class st3dBox(box.Box):
    stereo_modes = {'none': 0, 'top-bottom': 1, 'left-right': 2}

    def __init__(self):
        box.Box.__init__(self)
        self.name = constants.TAG_ST3D
        self.header_size = 8
        self.version = 0
        self.stereo_mode = 0

    @staticmethod
    def create(stereo_metadata):
        new_box = st3dBox()
        new_box.header_size = 8
        new_box.name = constants.TAG_ST3D
        new_box.version = 0 # uint8 + uint24 (flags)
        new_box.content_size += 4
        new_box.stereo_mode = st3dBox.stereo_modes[stereo_metadata] # uint8
        new_box.content_size += 1

        return new_box

    def stereo_mode_name(self):
        return  (key for key,value in st3dBox.stereo_modes.items()
                 if value==self.stereo_mode).next()

    def print_box(self, console):
        """ Prints the contents of this stereoscopic (st3d) box to the
            console.
        """
        stereo_mode = self.stereo_mode_name()
        console("\t\tStereo Mode: %s" % stereo_mode)

    def get_metadata_string(self):
        """ Outputs a concise single line stereo metadata string. """
        return "Stereo mode: %s" % (self.stereo_mode_name())

    def save(self, in_fh, out_fh, delta):
        if (self.header_size == 16):
            out_fh.write(struct.pack(">I", 1))
            out_fh.write(struct.pack(">Q", self.size()))
            out_fh.write(self.name)
        elif(self.header_size == 8):
            out_fh.write(struct.pack(">I", self.size()))
            out_fh.write(self.name)

        out_fh.write(struct.pack(">I", self.version))
        out_fh.write(struct.pack(">B", self.stereo_mode))
