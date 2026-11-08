"""Restore only original branding assets. Requires explicit --restore flag. No reboot."""
from pathlib import Path
import subprocess,time,hashlib,sys,json
assert sys.argv[1:]==['--restore'],'Use --restore to explicitly restore native branding'
R=Path(__file__).resolve().parents[1];S=R/'reports/boot-branding-readonly';A=['/Users/roman/Library/Android/sdk/platform-tools/adb','-s','192.168.178.105:5555'];block='/dev/block/platform/mstar_mci.0/by-name/MPOOL'
def run(*a):return subprocess.check_output(A+list(a),stderr=subprocess.STDOUT,timeout=120)
def sh(s):return run('shell',s)
def digest(d):return hashlib.sha256(d).hexdigest()
run('root');time.sleep(2);run('connect','192.168.178.105:5555');rw=False
try:
 current=run('exec-out','cat '+block);original=(S/'MPOOL-current.bin').read_bytes();assert len(current)==len(original)==3145728;expected=original[:49664]+current[49664:]
 candidates=[original,(R/'builds/proskurnin-boot-v1/MPOOL.proskurnin.candidate.bin').read_bytes()]
 v2=R/'builds/proskurnin-boot-v2/MPOOL.candidate.bin'
 if v2.exists():candidates.append(v2.read_bytes())
 v3=R/'builds/proskurnin-boot-v3/MPOOL.candidate.bin'
 if v3.exists():candidates.append(v3.read_bytes())
 assert current[:49664] in [c[:49664] for c in candidates],'Unknown current logo; stop'
 sh('mount -o remount,rw /');rw=True
 for path,src,ctx in [('/vendor/tvconfig/boot0.jpg','boot0.jpg','tv_config_file'),('/vendor/tvconfig/bootlogo.jpg','bootlogo.jpg','tv_config_file'),('/system/media/bootanimation.zip','bootanimation.zip','system_file')]:
  tmp=path+'.restore';run('push',str(S/src),tmp);sh('chown 0:0 '+tmp+' && chmod 0644 '+tmp+' && chcon u:object_r:'+ctx+':s0 '+tmp);assert digest((S/src).read_bytes()) in sh('sha256sum '+tmp).decode();sh('mv '+tmp+' '+path)
 assert run('exec-out','cat '+block)==current,'MPOOL changed during restoration; stop'
 prefix=R/'builds/proskurnin-boot-v1/MPOOL.logo-prefix.original.bin';run('push',str(prefix),'/data/local/tmp/proskurnin-original-prefix.bin');sh('dd if=/data/local/tmp/proskurnin-original-prefix.bin of='+block+' bs=512 count=97 && sync');assert run('exec-out','cat '+block)==expected;print('Original branding restored and verified. No reboot performed.')
finally:
 if rw:sh('sync; mount -o remount,ro /')
 run('unroot')
