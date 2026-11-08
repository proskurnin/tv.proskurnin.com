#!/usr/bin/env python3
"""Build only the offline diagnostic APK. Never connect to or install on a TV."""
from pathlib import Path
import subprocess, zipfile
ROOT = Path(__file__).resolve().parents[1]
B = ROOT/'builds/atv9-diagnostic-v2'
SDK = Path('/Users/roman/Library/Android/sdk')
BT = SDK/'build-tools/35.0.0'
AJ = SDK/'platforms/android-33/android.jar'
JAVA = Path(subprocess.check_output(['/usr/libexec/java_home'], text=True).strip())/'bin'
O = B/'app-out'
O.mkdir(exist_ok=False)
(O/'classes').mkdir()
def run(*args): subprocess.run([str(a) for a in args], check=True)
run(BT/'aapt2','link','-o',O/'base.apk','-I',AJ,'--manifest',B/'app/AndroidManifest.xml')
run(JAVA/'javac','-source','8','-target','8','-bootclasspath',str(AJ)+':'+str(BT/'core-lambda-stubs.jar'),'-encoding','UTF-8','-d',O/'classes',*sorted((B/'app/src').rglob('*.java')))
run(BT/'d8','--min-api','28','--lib',AJ,'--output',O,*sorted((O/'classes').rglob('*.class')))
with zipfile.ZipFile(O/'base.apk','a',zipfile.ZIP_DEFLATED) as z: z.write(O/'classes.dex','classes.dex')
run(BT/'zipalign','-p','4',O/'base.apk',O/'aligned.apk')
key = B/'diagnostic.keystore'
if not key.exists(): run(JAVA/'keytool','-genkeypair','-keystore',key,'-alias','diagnostic','-keyalg','RSA','-keysize','2048','-validity','3650','-storepass','diagnostic','-keypass','diagnostic','-dname','CN=Local TV Diagnostics')
run(BT/'apksigner','sign','--ks',key,'--ks-pass','pass:diagnostic','--out',B/'TVDiagnostics.apk',O/'aligned.apk')
run(BT/'apksigner','verify','--min-sdk-version','28','--verbose',B/'TVDiagnostics.apk')
