# Spherical Video V2 RFC (draft)
*This document describes a revised open metadata scheme by which MP4 (ISOBMFF)
and WebM (Matroska) multimedia containers may accommodate spherical videos. Comments are welcome by
discussing on the [Spatial Media Google
group](https://groups.google.com/forum/#!forum/spatial-media-discuss) or by
filing an [issue](https://github.com/google/spatial-media/issues/new) on
GitHub.*

------------------------------------------------------

## Metadata Format

### MP4 (ISOBMFF)
Spherical video metadata is stored in a new box, `sv3d`, defined in this RFC, in
an MP4 (ISOBMFF) container. The metadata is applicable to individual video
tracks in the container. Since many spherical videos are also stereoscopic, this
RFC also defines an additional optional box, `st3d`, to specify metadata
specific to stereoscopic rendering.

As the V2 specification stores its metadata in a different location, it is
possible for a file to contain both the V1 and V2 metadata. If both V1 and V2
metadata are contained they should contain semantically equivalent information,
with V2 taking priority when they differ.

#### Stereoscopic 3D Video Box (st3d)
##### Definition
Box Type: `st3d`  
Container: VisualSampleEntry (e.g. `avc1`, `mp4v`, `apcn`)  
Mandatory: No  
Quantity: Zero or one

Stores additional information about stereoscopic rendering in this video track.
This box must come after non-optional boxes defined by the ISOBMFF
specification and before optional boxes at the end of the VisualSampleEntry
definition such as the CleanApertureBox and PixelAspectRatioBox.

##### Syntax
```
aligned(8) class Stereoscopic3D extends FullBox(‘st3d’, 0, 0) {
    unsigned int(8) stereo_mode;
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
|   `3`   | **Stereoscopic Stereo-Mesh**: Indicates the video frame contains a stereoscopic view where the frame layout for left and right eyes are encoded in the (u,v) coordinates of two meshes. This may only be used with a mesh projection that contains a mesh for each eye. |

#### Spherical Video Box (sv3d)
##### Definition
Box Type: `sv3d`  
Container: VisualSampleEntry (e.g. `avc1`, `mp4v`, `apcn`)  
Mandatory: No  
Quantity: Zero or one

Stores additional information about spherical video content contained in this
video track. This box must come after non-optional boxes defined by the ISOBMFF
specification and before optional boxes at the end of the VisualSampleEntry
definition such as the CleanApertureBox and PixelAspectRatioBox. This box should
be placed after the Stereoscopic3D box if one is present.


##### Syntax
```
aligned(8) class SphericalVideoBox extends Box(‘sv3d’) {
}
```

#### Spherical Video Header (svhd)
##### Definition
Box Type: `svhd`  
Container: `sv3d`  
Mandatory: Yes  
Quantity: Exactly one

Contains spherical video information unrelated to the projection format.

##### Syntax
```
aligned(8) class SphericalVideoHeader extends FullBox(‘svhd’, 0, 0) {
    string metadata_source;
}
```

##### Semantics

- `metadata_source` is a null-terminated string in UTF-8 characters which
identifies the tool used to create the SV3D metadata.

#### Projection Box (proj)
##### Definition
Box Type: `proj`  
Container: `sv3d`  
Mandatory: Yes  
Quantity: Exactly one

Container for projection information about the spherical video content.
This container must contain exactly one subtype of the Projection Data Box
(e.g. an `equi` box) that defines the spherical projection.

##### Syntax
```
aligned(8) class Projection extends Box(‘proj’) {
}
```

#### Projection Header Box (prhd)
##### Definition
Box Type: `prhd`  
Container: `proj`  
Mandatory: Yes  
Quantity: Exactly one

Contains projection information about the spherical video content that is
independent of the video projection.

##### Syntax
```
aligned(8) class ProjectionHeader extends FullBox(‘prhd’, 0, 0) {
    int(32) pose_yaw_degrees;
    int(32) pose_pitch_degrees;
    int(32) pose_roll_degrees;
}
```

##### Semantics

- Pose values are 16.16 fixed point values measuring rotation in degrees. These
  rotations transform the the projection as follows:
  - `pose_yaw_degrees` counter-clockwise rotation in degrees around the up vector,
     restricted to -180.0 to 180.0
  - `pose_pitch_degrees` counter-clockwise rotation in degrees around the right
     vector post yaw transform, restricted to -90.0 to 90.0
  - `pose_roll_degrees` clockwise-rotation in degrees around the forward
     vector post yaw and pitch transform, restricted to -180.0 to 180.0

#### Projection Data Box
##### Definition
Box Type: Projection Dependent Identifier  
Container: `proj`  
Mandatory: Yes  
Quantity: Exactly one

Base class for all projection data boxes. Any new projection must subclass this
type with a unique `proj_type`. There must not be more than one subclass of a
ProjectionDataBox in a given `proj` box.

##### Syntax
```
aligned(8) class ProjectionDataBox(unsigned int(32) proj_type, unsigned int(8)version, unsigned int(24) flags)
    extends FullBox(proj_type, version, flags) {
}
```

#### Cubemap Projection Box (cbmp)
##### Definition
Box Type: `cbmp`  
Container: `proj`

Specifies that the track uses a cubemap projection and contains additional
projection dependent information. The
[cubemap's](https://en.wikipedia.org/wiki/Cube_mapping) face layout is
defined by a unique `layout` value.

##### Syntax
```
aligned(8) class CubemapProjection ProjectionDataBox(‘cbmp’, 0, 0) {
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

#### Equirectangular Projection Box (equi)
##### Definition
Box Type: `equi`  
Container: `proj`

Specifies that the track uses an equirectangular projection. The
[equirectangular projection](
https://en.wikipedia.org/wiki/Equirectangular_projection) should be arranged
such that the default pose has the forward vector in the center of the frame,
the up vector at top of the frame, and the right vector towards the right of the
frame.

##### Syntax
```
aligned(8) class EquirectangularProjection ProjectionDataBox(‘equi’, 0, 0) {
    unsigned int(32) projection_bounds_top;
    unsigned int(32) projection_bounds_bottom;
    unsigned int(32) projection_bounds_left;
    unsigned int(32) projection_bounds_right;
}
```

##### Semantics

- The projection bounds use 0.32 fixed point values. These values represent the
  proportion of projection cropped from each edge not covered by the video
  frame. For an uncropped frame all values are 0.
  - `projection_bounds_top` is the amount from the top of the frame to crop
  - `projection_bounds_bottom` is the amount from the bottom of the frame to
     crop; must be less than 0xFFFFFFFF - projection_bounds_top
  - `projection_bounds_left` is the amount from the left of the frame to crop
  - `projection_bounds_right` is the amount from the right of the frame to crop;
     must be less than 0xFFFFFFFF - projection_bounds_left

#### Mesh Projection Box (mshp)
##### Definition
Box Type: `mshp`  
Container: `proj`

Specifies that the track uses mesh projection. A mesh projection describes the
video projection in the form of a 3D mesh and associated metadata.

##### Syntax
```
aligned(8) class MeshProjection ProjectionDataBox(‘mshp’, 0, 0) {
    unsigned int(32) crc;
    unsigned int(32) encoding_four_cc;

    // All bytes below this point are compressed according to
    // the algorithm specified by the encoding_four_cc field.
    MeshBox() meshes[]; // At least 1 mesh box must be present.
    Box(); // further boxes as needed
}
```

##### Semantics
- `crc` is the CRC32 of every byte following the CRC until the end of the
  MeshProjection box.
- `encoding_four_cc` is the encoding/compression algorithm used for all bytes
  that follow this field until the end of the MeshProjection box.

  Supported compression algorithms are:
  - 'raw&nbsp;' (0x72617720) signals no compression or encoding.
  - 'dfl8' (0x64666c38) signals raw deflate compression that does not have zlib
     or gzip headers or a checksum. (https://tools.ietf.org/html/rfc1951)

- `meshes` contain the projection meshes for rendering.  If there is only one
  mesh box, it represents the monocular view and the stereo mode
  field expressed separately in the media container is used to determine
  the left and right eye view in case of stereo content. If the mshp box
  contains two mesh boxes, the first box represents the left eye mesh and the
  second box represents the right eye mesh.

#### Mesh Box (mesh)
##### Definition
Box Type: `mesh`  
Container: `mshp`  
Mandatory: Yes  
Quantity: One or Two

Contains vertex and texture coordinate information required to render the
projected video correctly.

A 3D mesh consists of the following information:

* Total number of unique vertices.
* For each unique vertex:
  * X, Y, Z, U, V coordinates as floating point.
* Number of vertex lists used to describe the projection.
  * For each vertex list:
    * Texture ID indicating which texture to sample from.
    * Triangle render method/type (triangle/strip/fan).
    * Number of vertex indices in this list.
    * For each vertex:
      * Index into the unique vertex list.

A texture ID could refer to the current video frame or a static image. This
allows portions of the spherical scene to be dynamic and other portions to be
static.

The multiple texture scheme helps cameras that do not capture the entire
spherical field of view (360 degrees horizontal and 180 degrees vertical). Such
cameras can replace the uncaptured portion of the spherical field of view with
a static image.

##### Syntax
```
aligned(8) class Mesh Box(‘mesh’) {
    const unsigned int(1) reserved = 0;
    unsigned int(31) coordinate_count;
    for (i = 0; i < coordinate_count; i++) {
      float(32) coordinate;
    }
    const unsigned int(1) reserved = 0;
    unsigned int(31) vertex_count;
    for (i = 0; i < vertex_count; i++) {
      unsigned int(ccsb) x_index_delta;
      unsigned int(ccsb) y_index_delta;
      unsigned int(ccsb) z_index_delta;
      unsigned int(ccsb) u_index_delta;
      unsigned int(ccsb) v_index_delta;
    }
    const unsigned int(1) padding[];

    const unsigned int(1) reserved = 0;
    unsigned int(31) vertex_list_count;
    for (i = 0; i < vertex_list_count; i++) {
      unsigned int(8) texture_id;
      unsigned int(8) index_type;
      const unsigned int(1) reserved = 0;
      unsigned int(31) index_count;
      for (j = 0; j < index_count; j++) {
        unsigned int(vcsb) index_as_delta;
      }
      const unsigned int(1) padding[];
    }
}
```

##### Semantics

- `reserved` are fields where all bits are set to 0. A MeshProjection box
    version change is required if any of these bits are allowed to be set to 1
    in a future revision of the spec.
- `coordinate_count` is the number of floating point values used in the
    vertices.
- `coordinate` is a floating point value used in mesh vertices.

- `vertex_count` is the number of position (x,y,z) and texture coordinate (u,v)
    pairings used in the projection mesh.
- `ccsb` coordinate count size in bits = `ceil(log2(coordinate_count * 2))`
- `x_index_delta` is a delta from the previous x_index into the
    list of coordinates. For the first element, the previous index is assumed to
    be zero. These integers are encoded in a zig-zag scheme, similar to
    [Protocol Buffers's signed integers]
    (https://developers.google.com/protocol-buffers/docs/encoding#signed-integers).
    An integer `n` that is greater than or equal to 0 is encoded as `n * 2`. An
    integer `n` that is less than 0 is encoded as `-n * 2 - 1`.
- `y_index_delta` is a delta from the previous y_index and has the same encoding
    and initial index as `x_index_delta`
- `z_index_delta` is a delta from the previous z_index and has the same encoding
    and initial index as `x_index_delta`
- `u_index_delta` is a delta from the previous u_index and has the same encoding
    and initial index as `x_index_delta`
- `v_index_delta` is a delta from the previous v_index and has the same encoding
    and initial index as `x_index_delta`
- `padding` contains 0-7 bits to align to the next byte boundary.
- `vertex_list_count` is the number of vertex index lists that describe the
    projection mesh.
- `texture_id` is the Texture ID the UV coordinates refer to.
    *   0 for video frames in this track.
    *   >0 reserved
- `index_type` specifies what the indices refer to. The valid values are:
    *   0: Triangles
    *   1: Triangle Strip
    *   2: Triangle Fan
- `index_count` is the number of vertex indices in this vertex list.
- `vcsb` vertex count size in bits = `ceil(log2(vertex_count * 2))`
- `index_as_delta` is a delta from the previous index into the
    list of unique vertices. This field has the same encoding
    and initial index as `x_index_delta`.

##### Notes:

* All fields are big-endian most-significant-bit first.
* Parsers should ignore boxes they don't know about.
* Parsers should ignore extra bytes at the end of a box.
* Boxes / fields may be added to the end of a box without incrementing the
version number.
* (x,y,z) coordinates are expressed in an OpenGL-style right-handed coordinate
  system where -Z is forward, +X is right and +Y is up. Triangles must be specified
  with counter-clockwise winding order.
* (u,v) coordinates are also expressed in an OpenGL-style texture coordinate
system, where the lower-left corner is the origin (0,0), and the upper-right is
(1,1).
* (u,v) coordinates, encoded in this box, need to be adjusted based on the
stereo mode of the stream before rendering.
   * If the stereo mode is monoscopic:
      * No (u,v) coordinate adjustments are required.
   * If the stereo mode is left-right:
      * left u' = u * 0.5
      * right u' = u * 0.5 + 0.5
   * If the stereo mode is top-bottom:
      * left v' = v * 0.5
      * right v' = v * 0.5 + 0.5
   * If the stereo mode is stereo-mesh:
      * Two mesh boxes must be present in the mshp box.
      * Unmodified (u,v) coordinates from the first mesh box are used for
rendering the left eye, and unmodified (u,v) coordinates from the second mesh
box are used for rendering the right eye.

### Example

Here is an example box hierarchy for a file containing the SV3D metadata for a
monoscopic equirectangular video:

```
[moov: Movie Box]
  [mdia: Media Box]
    [minf: Media Information Box]
      [stbl: Sample Table Box]
        [stsd: Sample Table Sample Descriptor]
          [avc1: Advance Video Coding Box]
            [avcC: AVC Configuration Box]
              ...
            [st3d: Stereoscopic 3D Video Box]
              stereo_mode = 0
            [sv3d: Spherical Video Box]
              [svhd: Spherical Video Header Box]
                metadata_source = "Spherical Metadata Tooling"
              [proj: Projection Box]
                [prhd: Projection Header Box]
                  pose_yaw_degrees = 0
                  pose_pitch_degrees = 0
                  pose_roll_degrees = 0
                [equi: Equirectangular Projection Box]
                  projection_bounds_top = 0
                  projection_bounds_bottom = 0
                  projection_bounds_left = 0
                  projection_bounds_right = 0
            [pasp: Pixel Aspect Ratio Box]
              ...
```

### WebM (Matroska)
Spherical video metadata is stored in a new master element, `Projection`,
placed inside a video track's `Video` master element.


As the V2 specification stores its metadata in a different location, it is
possible for a file to contain both the V1 and V2 metadata. If both V1 and
V2 metadata are contained they should contain semantically equivalent
information, with V2 taking priority when they differ.

Stereo mode is specified using the existing `StereoMode` element specified in
the Matroska spec. Only `StereoMode` values that have the same meaning as the
ones specified in the `st3d` box are allowed at this time. (e.g. 0 - mono,
1- left-right, 3 - top-bottom, 15 (provisional) - stereo-mesh).

#### `Projection` master element
##### Definition
ID: 0x7670  
Level: 4  
Mandatory: No  
Type: Master   
Default: N/A  
Minver: 4  
WebM: Yes  
Container: `Video` master element

Describes the video projection details. Used to render spherical and VR videos.

#### `ProjectionType` element
##### Definition
ID: 0x7671  
Level: 5  
Mandatory: Yes  
Type: uinteger  
Default: 0  
Minver: 4  
WebM: Yes  
Container: `Projection` master element

Describes the projection used for this video track.

##### Semantics
`ProjectionType` is an enum. The valid values are:

* 0: Rectangular
* 1: Equirectangular
* 2: Cubemap
* 3: Mesh


#### `ProjectionPrivate` element
##### Definition
ID: 0x7672  
Level: 5  
Mandatory: No  
Type: binary   
Default: N/A  
Minver: 4  
WebM: Yes  
Container: `Projection` master element

Private data that only applies to a specific projection.

##### Semantics
 * If `ProjectionType` equals 0 (Rectangular), then this element must not be
present.
 * If `ProjectionType` equals 1 (Equirectangular), then this element may be
present. If the element is present, then it must contain the same binary data 
that would be stored inside an ISOBMFF Equirectangular Projection Box
('equi'). If the element is not present, then the content must be treated as
if an element containing 20 zero bytes was present (i.e. a version 0 'equi'
box with no flags set and all projection_bounds fields set to 0).
 * If `ProjectionType` equals 2 (Cubemap), then this element must be present
and contain the same binary data that would be stored inside an ISOBMFF
Cubemap Projection Box ('cbmp').
 * If `ProjectionType` equals 3 (Mesh), then this element must be present
and contain the same binary data that would be stored inside an ISOBMFF
Mesh Projection Box ('mshp').

Note: ISOBMFF box size and fourcc fields are not included in the binary
data, but the FullBox version and flag fields are. This is to avoid
redundant framing information while preserving versioning and semantics
between the two container formats.

#### `ProjectionPoseYaw` element
##### Definition
ID: 0x7673  
Level: 5  
Mandatory: No  
Type: float   
Default: 0.0  
Minver: 4  
WebM: Yes  
Container: Projection master element

Specifies a yaw rotation to the projection.

##### Semantics
Value represents a counter-clockwise rotation, in degrees, around the up vector.
This rotation must be applied before any `ProjectionPosePitch` or
`ProjectionPoseRoll` rotations. The value of this field should be in the
 -180 to 180 degree range.

#### `ProjectionPosePitch` element
##### Definition
ID: 0x7674  
Level: 5  
Mandatory: No  
Type: float   
Default: 0.0  
Minver: 4  
WebM: Yes  
Container: Projection master element

Specifies a pitch rotation to the projection.

##### Semantics
Value represents a counter-clockwise rotation, in degrees, around the right
vector. This rotation must be applied after the `ProjectionPoseYaw` rotation
and before the `ProjectionPoseRoll` rotation. The value of this field
should be in the -90 to 90 degree range.

#### `ProjectionPoseRoll` element
##### Definition
ID: 0x7675  
Level: 5  
Mandatory: No  
Type: float   
Default: 0.0  
Minver: 4  
WebM: Yes  
Container: Projection master element

Specifies a roll rotation to the projection.

##### Semantics
Value represents a clockwise rotation, in degrees, around the forward
vector. This rotation must be applied after the `ProjectionPoseYaw` and
`ProjectionPosePitch` rotations. The value of this field should be in
the -180 to 180 degree range.

### Example

Here is an example element hierarchy for a file containing the Projection
metadata for a stereo left-right equirectangular video:

```
[Segment]
  [Tracks]
    [TrackEntry]
      ...
      [Video]
        ...
        [StereoMode value = 1]
        [Projection]
            [ProjectionType value = 1]
            [ProjectionPrivate]
              flags = 0
              version = 0
              projection_bounds_top = 0
              projection_bounds_bottom = 0
              projection_bounds_left = 0
              projection_bounds_right = 0
```
