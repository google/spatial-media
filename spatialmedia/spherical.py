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

"""Spherical Metadata Python Tool

Tool for examining and injecting spherical metadata into MP4 files.
"""

from mpeg import box
from mpeg import mpeg4
from mpeg import tag_trak
from mpeg import tag_uuid

from optparse import OptionParser
import os
import re
import StringIO
import struct
import xml.etree
import xml.etree.ElementTree

spherical_uuid_id = (
    "\xff\xcc\x82\x63\xf8\x55\x4a\x93\x88\x14\x58\x7a\x02\x52\x1f\xdd")

# XML contents.
rdf_prefix = " xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\" "

spherical_xml_header = \
    "<?xml version=\"1.0\"?>"\
    "<rdf:SphericalVideo\n"\
    "xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\"\n"\
    "xmlns:GSpherical=\"http://ns.google.com/videos/1.0/spherical/\">"

spherical_xml_contents = \
    "<GSpherical:Spherical>true</GSpherical:Spherical>"\
    "<GSpherical:Stitched>true</GSpherical:Stitched>"\
    "<GSpherical:StitchingSoftware>"\
    "Spherical Metadata Tool"\
    "</GSpherical:StitchingSoftware>"\
    "<GSpherical:ProjectionType>equirectangular</GSpherical:ProjectionType>"

spherical_xml_contents_top_bottom = \
    "<GSpherical:StereoMode>top-bottom</GSpherical:StereoMode>"
spherical_xml_contents_left_right = \
    "<GSpherical:StereoMode>left-right</GSpherical:StereoMode>"

# Parameter order matches that of the crop option.
spherical_xml_contents_crop_format = \
    "<GSpherical:CroppedAreaImageWidthPixels>{0}</GSpherical:CroppedAreaImageWidthPixels>"\
    "<GSpherical:CroppedAreaImageHeightPixels>{1}</GSpherical:CroppedAreaImageHeightPixels>"\
    "<GSpherical:FullPanoWidthPixels>{2}</GSpherical:FullPanoWidthPixels>"\
    "<GSpherical:FullPanoHeightPixels>{3}</GSpherical:FullPanoHeightPixels>"\
    "<GSpherical:CroppedAreaLeftPixels>{4}</GSpherical:CroppedAreaLeftPixels>"\
    "<GSpherical:CroppedAreaTopPixels>{5}</GSpherical:CroppedAreaTopPixels>"

spherical_xml_footer = "</rdf:SphericalVideo>"

spherical_tags_list = [
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

spherical_prefix = "{http://ns.google.com/videos/1.0/spherical/}"
spherical_tags = dict()
for tag in spherical_tags_list:
    spherical_tags[spherical_prefix + tag] = tag

integer_regex_group = "(\d+)"
crop_regex = '^{0}$'.format(':'.join([integer_regex_group] * 6))


def spherical_uuid(metadata):
    """Constructs a uuid containing spherical metadata.

    Args:
      metadata: String, xml to inject in spherical tag.

    Returns:
      uuid_leaf: a box containing spherical metadata.
    """
    uuid_leaf = box()
    assert(len(spherical_uuid_id) == 16)
    uuid_leaf.name = tag_uuid
    uuid_leaf.header_size = 8
    uuid_leaf.content_size = 0

    uuid_leaf.contents = spherical_uuid_id + metadata
    uuid_leaf.content_size = len(uuid_leaf.contents)

    return uuid_leaf


def mpeg4_add_spherical(mpeg4_file, in_fh, metadata):
    """Adds a spherical uuid box to an mpeg4 file for all video tracks.

    Args:
      mpeg4_file: mpeg4, Mpeg4 file structure to add metadata.
      in_fh: file handle, Source for uncached file contents.
      metadata: string, xml metadata to inject into spherical tag.
    """
    for element in mpeg4_file.moov_box.contents:
        if element.name == "trak":
            added = False
            element.remove("uuid")
            for sub_element in element.contents:
                if sub_element.name != "mdia":
                    continue
                for mdia_sub_element in sub_element.contents:
                    if mdia_sub_element.name != "hdlr":
                        continue
                    position = mdia_sub_element.content_start() + 8
                    in_fh.seek(position)
                    if (in_fh.read(4) == "vide"):
                        added = True
                        break

                if added:
                    if not element.add(spherical_uuid(metadata)):
                        return False
                    break

    mpeg4_file.resize()
    return True


def ParseSphericalXML(contents, console):
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
            index = contents.find("<rdf:SphericalVideo")
            if (index != -1):
                index += len("<rdf:SphericalVideo")
                contents = contents[:index] + rdf_prefix + contents[index:]
            parsed_xml = xml.etree.ElementTree.XML(contents)
            console("\t\tWarning missing rdf prefix:", rdf_prefix)
        except xml.etree.ElementTree.ParseError as e:
            console("\t\tParser Error on XML")
            console(e)
            console(contents)
            return

    sphericalDictionary = dict()
    for child in parsed_xml.getchildren():
        if child.tag in spherical_tags.keys():
            console("\t\tFound: " + spherical_tags[child.tag]
                    + " = " + child.text)
            sphericalDictionary[spherical_tags[child.tag]] = child.text
        else:
            tag = child.tag
            if (child.tag[:len(spherical_prefix)] == spherical_prefix):
                tag = child.tag[len(spherical_prefix):]
            console("\t\tUnknown: " + tag + " = " + child.text)

    return sphericalDictionary

def ParseSphericalMpeg4(mpeg4_file, fh, console):
    """Returns spherical metadata for a loaded mpeg4 file.

    Args:
      mpeg4_file: mpeg4, loaded mpeg4 file contents.
      fh: file handle, file handle for uncached file contents.

    Returns:
      Dictionary stored as (trackName, metadataDictionary)
    """
    metadataSets = dict()
    track_num = 0
    for element in mpeg4_file.moov_box.contents:
        if element.name == tag_trak:
            trackName = "Track %d" % track_num
            console("\t%s" % trackName)
            track_num += 1
            for sub_element in element.contents:
                if sub_element.name == tag_uuid:
                    if sub_element.contents is not None:
                        sub_element_id = sub_element.contents[:16]
                    else:
                        fh.seek(sub_element.content_start())
                        sub_element_id = fh.read(16)

                    if sub_element_id == spherical_uuid_id:
                        if sub_element.contents is not None:
                            contents = sub_element.contents[16:]
                        else:
                            contents = fh.read(sub_element.content_size - 16)
                        metadataSets[trackName] = \
                            ParseSphericalXML(contents, console)
    return metadataSets


def ParseMpeg4(input_file, console):
    in_fh = open(input_file, "rb")
    if in_fh is None:
        console("File: \"" + input_file + "\" does not exist or do not have "
                "permission.")

    mpeg4_file = mpeg4.load(in_fh)
    if (mpeg4_file is None):
        console("File could not be opened.")
        return

    console("Loaded file settings")
    return ParseSphericalMpeg4(mpeg4_file, in_fh, console)


def InjectMpeg4(input_file, output_file, metadata, console):
    in_fh = open(input_file, "rb")
    if in_fh is None:
        console("File: \"" + input_file + "\" does not exist or do not have "
                "permission.")

    mpeg4_file = mpeg4.load(in_fh)
    if (mpeg4_file is None):
        console("File could not be opened.")

    if not mpeg4_add_spherical(mpeg4_file, in_fh, metadata):
        console("Failed to insert spherical data")

    console("Saved file settings")
    ParseSphericalMpeg4(mpeg4_file, in_fh, console)

    out_fh = open(output_file, "wb")
    mpeg4_file.save(in_fh, out_fh)
    out_fh.close()
    in_fh.close()


def ParseMetadata(src, console):
    infile = os.path.abspath(src)

    try:
        in_fh = open(infile, "rb")
        in_fh.close()
    except:
        console("Error: " + infile +
                " does not exist or we do not have permission")

    console("Processing: " + infile)

    if (os.path.splitext(infile)[1].lower() == ".mp4"):
        return ParseMpeg4(infile, console)

    console("Unknown file type")
    return dict()


def InjectMetadata(src, dest, metadata, console):
    infile = os.path.abspath(src)
    outfile = os.path.abspath(dest)

    if (infile == outfile):
        return "Input and output cannot be the same"

    try:
        in_fh = open(infile, "rb")
        in_fh.close()
    except:
        console("Error: " + infile +
                " does not exist or we do not have permission")
        return

    console("Processing: " + infile)

    if (os.path.splitext(infile)[1].lower() == ".mp4"):
        InjectMpeg4(infile, outfile, metadata, console)
        return

    console("Unknown file type")


def GenerateSphericalXML(stereo=None, crop=None):
    # Configure inject xml.
    additional_xml = ""
    if stereo == "top-bottom":
        additional_xml += spherical_xml_contents_top_bottom

    if stereo == "left-right":
        additional_xml += spherical_xml_contents_left_right

    if crop:
        crop_match = re.match(crop_regex, crop)
        if not crop_match:
            console("Error: Invalid crop params: {crop}".format(crop=crop))
            return
        else:
            cropped_width_pixels = int(crop_match.group(1))
            cropped_height_pixels = int(crop_match.group(2))
            full_width_pixels = int(crop_match.group(3))
            full_height_pixels = int(crop_match.group(4))
            cropped_offset_left_pixels = int(crop_match.group(5))
            cropped_offset_top_pixels = int(crop_match.group(6))

            # This should never happen based on the crop regex.
            if full_width_pixels <= 0 or full_height_pixels <= 0:
                console("Error with crop params: full pano dimensions are "
                        "invalid: width = {width} height = {height}".format(
                            width=full_width_pixels,
                            height=full_height_pixels))
                return

            if (cropped_width_pixels <= 0 or
                    cropped_height_pixels <= 0 or
                    cropped_width_pixels > full_width_pixels or
                    cropped_height_pixels > full_height_pixels):
                console("Error with crop params: cropped area dimensions are "
                        "invalid: width = {width} height = {height}".format(
                            width=cropped_width_pixels,
                            height=cropped_height_pixels))
                return

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
                    console("Error with crop params: cropped area offsets are "
                            "invalid: left = {left} top = {top} "
                            "left+cropped width: {total_width} "
                            "top+cropped height: {total_height}".format(
                                left=cropped_offset_left_pixels,
                                top=cropped_offset_top_pixels,
                                total_width=total_width,
                                total_height=total_height))
                    return

            additional_xml += spherical_xml_contents_crop_format.format(
                cropped_width_pixels, cropped_height_pixels,
                full_width_pixels, full_height_pixels,
                cropped_offset_left_pixels, cropped_offset_top_pixels)

    spherical_xml = (spherical_xml_header +
                     spherical_xml_contents +
                     additional_xml +
                     spherical_xml_footer)
    return spherical_xml
