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

"""Utilities for examining/injecting spatial media metadata in MP4/MOV files."""

import os
import re
import StringIO
import struct
import traceback

from spatialmedia import mpeg

MPEG_FILE_EXTENSIONS = [".mp4", ".mov"]

SPATIAL_AUDIO_DEFAULT_METADATA = {
    "ambisonic_order": 1,
    "ambisonic_type": "periphonic",
    "ambisonic_channel_ordering": "ACN",
    "ambisonic_normalization": "SN3D",
    "channel_map": [0, 1, 2, 3],
}

class Metadata(object):
    def __init__(self):
        self.stereo = None
        self.spherical = None
        self.video = None
        self.audio = None

class ParsedMetadata(object):
    def __init__(self):
        self.audio = None
        self.video = dict()
        self.num_audio_channels = 0

def mpeg4_add_spherical_v2(mpeg4_file, in_fh, spherical_metadata, console):
    """Adds spherical metadata to the first video track of the input
       mpeg4_file. Returns False on failure.

    Args:
      mpeg4_file: mpeg4, Mpeg4 file structure to add metadata.
      in_fh: file handle, Source for uncached file contents.
      spherical_metadata: dictionary.
    """
    for element in mpeg4_file.moov_box.contents:
        if element.name == mpeg.constants.TAG_TRAK:
            for sub_element in element.contents:
                if sub_element.name != mpeg.constants.TAG_MDIA:
                    continue
                for mdia_sub_element in sub_element.contents:
                    if mdia_sub_element.name != mpeg.constants.TAG_HDLR:
                        continue
                    position = mdia_sub_element.content_start() + 8
                    in_fh.seek(position)
                    if in_fh.read(4) == mpeg.constants.TAG_VIDE:
                        return inject_spherical_atom(in_fh, sub_element, spherical_metadata, console)
    return False

def inject_spherical_atom(in_fh, video_media_atom, spherical_metadata, console):
    for atom in video_media_atom.contents:
        if atom.name != mpeg.constants.TAG_MINF:
            continue
        for element in atom.contents:
            if element.name != mpeg.constants.TAG_STBL:
                continue
            for sub_element in element.contents:
                if sub_element.name != mpeg.constants.TAG_STSD:
                    continue
                for sample_description in sub_element.contents:
                    if sample_description.name in\
                            mpeg.constants.VIDEO_SAMPLE_DESCRIPTIONS:
                        in_fh.seek(sample_description.position +
                                   sample_description.header_size + 16)

                        sv3d_atom = mpeg.sv3dBox.create(spherical_metadata)
                        sample_description.contents.append(sv3d_atom)
                        return True
    return False

def mpeg4_add_stereo(mpeg4_file, in_fh, stereo_metadata, console):
    """Adds stereo-mode metadata to the first video track of the input
       mpeg4_file. Returns False on failure.

    Args:
      mpeg4_file: mpeg4, Mpeg4 file structure to add metadata.
      in_fh: file handle, Source for uncached file contents.
      stereo_metadata: string.
    """
    for element in mpeg4_file.moov_box.contents:
        if element.name == mpeg.constants.TAG_TRAK:
            for sub_element in element.contents:
                if sub_element.name != mpeg.constants.TAG_MDIA:
                    continue
                for mdia_sub_element in sub_element.contents:
                    if mdia_sub_element.name != mpeg.constants.TAG_HDLR:
                        continue
                    position = mdia_sub_element.content_start() + 8
                    in_fh.seek(position)
                    if in_fh.read(4) == mpeg.constants.TAG_VIDE:
                        return inject_stereo_mode_atom(in_fh, sub_element, stereo_metadata, console)
    return False

def inject_stereo_mode_atom(in_fh, video_media_atom, stereo_metadata, console):
    for atom in video_media_atom.contents:
        if atom.name != mpeg.constants.TAG_MINF:
            continue
        for element in atom.contents:
            if element.name != mpeg.constants.TAG_STBL:
                continue
            for sub_element in element.contents:
                if sub_element.name != mpeg.constants.TAG_STSD:
                    continue
                for sample_description in sub_element.contents:
                    if sample_description.name in\
                            mpeg.constants.VIDEO_SAMPLE_DESCRIPTIONS:
                        in_fh.seek(sample_description.position +
                                   sample_description.header_size + 16)

                        st3d_atom = mpeg.st3dBox.create(stereo_metadata)
                        sample_description.contents.append(st3d_atom)
                        return True
    return False

def mpeg4_add_spatial_audio(mpeg4_file, in_fh, audio_metadata, console):
    """Adds spatial audio metadata to the first audio track of the input
       mpeg4_file. Returns False on failure.

    Args:
      mpeg4_file: mpeg4, Mpeg4 file structure to add metadata.
      in_fh: file handle, Source for uncached file contents.
      audio_metadata: dictionary ('ambisonic_type': string,
      'ambisonic_order': int),
      Supports 'periphonic' ambisonic type only.
    """
    for element in mpeg4_file.moov_box.contents:
        if element.name == mpeg.constants.TAG_TRAK:
            for sub_element in element.contents:
                if sub_element.name != mpeg.constants.TAG_MDIA:
                    continue
                for mdia_sub_element in sub_element.contents:
                    if mdia_sub_element.name != mpeg.constants.TAG_HDLR:
                        continue
                    position = mdia_sub_element.content_start() + 8
                    in_fh.seek(position)
                    if in_fh.read(4) == mpeg.constants.TAG_SOUN:
                        return inject_spatial_audio_atom(
                            in_fh, sub_element, audio_metadata, console)
    return True

def mpeg4_add_audio_metadata(mpeg4_file, in_fh, audio_metadata, console):
    num_audio_tracks = get_num_audio_tracks(mpeg4_file, in_fh)
    if num_audio_tracks > 1:
        console("Error: Expected 1 audio track. Found %d" % num_audio_tracks)
        return False

    return mpeg4_add_spatial_audio(mpeg4_file, in_fh, audio_metadata, console)

def inject_spatial_audio_atom(
    in_fh, audio_media_atom, audio_metadata, console):
    for atom in audio_media_atom.contents:
        if atom.name != mpeg.constants.TAG_MINF:
            continue
        for element in atom.contents:
            if element.name != mpeg.constants.TAG_STBL:
                continue
            for sub_element in element.contents:
                if sub_element.name != mpeg.constants.TAG_STSD:
                    continue
                for sample_description in sub_element.contents:
                    if sample_description.name in\
                            mpeg.constants.SOUND_SAMPLE_DESCRIPTIONS:
                        in_fh.seek(sample_description.position +
                                   sample_description.header_size + 16)
                        num_channels = get_num_audio_channels(
                            sub_element, in_fh)
                        num_ambisonic_components = \
                            get_expected_num_audio_components(
                                audio_metadata["ambisonic_type"],
                                audio_metadata["ambisonic_order"])
                        if num_channels != num_ambisonic_components:
                            err_msg = "Error: Found %d audio channel(s). "\
                                  "Expected %d channel(s) for %s ambisonics "\
                                  "of order %d."\
                                % (num_channels,
                                   num_ambisonic_components,
                                   audio_metadata["ambisonic_type"],
                                   audio_metadata["ambisonic_order"])
                            console(err_msg)
                            return False
                        sa3d_atom = mpeg.SA3DBox.create(
                            num_channels, audio_metadata)
                        sample_description.contents.append(sa3d_atom)
    return True

def parse_spherical_mpeg4(mpeg4_file, fh, console):
    """Returns spherical metadata for a loaded mpeg4 file.

    Args:
      mpeg4_file: mpeg4, loaded mpeg4 file contents.
      fh: file handle, file handle for uncached file contents.

    Returns:
      Dictionary stored as (trackName, metadataDictionary)
    """
    metadata = ParsedMetadata()
    track_num = 0
    for element in mpeg4_file.moov_box.contents:
        if element.name == mpeg.constants.TAG_TRAK:
            trackName = "Track %d" % track_num
            console("\t%s" % trackName)
            track_num += 1

            for sub_element in element.contents:
                if sub_element.name != mpeg.constants.TAG_MDIA:
                    continue
                for mdia_sub_element in sub_element.contents:
                    if mdia_sub_element.name != mpeg.constants.TAG_MINF:
                        continue
                    for stbl_elem in mdia_sub_element.contents:
                        if stbl_elem.name != mpeg.constants.TAG_STBL:
                            continue
                        for stsd_elem in stbl_elem.contents:
                            if stsd_elem.name != mpeg.constants.TAG_STSD:
                                continue
                            for container_elem in stsd_elem.contents:
                                if container_elem.name in \
                                        mpeg.constants.SOUND_SAMPLE_DESCRIPTIONS:
                                    metadata.num_audio_channels = \
                                        get_num_audio_channels(stsd_elem, fh)
                                    for sa3d_elem in container_elem.contents:
                                        if sa3d_elem.name == mpeg.constants.TAG_SA3D:
                                            sa3d_elem.print_box(console)
                                            metadata.audio = sa3d_elem
                                elif container_elem.name in \
                                        mpeg.constants.VIDEO_SAMPLE_DESCRIPTIONS:
                                    for stsd_subelem in container_elem.contents:
                                        if stsd_subelem.name == mpeg.constants.TAG_ST3D or \
                                           stsd_subelem.name == mpeg.constants.TAG_SV3D:
                                            stsd_subelem.print_box(console)
                                            metadata.video[trackName] = stsd_subelem
    return metadata

def parse_mpeg4(input_file, console):
    with open(input_file, "rb") as in_fh:
        mpeg4_file = mpeg.load(in_fh)
        if mpeg4_file is None:
            console("Error, file could not be opened.")
            return

        console("Loaded file...")
        return parse_spherical_mpeg4(mpeg4_file, in_fh, console)

    console("Error \"" + input_file + "\" does not exist or do not have "
            "permission.")


def inject_mpeg4(input_file, output_file, metadata, console):
    with open(input_file, "rb") as in_fh:

        mpeg4_file = mpeg.load(in_fh)
        if mpeg4_file is None:
            console("Error file could not be opened.")

        if metadata.stereo:
            if not mpeg4_add_stereo(
                mpeg4_file, in_fh, metadata.stereo, console):
                    console("Error failed to insert stereoscopic data")

        if metadata.spherical:
            if not mpeg4_add_spherical_v2(
                mpeg4_file, in_fh, metadata, console):
                    console("Error failed to insert spherical data")

        if metadata.audio:
            if not mpeg4_add_audio_metadata(
                mpeg4_file, in_fh, metadata.audio, console):
                    console("Error failed to insert spatial audio data")

        console("Saved file settings")
        parse_spherical_mpeg4(mpeg4_file, in_fh, console)

        with open(output_file, "wb") as out_fh:
            mpeg4_file.save(in_fh, out_fh)
        return

    console("Error file: \"" + input_file + "\" does not exist or do not have "
            "permission.")

def parse_metadata(src, console):
    infile = os.path.abspath(src)

    try:
        in_fh = open(infile, "rb")
        in_fh.close()
    except:
        console("Error: " + infile +
                " does not exist or we do not have permission")

    console("Processing: " + infile)
    extension = os.path.splitext(infile)[1].lower()

    if extension in MPEG_FILE_EXTENSIONS:
        return parse_mpeg4(infile, console)

    console("Unknown file type")
    return None


def inject_metadata(src, dest, metadata, console):
    infile = os.path.abspath(src)
    outfile = os.path.abspath(dest)

    if infile == outfile:
        return "Input and output cannot be the same"

    try:
        in_fh = open(infile, "rb")
        in_fh.close()
    except:
        console("Error: " + infile +
                " does not exist or we do not have permission")
        return

    console("Processing: " + infile)

    extension = os.path.splitext(infile)[1].lower()

    if (extension in MPEG_FILE_EXTENSIONS):
        inject_mpeg4(infile, outfile, metadata, console)
        return

    console("Unknown file type")


def get_descriptor_length(in_fh):
    """Derives the length of the MP4 elementary stream descriptor at the
       current position in the input file.
    """
    descriptor_length = 0
    for i in range(4):
        size_byte = struct.unpack(">c", in_fh.read(1))[0]
        descriptor_length = (descriptor_length << 7 |
                             ord(size_byte) & int("0x7f", 0))
        if (ord(size_byte) != int("0x80", 0)):
            break
    return descriptor_length


def get_expected_num_audio_components(ambisonics_type, ambisonics_order):
    """ Returns the expected number of ambisonic components for a given
        ambisonic type and ambisonic order.
    """
    if (ambisonics_type == 'periphonic'):
        return ((ambisonics_order + 1) * (ambisonics_order + 1))
    else:
        return -1

def get_num_audio_channels(stsd, in_fh):
    if stsd.name != mpeg.constants.TAG_STSD:
        print "get_num_audio_channels should be given a STSD box"
        return -1
    for sample_description in stsd.contents:
        if sample_description.name == mpeg.constants.TAG_MP4A:
            return get_aac_num_channels(sample_description, in_fh)
        elif sample_description.name in mpeg.constants.SOUND_SAMPLE_DESCRIPTIONS:
            return get_sample_description_num_channels(sample_description, in_fh)
    return -1

def get_sample_description_num_channels(sample_description, in_fh):
    """Reads the number of audio channels from a sound sample description.
    """
    p = in_fh.tell()
    in_fh.seek(sample_description.content_start() + 8)

    version = struct.unpack(">h", in_fh.read(2))[0]
    revision_level = struct.unpack(">h", in_fh.read(2))[0]
    vendor = struct.unpack(">i", in_fh.read(4))[0]
    if version == 0:
        num_audio_channels = struct.unpack(">h", in_fh.read(2))[0]
        sample_size_bytes = struct.unpack(">h", in_fh.read(2))[0]
    elif version == 1:
        num_audio_channels = struct.unpack(">h", in_fh.read(2))[0]
        sample_size_bytes = struct.unpack(">h", in_fh.read(2))[0]
        samples_per_packet = struct.unpack(">i", in_fh.read(4))[0]
        bytes_per_packet = struct.unpack(">i", in_fh.read(4))[0]
        bytes_per_frame = struct.unpack(">i", in_fh.read(4))[0]
        bytes_per_sample = struct.unpack(">i", in_fh.read(4))[0]
    elif version == 2:
        always_3 = struct.unpack(">h", in_fh.read(2))[0]
        always_16 = struct.unpack(">h", in_fh.read(2))[0]
        always_minus_2 = struct.unpack(">h", in_fh.read(2))[0]
        always_0 = struct.unpack(">h", in_fh.read(2))[0]
        always_65536 = struct.unpack(">i", in_fh.read(4))[0]
        size_of_struct_only = struct.unpack(">i", in_fh.read(4))[0]
        audio_sample_rate = struct.unpack(">d", in_fh.read(8))[0]
        num_audio_channels = struct.unpack(">i", in_fh.read(4))[0]
    else:
        print "Unsupported version for " + sample_description.name + " box"
        return -1

    in_fh.seek(p)
    return num_audio_channels

def get_aac_num_channels(box, in_fh):
    """Reads the number of audio channels from AAC's AudioSpecificConfig
       descriptor within the esds child box of the input mp4a or wave box.
    """
    p = in_fh.tell()
    if box.name not in [mpeg.constants.TAG_MP4A, mpeg.constants.TAG_WAVE]:
        return -1

    for element in box.contents:
        if element.name == mpeg.constants.TAG_WAVE:
            # Handle .mov with AAC audio, where the structure is:
            #     stsd -> mp4a -> wave -> esds
            channel_configuration = get_aac_num_channels(element, in_fh)
            break

        if element.name != mpeg.constants.TAG_ESDS:
          continue
        in_fh.seek(element.content_start() + 4)
        descriptor_tag = struct.unpack(">c", in_fh.read(1))[0]

        # Verify the read descriptor is an elementary stream descriptor
        if ord(descriptor_tag) != 3:  # Not an MP4 elementary stream.
            print "Error: failed to read elementary stream descriptor."
            return -1
        get_descriptor_length(in_fh)
        in_fh.seek(3, 1)  # Seek to the decoder configuration descriptor
        config_descriptor_tag = struct.unpack(">c", in_fh.read(1))[0]

        # Verify the read descriptor is a decoder config. descriptor.
        if ord(config_descriptor_tag) != 4:
            print "Error: failed to read decoder config. descriptor."
            return -1
        get_descriptor_length(in_fh)
        in_fh.seek(13, 1) # offset to the decoder specific config descriptor.
        decoder_specific_descriptor_tag = struct.unpack(">c", in_fh.read(1))[0]

        # Verify the read descriptor is a decoder specific info descriptor
        if ord(decoder_specific_descriptor_tag) != 5:
            print "Error: failed to read MP4 audio decoder specific config."
            return -1
        audio_specific_descriptor_size = get_descriptor_length(in_fh)
        assert audio_specific_descriptor_size >= 2
        decoder_descriptor = struct.unpack(">h", in_fh.read(2))[0]
        object_type = (int("F800", 16) & decoder_descriptor) >> 11
        sampling_frequency_index = (int("0780", 16) & decoder_descriptor) >> 7
        if sampling_frequency_index == 0:
            # TODO: If the sample rate is 96kHz an additional 24 bit offset
            # value here specifies the actual sample rate.
            print "Error: Greater than 48khz audio is currently not supported."
            return -1
        channel_configuration = (int("0078", 16) & decoder_descriptor) >> 3
    in_fh.seek(p)
    return channel_configuration


def get_num_audio_tracks(mpeg4_file, in_fh):
    """ Returns the number of audio track in the input mpeg4 file. """
    num_audio_tracks = 0
    for element in mpeg4_file.moov_box.contents:
        if (element.name == mpeg.constants.TAG_TRAK):
            for sub_element in element.contents:
                if (sub_element.name != mpeg.constants.TAG_MDIA):
                    continue
                for mdia_sub_element in sub_element.contents:
                    if (mdia_sub_element.name != mpeg.constants.TAG_HDLR):
                        continue
                    position = mdia_sub_element.content_start() + 8
                    in_fh.seek(position)
                    if (in_fh.read(4) == mpeg.constants.TAG_SOUN):
                        num_audio_tracks += 1
    return num_audio_tracks
