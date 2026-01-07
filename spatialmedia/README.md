# Spatial Media Metadata Injector

A tool for manipulating spatial media 
([spherical video](../docs/spherical-video-rfc.md) and
[spatial audio](../docs/spatial-audio-rfc.md)) metadata in MP4 and MOV files.
It can be used to inject spatial media metadata into a file or validate metadata
in an existing file.

**Now fully compatible with Python 3 and macOS Apple Silicon (M series)!**

## Requirements

- Python 3.8 or higher
- For macOS M series: Python installed via pyenv with tcl-tk@8 support (see [setup guide](../SETUP_MAC_M_SERIES.md))

## Usage

### GUI Application

Run the graphical interface:

```bash
python spatialmedia/gui.py
```

Or if installed as a package:

```bash
spatialmedia-gui
```

### Command Line Interface

#### Help

```bash
python -m spatialmedia -h
```

Prints help and usage information.

#### Examine

```bash
python -m spatialmedia <files...>
```

For each file specified, prints spatial media metadata contained in the file.

#### Inject

```bash
python -m spatialmedia -i [--stereo=(none|top-bottom|left-right)] [--spatial-audio] <input> <output>
```

Saves a version of `<input>` injected with spatial media metadata to `<output>`.
`<input>` and `<output>` must not be the same file.

##### --stereo

Selects the left/right eye frame layout; see the `StereoMode` element in the
[Spherical Video RFC](../docs/spherical-video-rfc.md) for more information.

Options:

- `none`: Mono frame layout.
- `top-bottom`: Top half contains the left eye and bottom half contains the right eye.
- `left-right`: Left half contains the left eye and right half contains the right eye.

##### --spatial-audio

Enables injection of spatial audio metadata. If enabled, the file must contain a
4-channel first-order ambisonics audio track with ACN channel ordering and SN3D
normalization; see the [Spatial Audio RFC](../docs/spatial-audio-rfc.md) for
more information.

## Building Standalone Application

### macOS (including Apple Silicon M series)

```bash
./build_macos_app.sh
```

This creates a `.app` bundle in the `dist/` directory that can be moved to your Applications folder.

### Manual Build

Install [PyInstaller](https://pyinstaller.org/), then run:

```bash
pip install -r requirements.txt
python build_executables.py
```

Or directly with PyInstaller:

```bash
pyinstaller spatialmedia/spatial_media_metadata_injector.spec
```
