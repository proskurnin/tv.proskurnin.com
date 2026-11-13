#!/usr/bin/env python3
"""Capture read-only Xiaomi CPU/RAM/process/service samples around a user cold start."""
import argparse,datetime,json,subprocess,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--adb',required=True);p.add_argument('--port',default='5038');p.add_argument('--device',default='192.168.18.144:5555');p.add_argument('--output',required=True,type=Path);p.add_argument('--samples',default='0,60,180,300');p.add_argument('--resume-after-off',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=a.resume_after_off);prefix=[a.adb,'-P',a.port,'-s',a.device]
 def run(*cmd,timeout=20):
  return subprocess.run(prefix+list(cmd),capture_output=True,text=True,timeout=timeout)
 def record(tag):
  identity=run('shell','getprop ro.product.model').stdout.strip()
  device=run('shell','getprop ro.product.device').stdout.strip()
  if (identity,device)!=('MiTV-MSSP1','nino'):raise RuntimeError('Wrong TV; stop')
  commands={'cpu':['shell','dumpsys','cpuinfo'],'mem':['shell','cat','/proc/meminfo'],'ps':['shell','top','-b','-n','2','-d','5','-m','25'],'pss':['shell','dumpsys','meminfo'],'services':['shell','dumpsys','activity','services'],'home':['shell','dumpsys','window','windows'],'storage':['shell','df','-k','/data'],'status':['shell','getprop','sys.boot_completed']}
  row={'tag':tag,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model':identity,'device':device,'results':{}}
  for k,cmd in commands.items():
   if k=='ps':
    first=run('shell','top','-b','-n','1','-m','25',timeout=15)
    time.sleep(5)
    second=run('shell','top','-b','-n','1','-m','25',timeout=15)
    row['results'][k]={'rc':max(first.returncode,second.returncode),'text':first.stdout+'\n--- second independent top after 5s ---\n'+second.stdout}
   else:
    r=run(*cmd,timeout=35);row['results'][k]={'rc':r.returncode,'text':r.stdout[-120000:]}
  (a.output/(tag+'.json')).write_text(json.dumps(row,ensure_ascii=False,indent=2))
  with (a.output/'timeline.jsonl').open('a') as f:f.write(json.dumps({'tag':tag,'utc':row['utc'],'focus':row['results']['home']['text'][-600:]},ensure_ascii=False)+'\n')
  print(tag,row['utc'],flush=True)
 initial=run('get-state')
 if a.resume_after_off:
  baseline=a.output/'baseline-before-off.json'
  if not baseline.exists():raise SystemExit('Cannot resume: baseline-before-off.json is missing')
  data=json.loads(baseline.read_text())
  if (data.get('model'),data.get('device'))!=('MiTV-MSSP1','nino'):raise SystemExit('Cannot resume: baseline is not Xiaomi nino')
  if initial.stdout.strip()=='device':raise SystemExit('TV is already online; refusing after-off resume')
 else:
  if initial.returncode or initial.stdout.strip()!='device':raise SystemExit('Connect/authorize ADB first; no changes made')
  record('baseline-before-off')
  input('Use the TV/remote POWER control to fully turn the TV off. Wait until the screen and status LED indicate shutdown, then press Enter here... ')
  if run('get-state').stdout.strip()=='device':raise SystemExit('ADB still sees TV; confirm full power-off, no data was changed')
 print('Waiting for Xiaomi to boot and ADB to return...',flush=True)
 deadline=time.monotonic()+900
 while time.monotonic()<deadline:
  if run('get-state').stdout.strip()=='device':break
  time.sleep(3)
 else:raise SystemExit('ADB did not return within 15 minutes; inspect TV manually')
 points=[int(x) for x in a.samples.split(',')]
 boot_ready=time.monotonic()
 for sec in points:
  end=boot_ready+sec
  while time.monotonic()<end:
   if run('get-state').stdout.strip()!='device':raise SystemExit('TV/ADB disconnected during sample')
   time.sleep(min(3,end-time.monotonic()))
  record('boot-plus-%04ds'%sec)
 print('Capture complete. No package/settings changes or app launches were performed.')
if __name__=='__main__':main()
