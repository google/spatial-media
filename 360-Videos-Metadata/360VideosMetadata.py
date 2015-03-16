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

spherical_xml = (
    "<?xml version=\"1.0\"?>\n"
    "<rdf:SphericalVideo"
    " xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\""
    " xmlns:GSpherical=\"http://ns.google.com/videos/1.0/spherical/\">\n"
    "  <GSpherical:Spherical>true</GSpherical:Spherical>\n"
    "  <GSpherical:Stitched>true</GSpherical:Stitched>\n"
    "  <GSpherical:StitchingSoftware>Spherical Metadata Tool"
    "</GSpherical:StitchingSoftware>\n"
    "  <GSpherical:ProjectionType>equirectangular"
    "</GSpherical:ProjectionType>\n"
    "</rdf:SphericalVideo>")

spherical_tags_list = [
    "Spherical",
    "Stitched",
    "StitchingSoftware",
    "ProjectionType",
    "SourceCount",
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


class atom:
    """MPEG4 atom contents and behaviour true for all atoms."""

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
        """Loads the atom located at a position in a mp4 file.

        Args:
          fh: file handle, input file handle.
          position: int or None, current file position.

        Returns:
          atom: atom, atom from loaded file location or None.
        """
        if (position is None):
            position = fh.tell()

        fh.seek(position)
        header_size = 8
        size = struct.unpack(">I", fh.read(4))[0]
        name = fh.read(4)

        if (name in containers):
            return container_atom.load(fh, position, end)

        if (size == 1):
            size = struct.unpack(">Q", fh.read(8))[0]
            header_size = 16

        if (size < 8):
            print "Error, invalid size in ", name, " at ", position
            return None

        if (position + size > end):
            print ("Error: Leaf atom size exceeds bounds.")
            return None

        new_atom = atom()
        new_atom.name = name
        new_atom.position = position
        new_atom.header_size = header_size
        new_atom.content_size = size - header_size
        new_atom.contents = None

        return new_atom

    @staticmethod
    def load_multiple(fh, position=None, end=None):
        loaded = list()
        while (position < end):
            new_atom = atom.load(fh, position, end)
            if (new_atom is None):
                print ("Error, failed to load atom.")
                return None
            loaded.append(new_atom)
            position = new_atom.position + new_atom.size()

        return loaded

    def save(self, in_fh, out_fh, delta):
        """Save an atoms contents prioritizing set contents and specialized
        beahviour for stco/co64 atoms.

        Args:
          in_fh: file handle, source to read atom contents from.
          out_fh: file handle, destination for written atom contents.
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
        """Sets the atom contents. This can be used to change an atom's
        contents"""
        contents = new_contents
        content_size = len(contents)

    def size(self):
        """Total size of a atom.

        Returns:
          Int, total size in bytes of the atom.
        """
        return self.header_size + self.content_size

    def print_structure(self, indent=""):
        """Prints the atom structure."""
        size1 = self.header_size
        size2 = self.content_size
        print indent, self.name, " [", size1, ", ", size2, " ]"


class container_atom(atom):
    """MPEG4 container atom contents / behaviour."""

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
            print ("Error: Container atom size exceeds bounds.")
            return None

        new_atom = container_atom()
        new_atom.name = name
        new_atom.position = position
        new_atom.header_size = header_size
        new_atom.content_size = size - header_size
        new_atom.contents = atom.load_multiple(
            fh, position + header_size, position + size)

        if (new_atom.contents is None):
            return None

        return new_atom

    def resize(self):
        """Recomputes the atom size and recurses on contents."""
        self.content_size = 0
        for element in self.contents:
            if isinstance(element, container_atom):
                element.resize()
            self.content_size += element.size()

    def print_structure(self, indent=""):
        """Prints the atom structure and recurses on contents."""
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
                if isinstance(element, container_atom):
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
        assert(isinstance(element, container_atom))
        for sub_element in element.contents:
            if not self.add(sub_element):
                return False

        return True

    def save(self, in_fh, out_fh, delta):
        """Saves atom structure to out_fh reading uncached content from
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

    # Large sizes must be incremental on windows.
    max_size = 64 * 1024 * 1024
    while (size > max_size):
      contents = in_fh.read(max_size)
      out_fh.write(contents)
      size = size - max_size

    contents = in_fh.read(size)
    out_fh.write(contents)


def index_copy(in_fh, out_fh, atom, mode, mode_length, delta=0):
    """Update and copy index table for stco/co64 files.

    Args:
      in_fh: file handle, source to read index table from.
      out_fh: file handle, destination for index file.
      atom: atom, stco/co64 atom to copy.
      mode: string, bit packing mode for index entries.
      mode_length: int, number of bytes for index entires.
      delta: int, offset change for index entries.
    """
    fh = in_fh
    if not atom.contents:
        fh.seek(atom.content_start())
    else:
        fh = StringIO.StringIO(atom.contents)

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


def stco_copy(in_fh, out_fh, atom, delta=0):
    """Copy for stco atom.

    Args:
      in_fh: file handle, source to read index table from.
      out_fh: file handle, destination for index file.
      atom: atom, stco atom to copy.
      delta: int, offset change for index entries.
    """
    index_copy(in_fh, out_fh, atom, ">I", 4, delta)


def co64_copy(in_fh, out_fh, atom, delta=0):
    """Copy for co64 atom.

    Args:
      in_fh: file handle, source to read index table from.
      out_fh: file handle, destination for index file.
      atom: atom, co64 atom to copy.
      delta: int, offset change for index entries.
    """
    index_copy(in_fh, out_fh, atom, ">Q", 8, delta)


class mpeg4(container_atom):
    """Specialized behaviour for the root mpeg4 container"""

    def __init__(self):
        self.contents = list()
        self.content_size = 0
        self.header_size = 0
        self.moov_atom = None
        self.free_atom = None
        self.mdat_atom = None
        self.ftyp_atom = None
        self.mdat_position = None

    @staticmethod
    def load(fh, position, size):
        """Load the mpeg4 file structure of a file.

        Args:
          fh: file handle, input file handle.
          position: int, current file position.
          size: int, maximum size. This is used to ensure correct atom sizes.

        return:
          mpeg4, the loaded mpeg4 structure.
        """
        contents = atom.load_multiple(fh, position, size)

        if (contents is None):
            print "Error, failed to load .mp4 file."
            return None

        if (len(contents) == 0):
            print ("Error, no atoms found.")
            return None

        loaded_mpeg4 = mpeg4()
        loaded_mpeg4.contents = contents

        for element in loaded_mpeg4.contents:
            if (element.name == "moov"):
                loaded_mpeg4.moov_atom = element
            if (element.name == "free"):
                loaded_mpeg4.free_atom = element
            if (element.name == "mdat"):
                loaded_mpeg4.mdat_atom = element
            if (element.name == "ftyp"):
                loaded_mpeg4.ftyp_atom = element

        if (loaded_mpeg4.moov_atom is None):
            print ("Error, file does not contain moov atom.")
            return None

        if (loaded_mpeg4.mdat_atom is None):
            print ("Error, file does not contain mdat atom.")
            return None

        loaded_mpeg4.mdat_position = loaded_mpeg4.mdat_atom.position
        loaded_mpeg4.mdat_position += loaded_mpeg4.mdat_atom.header_size

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
        delta = new_position - self.mdat_position

        for element in self.contents:
            element.save(in_fh, out_fh, delta)


def spherical_uuid():
    """Constructs a uuid containing spherical metadata.

    Returns:
      uuid_leaf: a atom containing spherical metadata.
    """
    uuid_leaf = atom()
    assert(len(spherical_uuid_id) == 16)
    uuid_leaf.name = tag_uuid
    uuid_leaf.header_size = 8
    uuid_leaf.content_size = 0

    uuid_leaf.contents = spherical_uuid_id + spherical_xml
    uuid_leaf.content_size = len(uuid_leaf.contents)

    return uuid_leaf


def mpeg4_add_spherical(mpeg4_file, in_fh):
    """Adds a spherical uuid atom to an mpeg4 file for all video tracks.

    Args:
      mpeg4_file: mpeg4, Mpeg4 file structure to add spherical
      metadata.
      in_fh: file handle, Source for uncached file contents.
    """
    for element in mpeg4_file.moov_atom.contents:
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
                    if not element.add(spherical_uuid()):
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
            path = path.strip('"')
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

    start = xml_contents.find('"') + 1
    end = xml_contents.rfind('"')
    xml_contents = xml_contents[start: end]

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
    for element in mpeg4_file.moov_atom.contents:
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


def ProcessMpeg4(input_file, output_file=None):
    in_fh = open(input_file, "rb")
    if in_fh is None:
        print ("File: \"", input_file, "\" does not exist or do not have "
               "permission.")
        return

    position = 0
    in_fh.seek(0, 2)
    total_size = in_fh.tell()

    mpeg4_file = mpeg4.load(in_fh, 0, total_size)
    if (mpeg4_file is None):
        return

    if not output_file:
        print "Loaded file settings"
        ParseSphericalMpeg4(mpeg4_file, in_fh)
        return

    if not mpeg4_add_spherical(mpeg4_file, in_fh):
        print "Failed to insert spherical data"
        return

    print "Saved file settings"
    ParseSphericalMpeg4(mpeg4_file, in_fh)

    out_fh = open(output_file, "wb")
    mpeg4_file.save(in_fh, out_fh)
    out_fh.close()
    in_fh.close()


def ProcessMKV(input_file, output_file=None):
    if not ffmpeg():
        print "please install ffmpeg for mkv support"
        exit(0)

    if (not output_file):
        print "Loaded file settings"
        ParseSphericalMKV(input_file)
    else:
        process = subprocess.Popen(
            ["ffmpeg", "-i", input_file, "-metadata:s:v",
             'spherical-video=\"' + spherical_xml + '\"', "-c:v", "copy",
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
        ProcessMKV(infile, None)
        return

    if (os.path.splitext(infile)[1].lower() == ".mp4"):
        ProcessMpeg4(infile, None)
        return

    print "Unknown file type"
    return


def InjectMetadata(src, dest):
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
        ProcessMKV(infile, outfile)
        return

    if (os.path.splitext(infile)[1].lower() == ".mp4"):
        ProcessMpeg4(infile, outfile)
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
    (opts, args) = parser.parse_args()

    if opts.inject:
        if len(args) != 2:
            print "Injecting metadata requires both a source and destination."
            return
        InjectMetadata(args[0], args[1])
        return

    if len(args) > 0:
        for src in args:
            PrintMetadata(src)
        return

    parser.print_help()
    return


if __name__ == "__main__":
    main()
