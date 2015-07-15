# Spherical Video RFC (draft)
*This document describes an open metadata scheme by which Matroska-like and MP4 multimedia containers may accommodate spherical video. Comments are welcome on the [webm-discuss](https://groups.google.com/a/webmproject.org/forum/#!forum/webm-discuss) mailing list or [file an issue](https://github.com/google/spatial-media/issues) on GitHub.* 

*Last modified: 2015-02-06*

------------------------------------------------------

## Metadata Format
Two kinds of metadata are needed to represent various characteristics of a spherical video: Global and Local metadata. Global metadata is stored in an XML format, namespaced as <http://ns.google.com/videos/1.0/spherical/>.

Example:

    <rdf:SphericalVideo xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                        xmlns:GSpherical="http://ns.google.com/videos/1.0/spherical/">
    ...
    </rdf:SphericalVideo>


Local metadata is stored either as metadata tracks or along with the video frames (see [Local Metadata](#LocalMetadata) below).

## Global Metadata
Global Metadata is metadata that applies to the file or track as a whole. It is stored in the container as defined in the following sections.


### Matroska/WebM
Global XML metadata is stored using Matroska/WebM's "Tags" mechanism, having the following structure:

- [Tags](http://matroska.org/technical/specs/tagging/index.html#Tags)
    - [Tag](http://matroska.org/technical/specs/tagging/index.html#Tag)
        - [Targets](http://matroska.org/technical/specs/tagging/index.html#Targets)
            - [TargetType](http://matroska.org/technical/specs/tagging/index.html#TargetType)
                - "Track"
            - [TagTrackUID](http://matroska.org/technical/specs/tagging/index.html#TagTrackUID)
                - <UID of the track>
        - [SimpleTag](http://matroska.org/technical/specs/tagging/index.html#SimpleTag)
            - [TagName](http://matroska.org/technical/specs/tagging/index.html#TagName)
                - "spherical-video" or "SPHERICAL-VIDEO"
            - [TagString](http://matroska.org/technical/specs/tagging/index.html#TagString)
                - &lt;xml data&gt;

### MP4
Spherical video metadata is stored in a uniquely-identified *moov.trak.uuid* box to avoid collisions with other potential metadata. This box shall cite the UUID value `ffcc8263-f855-4a93-8814-587a02521fdd`. The XML metadata itself is written within the *uuid* leaf as a UTF-8 string.

- moov
    - ...
    - trak
        - uuid[`ffcc8263-f855-4a93-8814-587a02521fdd`]
    - ...

### Allowed Global Metadata Elements


| **Name** | **Description** | **Type** | **Required** | **Default** | **V1.0 Requirements** |
|----------|-----------------|----------|--------------|-------------|-----------------------|
|Spherical | Flag indicating if the video is a spherical video | Boolean  | Yes | - |  Must be `true`. |
|Stitched  | Flag indicating if the video is stitched.          | Boolean  | Yes | - |  Must be `true`. |
|StitchingSoftware| Software used to stitch the spherical video. | String | Yes | - | |
|ProjectionType| Projection type used in the video frames. | String | Yes | - | Must be `equirectangular`. |
|[StereoMode](#StereoMode)| Description of stereoscopic 3D layout. | String | No | `mono` | Must be `mono`, `left-right`, or `top-bottom`. |
|SourceCount|Number of cameras used to create the spherical video. | Integer | No | - | |
|[InitialViewHeadingDegrees](#InitialView)|The heading angle of the initial view in degrees. | Integer | No | 0 | |
|[InitialViewPitchDegrees](#InitialView)|The pitch angle of the initial view in degrees. | Integer | No | 0 | |
|[InitialViewRollDegrees](#InitialView)|The roll angle of the initial view in degrees. | Integer | No | 0 | |
|Timestamp | Epoch timestamp of when the first frame in the video was recorded. | Integer | No | - | |
|FullPanoWidthPixels|Width of the encoded video frame in pixels.|Integer|No| See [Stereo Mode](#StereoMode).| |
|FullPanoHeightPixels|Height of the encoded video frame in pixels.|Integer|No| See [Stereo Mode](#StereoMode).| |
|CroppedAreaImageWidthPixels|Width of the video frame to display (e.g. cropping). | Integer | No | See [Stereo Mode](#StereoMode). | |
|CroppedAreaImageHeightPixels|Height of the video frame to display (e.g. cropping). | Integer | No | See [Stereo Mode](#StereoMode). | |
|CroppedAreaLeftPixels|Column where the left edge of the image was cropped from the full sized panorama|Integer|No|0| |
|CroppedAreaTopPixels|Row where the top edge of the image was cropped from the full sized panorama|Integer|No|0| |

<a name="StereoMode"\>
#### Stereo Mode

[SEI Frame Packing Arragement](http://www.itu.int/ITU-T/recommendations/rec.aspx?rec=10635) and the [StereoMode](http://www.matroska.org/technical/specs/index.html#StereoMode) tag for Matroska/WebM video files can be used to describe the left/right frame layout. To include non-h264 MPEG-4 files an additional StereoMode tag will override the native stereo configuration. The supported StereoMode values are shown below with the corresponding native values.

| **Name** | **Description** |Equivalent MKV Value | Equivalent h264 SEI FPI |
|----------|-----------------|---------------------|-------------------------|
| mono       | Whole frame contains a single mono view.| 0 | - |
| left-right | Left half contains the left eye while the right half contains the right eye.| 1 | 3 |
| top-bottom | The top half contains the left eye and the bottom half contains the right eye. | 3 | 4 |

Cropping, initial view, and projection properties are shared across the left/right eyes. Each video frame is divided into the left/right eye regions then cropping and view information is applied treating each region as a separate video frame. Default cropping information varies with the StereoMode tag as shown below.

| **Name**             |   **mono**      |     **left-right**   | **top-bottom**       |
|----------------------|-----------------|----------------------|----------------------|
|CroppedAreaImageWidth |Container Width. |Half Container Width. |Container Width.      |
|CroppedAreaImageHeight|Container Height.|Container Height.     |Half Container Height.|
|FullPanoWidthPixels   |Container Width. |Half Container Width. |Container Width.      |
|FullPanoHeightPixels  |Container Height.|Container Height.     |Half Container Height.|

<a name="InitialView"\>
#### Initial View

The default initial viewport is set such that the frame center occurs at the view center. A diagram of the rotation model for an equirectangular projection is shown below.

                   Heading
         -180           0           180
       90 +-------------+-------------+
          |             |             |
    P     |             |      o>     |
    i     |             ^             |
    t   0 +-------------X-------------+
    c     |             |             |
    h     |             |             |
          |             |             |
      -90 +-------------+-------------+

    X  - the default camera center
    ^  - the default up vector
    o  - the image center for a pitch of 45 and a heading of 90
    >  - the up vector for a rotation of 90 degrees.

<a name="LocalMetadata"/a>
### Local Metadata
Version 1 supports the following Local Metadata:

- GPS (latitude, longitude, altitude)
- Director's Cut (viewport for each frame)
- Hotspot (plaint text, including HTML)

### Two Types of Local Metadata
These are two types of local metadata: (1) strictly per-frame and (2) arbitrary local metadata (perhaps sampled at certain intervals -- in other words, not strictly per-frame). Both types of local metadata may be used concurrently, depending on the author's needs and available metadata granularity.

### Specification of Strictly Per-Frame Metadata
In this case, metadata content is stored at a frame-level accuracy: there is one chunk of metadata content for every frame.

#### WebM/Matroska
Metadata content will go into the [BlockAdditional](http://matroska.org/technical/specs/index.html#BlockAdditional) element of the corresponding [Block](http://matroska.org/technical/specs/index.html#Block) to which the metadata belongs.

#### MP4
User data unregistered SEI message syntax from the ISO-14496-10:2005 (see D.1.6). This message is an SEI message of Payload Type 5.

### Specifications of Local Metadata Sampled at Intervals
In this case, the metadata content not availble at frame-level accuracy, but rather sampled as a certain time interval.

#### WebM/Matroska
Metadata content should be stored as a separate metadata track. The metadata track entry must have the following values for specified fields:
- Track type: `0x21` (WebVTT Metadata as mentioned [here](http://www.webmproject.org/docs/container/))
- CodecID: `D_WEBVTT/METADATA`

Each metadata chunk must be stored as either [Blocks](http://matroska.org/technical/specs/index.html#Block) or [SimpleBlocks](http://matroska.org/technical/specs/index.html#SimpleBlock), per the Matroska specification, with the exception that no lacing is permitted. Metadata blocks should always be key frames and must be indicated accordingly in the flags -- depending on whether it's a SimpleBlock or a Block.

#### MP4
Create a track with ComponentSubType set to "meta" for Timed Text Metadata. The box structure is as follows:

- mdia
    - mdhd
    - hdlr
    - minf
        - nmhd
        - dinf
            - dref
                - url
        - stbl
            - stsd
                - gpsd
            - stts
            - stsc
            - stsz
            - stco

### Local Metadata Specification
Local metadata is stored as a binary stream.

Header bits (1 to 32): flags indicating which metadata are present.

- Bit 1: Flag for GPS data
- Bit 2: Flag for Director's Cut data
- Bit 3: Flag for Hotspot Data
- Bit 4 to 32: Reserved for future use

Depending on which flags are set, the actual metadata will follow in the exact order of the flags.

Each block of local metadata will be preceded by the length of that particular block of data. This will alow parsers to skip metadata blocks.

Example:

     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |g|d|h|                        Reserved                         |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                 GPS Data Length (if Bit 0 set)                |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    |                    GPS Data (if Bit 0 set)                    |
    |                                                               |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |           Director's Cut Data Length (if Bit 1 set)           |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    |              Director's Cut Data (if Bit 1 set)               |
    |                                                               |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |               Hotspot Data Length (if Bit 2 set)              |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    |                  Hotspot Data (if Bit 2 set)                  |
    |                                                               |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

The binary format for representing GPS data can be found in the [MPEG3.1 GPS-V Spec](http://wg11.sc29.org/mpeg-v/?page_id=2087). Exact specification for Director's Cut and Hotspot data are yet to be determined.

### Audio
Audio can be stored in the following two ways, and metadata is needed to signal which format is used and how many streams exist. For example, the four channels of the ambisonic B format might be stored and compressed as two stereo streams.

- Stereo, 2 channels, compressed as AAC
- 5.1, 6 channels, compressed as AAC

#### Matroska/WebM:
Specification - (http://matroska.org/technical/specs/notes.html#3D)
Stereo Modes - (http://www.matroska.org/technical/specs/index.html#StereoMode)

#### MP4:
See ISO/IEC 14496-10 for SEI message
See ISO/IEC 14496-12 for ISO BMFF

# Appendix 1 - Global Metadata Sample

    <rdf:SphericalVideo
      xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
      xmlns:GSpherical="http://ns.google.com/videos/1.0/spherical/">
      <GSpherical:Spherical>true</GSpherical:Spherical>
      <GSpherical:Stitched>true</GSpherical:Stitched>
      <GSpherical:StitchingSoftware>
        OpenCV for Windows v2.4.9
      </GSpherical:StitchingSoftware>
      <GSpherical:ProjectionType>equirectangular</GSpherical:ProjectionType>
      <GSpherical:SourceCount>6</GSpherical:SourceCount>
      <GSpherical:InitialViewHeadingDegrees>90</GSpherical:InitialViewHeadingDegrees>
      <GSpherical:InitialViewPitchDegrees>0</GSpherical:InitialViewPitchDegrees>
      <GSpherical:InitialViewRollDegrees>0</GSpherical:InitialViewRollDegrees>
      <GSpherical:Timestamp>1400454971</GSpherical:Timestamp>
      <GSpherical:CroppedAreaImageWidthPixels>
        1920
      </GSpherical:CroppedAreaImageWidthPixels>
      <GSpherical:CroppedAreaImageHeightPixels>
        1080
      </GSpherical:CroppedAreaImageHeightPixels>
      <GSpherical:FullPanoWidthPixels>1900</GSpherical:FullPanoWidthPixels>
      <GSpherical:FullPanoHeightPixels>960</GSpherical:FullPanoHeightPixels>
      <GSpherical:CroppedAreaLeftPixels>15</GSpherical:CroppedAreaLeftPixels>
      <GSpherical:CroppedAreaTopPixels>60</GSpherical:CroppedAreaTopPixels>
    </rdf:SphericalVideo>


# Appendix 2 - Matroska/WebM Local Metadata Track Sample

    <TrackEntry>
      <TrackNumber>3</TrackNumber>
      <TrackType>0x21</TrackType>
      <CodecID>D_WEBVTT/METADATA</CodecID>
    </TrackEntry>
    ...
    <SimpleBlock> (http://matroska.org/technical/specs/index.html#simpleblock_structure)
      <Binary Local Metadata>
    </SimpleBlock>

