#!/usr/bin/env python3
"""Read-only TV inventory; writes evidence only on this Mac."""
from pathlib import Path
import datetime, json, re, shlex, subprocess, sys
ROOT = Path(__file__).resolve().parents[1]
ADB = '/Users/roman/Library/Android/sdk/platform-tools/adb'
SERIAL = '192.168.18.247:5555'
out = ROOT / 'snapshots' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
out.mkdir(parents=True, mode=0o700)
def run(name, args):
    try:
        p = subprocess.run([ADB, *args], capture_output=True, text=True, timeout=45)
        result = {'command': [ADB, *args], 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except subprocess.TimeoutExpired:
        result = {'command': [ADB, *args], 'returncode': -1, 'stdout': '', 'stderr': 'Timeout after 45 seconds'}
    (out / (name + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2))
    (out / (name + '.txt')).write_text(result['stdout'] + result['stderr'])
    return result
run('connect', ['connect', SERIAL])
state = run('connection', ['-s', SERIAL, 'get-state'])
if state['returncode'] or state['stdout'].strip() != 'device':
    sys.exit('No confirmed device connection. Evidence: ' + str(out))
queries = {
    'identity': 'id; getprop ro.build.fingerprint; getprop ro.build.version.sdk; getprop ro.product.cpu.abilist',
    'user': 'am get-current-user',
    'home': 'cmd package resolve-activity --brief --user 0 -a android.intent.action.MAIN -c android.intent.category.HOME',
    'home-candidates': 'cmd package query-activities --brief --user 0 -a android.intent.action.MAIN -c android.intent.category.HOME',
    'packages-system': 'pm list packages -s -f --user 0',
    'packages-user': 'pm list packages -3 -f --user 0',
    'packages-disabled': 'pm list packages -d --user 0',
    'packages-enabled': 'pm list packages -e --user 0',
    'package-state': 'dumpsys package',
    'screensaver': 'settings --user 0 get secure screensaver_components',
    'screensaver-default': 'settings --user 0 get secure screensaver_default_component',
    'accessibility': 'settings --user 0 get secure enabled_accessibility_services',
    'accessibility-enabled': 'settings --user 0 get secure accessibility_enabled',
    'notification-listeners': 'settings --user 0 get secure enabled_notification_listeners',
    'freemytv-record': 'settings get global free_my_tv_disabled',
    'wifi-owners': "dumpsys wifi | grep -o -E 'cname=[^ ]*|^Wi-Fi is [a-z]+'",
    'tv-inputs': 'dumpsys tv_input',
    'power': 'dumpsys power',
    'storage': 'df -h /system /data',
    'package-command-help': 'cmd package help',
}
results = {name: run(name, ['-s', SERIAL, 'shell', command]) for name, command in queries.items()}
components = re.findall(r'^[A-Za-z][\w.]*/[\w.$]+$', results['home']['stdout'], re.M)
home = components[-1] if components else ''
if home and not home.startswith(('android/', 'io.freemytv/')):
    a = shlex.quote(ADB) + ' -s ' + SERIAL
    remote = shlex.quote('am start -W -n ' + shlex.quote(home))
    restore = shlex.quote('cmd package set-home-activity --user 0 ' + shlex.quote(home))
    text = ('# Review only. No commands in this file were executed.\n'
            '# Return from preview to the recorded stock screen:\n'
            + a + ' shell am force-stop io.freemytv\n' + a + ' shell ' + remote + '\n\n'
            '# Only if the default Home was changed, after separate approval:\n'
            + a + ' shell ' + restore + '\n\n'
            '# Remove the preview only after verifying stock Home and unchanged disabled list:\n'
            + a + ' uninstall io.freemytv\n')
    (out / 'rollback-review.txt').write_text(text)
else:
    (out / 'HOME-UNRESOLVED.txt').write_text('Do not change Home. Resolve the actual stock component first.\n')
print('Snapshot saved: ' + str(out))
print('Home: ' + (home or 'UNRESOLVED'))
print('No TV packages or settings changed. This is an inventory, not a firmware/data backup.')
