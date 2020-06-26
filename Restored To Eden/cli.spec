# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['cli.py'],
             pathex=['/Users/HG/Documents/GitHub/ingredient-sorter/Restored To Eden'],
             binaries=[("/usr/local/bin/wkhtmltopdf", '.')],
             datas=[("/Users/HG/Downloads/pyinstaller instructions/gdriveAssets", '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='cli',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False , icon='rte_icon.icns')
app = BUNDLE(exe,
             name='cli.app',
             icon='rte_icon.icns',
             info_plist={
             'NSHighResolutionCapable': 'True'
             },
             bundle_identifier='com.restoredtoeden.automatron')
