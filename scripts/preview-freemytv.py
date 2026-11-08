#!/usr/bin/env python3
"""Install the approved APK and open it explicitly; never assign HOME."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APK = ROOT / 'builds/freemytv-v1.3.0-preview-20261107/FreeMyTV.apk'
HASH = 'f28e9504f6ffb3c27e2dae69a07fc6549f84ada856f67c7256bb797615cf51a9'
BASE = ['/Users/roman/Library/Android/sdk/platform-tools/adb', '-s', '192.168.18.247:5555']
HOME = 'ru.sberdevices.starlauncher/.ui.mainscreen.MainActivity'
PKG = 'io.freemytv'
STAMP = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
JOURNAL = ROOT / 'reports' / ('freemytv-preview-' + STAMP)
RECOVERY = ROOT / 'recovery' / ('preview-' + STAMP)


def write(path, text):
    with path.open('w') as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())


def run(label, args, timeout=25):
    record = {'time': datetime.datetime.now().isoformat(), 'label': label, 'command': BASE + args}
    try:
        p = subprocess.run(BASE + args, capture_output=True, text=True, timeout=timeout)
        record.update(returncode=p.returncode, stdout=p.stdout, stderr=p.stderr)
    except (OSError, subprocess.TimeoutExpired) as e:
        record.update(returncode=None, error=str(e))
    with (JOURNAL / 'commands.jsonl').open('a') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
        f.flush()
        os.fsync(f.fileno())
    if record['returncode'] != 0:
        raise RuntimeError(f'{label}: code={record["returncode"]}')
    if re.search(r'SecurityException|Permission Denial|Error:|Exception occurred|Failure\s*\[', p.stdout + p.stderr, re.I):
        raise RuntimeError(f'{label}: error in response')
    print(f'OK: {label}; code=0')
    return p.stdout.strip()


def shell(label, *args):
    return run(label, ['shell', *args])


def packages(output):
    return sorted(line for line in output.splitlines() if line.startswith('package:'))


def snapshot(label):
    result = {}
    result['home'] = shell(label + ': Home', 'cmd', 'package', 'resolve-activity', '--brief', '--user', '0', '-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.HOME')
    result['stock_package'] = shell(label + ': stock package', 'dumpsys', 'package', 'ru.sberdevices.starlauncher')
    for flag, name in [('-e', 'enabled'), ('-d', 'disabled')]:
        result[name] = packages(shell(label + ': ' + name, 'pm', 'list', 'packages', flag, '--user', '0'))
    for key in ['screensaver_components', 'screensaver_default_component', 'screensaver_enabled', 'voice_interaction_service', 'voice_recognition_service', 'assistant', 'enabled_accessibility_services', 'accessibility_enabled', 'enabled_notification_listeners']:
        result[key] = shell(label + ': ' + key, 'settings', '--user', '0', 'get', 'secure', key)
    write(JOURNAL / (label + '.json'), json.dumps(result, ensure_ascii=False, indent=2))
    return result


def stock_ok(data):
    home = data['home'].splitlines()[-1] if data['home'] else ''
    if home not in [HOME, HOME.replace('/.', '/ru.sberdevices.starlauncher.')]:
        raise RuntimeError('Unexpected HOME resolver; stop')
    if 'package:ru.sberdevices.starlauncher' not in data['enabled']:
        raise RuntimeError('Stock launcher is not enabled')
    # Updated system apps also appear under "Hidden system packages".
    # Only the active Packages section describes the installed update.
    sections = re.findall(r'^Packages:\r?\n(.*?)(?=^\S|\Z)', data['stock_package'], re.M | re.S)
    if len(sections) != 1:
        raise RuntimeError('Cannot identify active Packages section')
    entries = re.findall(r'^  Package \[([^\]]+)\]', sections[0], re.M)
    if entries != ['ru.sberdevices.starlauncher']:
        raise RuntimeError('Unexpected active package entries')
    rows = re.findall(r'^[ \t]*User 0:[^\r\n]*\binstalled=(?:true|false)\b[^\r\n]*$', sections[0], re.M)
    if len(rows) != 1 or 'installed=true' not in rows[0] or not re.search(r'\benabled=[01]\b', rows[0]):
        raise RuntimeError('Stock launcher user state is unexpected')
    # Successful resolution of this exact component also confirms that it is available.


def main():
    JOURNAL.mkdir(parents=True)
    RECOVERY.mkdir(parents=True)
    print(f'Journal: {JOURNAL}')
    print('Approved: install io.freemytv and open preview only. No HOME assignment or reboot.')
    try:
        if hashlib.sha256(APK.read_bytes()).hexdigest() != HASH:
            raise RuntimeError('APK checksum mismatch')
        if run('Connection', ['get-state']) != 'device':
            raise RuntimeError('Device not ready')
        if shell('Current user', 'am', 'get-current-user') != '0':
            raise RuntimeError('Current user must be 0')
        existing = packages(shell('Existing Free My TV', 'pm', 'list', 'packages', '-u', PKG))
        if 'package:' + PKG in existing:
            raise RuntimeError('Free My TV already exists or has retained state; no replacement allowed')
        before = snapshot('before')
        stock_ok(before)
        write(RECOVERY / 'before.json', json.dumps(before, ensure_ascii=False, indent=2))
        rollback = '\n'.join([
            'Preview recovery only if needed; stop on first nonzero return code.',
            shlex.join(BASE + ['shell', 'am', 'force-stop', '--user', '0', PKG]),
            shlex.join(BASE + ['shell', 'am', 'start', '--user', '0', '-W', '-n', HOME]),
            '', 'Only if HOME assignment unexpectedly changed; not executed by this script:',
            shlex.join(BASE + ['shell', 'cmd', 'package', 'set-home-activity', '--user', '0', HOME]),
            'Never enable/disable other packages. Leave SberPlay disabled. No data clearing.',
        ])
        write(RECOVERY / 'rollback.txt', rollback + '\n')
        write(JOURNAL / 'rollback.txt', rollback + '\n')
        write(JOURNAL / 'status.txt', 'Baseline and rollback saved. Installation about to be attempted.\n')
        installed = run('Install', ['install', '--user', '0', str(APK)], timeout=180)
        if 'Success' not in installed.splitlines():
            raise RuntimeError('Installer did not confirm Success; inspect journal before retrying')
        installed_state = snapshot('installed')
        stock_ok(installed_state)
        compare(before, installed_state)
        opened = shell('Open preview', 'am', 'start', '--user', '0', '-W', '-n', PKG + '/.HomeActivity')
        print(opened)
        if not re.search(r'^Status:\s*ok\s*$', opened, re.M):
            raise RuntimeError('Activity launch not confirmed')
        after = snapshot('after')
        stock_ok(after)
        compare(before, after)
        write(JOURNAL / 'status.txt', 'CONFIRMED: APK installed, preview activity launched; protected settings and other package enabled/disabled lists unchanged. Manual UI tests pending.\n')
        print('CONFIRMED: preview launched. Stock HOME/settings/package states unchanged. No reboot.')
        print('Do not select Home Screen -> Free My TV or enable special permissions. Test the remote and UI.')
    except Exception as e:
        write(JOURNAL / 'status.txt', 'STOPPED: ' + str(e) + '\nInstallation or launch may already have occurred. Inspect journal; do not rerun blindly.\n')
        print(f'STOPPED: {e}\nNo more commands. Send journal path: {JOURNAL}')
        raise SystemExit(1)


def compare(before, after):
    for key in before:
        if key == 'stock_package':
            continue  # Full dump contains unrelated, changing package-history counters.
        old, new = before[key], after[key]
        if key in ['enabled', 'disabled']:
            old = [x for x in old if x != 'package:' + PKG]
            new = [x for x in new if x != 'package:' + PKG]
        if old != new:
            raise RuntimeError(f'Unexpected change: {key}; stop and inspect snapshots')
    if 'package:' + PKG not in after['enabled']:
        raise RuntimeError('Installed app not enabled for user 0')


if __name__ == '__main__':
    main()
