#!/usr/bin/env python3
"""Import device-only credentials into Preview's sandbox using an authorized shell.

Never enables root, grants permissions, changes Home or reads other apps' files.
The credential file must contain separately issued, server-registered Xiaomi tokens.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess

PACKAGE = 'local.proskurnin.xiaomipreview'


def validate(value):
    if not isinstance(value, dict) or set(value) != {'version', 'api_token', 'weather_token'}:
        raise ValueError('Expected version and two device credentials')
    if type(value['version']) is not int or value['version'] != 1:
        raise ValueError('Unsupported format')
    for key in ('api_token', 'weather_token'):
        token = value[key]
        if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{32,128}', token):
            raise ValueError('Invalid device credential format')
    if value['api_token'] == value['weather_token']:
        raise ValueError('Use distinct API and weather credentials')
    return json.dumps(value, separators=(',', ':'))


def read_private(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_uid != os.getuid() or info.st_size > 1024:
            raise ValueError('Configuration must be an owned private regular file, at most 1024 bytes')
        with os.fdopen(fd, 'r', closefd=False) as source:
            return validate(json.load(source))
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--device', default='192.168.18.144:5555')
    parser.add_argument('--adb', default=str(Path.home() / 'Library/Android/sdk/platform-tools/adb'))
    parser.add_argument('--adb-server-port', type=int, default=5037)
    args = parser.parse_args()
    payload = read_private(args.config)

    def adb(*command, input_text=None):
        try:
            r = subprocess.run([args.adb, '-P', str(args.adb_server_port), '-s', args.device, *command], input=input_text,
                               capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            raise RuntimeError('ADB timeout; stopped, do not retry before checking status') from None
        if r.returncode or re.search('permission denied|permission denial|SecurityException|offline|unauthorized|error:', r.stdout+r.stderr, re.I):
            raise RuntimeError('ADB unavailable or operation denied; stopped without bypass')
        return r.stdout

    if adb('get-state').strip() != 'device' or adb('shell', 'getprop ro.product.model').strip() != 'MiTV-MSSP1':
        raise RuntimeError('Unexpected or unavailable TV')
    package = adb('shell', 'dumpsys package '+PACKAGE)
    if not re.search(r'versionCode=(?:5[3-9]|[6-9][0-9]|[1-9][0-9]{2,})\b', package):
        raise RuntimeError('Install the supported Xiaomi Preview first')
    command = ('content call --uri content://'+PACKAGE+'.configuration --method configure --extra '
               + shlex.quote('payload:s:'+payload))
    # Secret sent over stdin, never written to a shared TV path or printed/logged.
    response = adb('shell', 'sh', input_text=command+'\n')
    if 'configured=true' not in response:
        raise RuntimeError('Import not confirmed; stopped')
    print('Device API settings imported. Provider keys remain on the server. Reopen Preview.')


if __name__ == '__main__':
    main()
