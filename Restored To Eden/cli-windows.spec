# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['cli.py'],
             pathex=['C:/users/jerry/source/repos/ingredient-sorter/Restored To Eden'],
             binaries=[("C:/users/jerry/source/repos/ingredient-sorter/Restored To Eden/wkhtmltopdf.exe", '.')],
             datas=[("C:/users/jerry/Desktop/gdriveAssets", '.'), ("C:/users/jerry/Desktop/gdriveAssets/config/config.json", 'config')],
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
          console=True )
