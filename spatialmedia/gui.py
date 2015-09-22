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

import ntpath
import os
import sys
path = os.path.dirname(sys.modules[__name__].__file__)
path = os.path.join(path, '..')
sys.path.insert(0, path)

from spatialmedia import spherical
import tkFileDialog

try:
    from Tkinter import *
except ImportError:
    try:
        from tkinter import *
    except ImportError:
        print("Tkinter library is not available.")
        exit(0)

class Console(object):
  def __init__(self):
    self.log = []

  def append(self, text):
    print text
    self.log.append(text)



class Application(Frame):
    def action_open(self):
        """Triggers open file diaglog, reading a new file's metadata."""
        tmp_in_file = tkFileDialog.askopenfilename(**self.open_options)
        if not tmp_in_file:
          return
        self.in_file = tmp_in_file

        self.set_message("Opened file: %s\n" % ntpath.basename(self.in_file))

        console = Console()
        metadata = spherical.parse_metadata(self.in_file, console.append)

        for line in console.log:
          print line
          if "Error" in line:
            self.set_error("Failed to load file %s" % ntpath.basename(self.in_file))
            self.var_spherical.set(0)
            self.disable_state()
            self.button_open.configure(state="normal")
            self.button_quit.configure(state="normal")
            return

        self.enable_state()
        self.checkbox_spherical.configure(state="normal")

        if not metadata:
            self.set_message("No metadata found.")

        if metadata:
            metadata = metadata.itervalues().next()
            self.var_spherical.set(1)

            self.set_message("Metadata found in %s\n" % ntpath.basename(self.in_file))
            if "Spherical" in metadata and metadata["Spherical"] == "true":
                self.var_spherical.set(1)
            else:
              self.var_spherical.set(0)

            if "StereoMode" in metadata and metadata["StereoMode"] == "top-bottom":
                self.var_3d.set(1)
            else:
                self.var_3d.set(0)
        else:
              self.set_message("No metadata found in %s\n" % ntpath.basename(self.in_file))
              self.var_spherical.set(0)
              self.var_3d.set(0)

        self.update_state()


    def action_inject_delay(self):
        stereo = None
        if (self.var_3d.get()):
          stereo = "top-bottom"

        xml = spherical.generate_spherical_xml(stereo=stereo)

        console = Console()
        spherical.inject_metadata(self.in_file, self.save_file, xml, console.append)
        self.set_message("Successfully saved file to %s\n" % ntpath.basename(self.save_file))
        self.button_open.configure(state="normal")
        self.button_quit.configure(state="normal")
        self.update_state()

    def action_inject(self):
        """Inject metadata into a new save file."""
        baseFileName = os.path.splitext(ntpath.basename(self.in_file))[0]
        self.save_options["initialfile"] = baseFileName + "_injected.mp4"
        self.save_file = tkFileDialog.asksaveasfilename(**self.save_options)
        if not self.save_file:
          return

        self.set_message("Saving file to %s\n" % ntpath.basename(self.save_file))

        self.disable_state()
        self.master.after(100, self.action_inject_delay)

    def action_set_spherical(self):
        self.update_state()

    def action_set_3d(self):
        self.update_state()

    def enable_state(self):
        self.button_open.configure(state="normal")
        self.button_quit.configure(state="normal")

    def disable_state(self):
        self.checkbox_spherical.configure(state="disabled")
        self.checkbox_3D.configure(state="disabled")
        self.options_projection.configure(state="disabled")
        self.button_inject.configure(state="disabled")
        self.button_open.configure(state="disabled")
        self.button_quit.configure(state="disabled")

    def update_state(self):
        self.checkbox_spherical.configure(state="normal")
        if self.var_spherical.get():
            self.checkbox_3D.configure(state="normal")
            self.options_projection.configure(state="normal")
            self.button_inject.configure(state="normal")
        else:
            self.checkbox_3D.configure(state="disabled")
            self.options_projection.configure(state="disabled")
            self.button_inject.configure(state="disabled")

    def set_error(self, text):
        self.label_message["text"] = text
        self.label_message.config(fg="red")

    def set_message(self, text):
        self.label_message["text"] = text
        self.label_message.config(fg="green")

    def create_widgets(self):
        """Sets up GUI contents."""

        row = 0
        column = 0

        titleFont = ('time', 12, 'bold')

        # Spherical Checkbox
        self.label_spherical = Label(self)
        self.label_spherical["text"] = "Spherical"
        self.label_spherical.grid(row=row, column=column)
        column +=1

        self.var_spherical = IntVar()
        self.checkbox_spherical = Checkbutton(self, variable=self.var_spherical)
        self.checkbox_spherical["command"] = self.action_set_spherical
        self.checkbox_spherical.grid(row=row, column=column, padx=14, pady=2)

        # 3D
        column = 0
        row = row + 1
        self.label_3D = Label(self)
        self.label_3D["text"] = "3D Top-bottom"
        self.label_3D.grid(row=row, column=column, padx=14, pady=2)
        column +=1

        self.var_3d = IntVar()
        self.checkbox_3D = Checkbutton(self, variable=self.var_3d)
        self.checkbox_3D["command"] = self.action_set_3d
        self.checkbox_3D.grid(row=row, column=column, padx=14, pady=2)

        # Projection
        column = 0
        row = row + 1
        self.label_projection = Label(self)
        self.label_projection["text"] = "Projection"
        self.label_projection.grid(row=row, column=column, padx=14, pady=2)
        column+=1

        self.options_projection = Label(self)
        self.options_projection["text"] = "Equirectangular"
        self.options_projection.grid(row=row, column=column, padx=14, pady=2)

        # Message Box
        row = row + 1
        column = 0
        self.label_message = Label(self)
        self.label_message["text"] = ""
        self.label_message.grid(row=row, column=column, rowspan=1, columnspan=2, padx=14, pady=2)

        # Button Frame
        column = 0
        row = row + 1
        buttons_frame = Frame(self)
        buttons_frame.grid(row=row, column=0, columnspan=3, padx=14, pady=2)

        self.button_open = Button(buttons_frame)
        self.button_open["text"] = "Open"
        self.button_open["fg"] = "black"
        self.button_open["command"] = self.action_open
        self.button_open.grid(row=0, column=0, padx=14, pady=2)

        self.button_inject = Button(buttons_frame)
        self.button_inject["text"] = "Save as"
        self.button_inject["fg"] = "black"
        self.button_inject["command"] = self.action_inject
        self.button_inject.grid(row=0, column=1, padx=14, pady=2)

        self.button_quit = Button(buttons_frame)
        self.button_quit["text"] = "Quit"
        self.button_quit["fg"] = "black"
        self.button_quit["command"] = self.quit
        self.button_quit.grid(row=0, column=2, padx=14, pady=2)


    def __init__(self, master=None):
        master.wm_title("Spherical Metadata Injector")
        master.config(menu=Menu(master))
        self.title = "Spherical Metadata Tool"
        self.open_options = {}
        self.open_options["filetypes"] = [("Mp4", ".mp4")]
        self.open_options["defaultextension"] =".mp4"

        self.save_options = {}
        self.save_options["filetypes"] = [("Mp4", ".mp4")]
        self.save_options["defaultextension"] =".mp4"

        Frame.__init__(self, master)
        self.create_widgets()
        self.pack()

        self.in_file = None
        self.disable_state()
        self.enable_state()
        master.attributes("-topmost", True)
        master.focus_force()
        self.after(50, lambda: master.attributes("-topmost", False))

def main():
    root = Tk()
    app = Application(master=root)
    app.mainloop()

if __name__ == "__main__":
    main()
