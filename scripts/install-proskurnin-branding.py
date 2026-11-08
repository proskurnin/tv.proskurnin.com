#!/usr/bin/env python3
from pathlib import Path
import subprocess,hashlib,json,time
R=Path(__file__).resolve().parents[1]; B=R/'builds/proskurnin-boot-v1'; O=R/'reports/proskurnin-branding-install'; O.mkdir(exist_ok=True)
ADB='/Users/roman/Library/Android/sdk/platform-tools/adb'; A=[ADB,'-s','192.168.178.105:5555']; block='/dev/block/platform/mstar_mci.0/by-name/MPOOL'
def run(*a):
 p=subprocess.run(A+list(a),capture_output=True,timeout=120); (O/'commands.log').open('ab').write((' '.join(a)+'\n').encode()+p.stdout+p.stderr); p.check_returncode(); return p.stdout
def sh(s):return run('shell',s)
def sha(b):return hashlib.sha256(b).hexdigest()
def readpool():
 raw=run('exec-out','cat '+block)
 if len(raw)!=3145728: raise RuntimeError('Unexpected MPOOL length: '+str(len(raw)))
 return raw
m=json.loads((B/'manifest.json').read_text());m['approved_for_MPOOL_write']=True;m['authorization']='User: Заменяй заставку на Proskurnin TV';(B/'manifest.json').write_text(json.dumps(m,indent=2))
for n,d in m['files'].items():assert sha((B/n).read_bytes())==d['sha256']
run('root');time.sleep(2);run('connect','192.168.178.105:5555')
assert b'uid=0' in sh('id')
remounted=False
try:
 old=readpool();(O/'MPOOL-before.bin').write_bytes(old);assert sha(old)==m['source_current_MPOOL_sha256'],'MPOOL changed; stop'
 pairs=[('/vendor/tvconfig/boot0.jpg','bootlogo.jpg','c0249202f740684544fb402b9254497f0569ffda7d637ec78ce2b0680f5c6a3b','tv_config_file'),('/vendor/tvconfig/bootlogo.jpg','bootlogo.jpg','c0249202f740684544fb402b9254497f0569ffda7d637ec78ce2b0680f5c6a3b','tv_config_file'),('/system/media/bootanimation.zip','bootanimation.zip','a6c134d2a208f32ebd7f58e7ac6006300d9643979d342e1fcba8b842dc14853f','system_file')]
 for dest,src,h,ctx in pairs:
  assert h in sh('sha256sum '+dest).decode(),dest+' original mismatch'
  run('pull',dest,str(O/Path(dest).name));sh('ls -lZ '+dest)
 sh('mkdir -p /data/local/tmp/proskurnin-branding-backup')
 for dest,src,h,ctx in pairs:sh('cp -p '+dest+' /data/local/tmp/proskurnin-branding-backup/'+Path(dest).name)
 run('push',str(B/'MPOOL.logo-prefix.original.bin'),'/data/local/tmp/proskurnin-branding-backup/MPOOL-prefix.bin')
 sh('mount -o remount,rw /');remounted=True
 for dest,src,h,ctx in pairs:
  tmp=dest+'.proskurnin-new';run('push',str(B/src),tmp)
  sh('chown 0:0 '+tmp+' && chmod 0644 '+tmp+' && chcon u:object_r:'+ctx+':s0 '+tmp)
  assert m['files'][src]['sha256'] in sh('sha256sum '+tmp).decode()
  sh('mv '+tmp+' '+dest)
 run('push',str(B/'MPOOL.logo-prefix.candidate.bin'),'/data/local/tmp/proskurnin-logo-prefix.bin')
 assert readpool()==old,'MPOOL changed during preparation'
 sh('dd if=/data/local/tmp/proskurnin-logo-prefix.bin of='+block+' bs=512 count=97 conv=notrunc && sync')
 actual=readpool();(O/'MPOOL-after.bin').write_bytes(actual)
 if sha(actual)!=m['files']['MPOOL.proskurnin.candidate.bin']['sha256']:
  sh('dd if=/data/local/tmp/proskurnin-branding-backup/MPOOL-prefix.bin of='+block+' bs=512 count=97 conv=notrunc && sync');assert readpool()==old;raise RuntimeError('Verification failed; prefix restored')
 for dest,src,h,ctx in pairs:assert m['files'][src]['sha256'] in sh('sha256sum '+dest).decode()
 m['installed']=True;m['readback_verified']=True;(B/'manifest.json').write_text(json.dumps(m,indent=2));print('INSTALLED_AND_READBACK_VERIFIED; NO_REBOOT')
finally:
 if remounted:sh('sync; mount -o remount,ro /')
 run('unroot')
