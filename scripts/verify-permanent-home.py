#!/usr/bin/env python3
"""Read-only verification of the existing persistent HOME assignment."""
import datetime
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]


def main():
    helpers = runpy.run_path(str(ROOT / 'scripts/preview-freemytv.py'), run_name='helpers')
    shell, write = helpers['shell'], helpers['write']
    journal = ROOT / 'reports' / ('permanent-home-verification-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    journal.mkdir(parents=True)
    shell.__globals__['JOURNAL'] = journal
    print(f'Journal: {journal}\nRead-only. No assignment, package changes or reboot.')
    try:
        if shell('Current user', 'am', 'get-current-user') != '0':
            raise RuntimeError('Unexpected user')
        current = helpers['snapshot']('current')
        if current['home'].splitlines()[-1] not in ['io.freemytv/.HomeActivity', 'io.freemytv/io.freemytv.HomeActivity']:
            raise RuntimeError('Free My TV is not the current HOME; no automatic correction')
        stock = dict(current)
        stock['home'] = helpers['HOME']
        helpers['stock_ok'](stock)
        component = shell('Stock HOME component', 'cmd', 'package', 'resolve-activity', '--brief', '--user', '0', '-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.HOME', '-p', 'ru.sberdevices.starlauncher')
        if component.splitlines()[-1] not in [helpers['HOME'], helpers['HOME'].replace('/.', '/ru.sberdevices.starlauncher.')]:
            raise RuntimeError('Stock HOME component availability not confirmed')
        baseline = json.loads((ROOT / 'reports/home-canary-20261107-174827-607183/after.json').read_text())
        for key in baseline:
            if key not in ['home', 'stock_package'] and baseline[key] != current[key]:
                raise RuntimeError('Difference from canary snapshot: ' + key + '; review needed, nothing changed')
        write(journal / 'status.txt', 'VERIFIED: persistent Free My TV HOME; stock launcher enabled and available; captured settings/package lists match canary. No mutations. Final checkpoint NOT created: awaiting owner cold-start/sleep/wake/stock-screen tests.\n')
        print('VERIFIED: Free My TV remains HOME; Sber launcher enabled and available. No changes made.')
        print('Final checkpoint pending owner tests. Send this output and results.')
    except Exception as e:
        write(journal / 'status.txt', 'STOPPED: ' + str(e) + '\nRead-only; no changes made.\n')
        print(f'STOPPED: {e}. Journal: {journal}')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
