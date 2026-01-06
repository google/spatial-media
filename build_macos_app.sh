#!/bin/bash
# Build script for Spatial Media Metadata Injector on macOS (including Apple Silicon)

set -e  # Exit on error

echo "🚀 Building Spatial Media Metadata Injector for macOS..."
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python not found"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Using Python $PYTHON_VERSION"

# Check if tkinter is available
if ! python -c "import tkinter" 2>/dev/null; then
    echo "❌ Error: tkinter not available"
    echo "Please see SETUP_MAC_M_SERIES.md for installation instructions"
    exit 1
fi
echo "✓ tkinter is available"

# Install build requirements
echo ""
echo "📦 Installing build requirements..."
pip install -q -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install requirements"
    exit 1
fi
echo "✓ Requirements installed"

# Clean previous builds
echo ""
echo "🧹 Cleaning previous builds..."
rm -rf build dist
echo "✓ Cleaned"

# Build with PyInstaller
echo ""
echo "🔨 Building application bundle..."
python build_executables.py

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

# Check if the app was created
if [ -d "dist/Spatial Media Metadata Injector.app" ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "📦 Application created at:"
    echo "   dist/Spatial Media Metadata Injector.app"
    echo ""
    echo "To install:"
    echo "   cp -r 'dist/Spatial Media Metadata Injector.app' /Applications/"
    echo ""
    echo "To run from here:"
    echo "   open 'dist/Spatial Media Metadata Injector.app'"
    echo ""
else
    echo "❌ Build completed but app bundle not found"
    exit 1
fi

