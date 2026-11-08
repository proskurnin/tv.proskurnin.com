#!/usr/bin/env python3
"""Build a resource-only overlay for the native Android power menu; no TV access."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
B = ROOT/'builds/proskurnin-power-menu'
O = B/'out'
O.mkdir(exist_ok=True)
SDK = Path('/Users/roman/Library/Android/sdk')
BT = SDK/'build-tools/35.0.0'
def run(*args):
    subprocess.run([str(a) for a in args], check=True)
run(BT/'aapt2', 'compile', '--dir', B/'res', '-o', O/'resources.zip')
run(BT/'aapt2', 'link', '-o', O/'base.apk', '-I', SDK/'platforms/android-33/android.jar',
    '--manifest', B/'AndroidManifest.xml', '--auto-add-overlay', O/'resources.zip')
run(BT/'zipalign', '-f', '-p', '4', O/'base.apk', O/'aligned.apk')
run(BT/'apksigner', 'sign', '--ks', ROOT/'builds/proskurnin-preview-v1/diagnostic.keystore',
    '--ks-pass', 'pass:diagnostic', '--out', B/'ProskurninPowerMenu.apk', O/'aligned.apk')
run(BT/'apksigner', 'verify', '--min-sdk-version', '28', '--verbose', B/'ProskurninPowerMenu.apk')
