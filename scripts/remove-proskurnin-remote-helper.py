#!/usr/bin/env python3
"""Explicit rollback of only the two input-helper files and their process."""
import argparse,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--remove-helper',action='store_true');p.add_argument('--serial',default='192.168.178.105:5555');a=p.parse_args()
if not a.remove_helper:p.error('Use --remove-helper only when removing the phone-remote input helper.')
adb=['/Users/roman/Library/Android/sdk/platform-tools/adb','-s',a.serial]
def run(*args):return subprocess.check_output(adb+list(args),text=True,timeout=20).strip()
print(run('root'));time.sleep(2);run('connect',a.serial)
try:
 if not run('shell','id').startswith('uid=0('):raise RuntimeError('adb root required on this firmware')
 run('shell','setprop ctl.stop proskurnin_remote')
 pids=subprocess.run(adb+['shell','pidof app_process'],text=True,capture_output=True).stdout.split()
 for pid in pids:
  if not pid.isdecimal():continue
  cmd=subprocess.run(adb+['exec-out','cat','/proc/'+pid+'/cmdline'],capture_output=True).stdout.split(b'\0')
  if b'local.proskurnin.remote.InputBridge' in cmd:run('shell','kill '+pid)
 run('shell','rm -f /vendor/etc/init/proskurnin_remote.rc /vendor/etc/proskurnin-remote/input-bridge.jar')
 run('shell','sync')
 print('Removed only Proskurnin Remote input helper and its autostart. No reboot required.')
finally:
 print(run('unroot'));time.sleep(2);run('connect',a.serial)
