#!/usr/bin/env python3
"""Build the local fixed-command power helper; does not install or execute power commands."""
from pathlib import Path
import os,subprocess,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'builds/proskurnin-power-actions';O=Path(tempfile.mkdtemp(prefix='out-',dir=B));(O/'classes').mkdir()
SDK=Path(os.environ.get('ANDROID_SDK_ROOT',str(Path.home()/'Library/Android/sdk')));BT=SDK/'build-tools/35.0.0';AJ=SDK/'platforms/android-33/android.jar';JAVA=Path(subprocess.check_output(['/usr/libexec/java_home'],text=True).strip())/'bin'
def run(*args):subprocess.run([str(x) for x in args],check=True)
run(JAVA/'javac','-source','8','-target','8','-bootclasspath',str(AJ)+':'+str(BT/'core-lambda-stubs.jar'),'-d',O/'classes',*sorted((B/'src').rglob('*.java')))
run(BT/'d8','--min-api','28','--lib',AJ,'--output',O,*sorted((O/'classes').rglob('*.class')))
with zipfile.ZipFile(B/'power-bridge.jar','w',zipfile.ZIP_DEFLATED) as z:z.write(O/'classes.dex','classes.dex')
print('Built power-bridge.jar; no device changes')
