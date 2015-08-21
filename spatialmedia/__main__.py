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

import sys
import os
path = os.path.dirname(sys.modules[__name__].__file__)
path = os.path.join(path, '..')
sys.path.insert(0, path)

from spatialmedia import spherical
import re

def console(contents):
    print (contents)


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
                      choices=["none", "top-bottom", "left-right"],
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

    spherical_xml = spherical.GenerateSphericalXML(opts.stereo, opts.crop)

    if opts.inject:
        if len(args) != 2:
            console("Injecting metadata requires both"
                    "a source and destination.")
            return
        spherical.InjectMetadata(args[0], args[1], spherical_xml, console)
        return

    if len(args) > 0:
        for src in args:
            spherical.ParseMetadata(src, console)
        return

    parser.print_help()
    return


if __name__ == "__main__":
    main()
