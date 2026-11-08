#!/usr/bin/env python3
"""Read only the identified Netac USB; write an exclusive local dump file."""
import argparse,hashlib,json,os,plistlib,subprocess,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/full-firmware-readonly-20261107-184246/device-dump/emmc-stage2'
SIZE=7818182656
def owner(path):
 if os.geteuid()==0 and os.environ.get('SUDO_UID') and os.environ.get('SUDO_GID'):
  os.chown(path,int(os.environ['SUDO_UID']),int(os.environ['SUDO_GID']))
p=argparse.ArgumentParser();p.add_argument('--device',required=True);p.add_argument('--probe',action='store_true');a=p.parse_args()
if a.device!='/dev/disk10':raise SystemExit('Unexpected device; re-review script for a new identifier')
d=plistlib.loads(subprocess.check_output(['diskutil','info','-plist',a.device]))
if not (d.get('Internal') is False and d.get('WholeDisk') is True and d.get('BusProtocol')=='USB' and d.get('TotalSize')==62264442880 and d.get('IORegistryEntryName')=='Netac OnlyDisk Media' and not d.get('MountPoint')):raise SystemExit('Device identity check failed')
OUT.mkdir(parents=True,exist_ok=True);os.chmod(OUT,0o700);owner(OUT)
with open('/dev/rdisk10','rb',buffering=0) as src:
 if a.probe:
  b=src.read(2097152)
  if len(b)!=2097152:raise SystemExit('Short probe read')
  (OUT/'prefix-2MiB.bin').write_bytes(b);os.chmod(OUT/'prefix-2MiB.bin',0o600);owner(OUT/'prefix-2MiB.bin')
  print(json.dumps({'probe_bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'all_zero':not any(b),'all_ff':all(x==255 for x in b)}));raise SystemExit
 target=OUT/'emmc.bin.partial';h=hashlib.sha256();n=0;last=time.monotonic()
 with target.open('xb') as dst:
  os.chmod(target,0o600);owner(target)
  while n<SIZE:
   b=src.read(min(8*1024*1024,SIZE-n))
   if not b:raise RuntimeError('Unexpected end of USB')
   dst.write(b);h.update(b);n+=len(b)
   if time.monotonic()-last>25:print(f'Read {n}/{SIZE} bytes',flush=True);last=time.monotonic()
  dst.flush();os.fsync(dst.fileno())
 final=OUT/'emmc.bin'
 if final.exists():raise RuntimeError('Final file already exists; leaving partial untouched')
 target.rename(final)
 (OUT/'acquisition.json').write_text(json.dumps({'device':a.device,'usb_capacity':d['TotalSize'],'bytes_read':n,'sha256_during_usb_read':h.hexdigest(),'status':'copied, not yet validated','source_was_opened':'rb'},indent=2))
 print(f'COPIED {n} bytes SHA256 {h.hexdigest()}',flush=True)
