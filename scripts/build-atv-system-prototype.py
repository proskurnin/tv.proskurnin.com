#!/usr/bin/env python3
"""Offline feasibility image only. Never accesses ADB, USB or block devices."""
import hashlib
import json
import shutil
import stat
import subprocess
import zipfile
from pathlib import Path

from dissect.extfs import ExtFS

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / 'reports/full-firmware-readonly-20261107-184246'
SRC = R / 'new-candidates/novex-original/system.bin'
GAPPS = R / 'port-feasibility/gapps/open_gapps-arm-9.0-tvmini-20220215.zip'
OUT = ROOT / 'builds/atv9-offline-prototype-v1'
E2 = Path('/opt/homebrew/opt/e2fsprogs/sbin')

def digest(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def run(args, name, allowed=(0,)):
    p = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    (OUT / name).write_text(p.stdout + p.stderr)
    if p.returncode not in allowed:
        raise RuntimeError(f'{name}: exit {p.returncode}')

assert digest(SRC) == 'ab6dd3dda97835899e04db628f5dff4791366e0c476b5b618edec938d17c2bae'
assert digest(GAPPS) == '6373351e7b424328cd71b224962860fe698fc17357302617254081766955d17a'
OUT.mkdir(exist_ok=False)
(OUT / 'NOT-FOR-TV.txt').write_text('OFFLINE PROTOTYPE ONLY. No installer. Vendor/kernel/SELinux compatibility and Google login are NOT verified. Do not flash.\n')
image = OUT / 'system.experimental.bin'
shutil.copyfile(SRC, image)
staging = OUT / 'gapps-source'
staging.mkdir()
context = OUT / 'system-file-context.bin'
context.write_bytes(b'u:object_r:system_file:s0\0')
selected = {'configupdater', 'googlebackuptransport', 'googlecontactssync',
            'gsfcore', 'tvetc', 'tvgmscore', 'tvvending', 'extservicesgoogle',
            'extsharedgoogle', 'calsync', 'googlepartnersetup',
            'googleonetimeinitializer', 'setupwraith', 'tvlauncher',
            'tvrecommendations', 'tvkeyboardgoogle', 'tvwidget', 'tvwallpaper'}
with zipfile.ZipFile(GAPPS) as z:
    assert z.testzip() is None
    for name in z.namelist():
        if not name.endswith('.tar.lz') or Path(name).name.split('-')[0] not in selected:
            continue
        arc = staging / Path(name).name
        arc.write_bytes(z.read(name))
        members = subprocess.check_output(['tar', '-tf', str(arc)], text=True).splitlines()
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in members)
        subprocess.run(['tar', '-xf', str(arc), '-C', str(staging)], check=True)

remove = [f'/system/priv-app/{n}' for n in ['GoogleApp', 'GooglePlayservices',
          'GooglePlayStore', 'GoogleAccountManager', 'GoogleServicesFramework',
          'Gmail', 'Provision', 'ExtServices']]
remove += [f'/system/app/{n}' for n in ['TvLauncher_Cetus_1_A', 'GeneralServices_zeasn',
           'TvStore_Cetus_1_A', 'OpenBrowser_sraf', 'dp-provider-Cetus', 'MBrowser3',
           'ScreenSaver', 'Camera2', 'LatinIME', 'ExtShared', 'FileManager_3.0',
           'Traceur', 'PrintSpooler', 'SoundRecorder']]
remove += ['/system/preinstall/googleDb', '/system/bin/presetGoogle.sh',
           '/system/fonts/NotoSerifCJK-Regular.ttc', '/system/fonts/NotoSansCJK-Regular.ttc']
commands = []
fs = ExtFS(SRC.open('rb'))

def delete(path):
    node = fs.get(path)
    if node.filetype == stat.S_IFDIR:
        for child in node.iterdir():
            if child.filename not in ('.', '..'):
                delete(path + '/' + child.filename)
        commands.append('rmdir ' + path)
    else:
        commands.append('rm ' + path)

for path in remove:
    delete(path)
dirs = set()
added = []
for p in sorted(staging.rglob('*')):
    if not p.is_file() or p.suffix == '.lz':
        continue
    rel = p.relative_to(staging)
    # Archive path is component/density/{app,priv-app,etc,...}/...
    assert len(rel.parts) >= 3
    target = '/system/' + '/'.join(rel.parts[2:])
    parent = Path(target).parent
    for d in reversed([parent] + list(parent.parents)):
        ds = str(d)
        if ds in ('/', '/system') or ds in dirs:
            continue
        try:
            if any(ds == rem or ds.startswith(rem + '/') for rem in remove):
                raise FileNotFoundError(ds)
            fs.get(ds)
        except Exception:
            commands += ['mkdir ' + ds, 'set_inode_field ' + ds + ' mode 040755',
                         f'ea_set -f {context} {ds} security.selinux']
        dirs.add(ds)
    try:
        if any(target == rem or target.startswith(rem + '/') for rem in remove):
            raise FileNotFoundError(target)
        fs.get(target)
        commands.append('rm ' + target)
    except Exception:
        pass
    commands += [f'write {p} {target}', f'set_inode_field {target} mode 0100644',
                 f'ea_set -f {context} {target} security.selinux']
    added.append({'target': target, 'bytes': p.stat().st_size, 'sha256': digest(p)})
cmdfile = OUT / 'debugfs.commands'
cmdfile.write_text('\n'.join(commands) + '\n')
run([E2 / 'debugfs', '-w', '-f', cmdfile, image], 'debugfs.log')
log = (OUT / 'debugfs.log').read_text()
assert not any(s in log for s in ['File not found', 'File exists', 'Could not', 'No space left'])
run([E2 / 'e2fsck', '-fy', image], 'fsck-before-resize.log', (0, 1))
run([E2 / 'resize2fs', '-f', image, '750M'], 'resize.log')
run([E2 / 'e2fsck', '-fn', image], 'fsck-final.log')
check = ExtFS(image.open('rb'))
for row in added:
    assert hashlib.sha256(check.get(row['target']).open().read()).hexdigest() == row['sha256']
for path in remove:
    try:
        check.get(path)
    except Exception:
        continue
    if not any(x['target'].startswith(path + '/') for x in added):
        raise RuntimeError('Removal failed: ' + path)
assert image.stat().st_size == 786432000
(OUT / 'manifest.json').write_text(json.dumps({'flash_ready': False,
    'purpose': 'offline feasibility only; no vendor adaptation or runtime validation',
    'source_sha256': digest(SRC), 'gapps_sha256': digest(GAPPS),
    'image_sha256': digest(image), 'image_bytes': image.stat().st_size,
    'removed': remove, 'added': added, 'fsck_passed': True}, indent=2))
print('Offline prototype verified:', image)
