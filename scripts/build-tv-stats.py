#!/usr/bin/env python3
"""Build optional read-only CPU/storage helper. No TV access or autostart."""
from pathlib import Path
import hashlib,os,subprocess,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'builds/proskurnin-stats';SDK=Path(os.environ.get('ANDROID_SDK_ROOT',str(Path.home()/'Library/Android/sdk')));BT=SDK/'build-tools/35.0.0';AJ=SDK/'platforms/android-33/android.jar'
JAVA=Path(os.environ.get('JAVA_HOME') or subprocess.check_output(['/usr/libexec/java_home'],text=True).strip())/'bin'
out=Path(tempfile.mkdtemp(prefix='out-',dir=B));(out/'classes').mkdir()
cert=subprocess.check_output([str(JAVA/'keytool'),'-exportcert','-keystore',str(ROOT/'builds/proskurnin-preview-v1/diagnostic.keystore'),'-alias','diagnostic','-storepass','diagnostic'])
source=out/'StatsBridge.java';source.write_text((B/'src/local/proskurnin/stats/StatsBridge.java').read_text().replace('CERTIFICATE_PLACEHOLDER',hashlib.sha256(cert).hexdigest()))
subprocess.run([str(JAVA/'javac'),'-source','8','-target','8','-bootclasspath',str(AJ),'-encoding','UTF-8','-d',str(out/'classes'),str(source)],check=True)
subprocess.run([str(BT/'d8'),'--min-api','28','--lib',str(AJ),'--output',str(out),*[str(f) for f in (out/'classes').rglob('*.class')]],check=True)
with zipfile.ZipFile(B/'stats-bridge.jar','w',zipfile.ZIP_DEFLATED) as z:z.write(out/'classes.dex','classes.dex')
print(B/'stats-bridge.jar')
