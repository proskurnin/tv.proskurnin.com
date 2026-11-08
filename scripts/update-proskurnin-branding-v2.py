from pathlib import Path
import subprocess,hashlib,json,time,struct,zlib
R=Path(__file__).resolve().parents[1];B=R/'builds/proskurnin-boot-v2';O=R/'reports/proskurnin-branding-v2';O.mkdir(exist_ok=True);A=['/Users/roman/Library/Android/sdk/platform-tools/adb','-s','192.168.178.105:5555'];block='/dev/block/platform/mstar_mci.0/by-name/MPOOL'
def run(*a):
 p=subprocess.run(A+list(a),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120);p.check_returncode();return p.stdout
def sh(s):return run('shell',s)
def read():
 d=run('exec-out','cat '+block);assert len(d)==3145728;return d
def sha(d):return hashlib.sha256(d).hexdigest()
oldmanifest=json.loads((R/'builds/proskurnin-boot-v1/manifest.json').read_text());assert oldmanifest['installed'];jpg=(B/'bootlogo.jpg').read_bytes();assert len(jpg)<=49420
run('root');time.sleep(2);run('connect','192.168.178.105:5555');rw=False
try:
 old=read();(O/'MPOOL-before.bin').write_bytes(old);assert old[:49664]==(R/'builds/proskurnin-boot-v1/MPOOL.proskurnin.candidate.bin').read_bytes()[:49664],'Logo prefix changed; stop'
 new=bytearray(old);new[244:49664]=jpg+b'\0'*(49420-len(jpg));struct.pack_into('<I',new,8,zlib.crc32(new[244:49664]));struct.pack_into('<I',new,240,zlib.crc32(new[:240]));assert new[49664:]==old[49664:]
 (B/'MPOOL.candidate.bin').write_bytes(new);(B/'MPOOL.prefix.bin').write_bytes(new[:49664]);(O/'MPOOL-prefix-before.bin').write_bytes(old[:49664])
 pairs=[('/vendor/tvconfig/boot0.jpg','bootlogo.jpg','tv_config_file'),('/vendor/tvconfig/bootlogo.jpg','bootlogo.jpg','tv_config_file'),('/system/media/bootanimation.zip','bootanimation.zip','system_file')]
 for dest,src,ctx in pairs:
  assert oldmanifest['files'][src]['sha256'] in sh('sha256sum '+dest).decode();run('pull',dest,str(O/Path(dest).name))
 run('push',str(O/'MPOOL-prefix-before.bin'),'/data/local/tmp/proskurnin-v1-prefix.bin');sh('mount -o remount,rw /');rw=True
 for dest,src,ctx in pairs:
  tmp=dest+'.proskurnin-v2';run('push',str(B/src),tmp);sh('chown 0:0 '+tmp+' && chmod 0644 '+tmp+' && chcon u:object_r:'+ctx+':s0 '+tmp);assert sha((B/src).read_bytes()) in sh('sha256sum '+tmp).decode();sh('mv '+tmp+' '+dest)
 assert read()==old
 run('push',str(B/'MPOOL.prefix.bin'),'/data/local/tmp/proskurnin-v2-prefix.bin');sh('dd if=/data/local/tmp/proskurnin-v2-prefix.bin of='+block+' bs=512 count=97 && sync')
 data=read();(O/'MPOOL-after.bin').write_bytes(data)
 if data!=bytes(new):
  sh('dd if=/data/local/tmp/proskurnin-v1-prefix.bin of='+block+' bs=512 count=97 && sync');assert read()==old;raise RuntimeError('Prefix reverted to v1')
 for dest,src,ctx in pairs:assert sha((B/src).read_bytes()) in sh('sha256sum '+dest).decode()
 (B/'manifest.json').write_text(json.dumps({'installed':True,'readback_verified':True,'resolution':[1920,1080],'fps':20,'intro_frames':20,'loop_frames':1,'all_frames_raw_mib':21*1920*1080*4/1048576,'files':{f:sha((B/f).read_bytes()) for f in ['bootlogo.jpg','bootanimation.zip','MPOOL.candidate.bin']},'runtime_verified':False},indent=2));print('V2 INSTALLED AND READBACK VERIFIED')
finally:
 if rw:sh('sync; mount -o remount,ro /')
 run('unroot')
