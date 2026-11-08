#!/usr/bin/env python3
"""Prepare native rollback after v2, only when explicitly requested. No TV access."""
import datetime, hashlib, json, os, plistlib, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'builds/atv9-diagnostic-v2'
U=Path('/Volumes/TVBACKUP')
def identity():
    v=plistlib.loads(subprocess.check_output(['diskutil','info','-plist',str(U)]))
    d=plistlib.loads(subprocess.check_output(['diskutil','info','-plist',v['ParentWholeDisk']]))
    assert v['VolumeUUID']=='4F325942-BA3F-3F27-9B08-CFFB99E29E02'
    assert v['FilesystemType']=='msdos' and v['MountPoint']==str(U)
    assert d['Internal'] is False and d['BusProtocol']=='USB'
    assert d['IORegistryEntryName']=='Netac OnlyDisk Media' and d['Size']==62264442880
    return v['ParentWholeDisk']
def verify(p,h,size):
    assert p.stat().st_size==size,str(p)
    with p.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==h,str(p)
    print('VERIFIED',p,flush=True)
disk=identity()
assert not (U/'ATV_V2_FAILED').exists()
assert not (U/'CtvUpgrade.v2.completed.disabled').exists()
m=json.loads((B/'manifest.json').read_text())['files']
n={x['file']:x for x in json.loads((B/'rollback-verification.json').read_text())['files']}
for part in ['system','vendor']:
    v=m[f'{part}.experimental.bin']; verify(U/f'emmc/{part}.bin',v['sha256'],v['bytes'])
    v=n[f'{part}.bin']; verify(U/f'ATV_ROLLBACK/emmc/{part}.bin',v['sha256'],v['bytes'])
v=m['install-CtvUpgrade.bin.candidate']; verify(U/'CtvUpgrade.bin',v['sha256'],v['bytes'])
v=m['restore-CtvUpgrade.bin.candidate']
restore=U/'ATV_ROLLBACK/restore-CtvUpgrade.bin.disabled'
verify(restore,v['sha256'],v['bytes'])
identity()
(U/'CtvUpgrade.bin').rename(U/'CtvUpgrade.v2.completed.disabled')
subprocess.run(['sync'],check=True)
(U/'ATV_V2_FAILED').mkdir()
(U/'emmc').rename(U/'ATV_V2_FAILED/emmc')
(U/'ATV_ROLLBACK/emmc').rename(U/'emmc')
for name,v in n.items(): verify(U/'emmc'/name,v['sha256'],v['bytes'])
identity()
with (U/'CtvUpgrade.bin').open('xb') as f:
    f.write(restore.read_bytes()); f.flush(); os.fsync(f.fileno())
v=m['restore-CtvUpgrade.bin.candidate']; verify(U/'CtvUpgrade.bin',v['sha256'],v['bytes'])
(U/'ATV_ROLLBACK/README.txt').write_text('NATIVE RESTORE ACTIVE AT USB ROOT. Native payload moved to root emmc/.\nV2 payload preserved in ATV_V2_FAILED/emmc/. Restore resets data.\n')
subprocess.run(['sync'],check=True)
(B/'USB-V2-ROLLBACK-PREPARED.json').write_text(json.dumps({
 'prepared_at':datetime.datetime.now().astimezone().isoformat(),'disk':disk,
 'tv_restore_completed':False,'native_files':n},indent=2)+'\n')
print('NATIVE ROLLBACK USB READY; TV NOT WRITTEN',flush=True)
