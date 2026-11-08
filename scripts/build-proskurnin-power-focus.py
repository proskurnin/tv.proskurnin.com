#!/usr/bin/env python3
"""Build only. Requires this TV's SystemUI APK for resource linking; never installs."""
from pathlib import Path
import argparse,os,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--system-ui',type=Path,required=True);a=p.parse_args()
sdk=Path(os.environ.get('ANDROID_SDK_ROOT',str(Path.home()/'Library/Android/sdk')));bt=sdk/'build-tools/35.0.0';b=root/'builds/proskurnin-power-focus';out=Path(tempfile.mkdtemp(prefix='out-',dir=b))
def run(*args):subprocess.run([str(v) for v in args],check=True)
run(bt/'aapt2','compile','--dir',b/'res','-o',out/'resources.zip')
run(bt/'aapt2','link','-o',out/'base.apk','-I',sdk/'platforms/android-33/android.jar','-I',a.system_ui,'--manifest',b/'AndroidManifest.xml',out/'resources.zip')
run(bt/'zipalign','-p','4',out/'base.apk',out/'aligned.apk')
run(bt/'apksigner','sign','--ks',root/'builds/proskurnin-preview-v1/diagnostic.keystore','--ks-pass','pass:diagnostic','--out',b/'ProskurninPowerFocus.apk',out/'aligned.apk')
run(bt/'apksigner','verify','--min-sdk-version','28',b/'ProskurninPowerFocus.apk')
print('Built power-focus overlay; no device changed')
