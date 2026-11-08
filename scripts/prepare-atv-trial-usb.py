#!/usr/bin/env python3
"""Stage the explicitly approved v1 trial on the identified Netac; never erase."""
import hashlib, json, os, plistlib, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'builds/atv9-offline-prototype-v1'
USB = Path('/Volumes/TVBACKUP')

def info(path):
    return plistlib.loads(subprocess.check_output(['diskutil', 'info', '-plist', str(path)]))

def identity():
    v = info(USB)
    d = info(v['ParentWholeDisk'])
    assert v['VolumeUUID'] == '4F325942-BA3F-3F27-9B08-CFFB99E29E02'
    assert v['FilesystemType'] == 'msdos' and v['MountPoint'] == str(USB)
    assert d['Internal'] is False and d['BusProtocol'] == 'USB'
    assert d['IORegistryEntryName'] == 'Netac OnlyDisk Media'
    assert d['Size'] == 62264442880
    return v['ParentWholeDisk']

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while data := f.read(8 * 1024**2):
            h.update(data)
    return h.hexdigest()

def verify(path, sha, size=None):
    if size is not None:
        assert path.stat().st_size == size, str(path)
    assert digest(path) == sha, str(path)
    print('VERIFIED', path.relative_to(USB) if path.is_relative_to(USB) else path.name, flush=True)

disk = identity()
assert not (USB / 'CtvUpgrade.bin').exists(), 'Active upgrade file already exists'
assert shutil.disk_usage(USB).free > 4000000000
auth = json.loads((B / 'TRIAL-AUTHORIZATION.json').read_text())
assert auth['user_confirmed_trial_v1_and_data_reset'] is True
approved = auth['approved_files_sha256']
backup = USB / 'SberTV_Backup_20261107'
saved = ROOT / 'reports/full-firmware-readonly-20261107-184246/device-dump/usb-archive-manifest.json'
assert json.loads((backup / 'manifest.json').read_text()) == json.loads(saved.read_text())
for x in json.loads(saved.read_text())['files']:
    verify(backup / x['file'], x['sha256'], x['bytes'])

rollback = {x['file']: x for x in json.loads((B / 'rollback/manifest.json').read_text())['files']}
jobs = []
for name in ['system', 'vendor']:
    jobs.append((B / f'{name}.experimental.bin', USB / f'emmc/{name}.bin', approved[f'{name}.experimental.bin']))
    jobs.append((B / f'rollback/{name}.bin', USB / f'ATV_ROLLBACK/emmc/{name}.bin', rollback[f'{name}.bin']['sha256']))
jobs.append((B / 'restore-CtvUpgrade.bin.candidate', USB / 'ATV_ROLLBACK/restore-CtvUpgrade.bin.disabled', approved['restore-CtvUpgrade.bin.candidate']))
jobs.append((B / 'install-CtvUpgrade.bin.candidate', USB / 'ATV_TRIAL_INSTALL.disabled', approved['install-CtvUpgrade.bin.candidate']))
records = []
for src, dst, sha in jobs:
    verify(src, sha)
    identity()
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        print('COPYING', dst.relative_to(USB), flush=True)
        with src.open('rb') as f, dst.open('xb') as out:
            shutil.copyfileobj(f, out, 8 * 1024**2)
            out.flush()
            os.fsync(out.fileno())
    verify(dst, sha, src.stat().st_size)
    records.append({'file': str(dst.relative_to(USB)), 'bytes': dst.stat().st_size, 'sha256': sha})

(USB / 'ATV_ROLLBACK/README.txt').write_text(
    'Rollback is NOT active. Do not rename only this container!\n'
    'To restore native OS, reconnect USB to Mac. Replace root emmc/system.bin and\n'
    'emmc/vendor.bin with the originals in this folder; verify hashes. Then replace\n'
    'root CtvUpgrade.bin with restore-CtvUpgrade.bin.disabled from this folder.\n'
    'Only then use the TV USB upgrade boot sequence. This resets user data.\n'
    'Restore has not been tested. Full private backup is in SberTV_Backup_20261107.\n')
identity()
active = USB / 'CtvUpgrade.bin'
with (USB / 'ATV_TRIAL_INSTALL.disabled').open('rb') as src, active.open('xb') as out:
    shutil.copyfileobj(src, out)
    out.flush()
    os.fsync(out.fileno())
verify(active, approved['install-CtvUpgrade.bin.candidate'], 16416)
subprocess.run(['sync'], check=True)
record = {'disk_at_preparation': disk, 'files': records, 'active_install_sha256': digest(active),
          'backup_reverified': True, 'tv_written': False, 'runtime_verified': False}
(B / 'USB-TRIAL-PREPARED.json').write_text(json.dumps(record, indent=2))
print('USB TRIAL READY; TV NOT WRITTEN', flush=True)
