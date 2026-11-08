#!/usr/bin/env python3
"""Build only the offline diagnostic APK. Never connect to or install on a TV."""
from pathlib import Path
import os,shutil
import subprocess, zipfile
ROOT = Path(__file__).resolve().parents[1]
B = ROOT/'builds/proskurnin-preview-v1'
SDK = Path(os.environ.get('ANDROID_SDK_ROOT',str(Path.home()/'Library/Android/sdk')))
BT = SDK/'build-tools/35.0.0'
AJ = SDK/'platforms/android-33/android.jar'
JAVA = Path(os.environ['JAVA_HOME'])/'bin' if os.environ.get('JAVA_HOME') else Path(subprocess.check_output(['/usr/libexec/java_home'],text=True).strip())/'bin' if Path('/usr/libexec/java_home').exists() else Path(shutil.which('javac')).resolve().parent
import tempfile
O = Path(tempfile.mkdtemp(prefix='app-out-',dir=B))

(O/'classes').mkdir()
def run(*args): subprocess.run([str(a) for a in args], check=True)
resources=[]
if (B/'app/res').exists():
 run(BT/'aapt2','compile','--dir',B/'app/res','-o',O/'resources.zip')
 resources=[O/'resources.zip']
run(BT/'aapt2','link','-o',O/'base.apk','-I',AJ,'--manifest',B/'app/AndroidManifest.xml',*resources)
run(JAVA/'javac','-source','8','-target','8','-bootclasspath',str(AJ)+':'+str(BT/'core-lambda-stubs.jar'),'-encoding','UTF-8','-d',O/'classes',*sorted((B/'app/src').rglob('*.java')))
run(BT/'d8','--min-api','28','--lib',AJ,'--output',O,*sorted((O/'classes').rglob('*.class')))
with zipfile.ZipFile(O/'base.apk','a',zipfile.ZIP_DEFLATED) as z:
 z.write(O/'classes.dex','classes.dex')
 for f in (B/'app/assets').rglob('*'):
  if f.is_file(): z.write(f,'assets/'+str(f.relative_to(B/'app/assets')))
run(BT/'zipalign','-p','4',O/'base.apk',O/'aligned.apk')
key = B/'diagnostic.keystore'
if not key.exists(): run(JAVA/'keytool','-genkeypair','-keystore',key,'-alias','diagnostic','-keyalg','RSA','-keysize','2048','-validity','3650','-storepass','diagnostic','-keypass','diagnostic','-dname','CN=Local TV Diagnostics')
run(BT/'apksigner','sign','--ks',key,'--ks-pass','pass:diagnostic','--out',B/'ProskurninPreview.apk',O/'aligned.apk')
run(BT/'apksigner','verify','--min-sdk-version','28','--verbose',B/'ProskurninPreview.apk')
