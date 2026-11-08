#!/usr/bin/env python3
"""User-authorized single-package change; stop on first failure, never reboot."""
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ADB = '/Users/roman/Library/Android/sdk/platform-tools/adb'
BASE = [ADB, '-s', '192.168.18.247:5555']
PACKAGE = 'ru.sberdevices.sberplay'
JOURNAL = ROOT / 'reports' / ('sberplay-batch-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
JOURNAL.mkdir(parents=True)
LOG = JOURNAL / 'commands.jsonl'


def save(name, text):
    with (JOURNAL / name).open('w') as file:
        file.write(text)
        file.flush()
        os.fsync(file.fileno())


def run(label, args):
    command = BASE + args
    record = {'time': datetime.datetime.now().isoformat(), 'label': label, 'command': command}
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=25)
        record.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
    except (subprocess.TimeoutExpired, OSError) as error:
        record.update(error=str(error), returncode=None)
    with LOG.open('a') as file:
        file.write(json.dumps(record, ensure_ascii=False) + '\n')
        file.flush()
        os.fsync(file.fileno())
    if record['returncode'] != 0:
        raise RuntimeError(f'{label}: code={record["returncode"]}; see journal')
    if re.search(r'SecurityException|Permission Denial|Error:|Exception occurred|Failure\s*\[', result.stdout + result.stderr, re.I):
        raise RuntimeError(f'{label}: error in response; see journal')
    print(f'OK: {label}; code=0')
    return result.stdout.strip()


def state(dump):
    # "Package Changes" also contains a bare "User 0:" heading.
    # Match only package-state rows containing an installed flag.
    lines = re.findall(r'^[ \t]*User 0:[^\r\n]*\binstalled=(?:true|false)\b[^\r\n]*$', dump, re.M)
    if len(lines) != 1 or 'installed=true' not in lines[0]:
        raise RuntimeError('Cannot identify installed package state for user 0')
    match = re.search(r'\benabled=(\d+)\b', lines[0])
    if not match:
        raise RuntimeError('Missing enabled state')
    return int(match.group(1))


print('Only ru.sberdevices.sberplay, user 0. No APK/data deletion or reboot.')
print(f'Journal: {JOURNAL}')
try:
    if run('Connection', ['get-state']) != 'device':
        raise RuntimeError('Device is not ready')
    if run('Current user', ['shell', 'am', 'get-current-user']) != '0':
        raise RuntimeError('Current user changed; no modification allowed')
    before = run('Before', ['shell', 'dumpsys', 'package', PACKAGE])
    save('before.txt', before + '\n')
    if state(before) != 0:
        raise RuntimeError('Expected enabled=0; state changed, stopping without modification')
    rollback = BASE + ['shell', 'pm', 'default-state', '--user', '0', PACKAGE]
    save('rollback.txt', 'Original: user 0, installed=true, enabled=0 (default).\n'
         'Run ONLY if reverting this batch. Stop on nonzero return code.\n'
         + shlex.join(rollback) + '\n'
         'Then read back and confirm User 0 enabled=0:\n'
         + shlex.join(BASE + ['shell', 'dumpsys', 'package', PACKAGE]) + '\n'
         'No other package/component changes are authorized.\n')
    save('status.txt', 'Snapshot and rollback saved. Disable command about to be attempted.\n')
    output = run('Disable SberPlay', ['shell', 'pm', 'disable-user', '--user', '0', PACKAGE])
    print(output)
    after = run('After', ['shell', 'dumpsys', 'package', PACKAGE])
    save('after.txt', after + '\n')
    if state(after) != 3:
        raise RuntimeError('Readback does not confirm enabled=3; stop and inspect journal')
    save('status.txt', 'CONFIRMED: user 0 enabled=0 -> enabled=3 (disabled-user).\nNo further TV changes performed. Manual functional tests pending.\n')
    print('CONFIRMED: SberPlay disabled for user 0 (enabled=3). No reboot.')
except Exception as error:
    save('status.txt', 'STOPPED: ' + str(error) + '\nDo not repeat blindly. Check commands.jsonl; a disable attempt may have occurred.\n')
    print(f'STOPPED: {error}\nNo further commands will run. Journal: {JOURNAL}')
    raise SystemExit(1)
