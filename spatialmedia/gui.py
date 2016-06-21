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
import tkFileDialog
import tkMessageBox
import traceback

try:
    from Tkinter import *
except ImportError:
    print("Tkinter library is not available.")
    exit(0)

path = os.path.dirname(sys.modules[__name__].__file__)
path = os.path.join(path, '..')
sys.path.insert(0, path)
from spatialmedia import metadata_utils 


class Console(object):
    def __init__(self):
        self.log = []

    def append(self, text):
        print(text.encode('utf-8'))
        self.log.append(text)


class Application(Frame):
    def action_open(self):
        """Triggers open file diaglog, reading a new file's metadata."""
        tmp_in_file = tkFileDialog.askopenfilename(**self.open_options)
        if not tmp_in_file:
            return
        self.in_file = tmp_in_file

        self.set_message("Current 360 video: %s" % ntpath.basename(self.in_file))

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
                self.set_error("Failed to load file %s"
                               % ntpath.basename(self.in_file))
                self.var_spherical.set(0)
                self.var_spatial_audio.set(0)
                self.disable_state()
                self.button_open.configure(state="normal")
                return

        self.enable_state()

        infile = os.path.abspath(self.in_file)
        file_extension = os.path.splitext(infile)[1].lower()

        self.var_spherical.set(1)
        self.enable_spatial_audio = parsed_metadata.num_audio_channels == 4

        if not metadata:
            self.var_3d.set(0)

        if not audio_metadata:
            self.var_spatial_audio.set(0)

        if metadata:
            metadata = metadata.itervalues().next()

            if metadata.get("Spherical", "") == "true":
                self.var_spherical.set(1)
            else:
                self.var_spherical.set(0)

            if metadata.get("StereoMode", "") == "top-bottom":
                self.var_3d.set(1)
            else:
                self.var_3d.set(0)

        if audio_metadata:
            self.var_spatial_audio.set(1)
            print audio_metadata.get_metadata_string()

        self.update_state()

    def action_inject_delay(self):
        stereo = None
        if (self.var_3d.get()):
            stereo = "top-bottom"

        metadata = metadata_utils.Metadata()
        metadata.video = metadata_utils.generate_spherical_xml(stereo=stereo)

        if self.var_spatial_audio.get():
            metadata.audio = metadata_utils.SPATIAL_AUDIO_DEFAULT_METADATA 

        console = Console()
        metadata_utils.inject_metadata(
            self.in_file, self.save_file, metadata, console.append)
        self.set_message("Successfully saved file to %s\n"
                         % ntpath.basename(self.save_file))
        self.button_open.configure(state="normal")
        self.update_state()

    def action_inject(self):
        """Inject metadata into a new save file."""
        split_filename = os.path.splitext(ntpath.basename(self.in_file))
        base_filename = split_filename[0]
        extension = split_filename[1]
        self.save_options["initialfile"] = (base_filename
                                            + "_injected" + extension)
        self.save_file = tkFileDialog.asksaveasfilename(**self.save_options)
        if not self.save_file:
            return

        self.set_message("Saving file to %s" % ntpath.basename(self.save_file))

        # Launch injection on a separate thread after disabling buttons.
        self.disable_state()
        self.master.after(100, self.action_inject_delay)

    def action_set_spherical(self):
        self.update_state()

    def action_set_spatial_audio(self):
        self.update_state()

    def action_set_3d(self):
        self.update_state()

    def enable_state(self):
        self.button_open.configure(state="normal")

    def disable_state(self):
        self.checkbox_spatial_audio.configure(state="disabled")
        self.checkbox_3D.configure(state="disabled")
        self.button_inject.configure(state="disabled")
        self.button_open.configure(state="disabled")

    def update_state(self):
        if self.var_spherical.get():
            self.checkbox_3D.configure(state="normal")
            self.button_inject.configure(state="normal")
            if self.enable_spatial_audio:
                self.checkbox_spatial_audio.configure(state="normal")
        else:
            self.checkbox_3D.configure(state="disabled")
            self.button_inject.configure(state="disabled")
            self.checkbox_spatial_audio.configure(state="disabled")

    def set_error(self, text):
        self.label_message["text"] = text
        self.label_message.config(fg="red")

    def set_message(self, text):
        self.label_message["text"] = text
        self.label_message.config(fg="blue")

    def create_widgets(self):
        """Sets up GUI contents."""

        row = 0
        column = 0

        self.var_spherical = IntVar()

        PAD_X = 10

        row = row + 1
        column = 0
        self.label_message = Label(self)
        self.label_message["text"] = "Click Open to open your 360 video."
        self.label_message.grid(row=row, column=column, rowspan=1,
                                columnspan=2, padx=PAD_X, pady=10, sticky=W)

        row = row + 1
        separator = Frame(self, relief=GROOVE, bd=1, height=2, bg="white")
        separator.grid(columnspan=row, padx=PAD_X, pady=4, sticky=N+E+S+W)

        # 3D
        row = row + 1
        self.label_3D = Label(self, anchor=W)
        self.label_3D["text"] = "My video is stereoscopic 3D (top/bottom layout)"
        self.label_3D.grid(row=row, column=column, padx=PAD_X, pady=7, sticky=W)
        column += 1

        self.var_3d = IntVar()
        self.checkbox_3D = Checkbutton(self, variable=self.var_3d)
        self.checkbox_3D["command"] = self.action_set_3d
        self.checkbox_3D.grid(row=row, column=column, padx=PAD_X, pady=2)

        # Spatial Audio Checkbox
        row += 1
        column = 0
        self.label_spatial_audio = Label(self, anchor=W)
        self.label_spatial_audio["text"] = "My video has spatial audio (ambiX ACN/SN3D format)"
        self.label_spatial_audio.grid(row=row, column=column, padx=PAD_X, pady=7, sticky=W)

        column += 1
        self.var_spatial_audio = IntVar()
        self.checkbox_spatial_audio = \
            Checkbutton(self, variable=self.var_spatial_audio)
        self.checkbox_spatial_audio["command"] = self.action_set_spatial_audio
        self.checkbox_spatial_audio.grid(
            row=row, column=column, padx=0, pady=0)

        row = row + 1
        separator = Frame(self, relief=GROOVE, bd=1, height=2, bg="white")
        separator.grid(columnspan=row, padx=PAD_X, pady=10, sticky=N+E+S+W)

        # Button Frame
        column = 0
        row = row + 1
        buttons_frame = Frame(self)
        buttons_frame.grid(row=row, column=0, columnspan=3, padx=PAD_X, pady=10)

        self.button_open = Button(buttons_frame)
        self.button_open["text"] = "Open"
        self.button_open["fg"] = "black"
        self.button_open["command"] = self.action_open
        self.button_open.grid(row=0, column=0, padx=14, pady=2)

        self.button_inject = Button(buttons_frame)
        self.button_inject["text"] = "Inject metadata"
        self.button_inject["fg"] = "black"
        self.button_inject["command"] = self.action_inject
        self.button_inject.grid(row=0, column=1, padx=14, pady=2)

    def __init__(self, master=None):
        master.wm_title("Spatial Media Metadata Injector")
        master.config(menu=Menu(master))
        self.title = "Spatial Media Metadata Injector"
        self.open_options = {}
        self.open_options["filetypes"] = [("Videos", ("*.mov", "*.mp4"))]

        self.save_options = {}

        Frame.__init__(self, master)
        self.create_widgets()
        self.pack()

        self.in_file = None
        self.disable_state()
        self.enable_state()
        master.attributes("-topmost", True)
        master.focus_force()
        self.after(50, lambda: master.attributes("-topmost", False))
        self.enable_spatial_audio = False

def report_callback_exception(self, *args):
    exception = traceback.format_exception(*args)
    tkMessageBox.showerror("Error", exception)

def main():
    root = Tk()
    Tk.report_callback_exception = report_callback_exception
    app = Application(master=root)
    app.mainloop()

if __name__ == "__main__":
    main()
