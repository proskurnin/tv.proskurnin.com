#!/usr/bin/env python3
"""Owner-requested Preview tests. Never change HOME, settings or package enabled states."""
import datetime, json, re, runpy, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
h=runpy.run_path(str(ROOT/'scripts/preview-freemytv.py'),run_name='helpers')
k=runpy.run_path(str(ROOT/'scripts/preview-kitchen.py'),run_name='helpers')
JOURNAL=ROOT/'reports'/('kitchen-background-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
JOURNAL.mkdir();h['shell'].__globals__['JOURNAL']=JOURNAL
shell,run=h['shell'],h['run'];PKG='io.freemytv.kitchenpreview'
def capture(name):
 p=subprocess.run(h['BASE']+['exec-out','screencap','-p'],capture_output=True,check=True,timeout=25)
 i=p.stdout.find(b'\x89PNG\r\n\x1a\n')
 if i<0:raise RuntimeError('No screenshot PNG')
 (JOURNAL/(name+'.png')).write_bytes(p.stdout[i:])
def save(name,*args):
 s=shell(name,*args);(JOURNAL/(name+'.txt')).write_text(s+'\n');return s
def launch():
 s=shell('Launch Preview','am','start','--user','0','-W','-n',PKG+'/.PreviewActivity')
 if not re.search(r'^Status:\s*ok\s*$',s,re.M):raise RuntimeError(s)
 return s
if __name__=='__main__':
 print('JOURNAL',JOURNAL,flush=True)
 try:
  assert run('Read-only connection',['get-state'])=='device'
  assert shell('Current user','am','get-current-user')=='0'
  before=h['snapshot']('before');assert 'io.freemytv/.HomeActivity' in before['home'];assert 'package:'+PKG in before['enabled']
  save('baseline-memory','dumpsys','meminfo',PKG+':home')
  save('baseline-temperature','cat','/sys/class/thermal/thermal_zone0/temp')
  result=run('Update Preview only',['install','-r','--user','0',str(ROOT/'builds/kitchen-preview-v1/FreeMyTV.apk')],timeout=180);assert 'Success' in result.splitlines()
  k['compare'](before,h['snapshot']('installed'))
  shell('Cold start: stop Preview only','am','force-stop','--user','0',PKG)
  video='/data/local/tmp/kitchen-background-cold.mp4'
  recording=subprocess.Popen(h['BASE']+['shell','screenrecord','--time-limit','10','--bit-rate','2000000',video],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  time.sleep(.6)
  (JOURNAL/'cold-start.txt').write_text(launch())
  out,err=recording.communicate(timeout=20);(JOURNAL/'recording.txt').write_bytes(out+err)
  if recording.returncode==0:run('Read cold-start recording',['pull',video,str(JOURNAL/'cold-start.mp4')])
  capture('enabled')
  save('enabled-memory','dumpsys','meminfo',PKG+':home')
  save('enabled-frames','dumpsys','gfxinfo',PKG+':home')
  save('background-log','logcat','-d','-s','KitchenBackground:I','AndroidRuntime:E','*:S')
  k['compare'](before,h['snapshot']('after-cold-start'))
  (JOURNAL/'status.txt').write_text('Install and cold launch confirmed. Remaining interaction tests pending.\n')
 except Exception as e:
  (JOURNAL/'status.txt').write_text('STOPPED: '+str(e)+'\nDo not retry blindly.\n');raise
