#!/usr/bin/env python3
"""Launch the already-installed preview; no installation or HOME assignment."""
import datetime
from pathlib import Path
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]
helpers = runpy.run_path(str(ROOT / 'scripts/preview-freemytv.py'), run_name='helpers')
shell = helpers['shell']
journal = ROOT / 'reports' / ('freemytv-launch-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
journal.mkdir(parents=True)
shell.__globals__['JOURNAL'] = journal
write = helpers['write']
snapshot = helpers['snapshot']
stock_ok = helpers['stock_ok']
print(f'Journal: {journal}')
print('Launch installed Free My TV only. No HOME assignment, installation or reboot.')
try:
    if shell('Current user', 'am', 'get-current-user') != '0':
        raise RuntimeError('Current user is not 0')
    before = snapshot('before')
    stock_ok(before)
    if 'package:io.freemytv' not in before['enabled']:
        raise RuntimeError('Free My TV is not installed and enabled for user 0')
    write(journal / 'status.txt', 'Baseline saved; direct Activity launch about to be attempted.\n')
    opened = shell('Open preview', 'am', 'start', '--user', '0', '-W', '-n', 'io.freemytv/.HomeActivity')
    print(opened)
    if not re.search(r'^Status:\s*ok\s*$', opened, re.M):
        raise RuntimeError('Activity launch not confirmed')
    after = snapshot('after')
    stock_ok(after)
    for key in before:
        if key != 'stock_package' and before[key] != after[key]:
            raise RuntimeError('Unexpected change: ' + key)
    write(journal / 'status.txt', 'CONFIRMED: preview Activity launched; stock HOME and captured settings/package lists unchanged. Manual visual/remote tests pending.\n')
    print('CONFIRMED: preview launched; Sber remains HOME. No other changes. Test the remote and UI.')
except Exception as e:
    write(journal / 'status.txt', 'STOPPED: ' + str(e) + '\nNo further commands. Preview may already be open.\n')
    print(f'STOPPED: {e}. Journal: {journal}')
    raise SystemExit(1)
