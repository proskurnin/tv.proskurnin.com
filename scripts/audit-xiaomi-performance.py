#!/usr/bin/env python3
"""Passive, bounded Xiaomi performance snapshot. No installation or device mutation."""
import argparse,datetime,json,re,subprocess,time
from pathlib import Path

COMMANDS=[
 ('model','getprop ro.product.model'),
 ('identity','getprop ro.product.device; getprop ro.build.fingerprint; getprop ro.build.version.sdk; getprop ro.product.cpu.abilist'),
 ('memory','cat /proc/meminfo'),
 ('storage','df -h /data'),
 ('cpu','dumpsys cpuinfo'),
 ('process-memory','dumpsys meminfo'),
 ('user-packages','pm list packages -3'),
 ('disabled-packages','pm list packages -d'),
 ('home','cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME'),
 ('services-settings','settings get secure voice_interaction_service; settings get secure screensaver_components; settings get secure enabled_accessibility_services'),
 ('cleaner-package','dumpsys package com.ram.tv'),
 ('analytics-package','dumpsys package com.miui.tv.analytics'),
 ('statistics-package','dumpsys package com.xiaomi.statistic'),
 ('webcontent-package','dumpsys package com.xm.webcontent'),
 ('memory-later','cat /proc/meminfo'),
 ('cpu-later','dumpsys cpuinfo'),
]

def filtered(name,text):
    # Do not retain broad package dumps, extras or any account-related output.
    if name.endswith('-package'):
        text='\n'.join(line for line in text.splitlines() if re.search(r'^\s*(Package \[|versionCode=|versionName=|codePath=|resourcePath=|userId=|pkgFlags=|flags=|privateFlags=|User 0:|enabledComponents:|disabledComponents:)',line))+'\n'
    return re.sub(r'(?i)(?:[0-9a-f]{2}:){5}[0-9a-f]{2}','<MAC redacted>',text)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--adb',required=True);p.add_argument('--port',default='5038');p.add_argument('--device',default='192.168.18.144:5555');p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True);history=[]
    prefix=[a.adb,'-P',a.port,'-s',a.device]
    def run(name,args):
        started=datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            r=subprocess.run(prefix+args,capture_output=True,text=True,timeout=15)
            row={'name':name,'command':args,'at':started,'exit_code':r.returncode}
            out=filtered(name,r.stdout[:250000]);err=r.stderr[:2000]
            if r.returncode or re.search('permission denial|permission denied|device offline|still authorizing',out+' '+err,re.I):row['blocked']=True
            (a.output/(name+'.txt')).write_text(out+('\nSTDERR: '+err if err else ''))
        except subprocess.TimeoutExpired:row={'name':name,'command':args,'at':started,'blocked':True,'error':'timeout'};out=''
        history.append(row);(a.output/'commands.json').write_text(json.dumps(history,ensure_ascii=False,indent=2)+'\n')
        if row.get('blocked'):raise SystemExit('STOP '+name+': command not available; no bypass or retry')
        print(name+': OK',flush=True);return out
    if run('adb-state',['get-state']).strip()!='device':raise SystemExit('STOP: ADB not authorized')
    for name,cmd in COMMANDS:
        result=run(name,['shell',cmd])
        if name=='model' and result.strip()!='MiTV-MSSP1':raise SystemExit('STOP: unexpected model; review target before proceeding')
    print('Read-only snapshot complete. No applications launched or changed.')
if __name__=='__main__':main()
