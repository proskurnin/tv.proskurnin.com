#!/usr/bin/env python3
"""Start/stop optional aggregate CPU helper on an explicitly selected TV. No root/autostart."""
from pathlib import Path
import argparse,subprocess,json,datetime,time,hashlib,shlex
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--device',required=True);p.add_argument('--model',required=True);p.add_argument('--adb',default='adb');p.add_argument('--port',type=int,default=5037);p.add_argument('action',choices=['start','stop','status']);a=p.parse_args()
 adb=[a.adb,'-P',str(a.port),'-s',a.device];log=[];stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S');folder=ROOT/'reports'/('tv-stats-helper-'+stamp);folder.mkdir(parents=True)
 def run(args,required=True):
  r=subprocess.run(adb+args,capture_output=True,text=True,timeout=20);log.append({'args':args,'rc':r.returncode,'output':r.stdout+r.stderr});(folder/'commands.json').write_text(json.dumps(log,ensure_ascii=False,indent=2))
  if required and r.returncode:raise RuntimeError('ADB command failed; see local report')
  return r
 if run(['shell','getprop','ro.product.model']).stdout.strip()!=a.model:raise RuntimeError('Device model differs; nothing changed')
 jar=ROOT/'builds/proskurnin-stats/stats-bridge.jar';remote='/data/local/tmp/proskurnin-stats.jar';command='CLASSPATH='+remote+' app_process /system/bin local.proskurnin.stats.StatsBridge'
 if a.action=='start':
  if not jar.is_file():raise RuntimeError('Build scripts/build-tv-stats.py first')
  run(['push',str(jar),remote]);digest=run(['shell','sha256sum',remote]).stdout.split()[0]
  if digest!=hashlib.sha256(jar.read_bytes()).hexdigest():raise RuntimeError('Helper checksum mismatch')
  current=run(['shell',command+' --ping'],required=False)
  if current.stdout.strip()!='READY':
   # One restricted process writes only the aggregate CPU line until STOP/reboot.
   run(['shell','CLASSPATH='+remote+' nohup app_process /system/bin local.proskurnin.stats.StatsBridge </dev/null >/dev/null 2>&1 &'])
   time.sleep(2)
 elif a.action=='stop':
  result=run(['shell',command+' --stop']);print(result.stdout.strip());return
 result=run(['shell',command+' --ping']);print(result.stdout.strip())
 if a.action=='start' and result.stdout.strip()!='READY':raise RuntimeError('Helper started but no fresh CPU file is available; see local report')
 print('CPU helper has no boot autostart. Start it again after reboot.')
if __name__=='__main__':main()
