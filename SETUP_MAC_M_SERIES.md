# Spatial Media - macOS Apple Silicon (M Series) Setup Guide

Complete setup guide for running Spatial Media Metadata Injector on macOS with Apple Silicon (M1, M2, M3, M4).

## ✨ What's Different on Mac M Series?

The Spatial Media app has been **fully updated and optimized** for:
- ✅ Python 3.8+ (Python 2 support removed)
- ✅ Native Apple Silicon performance (no Rosetta 2 required)
- ✅ Retina display optimization
- ✅ macOS-native appearance and window management
- ✅ Stable tkinter with tcl-tk@8

## Quick Start (5 Minutes)

If you already have Python 3.8+ with tkinter support:

```bash
cd /path/to/spatial-media
python3 spatialmedia/gui.py
```

If that works, you're done! Otherwise, continue with the full setup below.

## Full Setup Guide

### Prerequisites

- macOS 10.13 or later
- Homebrew (install from https://brew.sh)
- Command Line Tools for Xcode

### Step 1: Install pyenv

pyenv allows us to build Python with proper tkinter support:

```bash
brew install pyenv
```

### Step 2: Install tcl-tk@8

tcl-tk version 8 is more stable on macOS than version 9:

```bash
brew install tcl-tk@8
```

### Step 3: Configure Python Build Options

Set environment variables to build Python with tcl-tk@8 support:

```bash
export PYTHON_CONFIGURE_OPTS="--with-tcltk-includes='-I/opt/homebrew/opt/tcl-tk@8/include' --with-tcltk-libs='-L/opt/homebrew/opt/tcl-tk@8/lib -ltcl8.6 -ltk8.6'"
```

**Note:** For Intel Macs, replace `/opt/homebrew` with `/usr/local`.

### Step 4: Install Python 3.12

```bash
pyenv install 3.12.8
```

This will take a few minutes as it compiles Python from source.

### Step 5: Set Local Python Version

Navigate to your spatial-media directory and set the Python version:

```bash
cd /path/to/spatial-media
pyenv local 3.12.8
```

This creates a `.python-version` file that automatically activates Python 3.12.8 when you're in this directory.

### Step 6: Initialize pyenv in Your Shell

Add pyenv to your shell configuration:

```bash
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
```

Then reload your shell:

```bash
source ~/.zshrc
```

Or simply close and reopen your terminal.

### Step 7: Verify Installation

Check that everything is working:

```bash
# Verify Python version
python --version
# Should show: Python 3.12.8

# Verify tkinter works
python -c "import tkinter; print('✅ tkinter works!')"
# Should print: ✅ tkinter works!
```

### Step 8: Run the GUI

```bash
python spatialmedia/gui.py
```

The GUI should open immediately!

## 🎯 Usage

### GUI Application

```bash
python spatialmedia/gui.py
```

Or if installed as a package:

```bash
spatialmedia-gui
```

### Command Line

#### Check a video's metadata:
```bash
python -m spatialmedia video.mp4
```

#### Add 360° metadata:
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

#### Add everything (360° + 3D + spatial audio):
```bash
python -m spatialmedia --inject --stereo top-bottom --spatial-audio input.mp4 output.mp4
```

## 🛠️ Building Standalone App

### Option 1: Use the Build Script (Recommended)

```bash
./build_macos_app.sh
```

The app will be created at `dist/Spatial Media Metadata Injector.app`

### Option 2: Manual Build

Install dependencies:

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

## 🔧 Troubleshooting

### GUI Won't Open

**Error:** `ModuleNotFoundError: No module named '_tkinter'`

**Solution:** Python was not built with tkinter support. Follow Steps 1-6 above to rebuild Python with proper tkinter support.

### Wrong Python Version

**Problem:** Running `python --version` shows a different version

**Solution:** 
```bash
# Initialize pyenv in current shell
eval "$(pyenv init -)"

# Or restart your terminal
```

### GUI is Blurry on Retina Display

The updated code includes automatic Retina support. If it's still blurry, make sure you're using the updated `gui.py` file.

### Build Fails with UPX Error

UPX (executable packer) is disabled in the updated `.spec` file for Apple Silicon compatibility. Make sure you're using the updated spec file.

### tkinter Version Conflict

If you see errors related to tcl-tk 9.0, uninstall it and use tcl-tk@8:

```bash
brew uninstall tcl-tk
brew install tcl-tk@8
```

Then rebuild Python (repeat Steps 3-4).

## 📊 What Was Installed?

- **pyenv**: Python version manager
- **tcl-tk@8**: Toolkit for building graphical interfaces (version 8.6)
- **Python 3.12.8**: Latest stable Python built with tkinter support
- **.python-version**: File that auto-activates Python 3.12.8 in this directory

## 🎓 Technical Details

### Why pyenv?

- Homebrew's Python doesn't always include tkinter on Apple Silicon
- pyenv lets us build Python with custom configuration options
- Ensures consistent environment across all Mac M series chips

### Why tcl-tk@8 instead of tcl-tk (9.0)?

- tcl-tk 9.0 has compatibility issues with macOS
- tcl-tk 8.6 is more stable and tested
- The 8.6 branch is still maintained and receives security updates

### macOS Optimizations

The updated code includes:
- **Custom scaling** (1.4x for macOS) for Retina displays
- **Native macOS appearance** using `tk::mac::useThemedToplevel`
- **Fixed encoding issues** (Python 3 handles Unicode natively)
- **Platform detection** to apply macOS-specific settings

## 🚀 Next Steps

- Try the GUI with sample videos in the `data/` folder
- Read the main [README.md](README.md) for feature details
- Check [docs/](docs/) for format specifications

## 📝 Additional Resources

- **Project README**: [README.md](README.md)
- **Spherical Video RFC**: [docs/spherical-video-rfc.md](docs/spherical-video-rfc.md)
- **Spatial Audio RFC**: [docs/spatial-audio-rfc.md](docs/spatial-audio-rfc.md)
- **VR180 Format**: [docs/vr180.md](docs/vr180.md)

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] `python --version` shows Python 3.12.8
- [ ] `python -c "import tkinter"` runs without error
- [ ] `python spatialmedia/gui.py` opens the GUI
- [ ] `python -m spatialmedia --help` shows help text
- [ ] GUI can open videos from `data/` folder
- [ ] GUI can inject metadata successfully

## 🆘 Still Having Issues?

If you're still experiencing problems:

1. Make sure you've closed and reopened your terminal after adding pyenv to your shell
2. Verify tcl-tk@8 is installed: `brew list | grep tcl-tk`
3. Check pyenv versions: `pyenv versions`
4. Verify `.python-version` file exists in the spatial-media directory
5. Try rebuilding Python from scratch (repeat Steps 3-6)

---

**Last Updated:** January 2026  
**Tested On:** macOS Sonoma & Sequoia with Apple Silicon (M1, M2, M3, M4)  
**Python Version:** 3.12.8

