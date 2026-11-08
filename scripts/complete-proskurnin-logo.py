from pathlib import Path
import subprocess,hashlib,json,time
R=Path(__file__).resolve().parents[1];B=R/'builds/proskurnin-boot-v1';O=R/'reports/proskurnin-branding-install';A=['/Users/roman/Library/Android/sdk/platform-tools/adb','-s','192.168.178.105:5555'];block='/dev/block/platform/mstar_mci.0/by-name/MPOOL'
def run(*a):return subprocess.check_output(A+list(a),stderr=subprocess.STDOUT,timeout=90)
def sh(s):return run('shell',s)
def read():
 d=run('exec-out','cat '+block);assert len(d)==3145728;return d
m=json.loads((B/'manifest.json').read_text());run('root');time.sleep(2);run('connect','192.168.178.105:5555')
try:
 assert b'uid=0' in sh('id')
 old=read();assert old==(O/'MPOOL-before.bin').read_bytes()
 for dest,src in [('/vendor/tvconfig/boot0.jpg','bootlogo.jpg'),('/vendor/tvconfig/bootlogo.jpg','bootlogo.jpg'),('/system/media/bootanimation.zip','bootanimation.zip')]:assert m['files'][src]['sha256'] in sh('sha256sum '+dest).decode()
 assert m['files']['MPOOL.logo-prefix.candidate.bin']['sha256'] in sh('sha256sum /data/local/tmp/proskurnin-logo-prefix.bin').decode()
 # This vendor dd rejects all conv options. Block devices cannot be truncated by O_TRUNC.
 print(sh('dd if=/data/local/tmp/proskurnin-logo-prefix.bin of='+block+' bs=512 count=97 && sync').decode())
 data=read();(O/'MPOOL-after.bin').write_bytes(data)
 if data!=(B/'MPOOL.proskurnin.candidate.bin').read_bytes():
  sh('dd if=/data/local/tmp/proskurnin-branding-backup/MPOOL-prefix.bin of='+block+' bs=512 count=97 && sync');assert read()==old;raise RuntimeError('Rolled back prefix')
 m.update(installed=True,readback_verified=True);(B/'manifest.json').write_text(json.dumps(m,indent=2));print('VERIFIED ALL ASSETS AND COMPLETE MPOOL')
finally:run('unroot')
