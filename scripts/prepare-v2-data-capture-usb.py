#!/usr/bin/env python3
"""Activate the approved userdata capture on the identified Netac; no TV access."""
import datetime, hashlib, importlib.util, json, os, plistlib, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'builds/atv9-diagnostic-v2/data-capture'
U=Path('/Volumes/TVBACKUP')
CAPTURE='7affa89aae4fe57d00fc773d2d92f1e814e6bb5d233e17ae2ab2614384d98882'
INSTALL='88f9bced8f0eb1ada6a5dae0d1ea1149321ead99f3234f0fe73834f0f698417a'
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
auth=json.loads((B/'AUTHORIZATION.json').read_text())
assert auth['capture_sha256']==CAPTURE and auth['diagnostic_reboot_and_env_approved'] is True
m=json.loads((B/'manifest.json').read_text())
assert m['sha256']==CAPTURE
data=(B/'capture-CtvUpgrade.bin.candidate').read_bytes()
assert len(data)==16416 and hashlib.sha256(data).hexdigest()==CAPTURE
spec=importlib.util.spec_from_file_location('container',ROOT/'scripts/prepare-backup-research.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
text=c.unpack(data); assert c.pack(text)==data
expected=['usb start 0']; offset=0
for x in m['files']:
    assert x['partition_offset']==offset and x['start_sector']*512==3852271616+offset
    n=x['bytes']; assert 0<n<=67108864 and n%512==0
    assert not (U/x['file']).exists()
    expected += [f'mw.b 0x50000000 0xa5 0x{n:x}',
                 f"mmc read 0x50000000 0x{x['start_sector']:x} 0x{n:x}",
                 f"fatwrite usb 0:1 0x50000000 {x['file']} 0x{n:x}"]
    offset+=n
assert offset==3960471552
expected+=['setenv LetvUpgrade_complete 1','setenv ForcePowerOn 0','saveenv']
assert c.commands(text)==expected
assert shutil.disk_usage(U).free>offset+100*1024**2
disabled=U/'CtvUpgrade.v2-before-capture.disabled'
pending=U/'DATA_CAPTURE.pending'
assert not disabled.exists() and not pending.exists()
verify(U/'CtvUpgrade.bin',INSTALL,16416)
# Verify preserved recovery payload without rewriting it.
native=json.loads((ROOT/'builds/atv9-diagnostic-v2/rollback-verification.json').read_text())['files']
for x in native: verify(U/'ATV_ROLLBACK/emmc'/x['file'],x['sha256'],x['bytes'])
backup=json.loads((ROOT/'reports/full-firmware-readonly-20261107-184246/device-dump/usb-archive-manifest.json').read_text())
for x in backup['files']: assert (U/'SberTV_Backup_20261107'/x['file']).stat().st_size==x['bytes']
identity()
# Disable the installer first. Any interruption before final rename leaves it inactive.
(U/'CtvUpgrade.bin').rename(disabled)
subprocess.run(['sync'],check=True)
with pending.open('xb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
verify(pending,CAPTURE,16416)
identity()
pending.rename(U/'CtvUpgrade.bin')
verify(U/'CtvUpgrade.bin',CAPTURE,16416)
subprocess.run(['sync'],check=True)
(B/'USB-PREPARED.json').write_text(json.dumps({
 'prepared_at':datetime.datetime.now().astimezone().isoformat(),'disk':disk,
 'active_sha256':CAPTURE,'previous_installer':disabled.name,
 'native_payload_hashes_verified':True,'backup_preserved':True,
 'tv_executed':False,'usb_ejected':False},indent=2)+'\n')
print('DATA CAPTURE USB READY; TV NOT EXECUTED',flush=True)
