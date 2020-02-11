# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['run.py'],
             pathex=['/Users/syapele/dev/CERTABO'],
             datas=[
                ('screen.ini', '.'), 
                ('engines/*', 'engines'),
                ('constants.py', '.'),
                ('books/*', 'books'),
                ('Fonts/*', 'Fonts'),
                ('sprites/*', 'sprites'),
                ('sprites_1920/*', 'sprites_1920'),
                ('sprites_1380/*', 'sprites_1380'),
                ('certabo.png', '.'),
                ('certabo.bmp', '.'),
                ('usbtool.py', '.'),
                ('utils.py', '.'),
                ('stockfish.py', '.'),
                ('pystockfish.py', '.'),
                ('pypolyglot.py', '.'),
                ('messchess.py', '.'),
                ('httpecho.py', '.'),
                ('publish.py', '.'),
                ('leds.py', '.'),
                ('pc_scale.py', '.'),
                ('codes.py', '.')
                ],
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
          name='Certabo',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False , icon='certabo.icns')
app = BUNDLE(exe,
             name='Certabo.app',
             icon='certabo.icns',
             bundle_identifier=None)
