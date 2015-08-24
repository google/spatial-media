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

"""MPEG processing classes.

Tool for loading mpeg4 files and manipulating atoms.
"""

TRAK_TYPE_VIDE = "vide"

# Leaf types.
TAG_STCO = "stco"
TAG_CO64 = "co64"
TAG_FREE = "free"
TAG_MDAT = "mdat"
TAG_XML = "xml "
TAG_HDLR = "hdlr"
TAG_FTYP = "ftyp"

# Container types.
TAG_MOOV = "moov"
TAG_UDTA = "udta"
TAG_META = "meta"
TAG_TRAK = "trak"
TAG_MDIA = "mdia"
TAG_MINF = "minf"
TAG_STBL = "stbl"
TAG_UUID = "uuid"

CONTAINERS_LIST = [TAG_MOOV, TAG_UDTA, TAG_TRAK,
              TAG_MDIA, TAG_MINF, TAG_STBL]


