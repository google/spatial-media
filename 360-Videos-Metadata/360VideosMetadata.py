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

Tool for examining and injecting spherical metadata into MKV/MP4 files.
"""

from optparse import OptionParser
import os
import re
import StringIO
import struct
import subprocess
import sys
import xml.etree
import xml.etree.ElementTree

# Leaf types.
tag_stco = "stco"
tag_co64 = "co64"
tag_free = "free"
tag_mdat = "mdat"
tag_xml = "xml "
tag_hdlr = "hdlr"
tag_ftyp = "ftyp"

# Container types.
tag_moov = "moov"
tag_udta = "udta"
tag_meta = "meta"
tag_trak = "trak"
tag_mdia = "mdia"
tag_minf = "minf"
tag_stbl = "stbl"
tag_uuid = "uuid"

containers = [tag_moov, tag_udta, tag_trak,
              tag_mdia, tag_minf, tag_stbl]

spherical_uuid_id = (
    "\xff\xcc\x82\x63\xf8\x55\x4a\x93\x88\x14\x58\x7a\x02\x52\x1f\xdd")

# XML contents.
rdf_prefix = " xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\" "

spherical_xml_header = \
    """<?xml version=\"1.0\"?>
    <rdf:SphericalVideo
     xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\"
     xmlns:GSpherical=\"http://ns.google.com/videos/1.0/spherical/\">"""

spherical_xml_contents = \
      """ <GSpherical:Spherical>true</GSpherical:Spherical>
      <GSpherical:Stitched>true</GSpherical:Stitched>
      <GSpherical:StitchingSoftware>Spherical Metadata Tool</GSpherical:StitchingSoftware>
      <GSpherical:ProjectionType>equirectangular</GSpherical:ProjectionType>"""

spherical_xml_contents_top_bottom = \
    "  <GSpherical:StereoMode>top-bottom</GSpherical:StereoMode>"
spherical_xml_contents_left_right = \
    "  <GSpherical:StereoMode>left-right</GSpherical:StereoMode>"

# Parameter order matches that of the crop option.
spherical_xml_contents_crop_format = \
      """ <GSpherical:CroppedAreaImageWidthPixels>{0}</GSpherical:CroppedAreaImageWidthPixels>
      <GSpherical:CroppedAreaImageHeightPixels>{1}</GSpherical:CroppedAreaImageHeightPixels>
      <GSpherical:FullPanoWidthPixels>{2}</GSpherical:FullPanoWidthPixels>
      <GSpherical:FullPanoHeightPixels>{3}</GSpherical:FullPanoHeightPixels>
      <GSpherical:CroppedAreaLeftPixels>{4}</GSpherical:CroppedAreaLeftPixels>
      <GSpherical:CroppedAreaTopPixels>{5}</GSpherical:CroppedAreaTopPixels>"""

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
crop_regex = "^{0}$".format(":".join([integer_regex_group] * 6))

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

        if (self.name == tag_stco):
            stco_copy(in_fh, out_fh, self, delta)
        elif (self.name == tag_co64):
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
            if (element.name == "mdat" and loaded_mpeg4.first_mdat_box is None):
                loaded_mpeg4.first_mdat_box = element
            if (element.name == "ftyp"):
                loaded_mpeg4.ftyp_box = element

        if (loaded_mpeg4.moov_box is None):
            print ("Error, file does not contain moov box.")
            return None

        if (loaded_mpeg4.first_mdat_box is None):
            print ("Error, file does not contain mdat box.")
            return None

        loaded_mpeg4.first_mdat_position = loaded_mpeg4.first_mdat_box.position
        loaded_mpeg4.first_mdat_position += loaded_mpeg4.first_mdat_box.header_size

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
            if element.name == tag_mdat:
                new_position += element.header_size
                break
            new_position += element.size()
        delta = new_position - self.first_mdat_position

        for element in self.contents:
            element.save(in_fh, out_fh, delta)


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


def ffmpeg():
    """Returns whether ffmpeg is installed on the system.

    Returns:
      Bool, whether ffmpeg is available on the host system.
    """
    program = "ffmpeg"

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return True
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip("\"")
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return True
    return False


def ParseSphericalMKV(file_name):
    """Extracts spherical metadata from MKV file using ffmpeg. Uses ffmpeg.

    Args:
      file_name: string, file for parsing spherical metadata.
    """
    process = subprocess.Popen(["ffmpeg", "-i", file_name],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    index = err.find("spherical-video")
    if (index == -1):
        index = err.find("SPHERICAL-VIDEO")

    if (index == -1):
        return

    sub_err = err[index:]
    lines = sub_err.split("\n")
    xml_contents = []

    if lines[0].find(":") == -1:
        return

    xml_contents.append(lines[0][lines[0].index(":") + 2:])
    for line in lines[1:]:
        index = line.find(":")
        if index == -1:
            break

        prefix = line[:index]
        if re.match("^[ ]*$", prefix):
            xml_contents.append(line[index + 2:])
        else:
            break
    xml_contents = "\n".join(xml_contents)
    ParseSphericalXML(xml_contents)


def ParseSphericalXML(contents):
    """Prints spherical metadata for a set of xml data.

    Args:
      contents: string, spherical metadata xml contents.
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
            print "\t\tWarning missing rdf prefix:", rdf_prefix
        except xml.etree.ElementTree.ParseError as e:
            print "\t\tParser Error on XML"
            print e
            print contents
            return

    for child in parsed_xml.getchildren():
        if child.tag in spherical_tags.keys():
            print "\t\tFound:", spherical_tags[child.tag], "=", child.text
        else:
            tag = child.tag
            if (child.tag[:len(spherical_prefix)] == spherical_prefix):
                tag = child.tag[len(spherical_prefix):]
            print "\t\tUnknown:", tag, "=", child.text


def ParseSphericalMpeg4(mpeg4_file, fh):
    """Prints spherical metadata for a loaded mpeg4 file.

    Args:
      mpeg4_file: mpeg4, loaded mpeg4 file contents.
      fh: file handle, file handle for uncached file contents.
    """
    track_num = 0
    for element in mpeg4_file.moov_box.contents:
        if element.name == tag_trak:
            print "\tTrack", track_num
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
                        ParseSphericalXML(contents)


def PrintMpeg4(input_file):
    in_fh = open(input_file, "rb")
    if in_fh is None:
        print ("File: \"", input_file, "\" does not exist or do not have "
               "permission.")
        return

    mpeg4_file = mpeg4.load(in_fh)
    if (mpeg4_file is None):
        return

    print "Loaded file settings"
    ParseSphericalMpeg4(mpeg4_file, in_fh)
    return


def InjectMpeg4(input_file, output_file, metadata):
    in_fh = open(input_file, "rb")
    if in_fh is None:
        print ("File: \"", input_file, "\" does not exist or do not have "
               "permission.")
        return

    mpeg4_file = mpeg4.load(in_fh)
    if (mpeg4_file is None):
        return

    if not mpeg4_add_spherical(mpeg4_file, in_fh, metadata):
        print "Failed to insert spherical data"
        return

    print "Saved file settings"
    ParseSphericalMpeg4(mpeg4_file, in_fh)

    out_fh = open(output_file, "wb")
    mpeg4_file.save(in_fh, out_fh)
    out_fh.close()
    in_fh.close()


def PrintMKV(input_file):
    if not ffmpeg():
        print "please install ffmpeg for mkv support"
        exit(0)

    print "Loaded file settings"
    ParseSphericalMKV(input_file)

def InjectMKV(input_file, output_file, metadata):
    if not ffmpeg():
        print "please install ffmpeg for mkv support"
        exit(0)

    process = subprocess.Popen(
        ["ffmpeg", "-i", input_file, "-metadata:s:v",
         "spherical-video=" + metadata, "-c:v", "copy",
         "-c:a", "copy", output_file], stderr=subprocess.PIPE,
        stdout=subprocess.PIPE)
    print "Press y <enter> to confirm overwrite"
    process.wait()
    stdout, stderr = process.communicate()
    print "Saved file settings"
    ParseSphericalMKV(output_file)


def PrintMetadata(src):
    infile = os.path.abspath(src)

    try:
        in_fh = open(infile, "rb")
        in_fh.close()
    except:
        print "Error: ", infile, " does not exist or we do not have permission"
        return

    print "Processing: ", infile, "\n"

    if (os.path.splitext(infile)[1].lower() in [".webm", ".mkv"]):
        PrintMKV(infile)
        return

    if (os.path.splitext(infile)[1].lower() == ".mp4"):
        PrintMpeg4(infile)
        return

    print "Unknown file type"
    return


def InjectMetadata(src, dest, metadata):
    infile = os.path.abspath(src)
    outfile = os.path.abspath(dest)

    if (infile == outfile):
        print "Input and output cannot be the same"
        return

    try:
        in_fh = open(infile, "rb")
        in_fh.close()
    except:
        print "Error: ", infile, " does not exist or we do not have permission"
        return

    print "Processing: ", infile, "\n"

    if (os.path.splitext(infile)[1].lower() in [ ".webm", ".mkv"]):
        InjectMKV(infile, outfile, metadata)
        return

    if (os.path.splitext(infile)[1].lower() == ".mp4"):
        InjectMpeg4(infile, outfile, metadata)
        return

    print "Unknown file type"
    return


def main():
    """Main function for printing / injecting spherical metadata."""

    parser = OptionParser(usage="%prog [options] [files...]\n\n"
                                "By default prints out spherical metadata from"
                                "specified files.")
    parser.add_option("-i", "--inject",
                      action="store_true",
                      help="injects spherical metadata into a MP4/WebM file, "
                           "saving the result to a new file")
    parser.add_option("-s", "--stereo",
                      type="choice",
                      action="store",
                      dest="stereo",
                      choices=["none", "top-bottom", "left-right",],
                      default="none",
                      help="stereo frame order (top-bottom|left-right)",)
    parser.add_option("-c", "--crop",
                      type="string",
                      action="store",
                      default=None,
                      help=("crop region. Must specify 6 integers in the form "
                            "of \"w:h:f_w:f_h:x:y\" where "
                            "w=CroppedAreaImageWidthPixels "
                            "h=CroppedAreaImageHeightPixels "
                            "f_w=FullPanoWidthPixels "
                            "f_h=FullPanoHeightPixels "
                            "x=CroppedAreaLeftPixels "
                            "y=CroppedAreaTopPixels"),)

    (opts, args) = parser.parse_args()

    # Configure inject xml.
    additional_xml = ""
    if opts.stereo == "top-bottom":
        additional_xml += spherical_xml_contents_top_bottom

    if opts.stereo == "left-right":
        additional_xml += spherical_xml_contents_left_right

    if opts.crop:
        crop_match = re.match(crop_regex, opts.crop)
        if not crop_match:
            print "Error: Invalid crop params: {crop}".format(crop=opts.crop)
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
                print ("Error with crop params: full pano dimensions are "
                       "invalid: width = {width} height = {height}".format(
                           width=full_width_pixels, height=full_height_pixels))
                return

            if (cropped_width_pixels <= 0 or
                cropped_height_pixels <= 0 or
                cropped_width_pixels > full_width_pixels or
                cropped_height_pixels > full_height_pixels):
                print ("Error with crop params: cropped area dimensions are "
                       "invalid: width = {width} height = {height}".format(
                           width=cropped_width_pixels,
                           height=cropped_height_pixels))
                return

            # We are pretty restrictive and don't allow anything strange. There
            # could be use-cases for a horizontal offset that essentially
            # translates the domain, but we don't support this (so that no extra
            # work has to be done on the client).
            total_width = cropped_offset_left_pixels + cropped_width_pixels
            total_height = cropped_offset_top_pixels + cropped_height_pixels
            if (cropped_offset_left_pixels < 0 or
                cropped_offset_top_pixels < 0 or
                total_width > full_width_pixels or
                total_height > full_height_pixels):
                print ("Error with crop params: cropped area offsets are "
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

    if opts.inject:
        if len(args) != 2:
            print "Injecting metadata requires both a source and destination."
            return
        InjectMetadata(args[0], args[1], spherical_xml)
        return

    if len(args) > 0:
        for src in args:
            PrintMetadata(src)
        return

    parser.print_help()
    return


if __name__ == "__main__":
    main()
