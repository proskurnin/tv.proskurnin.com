#!/usr/bin/env python3
"""Offline vendor application removal experiment; never connects to a TV."""
import hashlib
import json
import stat
import subprocess
from pathlib import Path
from dissect.extfs import ExtFS

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / 'reports/full-firmware-readonly-20261107-184246'
OUT = ROOT / 'builds/atv9-offline-prototype-v1'
assert (OUT / 'NOT-FOR-TV.txt').is_file()
image = OUT / 'vendor.experimental.bin'
expected = next(x for x in json.loads((R / 'device-dump/emmc-stage2/partitions-verified.json').read_text())['partitions'] if x['name'] == 'vendor')
with (R / 'device-dump/emmc-stage2/emmc.bin').open('rb') as src, image.open('xb') as dst:
    src.seek(2389508096)
    left = 996147200
    h = hashlib.sha256()
    while left:
        b = src.read(min(left, 8*1024*1024))
        assert b
        h.update(b)
        dst.write(b)
        left -= len(b)
assert h.hexdigest() == expected['sha256']
fs = ExtFS(image.open('rb'))
commands = []
removed = []
def delete(node, path):
    if node.filetype == stat.S_IFDIR:
        for child in node.iterdir():
            if child.filename not in ('.', '..'):
                delete(child, path + '/' + child.filename)
        commands.append('rmdir ' + path)
    else:
        commands.append('rm ' + path)

# Keep the exact native drivers and hardware firmware updater. This does NOT
# establish compatibility with the donor framework or native SELinux policy.
for base in ['/app', '/priv-app']:
    for node in fs.get(base).iterdir():
        if node.filename in ('.', '..', 'GamepadService', 'RemoteControllerFwUpdater'):
            continue
        path = base + '/' + node.filename
        removed.append(path)
        delete(node, path)
fs.fh.close()
cmd = OUT / 'vendor-debugfs.commands'
cmd.write_text('\n'.join(commands) + '\n')
e2 = Path('/opt/homebrew/opt/e2fsprogs/sbin')
for args, log, allowed in [([e2/'debugfs','-w','-f',cmd,image], 'vendor-debugfs.log',(0,)),
                            ([e2/'e2fsck','-fy',image], 'vendor-fsck-fix.log',(0,1)),
                            ([e2/'e2fsck','-fn',image], 'vendor-fsck-final.log',(0,))]:
    p = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    (OUT/log).write_text(p.stdout+p.stderr)
    assert p.returncode in allowed, log
assert not any(s in (OUT/'vendor-debugfs.log').read_text() for s in ['File not found','Could not','No space left'])
check = ExtFS(image.open('rb'))
for path in removed:
    try:
        check.get(path)
    except Exception:
        continue
    raise RuntimeError('Application removal failed: '+path)
with image.open('rb') as f:
    sha = hashlib.file_digest(f,'sha256').hexdigest()
(OUT/'vendor-manifest.json').write_text(json.dumps({'flash_ready':False,
    'source_partition_sha256':expected['sha256'], 'image_sha256':sha,
    'image_bytes':image.stat().st_size, 'removed_app_directories':removed,
    'fsck_passed':True, 'driver_framework_compatibility_verified':False},indent=2))
print('Offline vendor prototype verified:', image)
