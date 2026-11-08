#!/usr/bin/env python3
"""Install/remove the separately approved, local power helper. Never issue power commands."""
from pathlib import Path
import argparse,hashlib,json,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
DIR='/vendor/etc/proskurnin-power';JAR=DIR+'/power-bridge.jar';RC='/vendor/etc/init/proskurnin_power.rc';CLASS='local.proskurnin.power.PowerBridge';PID='/data/local/tmp/proskurnin-power.pid'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--serial',default='192.168.18.247:5555');p.add_argument('--apply',action='store_true');p.add_argument('--restore',action='store_true');args=p.parse_args()
 b=ROOT/'builds/proskurnin-power-actions';r=ROOT/'reports/power-actions-v1';r.mkdir(exist_ok=True)
 files=[(b/'power-bridge.jar',JAR),(b/'proskurnin_power.rc',RC)]
 print(json.dumps({'action':'remove helper' if args.restore else 'install helper; menu remains disabled until enabled in launcher','files':{remote:sha(local) for local,remote in files},'reboot':False},indent=2),flush=True)
 if not args.apply:return
 a=[str(Path.home()/'Library/Android/sdk/platform-tools/adb'),'-s',args.serial]
 def run(*cmd):return subprocess.check_output(a+list(cmd),stderr=subprocess.STDOUT,timeout=30)
 def sh(cmd):return run('shell',cmd).decode().strip()
 def exists(path):return sh('if test -f '+path+'; then echo yes; fi')=='yes'
 def stop():
  sh('setprop ctl.stop proskurnin_power')
  if exists(PID):
   pid=sh('cat '+PID)
   if pid.isdigit():
    # Do not kill another app_process or a recycled PID.
    cmd=sh('if test -r /proc/'+pid+'/cmdline; then cat /proc/'+pid+'/cmdline; fi')
    if CLASS in cmd:sh('kill '+pid)
 def archive():
  sh('mkdir -p /data/local/tmp/proskurnin-power-disabled')
  for _,remote in files:
   if exists(remote):sh('mv '+remote+' /data/local/tmp/proskurnin-power-disabled/')
 touched=False;status={'installed':False,'rebooted':False}
 try:
  run('root');time.sleep(2);run('connect',args.serial);assert 'uid=0' in sh('id');assert sh('getprop ro.product.device')=='m7332_eu'
  if args.restore:
   stop();archive();status['removed']=True;print('Removed helper; launcher falls back to original menu',flush=True);return
  assert not any(exists(remote) for _,remote in files),'Existing helper: inspect before replacing'
  baseline={'accessibility':sh('settings get secure enabled_accessibility_services'),'helper_files_previously_present':False,'serial':args.serial}
  (r/'before.json').write_text(json.dumps(baseline,indent=2)+'\n')
  apk=sh('pm path local.proskurnin.preview').split(':',1)[1];run('pull',apk,str(r/'launcher-before.apk'))
  prefs=run('exec-out','cat /data/user/0/local.proskurnin.preview/shared_prefs/preview.xml');f=r/'preview-before.xml';f.write_bytes(prefs);f.chmod(0o600)
  assert 'setsid' in sh('command -v setsid'),'Need detached process launcher'
  assert any(x.split()[1]=='/vendor' and 'rw' in x.split()[3].split(',') for x in sh('cat /proc/mounts').splitlines())
  touched=True;sh('mkdir -p '+DIR+' && chmod 0755 '+DIR)
  for local,remote in files:
   run('push',str(local),remote);sh('chown 0:0 '+remote+' && chmod 0644 '+remote+' && chcon u:object_r:vendor_configs_file:s0 '+remote)
   assert sh('sha256sum '+remote).split()[0]==sha(local)
  sh('sync')
  sh('setsid /system/bin/app_process -Djava.class.path='+JAR+' /system/bin '+CLASS+' </dev/null >/data/local/tmp/proskurnin-power.log 2>&1 & echo $! >'+PID)
  time.sleep(2);pid=sh('cat '+PID);assert pid.isdigit();assert CLASS in sh('cat /proc/'+pid+'/cmdline')
  status.update(installed=True,pid=int(pid),hashes={remote:sha(local) for local,remote in files})
  print('Helper running; no power command executed; menu still controlled by launcher setting',flush=True)
 except Exception:
  if touched:
   try:stop();archive();status['rollback_removed_helper']=True
   except Exception as e:status['rollback_error']=str(e)
  raise
 finally:
  run('unroot');(r/('remove-status.json' if args.restore else 'install-status.json')).write_text(json.dumps(status,indent=2)+'\n')
if __name__=='__main__':main()
