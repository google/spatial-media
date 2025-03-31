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

"""MPEG SV3D box processing classes.

Enables the injection of an SV3D MPEG-4. The SV3D box specification
conforms to that outlined in docs/spatial-video-v2-rfc.md
"""

import struct

from spatialmedia.mpeg import box
from spatialmedia.mpeg import constants


def is_supported_box_name(name):
    """Returns true if the box name is a supported sv3d box."""
    return (name == constants.TAG_PRHD or
            name == constants.TAG_EQUI or
            name == constants.TAG_ST3D)


def load(fh, position=None, end=None):
    """ Loads the SV3D box located at position in an mp4 file.

    Args:
      fh: file handle, input file handle.
      position: int or None, current file position.

    Returns:
      new_box: box, SV3D box loaded from the file location or None.
    """
    if position is None:
        position = fh.tell()

    fh.seek(position)
    size = struct.unpack(">I", fh.read(4))[0]
    name = fh.read(4)

    if name == constants.TAG_PRHD:
        box = PRHDBox()
    elif name == constants.TAG_EQUI:
        box = EQUIBox()
    elif name == constants.TAG_ST3D:
        box = ST3DBox()
    else:
        print("Error: box is not a supported SV3D sub-box.")
        return None

    box.position = position
    box.content_size = size - box.header_size
    box.load_content(fh)
    return box


class PRHDBox(box.Box):
    def __init__(self):
        box.Box.__init__(self)
        self.name = constants.TAG_PRHD
        self.header_size = 8
        self.pose_yaw_degrees = 0
        self.pose_pitch_degrees = 0
        self.pose_roll_degrees = 0
        self.content_size = 16

    @staticmethod
    def create():
        return PRHDBox()

    def print_box(self, console):
        """ Prints the contents of this box to console."""
        console("\t\t\tPRHD {")
        console("\t\t\t\tPose Yaw Degrees: %d" % self.pose_yaw_degrees)
        console("\t\t\t\tPose Pitch Degrees: %d" % self.pose_pitch_degrees)
        console("\t\t\t\tPose Roll Degrees: %d" % self.pose_roll_degrees)
        console("\t\t\t}")

    def get_metadata_string(self):
        """ Outputs a concise single line proj metadata string. """
        return ("yaw:%d, pitch:%d, roll:%d" %
                (self.pose_yaw_degrees, self.pose_pitch_degrees, self.pose_roll_degrees))

    def save(self, in_fh, out_fh, delta):
        if (self.header_size == 16):
            out_fh.write(struct.pack(">I", 1))
            out_fh.write(struct.pack(">Q", self.size()))
            out_fh.write(self.name)
        elif(self.header_size == 8):
            out_fh.write(struct.pack(">I", self.size()))
            out_fh.write(self.name)
        out_fh.write(struct.pack(">I", 0)) # Version and flags
        out_fh.write(struct.pack(">I", self.pose_yaw_degrees))
        out_fh.write(struct.pack(">I", self.pose_pitch_degrees))
        out_fh.write(struct.pack(">I", self.pose_roll_degrees))

    def load_content(self, in_fh):
        in_fh.read(4) # Version and flags
        self.pose_yaw_degress = struct.unpack(">I", in_fh.read(4))[0]
        self.pose_pitch_degrees = struct.unpack(">I", in_fh.read(4))[0]
        self.pose_roll_degrees = struct.unpack(">I", in_fh.read(4))[0]


class EQUIBox(box.Box):
    def __init__(self):
        box.Box.__init__(self)
        self.name = constants.TAG_EQUI
        self.header_size = 8
        self.bounds_top = 0
        self.bounds_bottom = 0
        self.bounds_left = 0
        self.bounds_right = 0
        self.content_size = 20

    @staticmethod
    def create():
        return EQUIBox()

    def print_box(self, console):
        """ Prints the contents of this box to console."""
        console("\t\t\tEQUI {")
        console("\t\t\t\tBounds Top: %d" % self.bounds_top)
        console("\t\t\t\tBounds Bottom: %d" % self.bounds_bottom)
        console("\t\t\t\tBounds Left: %d" % self.bounds_left)
        console("\t\t\t\tBounds Right: %d" % self.bounds_right)
        console("\t\t\t}")

    def get_metadata_string(self):
        """ Outputs a concise single line proj metadata string. """
        return ("Equi (top:%d, bottom:%d, left:%d, right:%d)"
            % (self.bounds_top, self.bounds_bottom, self.bounds_left, self.bounds_right))

    def save(self, in_fh, out_fh, delta):
        if (self.header_size == 16):
            out_fh.write(struct.pack(">I", 1))
            out_fh.write(struct.pack(">Q", self.size()))
            out_fh.write(self.name)
        elif(self.header_size == 8):
            out_fh.write(struct.pack(">I", self.size()))
            out_fh.write(self.name)
        out_fh.write(struct.pack(">I", 0)) # Version and flags
        out_fh.write(struct.pack(">I", self.bounds_top))
        out_fh.write(struct.pack(">I", self.bounds_bottom))
        out_fh.write(struct.pack(">I", self.bounds_left))
        out_fh.write(struct.pack(">I", self.bounds_right))

    def load_content(self, in_fh):
        in_fh.read(4) # Version and flags
        self.bounds_top = struct.unpack(">I", in_fh.read(4))[0]
        self.bounds_bottom = struct.unpack(">I", in_fh.read(4))[0]
        self.bounds_left = struct.unpack(">I", in_fh.read(4))[0]
        self.bounds_right = struct.unpack(">I", in_fh.read(4))[0]


class ST3DBox(box.Box):
    def __init__(self):
        box.Box.__init__(self)
        self.name = constants.TAG_ST3D
        self.header_size = 8
        self.stereo_mode = 0
        self.content_size = 5

    @staticmethod
    def create():
        return ST3DBox()

    def set_stereo_mode_from_string(self, stereo_mode):
        if stereo_mode == "mono":
            self.stereo_mode = 0
        elif stereo_mode == "top-bottom":
            self.stereo_mode = 1
        elif stereo_mode == "left-right":
            self.stereo_mode = 2
        else:
            print("Error: unknown stereo mode")

    def print_box(self, console):
        """ Prints the contents of this box to console."""
        console("\t\t\tStereo Mode: %d" % self.stereo_mode)

    def get_metadata_string(self):
        """ Outputs a concise single line stereo metadata string. """
        return "Stereo Mode: %d" % self.stereo_mode

    def save(self, in_fh, out_fh, delta):
        if (self.header_size == 16):
            out_fh.write(struct.pack(">I", 1))
            out_fh.write(struct.pack(">Q", self.size()))
            out_fh.write(self.name)
        elif(self.header_size == 8):
            out_fh.write(struct.pack(">I", self.size()))
            out_fh.write(self.name)
        out_fh.write(struct.pack(">I", 0)) # Version and flags
        out_fh.write(struct.pack(">B", self.stereo_mode))

    def load_content(self, in_fh):
        in_fh.read(4) # Version and flags
        self.stereo_mode = int(struct.unpack(">B", in_fh.read(1))[0])
