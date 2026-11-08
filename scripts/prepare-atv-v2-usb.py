#!/usr/bin/env python3
"""Stage the approved v2 on the identified Netac, preserving native rollback."""
import datetime, hashlib, json, os, plistlib, shutil, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
B = ROOT/'builds/atv9-diagnostic-v2'
U = Path('/Volumes/TVBACKUP')
EXPECTED = {
 'system.experimental.bin':'4083b6d1cdd0c11278d2f726e41e4a9fc21787779629a79209d9d9be5b2a17db',
 'vendor.experimental.bin':'ab4e1a695d4dff828e7f4a2e24cddc0f62794c34eaee14b2573fa35af448bc91',
 'install-CtvUpgrade.bin.candidate':'88f9bced8f0eb1ada6a5dae0d1ea1149321ead99f3234f0fe73834f0f698417a',
 'restore-CtvUpgrade.bin.candidate':'7632c800eff43002c777564d3519ffd9850d870f5a75d992f5fe84e2f3e2de4c'}
def identity():
    v=plistlib.loads(subprocess.check_output(['diskutil','info','-plist',str(U)]))
    d=plistlib.loads(subprocess.check_output(['diskutil','info','-plist',v['ParentWholeDisk']]))
    assert v['VolumeUUID']=='4F325942-BA3F-3F27-9B08-CFFB99E29E02'
    assert v['FilesystemType']=='msdos' and v['MountPoint']==str(U)
    assert d['Internal'] is False and d['BusProtocol']=='USB'
    assert d['IORegistryEntryName']=='Netac OnlyDisk Media' and d['Size']==62264442880
    return v['ParentWholeDisk']
def verify(p,digest,size=None,joined=None):
    if size is not None: assert p.stat().st_size==size,str(p)
    h=hashlib.sha256()
    with p.open('rb') as f:
        while block:=f.read(8*1024**2):
            h.update(block)
            if joined is not None: joined.update(block)
    assert h.hexdigest()==digest,str(p)
    print('VERIFIED',p,flush=True)
def copy(src,dst):
    with src.open('rb') as f,dst.open('xb') as out:
        shutil.copyfileobj(f,out,8*1024**2); out.flush(); os.fsync(out.fileno())
disk=identity()
auth=json.loads((B/'TRIAL-AUTHORIZATION.json').read_text())
assert auth['approved_files_sha256']==EXPECTED and auth['data_reset_approved'] is True
assert not (U/'ATV_V2_STAGING').exists()
assert not (U/'ATV_ROLLBACK/emmc').exists()
assert not (U/'CtvUpgrade.native-before-v2.disabled').exists()
assert shutil.disk_usage(U).free>2000000000
manifest=json.loads((B/'manifest.json').read_text())
for name,digest in EXPECTED.items(): verify(B/name,digest,manifest['files'][name]['bytes'])
saved=ROOT/'reports/full-firmware-readonly-20261107-184246/device-dump/usb-archive-manifest.json'
backup=U/'SberTV_Backup_20261107'
archive=json.loads(saved.read_text())
assert json.loads((backup/'manifest.json').read_text())==archive
joined=hashlib.sha256()
for rec in archive['files']:
    verify(backup/rec['file'],rec['sha256'],rec['bytes'],joined if rec['file'].startswith('emmc.bin.part') else None)
assert joined.hexdigest()==archive['joined_emmc_sha256']
native={x['file']:x for x in json.loads((ROOT/'builds/atv9-offline-prototype-v1/rollback/manifest.json').read_text())['files']}
verify(U/'CtvUpgrade.bin',EXPECTED['restore-CtvUpgrade.bin.candidate'],16416)
verify(U/'ATV_ROLLBACK/restore-CtvUpgrade.bin.disabled',EXPECTED['restore-CtvUpgrade.bin.candidate'],16416)
for name in ['system.bin','vendor.bin']:
    rec=native[name]; verify(U/'emmc'/name,rec['sha256'],rec['bytes'])
identity()
# Disable the active native installer before any staging or payload changes.
(U/'CtvUpgrade.bin').rename(U/'CtvUpgrade.native-before-v2.disabled')
subprocess.run(['sync'],check=True)
stage=U/'ATV_V2_STAGING'; stage.mkdir()
for part in ['system','vendor']:
    print('COPYING v2',part,flush=True)
    src=B/f'{part}.experimental.bin'; dst=stage/f'{part}.bin'
    copy(src,dst); verify(dst,EXPECTED[src.name],src.stat().st_size)
identity()
(U/'emmc').rename(U/'ATV_ROLLBACK/emmc')
stage.rename(U/'emmc')
for part in ['system','vendor']:
    verify(U/f'emmc/{part}.bin',EXPECTED[f'{part}.experimental.bin'])
(U/'ATV_ROLLBACK/README.txt').write_text(
 'V2 TRIAL ACTIVE AT USB ROOT. Native system/vendor preserved here in emmc/.\n'
 'To restore: disable root CtvUpgrade.bin FIRST, preserve trial payload, move\n'
 'native emmc/ to root, verify native hashes, then activate the restore container LAST.\n'
 'Restore resets user data. Full backup remains in SberTV_Backup_20261107.\n')
identity()
# Activate only after readback of the final payload paths.
copy(B/'install-CtvUpgrade.bin.candidate',U/'CtvUpgrade.bin')
verify(U/'CtvUpgrade.bin',EXPECTED['install-CtvUpgrade.bin.candidate'],16416)
subprocess.run(['sync'],check=True)
(B/'USB-V2-PREPARED.json').write_text(json.dumps({
 'prepared_at':datetime.datetime.now().astimezone().isoformat(), 'disk':disk,
 'active_files_sha256':EXPECTED,'full_backup_readback_verified':True,
 'joined_emmc_sha256':joined.hexdigest(),'native_payload_preserved':'ATV_ROLLBACK/emmc',
 'tv_written':False,'usb_ejected':False},indent=2)+'\n')
print('V2 USB READY; TV NOT WRITTEN',flush=True)
