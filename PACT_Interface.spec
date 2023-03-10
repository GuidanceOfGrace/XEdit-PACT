# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['PACT_Interface.py', 'PACT_Start.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/Zen/AppData/Local/Programs/Python/Python39/Lib/site-packages/PySide6/plugins', 'PySide6/plugins/')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PACT_Interface',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['PACT.ico'],
)
