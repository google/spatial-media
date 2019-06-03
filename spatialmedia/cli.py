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

"""Spatial Media Metadata Injector GUI

GUI application for examining/injecting spatial media metadata in MP4/MOV files.
"""

import ntpath
import os
import sys
# import tkFileDialog
# import tkMessageBox
import traceback
import argparse

# try:
#     from Tkinter import *
# except ImportError:
#     print("Tkinter library is not available.")
#     exit(0)

path = os.path.dirname(sys.modules[__name__].__file__)
path = os.path.join(path, '..')
sys.path.insert(0, path)
from spatialmedia import metadata_utils

SPATIAL_AUDIO_LABEL = "My video has spatial audio (ambiX ACN/SN3D format)"
HEAD_LOCKED_STEREO_LABEL = "with head-locked stereo"

class Console(object):
    def __init__(self):
        self.log = []

    def append(self, text):
        print(text.encode('utf-8'))
        self.log.append(text)


class Application():
    def action_open(self, file_location):
        """Triggers open file diaglog, reading a new file's metadata."""
        tmp_in_file = file_location
        if not tmp_in_file:
            return
        self.in_file = tmp_in_file

        print("Current 360 video: %s" % ntpath.basename(self.in_file))

        console = Console()
        parsed_metadata = metadata_utils.parse_metadata(self.in_file,
                                                        console.append)

        metadata = None
        audio_metadata = None
        if parsed_metadata:
            metadata = parsed_metadata.video
            audio_metadata = parsed_metadata.audio

        for line in console.log:
            if "Error" in line:
                print("Failed to load file %s"
                               % ntpath.basename(self.in_file))
                self.var_spherical = False
                self.var_spatial_audio = False
                return

        if audio_metadata:
            print(audio_metadata.get_metadata_string())

    def action_inject_delay(self):
        stereo = None
        if (self.var_3d):
            stereo = "top-bottom"

        metadata = metadata_utils.Metadata()
        metadata.video = metadata_utils.generate_spherical_xml(stereo=stereo)

        if self.var_spatial_audio:
          metadata.audio = metadata_utils.get_spatial_audio_metadata(
              self.spatial_audio_description.order,
              self.spatial_audio_description.has_head_locked_stereo)

        console = Console()
        metadata_utils.inject_metadata(
            self.in_file, self.save_file, metadata, console.append)
        print("Successfully saved file to %s\n"
                         % ntpath.basename(self.save_file))

    def action_inject(self, save_file_location):
        """Inject metadata into a new save file."""
        # split_filename = os.path.splitext(ntpath.basename(self.in_file))
        # base_filename = split_filename[0]
        # extension = split_filename[1]
        self.save_file = save_file_location
        if not self.save_file:
            return

        print("Saving file to %s" % ntpath.basename(self.save_file))

        # Launch injection on a separate thread after disabling buttons.
        self.action_inject_delay()


    def create_widgets(self):
        """Sets up GUI contents."""
        # self.var_spherical = IntVar()
        # self.var_3d = IntVar()
        # self.var_spatial_audio = IntVar()
        # self.button_open["command"] = self.action_open
        # self.button_inject["command"] = self.action_inject
        pass

    def __init__(self):
        parser = argparse.ArgumentParser(description='Add 3D video metadata')
        parser.add_argument('-i', required=True, help='The input video', type=str)
        parser.add_argument('-o', required=True, help='The output video', type=str)
        parser.add_argument('-s', action='store_true', help='Stereoscopic Top/Bottom Video')
        parser.add_argument('-a', action='store_true', help='Spatial Audio')

        args =  parser.parse_args()

        self.in_file = None
        self.spatial_audio_description = None
        self.var_spherical = True
        self.var_spatial_audio = args.a
        self.var_3d = args.s
        self.action_open(args.i)
        self.action_inject(args.o)
        # self.action_inject()

def report_callback_exception(self, *args):
    exception = traceback.format_exception(*args)
    print(exception)

def main():
    app = Application()

if __name__ == "__main__":
    main()
