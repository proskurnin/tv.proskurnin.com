#!/usr/bin/env python3
"""Install/restore only the v7 animation over verified v6. No partition writes/reboot."""
from pathlib import Path
import argparse, hashlib, json, subprocess, time
ROOT=Path(__file__).resolve().parents[1]
OLD='25940a69880a9ed0ad55154ce242f6e945bd0b131dc0b0b3915f906a309c9dcc'
JPEG='988e732d1ea85b073e30465ef45e5101c20b88a0e2057af13465b70ab21b9bdd'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--serial',default='192.168.18.247:5555');p.add_argument('--apply',action='store_true');p.add_argument('--restore',action='store_true');args=p.parse_args()
 build=ROOT/'builds/proskurnin-boot-v7';report=ROOT/'reports/power-actions-v1';original=report/'bootanimation-v6.zip';new=build/'bootanimation.zip';manifest=json.loads((build/'manifest.json').read_text())
 assert sha(original)==OLD
 assert sha(new)==manifest['files']['bootanimation.zip']
 assert sha(build/'bootlogo.jpg')==JPEG,'Static artwork must stay identical to v5'
 target=original if args.restore else new
 print('Prepared animation only',sha(target),flush=True)
 if not args.apply:return
 adb=[str(Path.home()/'Library/Android/sdk/platform-tools/adb'),'-s',args.serial]
 def run(*cmd):return subprocess.check_output(adb+list(cmd),stderr=subprocess.STDOUT,timeout=60)
 def sh(cmd):return run('shell',cmd).decode().strip()
 def hashremote(path):return sh('sha256sum '+path).split()[0]
 dest='/system/media/bootanimation.zip';tmp=dest+'.proskurnin-v7-new';mounted=False;changed=False
 status={'installed':False,'restored':False,'rebooted':False}
 try:
  run('root');time.sleep(2);run('connect',args.serial)
  assert 'uid=0' in sh('id');assert sh('getprop ro.product.device')=='m7332_eu'
  assert hashremote(dest) in ({OLD,sha(new)} if args.restore else {OLD})
  for path in ['/vendor/tvconfig/boot0.jpg','/vendor/tvconfig/bootlogo.jpg']:assert hashremote(path)==JPEG
  mounts=sh('cat /proc/mounts');assert any(x.split()[1]=='/' and 'ro' in x.split()[3].split(',') for x in mounts.splitlines())
  sh('mkdir -p /data/local/tmp/proskurnin-boot-v7');run('push',str(original),'/data/local/tmp/proskurnin-boot-v7/bootanimation-v6.zip');assert hashremote('/data/local/tmp/proskurnin-boot-v7/bootanimation-v6.zip')==OLD
  sh('mount -o remount,rw /');mounted=True
  def replace(source):
   run('push',str(source),tmp);sh('chown 0:0 '+tmp+' && chmod 0644 '+tmp+' && chcon u:object_r:system_file:s0 '+tmp)
   assert hashremote(tmp)==sha(source);sh('mv '+tmp+' '+dest+' && sync');assert hashremote(dest)==sha(source)
  changed=True;replace(target);status.update(installed=not args.restore,restored=args.restore,sha256=sha(target),readback_verified=True)
 except Exception:
  if changed:
   try:replace(original);status['rollback_verified']=True
   except Exception as error:status['rollback_error']=str(error)
  raise
 finally:
  if mounted:sh('sync && mount -o remount,ro /')
  run('unroot')
  (report/('animation-restore.json' if args.restore else 'animation-install.json')).write_text(json.dumps(status,indent=2)+'\n')
 print('Verified; no reboot, no MPOOL or static logo changes',flush=True)
if __name__=='__main__':main()
