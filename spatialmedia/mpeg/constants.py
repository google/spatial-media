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

"""MPEG-4 constants."""

TRAK_TYPE_VIDE = "vide"

# Leaf types.
TAG_STCO = "stco"
TAG_CO64 = "co64"
TAG_FREE = "free"
TAG_MDAT = "mdat"
TAG_XML = "xml "
TAG_HDLR = "hdlr"
TAG_FTYP = "ftyp"
TAG_ESDS = "esds"
TAG_SOUN = "soun"
TAG_SA3D = "SA3D"

# Container types.
TAG_MOOV = "moov"
TAG_UDTA = "udta"
TAG_META = "meta"
TAG_TRAK = "trak"
TAG_MDIA = "mdia"
TAG_MINF = "minf"
TAG_STBL = "stbl"
TAG_STSD = "stsd"
TAG_UUID = "uuid"

# Sound sample descriptions.
TAG_NONE = "NONE"
TAG_RAW_ = "raw "
TAG_TWOS = "twos"
TAG_SOWT = "sowt"
TAG_FL32 = "fl32"
TAG_FL64 = "fl64"
TAG_IN24 = "in24"
TAG_IN32 = "in32"
TAG_ULAW = "ulaw"
TAG_ALAW = "alaw"
TAG_LPCM = "lpcm"
TAG_MP4A = "mp4a"

SOUND_SAMPLE_DESCRIPTIONS = frozenset([
    TAG_NONE,
    TAG_RAW_,
    TAG_TWOS,
    TAG_SOWT,
    TAG_FL32,
    TAG_FL64,
    TAG_IN24,
    TAG_IN32,
    TAG_ULAW,
    TAG_ALAW,
    TAG_LPCM,
    TAG_MP4A,
    ])

CONTAINERS_LIST = frozenset([
    TAG_MDIA,
    TAG_MINF,
    TAG_MOOV,
    TAG_STBL,
    TAG_STSD,
    TAG_TRAK,
    TAG_UDTA,
    ]).union(SOUND_SAMPLE_DESCRIPTIONS)

