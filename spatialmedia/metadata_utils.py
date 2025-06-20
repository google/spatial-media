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

import collections
import os
import re
import struct
import traceback
import xml.etree
import xml.etree.ElementTree

from spatialmedia import mpeg

MPEG_FILE_EXTENSIONS = [".mp4", ".mov"]

SPHERICAL_UUID_ID = (
    b"\xff\xcc\x82\x63\xf8\x55\x4a\x93\x88\x14\x58\x7a\x02\x52\x1f\xdd")

# XML contents.
RDF_PREFIX = " xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\" "

SPHERICAL_XML_HEADER = \
    "<?xml version=\"1.0\"?>"\
    "<rdf:SphericalVideo\n"\
    "xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\"\n"\
    "xmlns:GSpherical=\"http://ns.google.com/videos/1.0/spherical/\">"

SPHERICAL_XML_CONTENTS = \
    "<GSpherical:Spherical>true</GSpherical:Spherical>"\
    "<GSpherical:Stitched>true</GSpherical:Stitched>"\
    "<GSpherical:StitchingSoftware>"\
    "Spherical Metadata Tool"\
    "</GSpherical:StitchingSoftware>"\
    "<GSpherical:ProjectionType>equirectangular</GSpherical:ProjectionType>"

NOT_SPHERICAL_XML_CONTENTS = \
    "<GSpherical:Spherical>false</GSpherical:Spherical>"\
    "<GSpherical:Stitched>false</GSpherical:Stitched>"\
    "<GSpherical:StitchingSoftware>"\
    "Spherical Metadata Tool"\
    "</GSpherical:StitchingSoftware>"\
    "<GSpherical:ProjectionType>rectangular</GSpherical:ProjectionType>"

SPHERICAL_XML_CONTENTS_TOP_BOTTOM = \
    "<GSpherical:StereoMode>top-bottom</GSpherical:StereoMode>"
SPHERICAL_XML_CONTENTS_LEFT_RIGHT = \
    "<GSpherical:StereoMode>left-right</GSpherical:StereoMode>"

# Parameter order matches that of the crop option.
SPHERICAL_XML_CONTENTS_CROP_FORMAT = \
    "<GSpherical:CroppedAreaImageWidthPixels>{0}"\
    "</GSpherical:CroppedAreaImageWidthPixels>"\
    "<GSpherical:CroppedAreaImageHeightPixels>{1}"\
    "</GSpherical:CroppedAreaImageHeightPixels>"\
    "<GSpherical:FullPanoWidthPixels>{2}</GSpherical:FullPanoWidthPixels>"\
    "<GSpherical:FullPanoHeightPixels>{3}</GSpherical:FullPanoHeightPixels>"\
    "<GSpherical:CroppedAreaLeftPixels>{4}</GSpherical:CroppedAreaLeftPixels>"\
    "<GSpherical:CroppedAreaTopPixels>{5}</GSpherical:CroppedAreaTopPixels>"

SPHERICAL_XML_FOOTER = "</rdf:SphericalVideo>"

SPHERICAL_TAGS_LIST = [
    "Spherical",
    "Stitched",
    "StitchingSoftware",
    "ProjectionType",
    "SourceCount",
    "StereoMode",
    "InitialViewHeadingDegrees",
    "InitialViewPitchDegrees",
    "InitialViewRollDegrees",
    "Timestamp",
    "CroppedAreaImageWidthPixels",
    "CroppedAreaImageHeightPixels",
    "FullPanoWidthPixels",
    "FullPanoHeightPixels",
    "CroppedAreaLeftPixels",
    "CroppedAreaTopPixels",
]

class Metadata(object):
    def __init__(self, projection=None, stereo_mode=None):
        self.projection = None if (not projection or projection == "none") else projection
        self.stereo_mode = None if (not stereo_mode or stereo_mode == "none") else stereo_mode
        self.video = None
        self.audio = None

class ParsedMetadata(object):
    def __init__(self):
        self.video = dict()
        self.audio = None
        self.num_audio_channels = 0

SPHERICAL_PREFIX = "{http://ns.google.com/videos/1.0/spherical/}"
SPHERICAL_TAGS = dict()
for tag in SPHERICAL_TAGS_LIST:
    SPHERICAL_TAGS[SPHERICAL_PREFIX + tag] = tag

integer_regex_group = r"(\d+)"
crop_regex = "^{0}$".format(":".join([integer_regex_group] * 6))

MAX_SUPPORTED_AMBIX_ORDER = 1

SpatialAudioDescription = collections.namedtuple(
    'SpatialAudioDescription',
    'order is_supported has_head_locked_stereo')

def get_spatial_audio_description(num_channels):
  for i in range(1, MAX_SUPPORTED_AMBIX_ORDER+1):
    if (i + 1)*(i + 1) == num_channels:
      return SpatialAudioDescription(
          order=i, is_supported=True, has_head_locked_stereo=False)
    elif ((i + 1)*(i + 1) + 2) == num_channels:
      return SpatialAudioDescription(
          order=i, is_supported=True, has_head_locked_stereo=True)

  return SpatialAudioDescription(
      order=-1, is_supported=False, has_head_locked_stereo=True)

def spherical_uuid(metadata):
    """Constructs a uuid containing spherical metadata.

    Args:
      metadata: String, xml to inject in spherical tag.

    Returns:
      uuid_leaf: a box containing spherical metadata.
    """
    uuid_leaf = mpeg.Box()
    assert(len(SPHERICAL_UUID_ID) == 16)
    uuid_leaf.name = mpeg.constants.TAG_UUID
    uuid_leaf.header_size = 8
    uuid_leaf.content_size = 0

    uuid_leaf.contents = SPHERICAL_UUID_ID + metadata.encode("utf-8")
    uuid_leaf.content_size = len(uuid_leaf.contents)

    return uuid_leaf


def mpeg4_add_spherical_xml_v1(mpeg4_file, in_fh, metadata):
    """Adds a spherical uuid box to an mpeg4 file for all video tracks.

    Args:
      mpeg4_file: mpeg4, Mpeg4 file structure to add metadata.
      in_fh: file handle, Source for uncached file contents.
      metadata: string, xml metadata to inject into spherical tag.
    """
    for element in mpeg4_file.moov_box.contents:
        if element.name == mpeg.constants.TAG_TRAK:
            added = False
            element.remove(mpeg.constants.TAG_UUID)
            for sub_element in element.contents:
                if sub_element.name != mpeg.constants.TAG_MDIA:
                    continue
                for mdia_sub_element in sub_element.contents:
                    if mdia_sub_element.name != mpeg.constants.TAG_HDLR:
                        continue
                    position = mdia_sub_element.content_start() + 8
                    in_fh.seek(position)
                    if in_fh.read(4) == mpeg.constants.TRAK_TYPE_VIDE:
                        added = True
                        break

                if added:
                    if not element.add(spherical_uuid(metadata)):
                        return False
                    break

    mpeg4_file.resize()
    return True

def mpeg4_add_spherical_v2(mpeg4_file, in_fh, projection, stereo_mode):
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
                        ret = inject_spatial_video_v2_atoms(
                            in_fh, sub_element, projection, stereo_mode)
                        mpeg4_file.resize()
                        return ret


def inject_spatial_video_v2_atoms(in_fh, video_media_atom, projection, stereo_mode):
    """Adds spherical v2 boxes to an mpeg4 file for all video tracks.

    Args:
      mpeg4_file: mpeg4, Mpeg4 file structure to add metadata.
      in_fh: file handle, Source for uncached file contents.
      metadata: string, xml metadata to inject into spherical tag.
    """
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
                        # Should remove any existing boxes...
                        if stereo_mode:
                            st3d_atom = mpeg.sv3d.ST3DBox.create()
                            st3d_atom.name = mpeg.constants.TAG_ST3D
                            st3d_atom.set_stereo_mode_from_string(stereo_mode)

                            sample_description.remove(st3d_atom.name)
                            sample_description.add(st3d_atom)

                        if projection:
                            proj_atom = mpeg.container.Container(header_size=8)
                            proj_atom.name = mpeg.constants.TAG_PROJ

                            proj_atom.add(mpeg.sv3d.PRHDBox.create())
                            proj_atom.add(mpeg.sv3d.EQUIBox.create())

                            sv3d_atom = mpeg.container.Container(header_size=8)
                            sv3d_atom.name = mpeg.constants.TAG_SV3D

                            sv3d_atom.add(proj_atom)

                            sample_description.remove(sv3d_atom.name)
                            sample_description.add(sv3d_atom)

    return True


def mpeg4_add_spatial_audio(mpeg4_file, in_fh, audio_metadata, console):
    """Adds spatial audio metadata to the first audio track of the input
       mpeg4_file. Returns False on failure.

    Args:
      mpeg4_file: mpeg4, Mpeg4 file structure to add metadata.
      in_fh: file handle, Source for uncached file contents.
      audio_metadata: dictionary ('ambisonic_type': string,
      'ambisonic_order': int, 'head_locked_stereo': Bool),
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
                        expected_num_channels = \
                            get_expected_num_audio_channels(
                                audio_metadata["ambisonic_type"],
                                audio_metadata["ambisonic_order"],
                                audio_metadata["head_locked_stereo"])
                        if num_channels != expected_num_channels:
                            head_locked_stereo_msg = (" with head-locked stereo" if
                                            audio_metadata["head_locked_stereo"] else "")
                            err_msg = "Error: Found %d audio channel(s). "\
                                  "Expected %d channel(s) for %s ambisonics "\
                                  "of order %d%s."\
                                % (num_channels,
                                   expected_num_channels,
                                   audio_metadata["ambisonic_type"],
                                   audio_metadata["ambisonic_order"],
                                   head_locked_stereo_msg)
                            console(err_msg)
                            return False
                        sa3d_atom = mpeg.SA3DBox.create(
                            num_channels, audio_metadata)
                        sample_description.contents.append(sa3d_atom)
    return True

def parse_spherical_xml(contents, console):
    """Returns spherical metadata for a set of xml data.

    Args:
      contents: string, spherical metadata xml contents.

    Returns:
      dictionary containing the parsed spherical metadata values.
    """
    try:
        parsed_xml = xml.etree.ElementTree.XML(contents)
    except xml.etree.ElementTree.ParseError:
        try:
            console(traceback.format_exc())
            console(contents)
            index = contents.find("<rdf:SphericalVideo")
            if index != -1:
                index += len("<rdf:SphericalVideo")
                contents = contents[:index] + RDF_PREFIX + contents[index:]
            parsed_xml = xml.etree.ElementTree.XML(contents)
            console("\t\tWarning missing rdf prefix:", RDF_PREFIX)
        except xml.etree.ElementTree.ParseError as e:
            console("\t\tParser Error on XML")
            console(traceback.format_exc())
            console(contents)
            return

    sphericalDictionary = dict()
    for child in list(parsed_xml):
        if child.tag in SPHERICAL_TAGS.keys():
            console("\t\t" + SPHERICAL_TAGS[child.tag]
                    + " = " + child.text)
            sphericalDictionary[SPHERICAL_TAGS[child.tag]] = child.text
        else:
            tag = child.tag
            if child.tag[:len(spherical_prefix)] == spherical_prefix:
                tag = child.tag[len(spherical_prefix):]
            console("\t\tUnknown: " + tag + " = " + child.text)

    return sphericalDictionary


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
                if sub_element.name == mpeg.constants.TAG_UUID:
                    if sub_element.contents:
                        sub_element_id = sub_element.contents[:16]
                    else:
                        fh.seek(sub_element.content_start())
                        sub_element_id = fh.read(16)

                    if sub_element_id == SPHERICAL_UUID_ID:
                        if sub_element.contents:
                            contents = sub_element.contents[16:]
                        else:
                            contents = fh.read(sub_element.content_size - 16)
                        metadata.video[trackName] = \
                            parse_spherical_xml(contents.decode("utf-8"), console)

                if sub_element.name == mpeg.constants.TAG_MDIA:
                    for mdia_sub_element in sub_element.contents:
                        if mdia_sub_element.name != mpeg.constants.TAG_MINF:
                            continue
                        for stbl_elem in mdia_sub_element.contents:
                            if stbl_elem.name != mpeg.constants.TAG_STBL:
                                continue
                            for stsd_elem in stbl_elem.contents:
                                if stsd_elem.name != mpeg.constants.TAG_STSD:
                                    continue
                                for sa3d_container_elem in stsd_elem.contents:
                                    if sa3d_container_elem.name not in \
                                            mpeg.constants.SOUND_SAMPLE_DESCRIPTIONS:
                                        continue
                                    metadata.num_audio_channels = \
                                        get_num_audio_channels(stsd_elem, fh)
                                    for sa3d_elem in sa3d_container_elem.contents:
                                        if sa3d_elem.name == mpeg.constants.TAG_SA3D:
                                            sa3d_elem.print_box(console)
                                            metadata.audio = sa3d_elem

                                for sv3d_container_elem in stsd_elem.contents:
                                    if sv3d_container_elem.name not in \
                                            mpeg.constants.VIDEO_SAMPLE_DESCRIPTIONS:
                                        continue
                                    for sub_elem in sv3d_container_elem.contents:
                                        if sub_elem.name == mpeg.constants.TAG_SV3D:
                                            console("\t\tSV3D {")
                                            sub_elem.print_box(console)
                                            console("\t\t}")
                                        elif sub_elem.name == mpeg.constants.TAG_ST3D:
                                            console("\t\tST3D {")
                                            sub_elem.print_box(console)
                                            console("\t\t} ")

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

        if metadata.video and not mpeg4_add_spherical_xml_v1(mpeg4_file, in_fh, metadata.video):
            console("Error failed to insert spherical data")

        if ((metadata.projection or metadata.stereo_mode)
            and not mpeg4_add_spherical_v2(mpeg4_file, in_fh, metadata.projection, metadata.stereo_mode)):
            console("Error failed to insert spherical data v2")

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


def generate_spherical_xml(projection="equiretangular", stereo=None, crop=None):
    # Configure inject xml.
    additional_xml = ""
    if stereo == "top-bottom":
        additional_xml += SPHERICAL_XML_CONTENTS_TOP_BOTTOM

    if stereo == "left-right":
        additional_xml += SPHERICAL_XML_CONTENTS_LEFT_RIGHT

    if crop:
        crop_match = re.match(crop_regex, crop)
        if not crop_match:
            print("Error: Invalid crop params: {crop}".format(crop=crop))
            return False
        else:
            cropped_width_pixels = int(crop_match.group(1))
            cropped_height_pixels = int(crop_match.group(2))
            full_width_pixels = int(crop_match.group(3))
            full_height_pixels = int(crop_match.group(4))
            cropped_offset_left_pixels = int(crop_match.group(5))
            cropped_offset_top_pixels = int(crop_match.group(6))

            # This should never happen based on the crop regex.
            if full_width_pixels <= 0 or full_height_pixels <= 0:
                print("Error with crop params: full pano dimensions are "\
                        "invalid: width = {width} height = {height}".format(
                            width=full_width_pixels,
                            height=full_height_pixels))
                return False

            if (cropped_width_pixels <= 0 or
                    cropped_height_pixels <= 0 or
                    cropped_width_pixels > full_width_pixels or
                    cropped_height_pixels > full_height_pixels):
                print("Error with crop params: cropped area dimensions are "\
                        "invalid: width = {width} height = {height}".format(
                            width=cropped_width_pixels,
                            height=cropped_height_pixels))
                return False

            # We are pretty restrictive and don't allow anything strange. There
            # could be use-cases for a horizontal offset that essentially
            # translates the domain, but we don't support this (so that no
            # extra work has to be done on the client).
            total_width = cropped_offset_left_pixels + cropped_width_pixels
            total_height = cropped_offset_top_pixels + cropped_height_pixels
            if (cropped_offset_left_pixels < 0 or
                    cropped_offset_top_pixels < 0 or
                    total_width > full_width_pixels or
                    total_height > full_height_pixels):
                    print("Error with crop params: cropped area offsets are "\
                            "invalid: left = {left} top = {top} "\
                            "left+cropped width: {total_width} "\
                            "top+cropped height: {total_height}".format(
                                left=cropped_offset_left_pixels,
                                top=cropped_offset_top_pixels,
                                total_width=total_width,
                                total_height=total_height))
                    return False

            additional_xml += SPHERICAL_XML_CONTENTS_CROP_FORMAT.format(
                cropped_width_pixels, cropped_height_pixels,
                full_width_pixels, full_height_pixels,
                cropped_offset_left_pixels, cropped_offset_top_pixels)

    spherical_xml = (SPHERICAL_XML_HEADER +
                     (SPHERICAL_XML_CONTENTS if projection == "equirectangular"
                      else NOT_SPHERICAL_XML_CONTENTS) +
                     additional_xml +
                     SPHERICAL_XML_FOOTER)
    return spherical_xml


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


def get_expected_num_audio_channels(
    ambisonics_type, ambisonics_order, head_locked_stereo):
    """ Returns the expected number of ambisonic components for a given
        ambisonic type and ambisonic order.
    """
    head_locked_stereo_channels = 2 if head_locked_stereo == True else 0
    if (ambisonics_type == 'periphonic'):
        return (((ambisonics_order + 1) * (ambisonics_order + 1)) +
                head_locked_stereo_channels)
    else:
        return -1

def get_num_audio_channels(stsd, in_fh):
    if stsd.name != mpeg.constants.TAG_STSD:
        print("get_num_audio_channels should be given a STSD box")
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
        print("Unsupported version for " + sample_description.name + " box")
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
            print("Error: failed to read elementary stream descriptor.")
            return -1
        get_descriptor_length(in_fh)
        in_fh.seek(3, 1)  # Seek to the decoder configuration descriptor
        config_descriptor_tag = struct.unpack(">c", in_fh.read(1))[0]

        # Verify the read descriptor is a decoder config. descriptor.
        if ord(config_descriptor_tag) != 4:
            print("Error: failed to read decoder config. descriptor.")
            return -1
        get_descriptor_length(in_fh)
        in_fh.seek(13, 1) # offset to the decoder specific config descriptor.
        decoder_specific_descriptor_tag = struct.unpack(">c", in_fh.read(1))[0]

        # Verify the read descriptor is a decoder specific info descriptor
        if ord(decoder_specific_descriptor_tag) != 5:
            print("Error: failed to read MP4 audio decoder specific config.")
            return -1
        audio_specific_descriptor_size = get_descriptor_length(in_fh)
        assert audio_specific_descriptor_size >= 2
        decoder_descriptor = struct.unpack(">h", in_fh.read(2))[0]
        object_type = (int("F800", 16) & decoder_descriptor) >> 11
        sampling_frequency_index = (int("0780", 16) & decoder_descriptor) >> 7
        if sampling_frequency_index == 0:
            # TODO: If the sample rate is 96kHz an additional 24 bit offset
            # value here specifies the actual sample rate.
            print("Error: Greater than 48khz audio is currently not supported.")
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


def get_spatial_audio_metadata(ambisonic_order, head_locked_stereo):
    num_channels = get_expected_num_audio_channels(
        "periphonic", ambisonic_order, head_locked_stereo)
    metadata = {
        "ambisonic_order": 0,
        "head_locked_stereo": False,
        "ambisonic_type": "periphonic",
        "ambisonic_channel_ordering": "ACN",
        "ambisonic_normalization": "SN3D",
        "channel_map": [],
    }
    metadata['ambisonic_order'] = ambisonic_order
    metadata['head_locked_stereo'] = head_locked_stereo
    metadata['channel_map'] = range(0, num_channels)
    return metadata
