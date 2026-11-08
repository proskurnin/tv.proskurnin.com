#!/usr/bin/env python3
"""Read-only ADB audit. Raw dumps remain in memory; only selected fields are saved."""
from pathlib import Path
import datetime, json, re, shlex, subprocess, sys, os

ROOT = Path(__file__).resolve().parents[1]
ADB = '/Users/roman/Library/Android/sdk/platform-tools/adb'
TARGET = '192.168.18.247:5555'
ERROR = re.compile(r'Permission Denial|Permission denied|SecurityException|not allowed to dump|dumps disabled|Unknown command|Can.t find service|not found|device offline|unauthorized', re.I)
records = []
output = None

def clean(text):
    text = text.replace(TARGET, '<TV>:5555').replace('192.168.18.247', '<TV>')
    text = re.sub(r'(?i)\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b', '<MAC>', text)
    text = re.sub(r'(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '<UUID>', text)
    text = re.sub(r'https?://\S+', '<URL>', text)
    text = re.sub(r'(?i)(?:uniqueId|address)\s*[=:]\s*(?:"[^"]*"|[^,}\s]+)', '<redacted>', text)
    text = re.sub(r'(DisplayDeviceInfo|DisplayInfo)\{"[^"]*"', r'\1{"<display>"', text)
    # Discard whole lines containing potentially identifying fields.
    return '\n'.join(line for line in text.splitlines() if not re.search(
        r'(?i)serial|\bmac\b|\baddress\b|uniqueId|\bdescriptor\b|\bssid\b|\bbssid\b|account|token|password|deviceName|bluetooth_name', line))

def save():
    if output is None:
        return
    (output / 'audit.json').write_text(json.dumps(records, ensure_ascii=False, indent=2))
    sections = ['# Read-only TV audit', 'Raw dumps are not saved. Only selected diagnostic fields are retained.']
    for r in records:
        sections += ['## ' + r['name'], 'Command: `' + r['command'] + '`',
                     'Exit: ' + str(r['returncode']), '```text\n' + r['output'] + '\n```']
    (output / 'audit.md').write_text('\n\n'.join(sections) + '\n')

def collect(name, args, select=None, check=True):
    global output
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=60)
        raw = p.stdout + p.stderr
        rc = p.returncode
    except subprocess.TimeoutExpired:
        raw, rc = 'Command timed out after 60 seconds; audit stopped.', -1
    bad = rc != 0 or (check and ERROR.search(raw))
    if select:
        retained = '\n'.join(line for line in raw.splitlines() if select.search(line))
        if bad:
            retained += '\n' + '\n'.join(line for line in raw.splitlines() if ERROR.search(line))
    else:
        retained = raw
    records.append({'name': name, 'command': clean(shlex.join(args)),
                    'returncode': rc, 'output': clean(retained), 'blocked': bool(bad)})
    save()
    if bad:
        print('STOP: ' + name + '. No fallback or bypass attempted.')
        print('Report: ' + str(output))
        sys.exit(1)
    print('OK: ' + name)
    return p.stdout

def shell(name, command, pattern=None):
    return collect(name, [ADB, '-s', TARGET, 'shell', command],
                   re.compile(pattern, re.I) if pattern else None)

def main():
    global output
    if not Path(ADB).is_file():
        sys.exit('ADB missing. Nothing installed or attempted.')
    print('This opens ADB to the previously agreed TV address. TV commands only read data.')
    print('If the TV asks to allow debugging, confirm only the request for your Mac.')
    collect('macOS', ['sw_vers'], check=False)
    collect('Mac CPU', ['uname', '-m'], check=False)
    collect('ADB version', [ADB, 'version'], check=False)
    output = ROOT / 'snapshots' / ('readonly-audit-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    output.mkdir(mode=0o700)
    collect('Connect', [ADB, 'connect', TARGET])
    input('Confirm the prompt on the TV if shown, then press Enter here. Ctrl+C cancels: ')
    state = collect('Connection state', [ADB, '-s', TARGET, 'get-state'])
    if state.strip() != 'device':
        sys.exit('No device connection; stopped.')
    shell('Shell identity', 'id')
    shell('Current user', 'am get-current-user')
    props = ['ro.product.manufacturer','ro.product.brand','ro.product.model','ro.product.name',
             'ro.product.device','ro.product.board','ro.board.platform','ro.hardware',
             'ro.build.display.id','ro.build.id','ro.build.version.incremental','ro.build.fingerprint',
             'ro.build.version.release','ro.build.version.sdk','ro.build.version.security_patch',
             'ro.product.cpu.abilist','ro.product.cpu.abi','ro.config.low_ram',
             'ro.build.type','ro.debuggable','ro.secure','ro.boot.verifiedbootstate','ro.boot.flash.locked']
    shell('Build and hardware', '; '.join('printf '+shlex.quote(p+'=')+'; getprop '+p for p in props))
    shell('CPU', 'cat /proc/cpuinfo', r'^\s*(processor|model name|CPU architecture|CPU implementer|CPU part|Hardware|Features)\s*:')
    shell('RAM', 'cat /proc/meminfo', r'^(MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree):')
    shell('Storage', 'df -h /system /data')
    shell('Display size', 'wm size')
    shell('Display density', 'wm density')
    shell('Display modes', 'dumpsys display', r'DisplayDeviceInfo|DisplayInfo|supportedModes|activeMode|mActiveMode|refreshRate|fps|modeId|mDefaultMode')
    shell('Home', 'cmd package resolve-activity --brief --user 0 -a android.intent.action.MAIN -c android.intent.category.HOME')
    shell('Home candidates', 'cmd package query-activities --brief --user 0 -a android.intent.action.MAIN -c android.intent.category.HOME')
    for key in ['screensaver_components','screensaver_default_component','screensaver_enabled',
                'voice_interaction_service','voice_recognition_service','assistant',
                'enabled_accessibility_services','accessibility_enabled']:
        shell('Secure setting: '+key, 'settings --user 0 get secure '+key)
    for key in ['hdmi_control_enabled','hdmi_control_auto_device_off_enabled',
                'hdmi_control_auto_wakeup_enabled','bluetooth_on']:
        shell('Global setting: '+key, 'settings get global '+key)
    for flag, label in [('-s','System packages'),('-3','User packages'),('-d','Disabled packages')]:
        shell(label, 'pm list packages '+flag+' --user 0')
    shell('Package components and permissions', 'dumpsys package',
          r'^\s*(Package \[|userId=|sharedUser=|versionCode=|versionName=|flags=|privateFlags=|pkgFlags=|User 0:|[a-zA-Z][\w.]*\.permission\.[\w.]+)|[\w.]+/[\w.$]+|VoiceInteractionService|TV_INPUT_HARDWARE|TV_INPUT_BUTTON|CONNECT_INPUT|AddAccessory')
    services = shell('Available dump services', 'dumpsys -l')
    service_names = set(services.split())
    checks = [
        ('dreams','Dream service',r'mCurrentDream|mDreamComponents|mDreamsEnabled|mIsDreaming'),
        ('voiceinteraction','Voice service',r'mComponent|mCurInteractor|mCurRecognizer|mServiceComponent|mSessionComponent|mRecognitionService|mInteractorComponent|mRecognizerComponent|mImpl|mInfo|mSupports'),
        ('tv_input','TV inputs',r'TvInputInfo|ComponentInfo|hdmi_port=|mService|serviceStateMap'),
        ('hdmi_control','HDMI CEC',r'mHdmiControlEnabled|mIsCecAvailable|mCecVersion|mSystemAudio|mArc|mAuto|mActiveSource|mActiveRoutingPath|mPortInfo|port_id|cec_supported|arc_supported'),
        ('input','Remote input capabilities',r'^\s*(Device \d+:|Sources:|KeyboardType:|Keyboard Type:|KeyLayoutFile:|KeyCharacterMapFile:|ControllerNumber:|HasMic:|Classes:)'),
        ('bluetooth_manager','Bluetooth state',r'^\s*(enabled:|state:|mEnable\s*=|mState\s*=|mQuietEnable\s*=|mBinding\s*=)'),
        ('audio','Audio state',r'^\s*(STREAM_[A-Z_]+:|Muted:|Min:|Max:|mMode=|mRingerMode\w*=|mSafeMediaVolumeState=)|mHdmiSystemAudioSupported'),
        ('power','Power state',r'^\s*(mWakefulness=|mIsPowered=|mWakefulnessChanging=|mStayOn=|mScreenOffTimeoutSetting=|mSleepTimeoutSetting=|mDreamsSupportedConfig=|mDreamsEnabledSetting=)'),
    ]
    for svc, label, pattern in checks:
        if svc not in service_names:
            records.append({'name':label,'command':'dumpsys -l (availability only)', 'returncode':0,
                            'output':'Service not listed; not queried. No alternative attempted.', 'blocked':False})
            save()
            continue
        shell(label, 'dumpsys '+svc, pattern)
    print('\nSnapshot saved: ' + str(output))
    print('No TV settings or packages changed. Send only this path back to the assistant.')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        save()
        print('\nCancelled; no further commands run.')
        sys.exit(130)
