#!/usr/bin/env python3
"""Remove only our resource overlay, restoring the firmware's previous power behavior."""
import argparse
import subprocess
p=argparse.ArgumentParser()
p.add_argument('--restore',action='store_true')
p.add_argument('--serial',default='192.168.178.105:5555')
a=p.parse_args()
if not a.restore:p.error('Use --restore. A subsequent TV restart is required.')
adb=['/Users/roman/Library/Android/sdk/platform-tools/adb','-s',a.serial,'shell']
def sh(c):return subprocess.check_output(adb+[c],text=True).strip()
if not sh('id').startswith('uid=0('):raise SystemExit('Run adb root for this TV, reconnect, then repeat.')
print(sh('test -f /vendor/overlay/ProskurninPowerMenu.apk && mv /vendor/overlay/ProskurninPowerMenu.apk /data/local/tmp/ProskurninPowerMenu.disabled.apk && sync'))
print('Power overlay removed. Restart TV to restore the original behavior (long press may do nothing).')
