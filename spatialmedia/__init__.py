#!/usr/bin/env python3
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

"""Spatial Media Metadata Tools

Tools for examining and injecting spatial media metadata in MP4/MOV files.
Modernized for Python 3 and macOS Apple Silicon (M series).
"""

__version__ = "2.1.0"
__author__ = "Google Inc."
__license__ = "Apache License 2.0"
__python_requires__ = ">=3.8"

# Ensure the package is available on the current path or is installed.
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

__all__ = ["metadata_utils", "mpeg"]

import spatialmedia.metadata_utils
import spatialmedia.mpeg
