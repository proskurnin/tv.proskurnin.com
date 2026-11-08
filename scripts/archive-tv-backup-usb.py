#!/usr/bin/env python3
"""Copy verified local backup to the selected FAT32 USB, no TV/device writes."""
import hashlib,json,os,plistlib,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'reports/full-firmware-readonly-20261107-184246/device-dump'
USB=Path('/Volumes/TVBACKUP')
info=plistlib.loads(subprocess.check_output(['diskutil','info','-plist',str(USB)]))
assert info.get('VolumeUUID')=='4F325942-BA3F-3F27-9B08-CFFB99E29E02'
assert info.get('FilesystemType')=='msdos' and info.get('BusProtocol')=='USB'
assert info.get('Internal') is False and info['TotalSize']>60000000000
assert shutil.disk_usage(USB).free>8000000000
v=json.loads((R/'complete-verification.json').read_text())
expected={x['role']:x for x in v['files']}
assert expected['emmc']['sha256']=='5ef8a6d9ec6e60c2dbcf76c88299ee832f7d879a701bd0f42328520e93cb9d74'
out=USB/'SberTV_Backup_20261107';out.mkdir(exist_ok=False)
# Prevent accidental rerun on the TV. Preserve the reviewed script under a disabled name.
script=USB/'CtvUpgrade.bin'
if script.exists():
 assert hashlib.sha256(script.read_bytes()).hexdigest()=='40c803fe22472ebd25de827027901d1df19d8c46ebac7832619025d9f3be0be0'
 disabled=USB/'CtvUpgrade.boot-tail.completed.disabled'
 if disabled.exists():raise RuntimeError('Disabled script already exists')
 script.rename(disabled)
records=[];whole=hashlib.sha256();total=0;last=time.monotonic()
with (R/'emmc-stage2/emmc.bin').open('rb') as src:
 for i in range(4):
  length=min(2*1024**3,expected['emmc']['bytes']-total)
  if length<=0:break
  name=f'emmc.bin.part{i:02d}';target=out/name;h=hashlib.sha256();left=length
  with target.open('xb') as dst:
   while left:
    b=src.read(min(8*1024*1024,left))
    if not b:raise RuntimeError('Short source file')
    dst.write(b);h.update(b);whole.update(b);left-=len(b);total+=len(b)
    if time.monotonic()-last>25:print(f'Writing USB {total}/{expected["emmc"]["bytes"]}',flush=True);last=time.monotonic()
   dst.flush();os.fsync(dst.fileno())
  records.append({'file':name,'bytes':length,'sha256':h.hexdigest()})
assert total==expected['emmc']['bytes'] and whole.hexdigest()==expected['emmc']['sha256']
for i in [1,2]:
 name=f'BOOT{i}.BIN';b=(R/'boot-complete'/name).read_bytes();h=hashlib.sha256(b).hexdigest();assert h==expected[f'boot{i}']['sha256']
 with (out/name).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 records.append({'file':name,'bytes':len(b),'sha256':h})
# Read back all destination data; concatenate the split image logically when hashing.
whole2=hashlib.sha256()
for x in records:
 f=out/x['file'];assert f.stat().st_size==x['bytes'];h=hashlib.sha256()
 with f.open('rb') as src:
  while b:=src.read(8*1024*1024):
   h.update(b)
   if x['file'].startswith('emmc.'):whole2.update(b)
 assert h.hexdigest()==x['sha256'];print('Read-back verified:',x['file'],flush=True)
assert whole2.hexdigest()==expected['emmc']['sha256']
manifest={'files':records,'joined_emmc_sha256':whole2.hexdigest(),'usb_readback_verified':True,'restore_tested':False,'automatic_upgrade_file_removed_by_rename':True}
text=json.dumps(manifest,indent=2)
(out/'manifest.json').write_text(text);(R/'usb-archive-manifest.json').write_text(text)
(out/'SHA256SUMS').write_text(''.join(x['sha256']+'  '+x['file']+'\n' for x in records))
(out/'README.txt').write_text('Sber SDX-43U4123B backup, 2026-11-07. Private: contains device and user data.\n'
'User area emmc.bin is split into parts 00 through 03 for FAT32. Join in numeric order on a filesystem supporting files over 4 GB.\n'
'Joined size: 7818182656 bytes. Joined SHA256: '+whole2.hexdigest()+'\n'
'BOOT1.BIN and BOOT2.BIN are separate 4194304-byte boot regions. Final sectors were read twice and overlap checked.\n'
'This is not a flashable USB firmware. Do not rename any of these files CtvUpgrade.bin.\n'
'Restore procedure has NOT been tested. RPMB and hardware eMMC configuration registers are not included.\n'
'The backup stages ran at different times and scripts saved bootloader ENV; this is not an atomic pre-change snapshot.\n')
print('USB BACKUP COMPLETE AND READ-BACK VERIFIED',flush=True)
