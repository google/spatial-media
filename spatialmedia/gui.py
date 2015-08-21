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
Naming conventions are styled to match TKinter naming conventions.
"""

import sys
import os
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


class Application(Frame):
    def open(self):
        """Triggers open file diaglog, reading a new file's metadata."""
        self.in_file = tkFileDialog.askopenfilename(**self.open_options)
        if self.in_file:
            self.set_text("Opened file: %s\n" % self.in_file)
            spherical.ParseMetadata(self.in_file, self.append_text)

    def inject(self):
        """Inject metadata into a new save file."""
        self.save_file = tkFileDialog.asksaveasfilename(**self.open_options)
        if self.save_file:
            self.set_text("Saved file to: %s\n" % self.save_file)
            xml = spherical.GenerateSphericalXML()
            spherical.InjectMetadata(self.in_file, self.save_file, xml, self.append_text)

    def set_text(self, text):
        """Updates text box contents."""
        self.textbox.config(state=NORMAL)
        self.textbox.delete(1.0, END)
        self.textbox.insert(END, text)
        self.textbox.config(state=DISABLED)

    def append_text(self, text):
        self.textbox.config(state=NORMAL)
        self.textbox.insert(END, "\n")
        self.textbox.insert(END, text)
        self.textbox.config(state=DISABLED)

    def create_widgets(self):
        """Sets up GUI contents."""
        self.textbox = Text(self)
        self.textbox.config(state=DISABLED)
        self.textbox.pack({"side": "top"})

        buttons_frame = Frame(self)
        buttons_frame.pack(side=BOTTOM)

        self.button_open = Button(buttons_frame)
        self.button_open["text"] = "Open"
        self.button_open["fg"] = "black"
        self.button_open["command"] = self.open
        self.button_open.pack({"side": "left"})

        self.button_quit = Button(buttons_frame)
        self.button_quit["text"] = "Quit"
        self.button_quit["fg"] = "black"
        self.button_quit["command"] = self.quit
        self.button_quit.pack({"side": "right"})

        self.button_inject = Button(buttons_frame)
        self.button_inject["text"] = "Inject",
        self.button_inject["command"] = self.inject
        self.button_inject.pack({"side": "right"})

    def __init__(self, master=None):
        self.title = "Spherical Metadata Tool"
        self.open_options = {}
        self.open_options["filetypes"] = [("Mp4", ".mp4")]

        Frame.__init__(self, master)
        self.create_widgets()
        self.pack()
        self.open()
        if not self.in_file:
            master.destroy()
            return


def main():
    root = Tk()
    app = Application(master=root)
    app.mainloop()

if __name__ == "__main__":
    main()
