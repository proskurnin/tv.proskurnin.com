#!/usr/bin/env python3
"""Build a manual 4K surface diagnostic. Never connect, install or change display settings."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tests/android-4k'
DEST = ROOT / 'builds/proskurnin-4k-probe'
DEST.mkdir(exist_ok=True)
SDK = Path(os.environ.get('ANDROID_SDK_ROOT', str(Path.home() / 'Library/Android/sdk')))
BT = SDK / 'build-tools/35.0.0'
ANDROID = SDK / 'platforms/android-33/android.jar'
JAVA = (Path(os.environ['JAVA_HOME']) / 'bin' if os.environ.get('JAVA_HOME') else
        Path(subprocess.check_output(['/usr/libexec/java_home'], text=True).strip()) / 'bin'
        if Path('/usr/libexec/java_home').exists() else Path(shutil.which('javac')).resolve().parent)


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True)


with tempfile.TemporaryDirectory(prefix='probe-', dir=DEST) as directory:
    out = Path(directory)
    (out / 'classes').mkdir()
    run(BT / 'aapt2', 'link', '-o', out / 'base.apk', '-I', ANDROID,
        '--manifest', SOURCE / 'AndroidManifest.xml')
    run(JAVA / 'javac', '-source', '8', '-target', '8', '-encoding', 'UTF-8', '-bootclasspath',
        str(ANDROID) + os.pathsep + str(BT / 'core-lambda-stubs.jar'), '-d', out / 'classes', SOURCE / 'SurfaceProbe.java')
    run(BT / 'd8', '--min-api', '28', '--lib', ANDROID, '--output', out,
        *sorted((out / 'classes').rglob('*.class')))
    with zipfile.ZipFile(out / 'base.apk', 'a', zipfile.ZIP_DEFLATED) as archive:
        archive.write(out / 'classes.dex', 'classes.dex')
    run(BT / 'zipalign', '-p', '4', out / 'base.apk', out / 'aligned.apk')
    key = DEST / 'probe.keystore'
    if not key.exists():
        run(JAVA / 'keytool', '-genkeypair', '-keystore', key, '-alias', 'probe', '-keyalg', 'RSA',
            '-keysize', '2048', '-validity', '3650', '-storepass', 'diagnostic', '-keypass', 'diagnostic',
            '-dname', 'CN=Local Display Probe')
    run(BT / 'apksigner', 'sign', '--ks', key, '--ks-pass', 'pass:diagnostic',
        '--out', DEST / 'DisplayProbe.apk', out / 'aligned.apk')
    run(BT / 'apksigner', 'verify', '--min-sdk-version', '28', '--verbose', DEST / 'DisplayProbe.apk')
print(DEST / 'DisplayProbe.apk')
