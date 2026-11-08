#!/usr/bin/env python3
"""Activate previously verified native rollback on the specific Netac, no erasure."""
import datetime, hashlib, json, os, plistlib, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'builds/atv9-offline-prototype-v1'
U = Path('/Volumes/TVBACKUP')
INSTALL = '88f9bced8f0eb1ada6a5dae0d1ea1149321ead99f3234f0fe73834f0f698417a'
RESTORE = '7632c800eff43002c777564d3519ffd9850d870f5a75d992f5fe84e2f3e2de4c'

def identity():
    v = plistlib.loads(subprocess.check_output(['diskutil', 'info', '-plist', str(U)]))
    d = plistlib.loads(subprocess.check_output(['diskutil', 'info', '-plist', v['ParentWholeDisk']]))
    assert v['VolumeUUID'] == '4F325942-BA3F-3F27-9B08-CFFB99E29E02'
    assert v['FilesystemType'] == 'msdos' and v['MountPoint'] == str(U)
    assert d['Internal'] is False and d['BusProtocol'] == 'USB'
    assert d['IORegistryEntryName'] == 'Netac OnlyDisk Media' and d['Size'] == 62264442880
    return v['ParentWholeDisk']

def verify(p, sha, size):
    assert p.stat().st_size == size, str(p)
    h = hashlib.sha256()
    with p.open('rb') as f:
        while block := f.read(8 * 1024**2):
            h.update(block)
    assert h.hexdigest() == sha, str(p)
    print('VERIFIED', p.relative_to(U), flush=True)

disk = identity()
assert json.loads((B / 'TRIAL-RESULT.json').read_text())['rollback_requested'] is True
native = {x['file']: x for x in json.loads((B / 'rollback/manifest.json').read_text())['files']}
assert not (U / 'ATV_FAILED_TRIAL').exists()
assert not (U / 'CtvUpgrade.trial.completed.disabled').exists()
backup = U / 'SberTV_Backup_20261107'
saved = ROOT / 'reports/full-firmware-readonly-20261107-184246/device-dump/usb-archive-manifest.json'
assert json.loads((backup / 'manifest.json').read_text()) == json.loads(saved.read_text())
for x in json.loads(saved.read_text())['files']:
    assert (backup / x['file']).stat().st_size == x['bytes']
verify(U / 'CtvUpgrade.bin', INSTALL, 16416)
verify(U / 'ATV_ROLLBACK/restore-CtvUpgrade.bin.disabled', RESTORE, 16416)
for name in ['system.bin', 'vendor.bin']:
    x = native[name]
    verify(U / 'ATV_ROLLBACK/emmc' / name, x['sha256'], x['bytes'])
identity()
# First disable installation; interruption from this point leaves no active installer.
(U / 'CtvUpgrade.bin').rename(U / 'CtvUpgrade.trial.completed.disabled')
(U / 'ATV_FAILED_TRIAL').mkdir()
(U / 'emmc').rename(U / 'ATV_FAILED_TRIAL/emmc')
(U / 'ATV_ROLLBACK/emmc').rename(U / 'emmc')
for name in ['system.bin', 'vendor.bin']:
    x = native[name]
    verify(U / 'emmc' / name, x['sha256'], x['bytes'])
(U / 'ATV_ROLLBACK/README.txt').write_text(
    'NATIVE ROLLBACK IS NOW ACTIVE. Original system/vendor moved to root emmc/.\n'
    'Root CtvUpgrade.bin restores these two partitions and resets data.\n'
    'Trial images preserved in ATV_FAILED_TRIAL/emmc/. Full backup untouched.\n'
    'Do not switch files manually. Restore outcome not yet tested.\n')
identity()
with (U / 'CtvUpgrade.bin').open('xb') as f:
    f.write((U / 'ATV_ROLLBACK/restore-CtvUpgrade.bin.disabled').read_bytes())
    f.flush()
    os.fsync(f.fileno())
verify(U / 'CtvUpgrade.bin', RESTORE, 16416)
subprocess.run(['sync'], check=True)
(B / 'USB-ROLLBACK-PREPARED.json').write_text(json.dumps({
    'prepared_at': datetime.datetime.now().astimezone().isoformat(),
    'disk': disk, 'active_container_sha256': RESTORE,
    'native_files': [native[n] for n in ['system.bin', 'vendor.bin']],
    'usb_hashes_verified': True, 'full_backup_preserved': True,
    'tv_restore_completed': False}, indent=2))
print('NATIVE ROLLBACK USB READY', flush=True)
