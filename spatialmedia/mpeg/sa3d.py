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

"""MPEG SA3D box processing classes.

Enables the injection of an SA3D MPEG-4. The SA3D box specification
conforms to that outlined in docs/spatial-audio-rfc.md
"""

import struct

from spatialmedia.mpeg import box
from spatialmedia.mpeg import constants


def load(fh, position=None, end=None):
    """ Loads the SA3D box located at position in an mp4 file.

    Args:
      fh: file handle, input file handle.
      position: int or None, current file position.

    Returns:
      new_box: box, SA3D box loaded from the file location or None.
    """
    if position is None:
        position = fh.tell()

    fh.seek(position)
    new_box = SA3DBox()
    new_box.position = position
    size = struct.unpack(">I", fh.read(4))[0]
    name = fh.read(4)

    if (name != constants.TAG_SA3D):
        print("Error: box is not an SA3D box.")
        return None

    if (position + size > end):
        print("Error: SA3D box size exceeds bounds.")
        return None

    new_box.content_size = size - new_box.header_size
    new_box.version = struct.unpack(">B", fh.read(1))[0]
    new_box.ambisonic_type = struct.unpack(">B", fh.read(1))[0]
    new_box.ambisonic_order = struct.unpack(">I", fh.read(4))[0]
    new_box.ambisonic_channel_ordering = struct.unpack(">B", fh.read(1))[0]
    new_box.ambisonic_normalization = struct.unpack(">B", fh.read(1))[0]
    new_box.num_channels = struct.unpack(">I", fh.read(4))[0]
    for i in range(0, new_box.num_channels):
        new_box.channel_map.append(
            struct.unpack(">I", fh.read(4))[0])
    return new_box


class SA3DBox(box.Box):
    ambisonic_types = {'periphonic': 0}
    ambisonic_orderings = {'ACN': 0}
    ambisonic_normalizations = {'SN3D': 0}

    def __init__(self):
        box.Box.__init__(self)
        self.name = constants.TAG_SA3D
        self.header_size = 8
        self.version = 0
        self.ambisonic_type = 0
        self.ambisonic_order = 0
        self.ambisonic_channel_ordering = 0
        self.ambisonic_normalization = 0
        self.num_channels = 0
        self.channel_map = list()

    @staticmethod
    def create(num_channels, audio_metadata):
        new_box = SA3DBox()
        new_box.header_size = 8
        new_box.name = constants.TAG_SA3D
        new_box.version = 0                     # uint8
        new_box.content_size += 1               # uint8
        new_box.ambisonic_type = SA3DBox.ambisonic_types[
            audio_metadata["ambisonic_type"]]
        new_box.content_size += 1               # uint8
        new_box.ambisonic_order = audio_metadata["ambisonic_order"]
        new_box.content_size += 4               # uint32
        new_box.ambisonic_channel_ordering = SA3DBox.ambisonic_orderings[
            audio_metadata["ambisonic_channel_ordering"]]
        new_box.content_size += 1               # uint8
        new_box.ambisonic_normalization = SA3DBox.ambisonic_normalizations[
            audio_metadata["ambisonic_normalization"]]
        new_box.content_size += 1               # uint8
        new_box.num_channels = num_channels
        new_box.content_size += 4               # uint32

        channel_map = audio_metadata["channel_map"]
        for channel_element in channel_map:
            new_box.channel_map.append(channel_element)
            new_box.content_size += 4  # uint32
        return new_box

    def ambisonic_type_name(self):
        return  (key for key,value in SA3DBox.ambisonic_types.items()
                 if value==self.ambisonic_type).next()

    def ambisonic_channel_ordering_name(self):
        return (key for key,value in SA3DBox.ambisonic_orderings.items()
                if value==self.ambisonic_channel_ordering).next()

    def ambisonic_normalization_name(self):
        return (key for key,value in SA3DBox.ambisonic_normalizations.items()
                if value==self.ambisonic_normalization).next()

    def print_box(self, console):
        """ Prints the contents of this spatial audio (SA3D) box to the
            console.
        """
        ambisonic_type = self.ambisonic_type_name()
        channel_ordering = self.ambisonic_channel_ordering_name()
        ambisonic_normalization = self.ambisonic_normalization_name()
        console("\t\tAmbisonic Type: %s" % ambisonic_type)
        console("\t\tAmbisonic Order: %d" % self.ambisonic_order)
        console("\t\tAmbisonic Channel Ordering: %s" % channel_ordering)
        console("\t\tAmbisonic Normalization: %s" % ambisonic_normalization)
        console("\t\tNumber of Channels: %d" % self.num_channels)
        console("\t\tChannel Map: %s" % str(self.channel_map))

    def get_metadata_string(self):
        """ Outputs a concise single line audio metadata string. """
        metadata = "%s, %s, %s, Order %d, %d Channel(s), Channel Map: %s" \
            % (self.ambisonic_normalization_name(),\
               self.ambisonic_channel_ordering_name(),\
               self.ambisonic_type_name(),\
               self.ambisonic_order,\
               self.num_channels,\
               str(self.channel_map))
        return metadata

    def save(self, in_fh, out_fh, delta):
        if (self.header_size == 16):
            out_fh.write(struct.pack(">I", 1))
            out_fh.write(struct.pack(">Q", self.size()))
            out_fh.write(self.name)
        elif(self.header_size == 8):
            out_fh.write(struct.pack(">I", self.size()))
            out_fh.write(self.name)

        out_fh.write(struct.pack(">B", self.version))
        out_fh.write(struct.pack(">B", self.ambisonic_type))
        out_fh.write(struct.pack(">I", self.ambisonic_order))
        out_fh.write(struct.pack(">B", self.ambisonic_channel_ordering))
        out_fh.write(struct.pack(">B", self.ambisonic_normalization))
        out_fh.write(struct.pack(">I", self.num_channels))
        for i in self.channel_map:
            if (i != None):
                out_fh.write(struct.pack(">I", int(i)))
