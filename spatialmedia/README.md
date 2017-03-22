# Spatial Media Metadata Injector

A tool for manipulating spatial media 
([spherical video](../docs/spherical-video-rfc.md) and
[spatial audio](../docs/spatial-audio-rfc.md)) metadata in MP4 and MOV files.
It can be used to inject spatial media metadata into a file or validate metadata
in an existing file.

## Usage

[Python 2.7](https://www.python.org/downloads/) must be used to run the tool.
From within the directory above `spatialmedia`:

#### Help

    python spatialmedia -h

Prints help and usage information.

#### Examine

    python spatialmedia <files...>

For each file specified, prints spatial media metadata contained in the file.

#### Inject

    python spatialmedia -i [--stereo=(none|top-bottom|left-right)] [--spatial-audio] <input> <output>

Saves a version of `<input>` injected with spatial media metadata to `<output>`.
`<input>` and `<output>` must not be the same file.

##### --stereo

Selects the left/right eye frame layout; see the `StereoMode` element in the
[Spherical Video RFC](../docs/spherical-video-rfc.md) for more information.

Options:

- `none`: Mono frame layout.

- `top-bottom`: Top half contains the left eye and bottom half contains the
right eye.

- `left-right`: Left half contains the left eye and right half contains the
right eye.

##### --spatial-audio

Enables injection of spatial audio metadata. If enabled, the file must contain a
4-channel first-order ambisonics audio track with ACN channel ordering and SN3D
normalization; see the [Spatial Audio RFC](../docs/spatial-audio-rfc.md) for
more information.

## Building standalone GUI application

Install [PyInstaller](http://pythonhosted.org/PyInstaller/), then run the
following:

    pyinstaller spatial_media_metadata_injector.spec
