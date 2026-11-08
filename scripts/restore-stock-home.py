#!/usr/bin/env python3
"""Restore only the recorded stock HOME after preview installation."""
import datetime
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
helpers = runpy.run_path(str(ROOT / 'scripts/preview-freemytv.py'), run_name='helpers')
shell = helpers['shell']
env = shell.__globals__
journal = ROOT / 'reports' / ('restore-stock-home-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
journal.mkdir(parents=True)
env['JOURNAL'] = journal
write = helpers['write']
snapshot = helpers['snapshot']
stock_ok = helpers['stock_ok']
HOME = helpers['HOME']
print(f'Journal: {journal}')
print('Restore recorded Sber HOME only. No package changes, preview launch or reboot.')
try:
    if shell('Current user', 'am', 'get-current-user') != '0':
        raise RuntimeError('Current user is not 0')
    before = snapshot('before')
    current = before['home'].splitlines()[-1]
    if current not in ['android/com.android.internal.app.ResolverActivity', HOME]:
        raise RuntimeError('Unexpected HOME; stop for review')
    probe = dict(before)
    probe['home'] = HOME
    stock_ok(probe)
    write(journal / 'planned-change.txt', 'Restore saved HOME: ' + HOME + '\nNo other changes authorized.\n')
    if current != HOME:
        print(shell('Restore stock HOME', 'cmd', 'package', 'set-home-activity', '--user', '0', HOME))
    after = snapshot('after')
    stock_ok(after)
    for key in before:
        if key not in ['home', 'stock_package'] and before[key] != after[key]:
            raise RuntimeError('Unexpected change: ' + key)
    write(journal / 'status.txt', 'CONFIRMED: stock Sber HOME restored; other captured settings and package lists unchanged. Preview not launched.\n')
    print('CONFIRMED: Sber HOME restored. Press Home on the remote to verify. Preview not launched.')
except Exception as e:
    write(journal / 'status.txt', 'STOPPED: ' + str(e) + '\nInspect journal before retrying.\n')
    print(f'STOPPED: {e}. No further commands. Journal: {journal}')
    raise SystemExit(1)
