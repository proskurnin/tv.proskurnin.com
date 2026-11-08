#!/usr/bin/env python3
"""Update only the launcher's private weather routing file, preserving adbd mode."""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ADB = '/Users/roman/Library/Android/sdk/platform-tools/adb'
DEVICE = '192.168.178.105:5555'

def adb(*args):
    return subprocess.run([ADB, '-s', DEVICE, *args], text=True, capture_output=True, check=True, timeout=30).stdout

def connect():
    subprocess.run([ADB, 'connect', DEVICE], capture_output=True, check=True, timeout=15)
    adb('wait-for-device')

def main():
    source = ROOT / 'integrations/server/private/weather-routing.json'
    if source.is_symlink() or source.stat().st_mode & 0o077:
        raise ValueError('Weather config must be a private regular file')
    config = json.loads(source.read_text())
    if len(config['token']) < 32 or config['base_url'] != 'https://ru01.firstvds.proskurn.in/tv-api/v1/weather/':
        raise ValueError('Invalid weather configuration')
    initially_root = 'uid=0(' in adb('shell', 'id')
    try:
        if not initially_root:
            adb('root'); connect()
        if 'uid=0(' not in adb('shell', 'id'):
            raise ValueError('This provisioning method requires root adbd')
        directory = '/data/user/0/local.proskurnin.preview/files'
        uid = adb('shell', 'stat -c %u /data/user/0/local.proskurnin.preview').strip()
        if not uid.isdigit(): raise ValueError('Invalid app UID')
        adb('shell', f'mkdir -p {directory}; chown {uid}:{uid} {directory}; chmod 700 {directory}')
        adb('push', str(source), directory + '/weather-routing.json.new')
        adb('shell', f'chown {uid}:{uid} {directory}/weather-routing.json.new; chmod 600 {directory}/weather-routing.json.new; mv {directory}/weather-routing.json.new {directory}/weather-routing.json; restorecon {directory}/weather-routing.json')
        print('Private weather routes updated. Use Weather > Refresh now. No app restart or reboot performed.')
    finally:
        if not initially_root:
            adb('unroot'); connect()

if __name__ == '__main__': main()
