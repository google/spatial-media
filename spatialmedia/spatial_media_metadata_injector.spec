# -*- mode: python -*-
# PyInstaller spec for Spatial Media Metadata Injector
# Optimized for Python 3 and macOS (including Apple Silicon M series)

import sys
import platform

block_cipher = None

# Analysis phase - collect all dependencies
a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Create PYZ archive
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

# Platform-specific builds
if sys.platform == 'darwin':
    # macOS app bundle (works on both Intel and Apple Silicon)
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='Spatial Media Metadata Injector',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,  # Disable UPX for better compatibility with Apple Silicon
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,  # Auto-detect architecture
        codesign_identity=None,
        entitlements_file=None,
    )
    
    app = BUNDLE(
        exe,
        name='Spatial Media Metadata Injector.app',
        icon=None,
        bundle_identifier='com.google.spatialmedia',
        version='2.1.0',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'LSMinimumSystemVersion': '10.13.0',
            'CFBundleShortVersionString': '2.1.0',
            'CFBundleVersion': '2.1.0',
            'NSHumanReadableCopyright': 'Copyright © 2016 Google Inc. All rights reserved.',
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'Video File',
                    'CFBundleTypeRole': 'Editor',
                    'LSItemContentTypes': ['public.movie', 'public.mpeg-4'],
                    'LSHandlerRank': 'Alternate',
                }
            ],
        },
    )

elif sys.platform.startswith('win'):
    # Windows executable
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='Spatial Media Metadata Injector',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

else:
    # Linux executable
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='Spatial Media Metadata Injector',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
