# -*- mode: python -*-
# PyInstaller spec.

import sys

block_cipher = None

a = Analysis(['gui.py'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='Spatial Media Metadata Injector',
          debug=False,
          strip=False,
          upx=True,
          console=False )
if sys.platform == 'darwin':
    app = BUNDLE(exe,
                 name='Spatial Media Metadata Injector.app',
                 icon=None,
                 bundle_identifier=None,
                 info_plist={'NSHighResolutionCapable': 'True'})
