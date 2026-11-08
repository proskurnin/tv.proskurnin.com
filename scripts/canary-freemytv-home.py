#!/usr/bin/env python3
"""Approved canary: change only user 0 HOME, then stop for manual tests."""
import datetime
import json
from pathlib import Path
import runpy
import shlex

ROOT = Path(__file__).resolve().parents[1]
NEW_HOME = 'io.freemytv/.HomeActivity'


def main():
    helpers = runpy.run_path(str(ROOT / 'scripts/preview-freemytv.py'), run_name='helpers')
    shell, write = helpers['shell'], helpers['write']
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    journal = ROOT / 'reports' / ('home-canary-' + stamp)
    recovery = ROOT / 'recovery' / ('home-canary-' + stamp)
    journal.mkdir(parents=True)
    recovery.mkdir(parents=True)
    shell.__globals__['JOURNAL'] = journal
    snapshot, stock_ok = helpers['snapshot'], helpers['stock_ok']
    old_home = helpers['HOME']
    print(f'Journal: {journal}\nRecovery: {recovery}')
    print('Only user 0 HOME assignment. Stock launcher stays enabled. No launch or reboot.')
    try:
        if shell('Current user', 'am', 'get-current-user') != '0':
            raise RuntimeError('Unexpected current user')
        before = snapshot('before')
        stock_ok(before)
        if 'package:io.freemytv' not in before['enabled']:
            raise RuntimeError('Free My TV is not enabled for user 0')
        # Confirm the specific candidate before changing the preferred home.
        candidate = shell('Free My TV HOME candidate', 'cmd', 'package', 'resolve-activity', '--brief', '--user', '0', '-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.HOME', '-p', 'io.freemytv')
        if candidate.splitlines()[-1] not in [NEW_HOME, 'io.freemytv/io.freemytv.HomeActivity']:
            raise RuntimeError('Free My TV HOME candidate not confirmed')
        rollback = shlex.join(helpers['BASE'] + ['shell', 'cmd', 'package', 'set-home-activity', '--user', '0', old_home])
        restore_text = ('Original HOME: ' + old_home + '\n'
                        'Immediate return of HOME assignment (not executed):\n' + rollback + '\n'
                        'Check exit code; stop on error. Then press Home and verify the stock screen.\n'
                        'Do not enable/disable packages or clear data. SberPlay remains disabled.\n')
        for folder in [journal, recovery]:
            write(folder / 'before.json', json.dumps(before, ensure_ascii=False, indent=2))
            write(folder / 'rollback.txt', restore_text)
        write(journal / 'status.txt', 'Snapshot and rollback saved; HOME assignment about to be attempted.\n')
        print(shell('Assign Free My TV HOME', 'cmd', 'package', 'set-home-activity', '--user', '0', NEW_HOME))
        after = snapshot('after')
        if after['home'].splitlines()[-1] not in [NEW_HOME, 'io.freemytv/io.freemytv.HomeActivity']:
            raise RuntimeError('New HOME readback not confirmed')
        probe = dict(after)
        probe['home'] = old_home
        stock_ok(probe)
        stock_candidate = shell('Stock HOME component available', 'cmd', 'package', 'resolve-activity', '--brief', '--user', '0', '-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.HOME', '-p', 'ru.sberdevices.starlauncher')
        if stock_candidate.splitlines()[-1] not in [old_home, old_home.replace('/.', '/ru.sberdevices.starlauncher.')]:
            raise RuntimeError('Stock HOME component availability not confirmed')
        for key in before:
            if key not in ['home', 'stock_package'] and before[key] != after[key]:
                raise RuntimeError('Unexpected change: ' + key)
        write(journal / 'status.txt', 'CONFIRMED: Free My TV is HOME for user 0; stock launcher enabled and its HOME component available. Other captured settings/package lists unchanged. STOPPED for user tests; no reboot.\n')
        print('CONFIRMED: Free My TV is HOME. Stock Sber remains enabled. No reboot.')
        print('Stopped. Press Home and test manually. Do not use the in-app Home Screen switch.')
    except Exception as e:
        write(journal / 'status.txt', 'STOPPED: ' + str(e) + '\nHOME may already have changed. Inspect journal before retrying. Saved rollback.txt is the return command.\n')
        print(f'STOPPED: {e}. No more commands. Journal: {journal}')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
