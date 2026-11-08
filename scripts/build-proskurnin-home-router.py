#!/usr/bin/env python3
"""Build the permission-free HOME router; no TV access."""
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'builds/proskurnin-home-router'
O = B / 'out'
SDK = Path('/Users/roman/Library/Android/sdk')
BT = SDK / 'build-tools/35.0.0'
AJ = SDK / 'platforms/android-33/android.jar'
JAVA = Path(subprocess.check_output(['/usr/libexec/java_home'], text=True).strip()) / 'bin'
O.mkdir(exist_ok=True)
(O / 'classes').mkdir(exist_ok=True)

def run(*args):
    subprocess.run([str(a) for a in args], check=True)

run(BT/'aapt2', 'link', '-o', O/'base.apk', '-I', AJ, '--manifest', B/'app/AndroidManifest.xml')
run(JAVA/'javac', '-source', '8', '-target', '8', '-bootclasspath', AJ,
    '-encoding', 'UTF-8', '-d', O/'classes', *sorted((B/'app/src').rglob('*.java')))
run(BT/'d8', '--min-api', '28', '--lib', AJ, '--output', O, *sorted((O/'classes').rglob('*.class')))
with zipfile.ZipFile(O/'base.apk', 'a', zipfile.ZIP_DEFLATED) as archive:
    archive.write(O/'classes.dex', 'classes.dex')
run(BT/'zipalign', '-f', '-p', '4', O/'base.apk', O/'aligned.apk')
run(BT/'apksigner', 'sign', '--ks', ROOT/'builds/proskurnin-preview-v1/diagnostic.keystore',
    '--ks-pass', 'pass:diagnostic', '--out', B/'ProskurninHomeRouter.apk', O/'aligned.apk')
run(BT/'apksigner', 'verify', '--min-sdk-version', '28', '--verbose', B/'ProskurninHomeRouter.apk')
