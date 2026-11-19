# exe 版の配布 zip を作る（Python の zipfile で作る。Linux の zip だと日本語のファイル名が Windows で文字化けする）
# 使い方（exe/ フォルダで）: python3 ../tools/mkzip.py 1.4.5
#   前もって: npx electron-builder --win portable --x64  （dist/JingleMaker.exe ができる）
import sys, zipfile, os

ver = sys.argv[1]
here = os.getcwd()
files = [
    ('JingleMaker/JingleMaker.exe', os.path.join(here, 'dist', 'JingleMaker.exe')),
    ('JingleMaker/はじめにお読みください.txt', os.path.join(here, 'はじめにお読みください.txt')),
    ('JingleMaker/ジングルオケ/', None),
    ('JingleMaker/ライセンス/Electron_LICENSE.txt', os.path.join(here, 'node_modules', 'electron', 'dist', 'LICENSE')),
    ('JingleMaker/ライセンス/Chromium_LICENSES.html', os.path.join(here, 'node_modules', 'electron', 'dist', 'LICENSES.chromium.html')),
]
out = zipfile.ZipFile(f'JingleMaker_v{ver}.zip', 'w', zipfile.ZIP_DEFLATED)
for name, path in files:
    zi = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
    zi.flag_bits |= 0x800   # UTF-8 のファイル名
    if path is None:
        zi.external_attr = 0o40755 << 16 | 0x10; zi.compress_type = zipfile.ZIP_STORED; out.writestr(zi, b'')
    else:
        zi.external_attr = 0o644 << 16; zi.compress_type = zipfile.ZIP_DEFLATED
        with open(path, 'rb') as f: out.writestr(zi, f.read())
out.close()
print(f'JingleMaker_v{ver}.zip')
