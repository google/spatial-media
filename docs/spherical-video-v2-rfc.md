# Spherical Video V2 RFC (draft)
*This document describes a revised open metadata scheme by which MP4 (ISOBMFF)
multimedia containers may accommodate spherical videos. Comments are welcome on
the [spatial-media-discuss]
(https://groups.google.com/forum/#!forum/spatial-media-discuss)
mailing list or by [filing an issue]
(https://github.com/google/spatial-media/issues) on GitHub.*

------------------------------------------------------

## Metadata Format

### MP4 (ISOBMFF)
Spherical video metadata is stored in a new box, `SV3D`, defined in this RFC, in
an MP4 (ISOBMFF) container. The metadata is applicable to individual video
tracks in the container.

As the V2 specification stores its metadata in a different location, it is
possible for a file to contain both the V1 and V2 metadata. If both V1 and V2
metadata are contained they should contain semantically equivalent information,
with V2 taking priority when they differ.

#### Spherical Video Box (SV3D)
##### Definition
Box Type: `SV3D`  
Container: Video Sample Description box (e.g. `avc1`, `mp4v`, `apcn`)  
Mandatory: No  
Quantity: Zero or one

Stores additional information about spherical video content contained in this
video track.

##### Syntax
```
aligned(8) class SphericalVideoBox extends Box(‘SV3D’) {
}
```

#### Spherical Video Header (SVHD)
##### Definition
Box Type: `SVHD`  
Container: `SV3D`  
Mandatory: Yes  
Quantity: Exactly one

Contains spherical video information unrelated to the projection format.

##### Syntax
```
aligned(8) class SphericalVideoHeader extends FullBox(‘SVHD’, 0, 0) {
    string metadata_source;
}
```

##### Semantics

- `metadata_source` is a string identifier for the source tool of the SV3D
metadata.

#### Projection Box (PROJ)
##### Definition
Box Type: `PROJ`  
Container: `SV3D`  
Mandatory: Yes  
Quantity: Exactly one

Container for projection information about the spherical video content.
This container must contain exactly one projection (e.g. an `EQUI` box) which
defines the spherical video's projection.

##### Syntax
```
aligned(8) class Projection extends Box(‘PROJ’) {
}
```

#### Projection Header Box (PRHD)
##### Definition
Box Type: `PRHD`  
Container: `PROJ`  
Mandatory: Yes  
Quantity: Exactly one

Contains projection information about the spherical video content that is
independent of the video projection.

##### Syntax
```
aligned(8) class ProjectionHeader extends FullBox(‘PROJ’, 0, 0) {
    unsigned int(8) stereo_mode;

    int(32) pose_yaw_degrees;
    int(32) pose_pitch_degrees;
    int(32) pose_roll_degrees;
}
```

##### Semantics

- `stereo_mode` is an 8-bit unsigned integer that specifies the stereo frame
   layout. The values 0 to 255 are reserved for current and future layouts. The
   following values are defined:

| `stereo_mode` | Stereo Mode Description |
|:-----------------|:---------------------------|
|   `0`   | **Monoscopic**: Indicates the video frame contains a single monoscopic view. |
|   `1`   | **Stereoscopic Top-Bottom**: Indicates the video frame contains a stereoscopic view storing the left eye on top half of the frame and right eye at the bottom half of the frame.|
|   `2`   | **Stereoscopic Left-Right**: Indicates the video frame contains a stereoscopic view storing the left eye on left half of the frame and right eye on the right half of the frame.|

- Pose values are 16.16 fixed point values measuring rotation in degrees. These
  rotations transform the the projection as follows:
  - `pose_yaw_degrees` clockwise rotation by the up vector
  - `pose_pitch_degrees` counter-clockwise rotation over the right vector post
     yaw transform
  - `pose_roll_degrees` counter clockwise-rotation over the forward vector post
     yaw and pitch transform

#### Projection Data Box
##### Definition
Box Type: Projection Dependent Identifier  
Container: `PROJ`  
Mandatory: Yes  
Quantity: Exactly one

Base class for all projection data boxes. Any new projection must subclass this
type with a unique proj_type.

##### Syntax
```
aligned(8) class ProjectionDataBox(unsigned int(32) proj_type, unsigned int(32) version, unsigned int(32) flags)
    extends FullBox(proj_type, version, flags) {
}
```

#### Cubemap Projection Box (CBMP)
##### Definition
Box Type: `CBMP`  
Container: `PROJ`

Contains the projection dependent information for a cubemap video. The
[cubemap's](https://en.wikipedia.org/wiki/Cube_mapping) face layout is defined
by a unique `layout` value.

##### Syntax
```
aligned(8) class CubemapProjection ProjectionDataBox(‘CBMP’, 0, 0) {
    unsigned int(32) layout;
    unsigned int(32) padding;
}
```

##### Semantics
- `layout` is a 32-bit unsigned integer describing the layout of cube faces. The
  values 0 to 255 are reserved for current and future layouts.
  - a value of `0` corresponds to a grid with 3 columns and 2 rows. Faces are
    oriented upwards for the front, left, right, and back faces. The up face is
    oriented so the top of the face is forwards and the down face is oriented
    so the top of the face is to the back.
<center>
<table>
  <tr>
    <td>right face</td>
    <td>left face</td>
    <td>up face</td>
  </tr>
  <tr>
    <td>down face</td>
    <td>front face</td>
    <td>back face</td>
  </tr>
</table>
</center>

- `padding` is a 32-bit unsigned integer measuring the number of pixels to pad
    from the edge of each cube face.

#### Equirectangular Projection Box (EQUI)
##### Definition
Box Type: `EQUI`  
Container: `PROJ`

Contains the projection dependent information for a equirectangular video. The
[equirectangular projection](
https://en.wikipedia.org/wiki/Equirectangular_projection) should be arranged
such that the default pose has the forward vector in the center of the frame,
the up vector at top of the frame, and the right vector towards the right of the
frame.

##### Syntax
```
aligned(8) class EquirectangularProjection ProjectionDataBox(‘EQUI’, 0, 0) {
    unsigned int(32) crop_top;
    unsigned int(32) crop_bottom;
    unsigned int(32) crop_left;
    unsigned int(32) crop_right;
}
```

##### Semantics

- The crop values use a 0.32 fixed point float. These values repesent the
  proportion of projection cropped from each edge not covered by the video
  frame. For an uncropped frame all values are 0.
  - `crop_top` is the amount from the top of the frame to crop
  - `crop_bottom` is the amount from the bottom of the frame to crop; must be
    less than 0xFFFFFFFF - crop_top
  - `crop_left` is the amount from the left of the frame to crop
  - `crop_right` is the amount from the right of the frame to crop; must be
    less than 0xFFFFFFFF - crop_left

### Example

Here is an example box hierarchy for a file containing the SV3D metadata for a
monoscopic equirectangular video:

- moov
  - trak
    - mdia
      - minf
        - stbl
          - stsd
            - avc1
              - pasp
              - SV3D
                - SVHD
                - PROJ
                  - PRHD
                  - EQUI

where the SVHD box contains:

| Field Name | Value |
|:-----------|:------|
| `metadata_source`| `Spherical Metadata Tooling` |

the PRHD box contains:

| Field Name | Value |
|:-----------|:-----|
| `stereo_mode` | `0` |
| `pose_yaw_degrees` | `0` |
| `pose_pitch_degrees` | `0` |
| `pose_roll_degrees` | `0` |

and the EQUI box contains:

| Field Name | Value |
|:-----------|:-----|
| `crop_top` | `0` |
| `crop_bottom` | `0` |
| `crop_left` | `0` |
| `crop_right` | `0` |

