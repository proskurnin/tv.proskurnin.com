#!/usr/bin/env python3
from pathlib import Path
import os,shutil
import subprocess,zipfile,tempfile
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'builds/proskurnin-remote-v1';O=Path(tempfile.mkdtemp(prefix='out-',dir=B))
SDK=Path(os.environ.get('ANDROID_SDK_ROOT',str(Path.home()/'Library/Android/sdk')));BT=SDK/'build-tools/35.0.0';AJ=SDK/'platforms/android-33/android.jar';JAVA=Path(os.environ['JAVA_HOME'])/'bin' if os.environ.get('JAVA_HOME') else Path(subprocess.check_output(['/usr/libexec/java_home'],text=True).strip())/'bin' if Path('/usr/libexec/java_home').exists() else Path(shutil.which('javac')).resolve().parent
def run(*args):subprocess.run([str(x) for x in args],check=True)
for part in ['app','bridge']:
 out=O/part;(out/'classes').mkdir(parents=True)
 run(JAVA/'javac','-source','8','-target','8','-bootclasspath',str(AJ)+':'+str(BT/'core-lambda-stubs.jar'),'-encoding','UTF-8','-d',out/'classes',*sorted((B/part/'src').rglob('*.java')))
 run(BT/'d8','--min-api','28','--lib',AJ,'--output',out,*sorted((out/'classes').rglob('*.class')))
 if part=='bridge':
  with zipfile.ZipFile(B/'input-bridge.jar','w',zipfile.ZIP_DEFLATED) as z:z.write(out/'classes.dex','classes.dex')
  continue
 run(BT/'aapt2','compile','--dir',B/'app/res','-o',out/'resources.zip')
 run(BT/'aapt2','link','-o',out/'base.apk','-I',AJ,'--manifest',B/'app/AndroidManifest.xml',out/'resources.zip')
 with zipfile.ZipFile(out/'base.apk','a',zipfile.ZIP_DEFLATED) as z:
  z.write(out/'classes.dex','classes.dex')
  for f in (B/'app/assets').rglob('*'):
   if f.is_file():z.write(f,'assets/'+str(f.relative_to(B/'app/assets')))
 run(BT/'zipalign','-p','4',out/'base.apk',out/'aligned.apk')
 run(BT/'apksigner','sign','--ks',ROOT/'builds/proskurnin-preview-v1/diagnostic.keystore','--ks-pass','pass:diagnostic','--out',B/'ProskurninRemote.apk',out/'aligned.apk')
 run(BT/'apksigner','verify','--min-sdk-version','28','--verbose',B/'ProskurninRemote.apk')
print('Built remote APK and input bridge')
