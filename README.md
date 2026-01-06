# Spatial Media

A collection of specifications and tools for 360° video and spatial audio, including:

- [Spatial Audio](docs/spatial-audio-rfc.md) metadata specification
- [Spherical Video](docs/spherical-video-rfc.md) metadata specification
- [Spherical Video V2](docs/spherical-video-v2-rfc.md) metadata specification
- [VR180 Video Format](docs/vr180.md) VR180 video format
- [Spatial Media tools](spatialmedia/) for injecting spatial media metadata in media files

## ✨ What's New - Python 3 & macOS M Series Support!

This repository has been **fully updated and optimized for modern systems:**

- ✅ **Python 3.8+** (Python 2 support removed)
- ✅ **macOS Apple Silicon (M1, M2, M3, M4)** with native performance
- ✅ **Modern tkinter** with proper Retina display support
- ✅ **Updated build system** using modern PyInstaller
- ✅ **Improved GUI** with better macOS integration

## 🚀 Quick Start

### macOS M Series Setup

For Apple Silicon Macs, see the comprehensive setup guide: **[SETUP_MAC_M_SERIES.md](SETUP_MAC_M_SERIES.md)**

**TL;DR:**
```bash
# Install pyenv and Python with tkinter support
brew install pyenv tcl-tk@8
export PYTHON_CONFIGURE_OPTS="--with-tcltk-includes='-I/opt/homebrew/opt/tcl-tk@8/include' --with-tcltk-libs='-L/opt/homebrew/opt/tcl-tk@8/lib -ltcl8.6 -ltk8.6'"
pyenv install 3.12.8
cd spatial-media
pyenv local 3.12.8

# Run the GUI
python spatialmedia/gui.py
```

### Other Platforms

**Requirements:**
- Python 3.8 or higher
- tkinter (usually included with Python)

**Install:**
```bash
pip install -e .
```

**Run GUI:**
```bash
python spatialmedia/gui.py
# or if installed as package:
spatialmedia-gui
```

**Run CLI:**
```bash
python -m spatialmedia --help
```

## 📖 Usage

### GUI Application

Launch the graphical interface:

```bash
python spatialmedia/gui.py
```

Features:
- Open and examine 360° videos
- Add spherical video metadata
- Add stereoscopic 3D metadata (top-bottom, left-right)
- Add spatial audio metadata (ambisonics)
- Batch process multiple files

### Command Line Interface

#### Examine metadata:
```bash
python -m spatialmedia video.mp4
```

#### Inject 360° metadata:
```bash
python -m spatialmedia --inject input.mp4 output.mp4
```

#### Add 3D stereoscopic metadata:
```bash
python -m spatialmedia --inject --stereo top-bottom input.mp4 output.mp4
```

#### Add spatial audio metadata:
```bash
python -m spatialmedia --inject --spatial-audio input.mp4 output.mp4
```

#### Combine all options:
```bash
python -m spatialmedia --inject --stereo top-bottom --spatial-audio input.mp4 output.mp4
```

## 🛠️ Building Standalone Application

### macOS (including Apple Silicon)

Use the provided build script:

```bash
./build_macos_app.sh
```

The app bundle will be created at `dist/Spatial Media Metadata Injector.app`

### Manual Build

Install build dependencies:

```bash
pip install -r requirements.txt
```

Build with PyInstaller:

```bash
python build_executables.py
```

Or directly:

```bash
pyinstaller spatialmedia/spatial_media_metadata_injector.spec
```

## 📋 Features

✅ **360° Video Support** - Add spherical video metadata for YouTube, Facebook, and other platforms  
✅ **Stereoscopic 3D** - Support for top-bottom and left-right layouts  
✅ **Spatial Audio** - First-order ambisonics (ACN/SN3D format)  
✅ **Batch Processing** - Process multiple files at once (GUI)  
✅ **Cross-Platform** - Works on macOS, Windows, and Linux  
✅ **Native Performance** - Optimized for Apple Silicon

## 📁 Supported Formats

- **Video:** MP4, MOV
- **Audio:** First-order periphonic ambisonics (4+ channels, ACN channel ordering, SN3D normalization)
- **Stereo Layouts:** Top-bottom, left-right

## 📚 Documentation

- **macOS M Series Setup:** [SETUP_MAC_M_SERIES.md](SETUP_MAC_M_SERIES.md)
- **Tool Documentation:** [spatialmedia/README.md](spatialmedia/README.md)
- **Spatial Audio Spec:** [docs/spatial-audio-rfc.md](docs/spatial-audio-rfc.md)
- **Spherical Video Spec:** [docs/spherical-video-rfc.md](docs/spherical-video-rfc.md)
- **Spherical Video V2 Spec:** [docs/spherical-video-v2-rfc.md](docs/spherical-video-v2-rfc.md)
- **VR180 Format:** [docs/vr180.md](docs/vr180.md)

## 🧪 Testing

Test videos are provided in the `data/` directory:
- `testsrc_320x240_h264.mp4` - H.264 encoded video
- `testsrc_320x240_vp9.mp4` - VP9 encoded video
- `testsrc_32x24_prores.mov` - ProRes encoded video

## 💻 System Requirements

### Supported Python Versions
- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12

### Supported Operating Systems
- macOS 10.13+ (Intel and Apple Silicon)
- Windows 10, 11
- Linux (modern distributions)

### Not Supported
- ❌ Python 2.x (removed)
- ❌ macOS < 10.13

## 🔧 Troubleshooting

### macOS: GUI won't open
See [SETUP_MAC_M_SERIES.md](SETUP_MAC_M_SERIES.md) for detailed troubleshooting.

Common issue: Python not built with tkinter support. Solution:
```bash
python -c "import tkinter; print('✅ tkinter works!')"
```

### Windows: Missing tkinter
tkinter is included with the standard Python installer. Make sure you didn't uncheck it during installation.

### Linux: Missing tkinter
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

## 📄 License

Copyright 2016 Google Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## 🙏 Acknowledgments

- Original Spatial Media tools by Google Inc.
- Updated for Python 3 and Apple Silicon compatibility

---

**Last Updated:** January 2026  
**Version:** 2.1.0  
**Python:** 3.8+
