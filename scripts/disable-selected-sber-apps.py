#!/usr/bin/env python3
"""Disable only the five owner-selected apps; preserve data and stop on errors."""
import datetime
import json
from pathlib import Path
import re
import runpy
import shlex

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ('ru.sberdevices.music', 'ru.sberdevices.starkidsroom.prod',
            'com.salute.star', 'ru.sberdevices.survey', 'ru.sberdevices.starbrowser')


def active_state(dump, package):
    sections = re.findall(r'^Packages:\r?\n(.*?)(?=^\S|\Z)', dump, re.M | re.S)
    if len(sections) != 1:
        raise RuntimeError('Cannot identify active Packages section: ' + package)
    section = sections[0]
    if re.findall(r'^  Package \[([^\]]+)\]', section, re.M) != [package]:
        raise RuntimeError('Unexpected active package: ' + package)
    rows = re.findall(r'^[ \t]*User 0:[^\r\n]*\binstalled=(?:true|false)\b[^\r\n]*$', section, re.M)
    if len(rows) != 1 or 'installed=true' not in rows[0]:
        raise RuntimeError('Package not installed for user 0: ' + package)
    match = re.search(r'\benabled=(\d+)\b', rows[0])
    if not match:
        raise RuntimeError('Missing enabled state: ' + package)
    if re.search(r'^\s*sharedUser(?:Id)?=', section, re.M) or 'android.permission.TV_INPUT_HARDWARE' in section:
        raise RuntimeError('Shared UID or hardware TV input dependency requires review: ' + package)
    return int(match.group(1))


def main():
    helpers = runpy.run_path(str(ROOT / 'scripts/preview-freemytv.py'), run_name='helpers')
    shell, write, snapshot = helpers['shell'], helpers['write'], helpers['snapshot']
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    journal = ROOT / 'reports' / ('selected-sber-apps-' + stamp)
    recovery = ROOT / 'recovery' / ('selected-sber-apps-' + stamp)
    journal.mkdir(parents=True)
    recovery.mkdir(parents=True)
    shell.__globals__['JOURNAL'] = journal
    attempted, completed = [], []
    print(f'Journal: {journal}\nRecovery: {recovery}')
    print('Only the five selected apps, user 0. No uninstall, data clearing or reboot.')
    try:
        if shell('Current user', 'am', 'get-current-user') != '0':
            raise RuntimeError('Unexpected user')
        before = snapshot('before')
        if before['home'].splitlines()[-1] not in ['io.freemytv/.HomeActivity', 'io.freemytv/io.freemytv.HomeActivity']:
            raise RuntimeError('Unexpected HOME')
        if 'package:ru.sberdevices.starlauncher' not in before['enabled']:
            raise RuntimeError('Stock Home is not enabled')
        original = {}
        rollback = []
        for pkg in PACKAGES:
            dump = shell('Before ' + pkg, 'dumpsys', 'package', pkg)
            write(recovery / (pkg + '-before.txt'), dump + '\n')
            value = active_state(dump, pkg)
            if value not in [0, 1]:
                raise RuntimeError('Already disabled or unexpected state: ' + pkg)
            original[pkg] = value
            command = helpers['BASE'] + ['shell', 'pm', 'default-state' if value == 0 else 'enable', '--user', '0', pkg]
            rollback.append(pkg + ':\n' + shlex.join(command))
        write(recovery / 'original-states.json', json.dumps(original, indent=2))
        write(recovery / 'before.json', json.dumps(before, ensure_ascii=False, indent=2))
        write(recovery / 'rollback.txt', 'Restore only packages attempted by this batch, in reverse order. Check each return code and read back enabled state. Do not alter component overrides.\n\n' + '\n\n'.join(reversed(rollback)) + '\n')
        for index, pkg in enumerate(PACKAGES, 1):
            # Stop if its state changed between inventory and this individual operation.
            latest = shell('Recheck ' + pkg, 'dumpsys', 'package', pkg)
            if active_state(latest, pkg) != original[pkg]:
                raise RuntimeError('State changed before disable: ' + pkg)
            attempted.append(pkg)
            write(journal / 'progress.json', json.dumps({'attempted': attempted, 'completed': completed}, indent=2))
            print(shell('Disable ' + pkg, 'pm', 'disable-user', '--user', '0', pkg))
            after_dump = shell('Verify ' + pkg, 'dumpsys', 'package', pkg)
            write(journal / (pkg + '-after.txt'), after_dump + '\n')
            if active_state(after_dump, pkg) != 3:
                raise RuntimeError('disabled-user not confirmed: ' + pkg)
            completed.append(pkg)
            write(journal / 'progress.json', json.dumps({'attempted': attempted, 'completed': completed}, indent=2))
            after = snapshot('after-' + str(index))
            for key in before:
                if key == 'stock_package':
                    continue
                expected = before[key]
                if key == 'enabled':
                    expected = sorted(set(expected) - {'package:' + x for x in completed})
                elif key == 'disabled':
                    expected = sorted(set(expected) | {'package:' + x for x in completed})
                if after[key] != expected:
                    raise RuntimeError('Unexpected change: ' + key)
        write(journal / 'status.txt', 'CONFIRMED: all five selected packages disabled-user for user 0. Other captured settings/package states unchanged. No reboot. Manual tests pending.\n')
        print('CONFIRMED: all five selected apps disabled; data retained. No other changes or reboot.')
    except Exception as e:
        write(journal / 'status.txt', 'STOPPED: ' + str(e) + '\nAttempted: ' + ', '.join(attempted) + '\nConfirmed disabled: ' + ', '.join(completed) + '\nInspect journal; do not rerun blindly.\n')
        print(f'STOPPED: {e}. No further commands. Journal: {journal}')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
