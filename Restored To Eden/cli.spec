# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['cli.py'],
             pathex=['/Users/jerriosity/Documents/GitHub/ingredient-sorter/Restored To Eden'],
             binaries=[('/Users/jerriosity/Documents/GitHub/ingredient-sorter/Restored To Eden/wkhtmltopdf', '.')],
             datas=[('/Users/jerriosity/Documents/GitHub/ingredient-sorter/gdriveAssets', '.')],
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
          [],
          exclude_binaries=True,
          name='cli',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='cli')
app = BUNDLE(exe,
             name='RTE Automatron.app',
             icon='rte_icon.icns',
             info_plist={
             'NSHighResolutionCapable': 'True'
             },
             bundle_identifier='com.restoredtoeden.automatron')
