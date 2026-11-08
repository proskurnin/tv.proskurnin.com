#!/usr/bin/env python3
"""Install and open the isolated, owner-requested UI preview; never assign HOME."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'io.freemytv.kitchenpreview'
APK = ROOT / 'builds/kitchen-preview-v1/FreeMyTV.apk'
HASH = '0ea877f5747225334d341f5ac0347194799a3a7d7251580ade03147180d8393f'


def compare(before, after):
    for key in before:
        if key == 'stock_package':
            continue
        old, new = before[key], after[key]
        if key in ['enabled', 'disabled']:
            old = [v for v in old if v != 'package:' + PACKAGE]
            new = [v for v in new if v != 'package:' + PACKAGE]
        if old != new:
            raise RuntimeError('Unexpected change: ' + key)
    if 'package:' + PACKAGE not in after['enabled']:
        raise RuntimeError('Test app is not enabled')


def main():
    h = runpy.run_path(str(ROOT / 'scripts/preview-freemytv.py'), run_name='helpers')
    shell, run, write, snapshot = h['shell'], h['run'], h['write'], h['snapshot']
    journal = ROOT / 'reports' / ('kitchen-preview-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    journal.mkdir(parents=True)
    shell.__globals__['JOURNAL'] = journal
    print(f'Journal: {journal}\nIsolated UI preview only. No HOME assignment, package disabling or reboot.')
    try:
        if hashlib.sha256(APK.read_bytes()).hexdigest() != HASH:
            raise RuntimeError('APK hash mismatch')
        if shell('Current user', 'am', 'get-current-user') != '0':
            raise RuntimeError('Unexpected user')
        existing = shell('Existing preview', 'pm', 'list', 'packages', '-u', PACKAGE)
        if 'package:' + PACKAGE in existing.splitlines():
            raise RuntimeError('Preview already exists; stop to inspect, do not replace or clear it')
        before = snapshot('before')
        if not before['home'] or 'ResolverActivity' in before['home']:
            raise RuntimeError('HOME is not resolved before installation')
        write(journal / 'return.txt', 'Press Home to leave preview; existing HOME is unchanged.\nOptional removal of this preview only:\n' + h['BASE'][0] + ' -s 192.168.18.247:5555 shell pm uninstall --user 0 ' + PACKAGE + '\nNo other package/data changes.\n')
        installed = run('Install isolated preview', ['install', '--user', '0', str(APK)], timeout=180)
        if 'Success' not in installed.splitlines():
            raise RuntimeError('Install did not confirm Success')
        compare(before, snapshot('installed'))
        opened = shell('Open isolated preview', 'am', 'start', '--user', '0', '-W', '-n', PACKAGE + '/.PreviewActivity')
        print(opened)
        if not re.search(r'^Status:\s*ok\s*$', opened, re.M):
            raise RuntimeError('Activity launch not confirmed')
        compare(before, snapshot('after'))
        for service in ['meminfo', 'gfxinfo']:
            value = shell('Initial ' + service, 'dumpsys', service, PACKAGE + ':home')
            write(journal / (service + '.txt'), value + '\n')
        write(journal / 'status.txt', 'CONFIRMED: isolated preview launched; HOME and other captured settings/package states unchanged. Physical navigation, theme toggle and performance tests pending.\n')
        print('CONFIRMED: Kitchen Preview launched. Existing HOME unchanged. Test arrows, OK, Back, apps, HDMI and both themes.')
    except Exception as e:
        write(journal / 'status.txt', 'STOPPED: ' + str(e) + '\nApp may already be installed/launched. Do not repeat blindly. No more commands.\n')
        print(f'STOPPED: {e}. Journal: {journal}')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
