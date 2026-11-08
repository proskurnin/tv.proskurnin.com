#!/usr/bin/env python3
"""Remove only Proskurnin's Home key filter and restore Google Home; no package disabling."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--restore',action='store_true');p.add_argument('--serial',default='192.168.178.105:5555');a=p.parse_args()
if not a.restore:p.error('Pass --restore to restore Google Home. Also turn off startup in Proskurnin appearance settings.')
base=['/Users/roman/Library/Android/sdk/platform-tools/adb','-s',a.serial,'shell']
if subprocess.check_output(base+['pm','list','packages','local.proskurnin.homerouter'],text=True).strip():
 sys.exit(subprocess.call([sys.executable,str(Path(__file__).with_name('restore-home-router.py')),'--restore','--serial',a.serial]))
raw=subprocess.check_output(base+['settings','get','secure','enabled_accessibility_services'],text=True).strip()
entries=[] if raw in ('','null') else raw.split(':')
entries=[x for x in entries if x not in ('local.proskurnin.preview/.HomeKeyService','local.proskurnin.preview/local.proskurnin.preview.HomeKeyService')]
if entries:subprocess.run(base+['settings','put','secure','enabled_accessibility_services',':'.join(entries)],check=True)
else:
 subprocess.run(base+['settings','delete','secure','enabled_accessibility_services'],check=True)
 subprocess.run(base+['settings','put','secure','accessibility_enabled','0'],check=True)
subprocess.run(base+['cmd','package','set-home-activity','--user','0','com.google.android.tvlauncher/.MainActivity'],check=True)
print('Google Home restored. Turn off “Запуск после включения ТВ” in Proskurnin appearance settings to stop its boot launch.')
