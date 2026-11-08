#!/usr/bin/env python3
"""Restore Google as native HOME without uninstalling either launcher. Requires adb root."""
import argparse
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--restore', action='store_true')
p.add_argument('--serial', default='192.168.178.105:5555')
a = p.parse_args()
if not a.restore:
    p.error('Use --restore to restore Google HOME and stop custom boot launching.')
adb = ['/Users/roman/Library/Android/sdk/platform-tools/adb', '-s', a.serial, 'shell']
def shell(command):
    return subprocess.check_output(adb + [command], text=True).strip()
if not shell('id').startswith('uid=0('):
    raise SystemExit('Run adb -s ' + a.serial + ' root, reconnect, then repeat.')
print(shell('pm disable --user 0 local.proskurnin.homerouter/.HomeActivity'))
print(shell('pm disable --user 0 local.proskurnin.preview/.BootHomeReceiver'))
entries = shell('settings get secure enabled_accessibility_services').split(':')
entries = [x for x in entries if x not in ('', 'null', 'local.proskurnin.preview/.HomeKeyService',
           'local.proskurnin.preview/local.proskurnin.preview.HomeKeyService')]
if entries:
    import shlex
    shell('settings put secure enabled_accessibility_services ' + shlex.quote(':'.join(entries)))
else:
    shell('settings delete secure enabled_accessibility_services')
    shell('settings put secure accessibility_enabled 0')
print(shell('cmd package set-home-activity --user 0 com.google.android.tvlauncher/.MainActivity'))
print(shell('cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME'))
print('Google native HOME restored. App and favourites retained; no reboot required.')
