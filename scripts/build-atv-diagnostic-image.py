#!/usr/bin/env python3
"""Create a local v2 experiment from the frozen v1; no device/USB writes."""
import hashlib, json, shutil, stat, subprocess
from pathlib import Path
from dissect.extfs import ExtFS
ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT/'builds/atv9-offline-prototype-v1'
B = ROOT/'builds/atv9-diagnostic-v2'
IMAGE = B/'system.experimental.bin'
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
expected = {'system.experimental.bin':'0169fe72b6d18318425704af32f4a6d277b7d672a38bbebaf35265c202d430ed',
 'vendor.experimental.bin':'ab4e1a695d4dff828e7f4a2e24cddc0f62794c34eaee14b2573fa35af448bc91',
 'install-CtvUpgrade.bin.candidate':'88f9bced8f0eb1ada6a5dae0d1ea1149321ead99f3234f0fe73834f0f698417a',
 'restore-CtvUpgrade.bin.candidate':'7632c800eff43002c777564d3519ffd9850d870f5a75d992f5fe84e2f3e2de4c'}
assert not IMAGE.exists(), 'Do not overwrite an existing candidate'
for name, digest in expected.items(): assert sha(OLD/name)==digest, name
src = ExtFS((OLD/'system.experimental.bin').open('rb'))
key = Path('/Users/roman/.android/adbkey.pub').read_bytes().split()[0]
import base64
assert len(base64.b64decode(key))==524
assert b'/adb_keys' in src.get('/system/bin/adbd').open().read()
assert src.get('/system/bin/logcatd').filetype==stat.S_IFREG
changes = {}
prop = src.get('/system/etc/prop.default').open().read().decode()
assert not any(l.startswith('ro.adb.secure=') for l in prop.splitlines())
changes['/system/etc/prop.default'] = (prop+'\n# v2 diagnostic transport: RSA authentication required\nro.adb.secure=1\npersist.adb.tcp.port=5555\n').encode()
changes['/adb_keys'] = key+b' local-tv-diagnostics\n'
changes['/system/etc/init/tv-diagnostics.rc'] = b'''# Bounded persistent logging; keep native SELinux policy.
on post-fs-data
    setprop logd.logpersistd.size 16
    setprop logd.logpersistd.buffer all
    setprop logd.logpersistd logcatd

on boot
    setprop service.adb.tcp.port 5555
    start adbd
'''
changes['/system/app/TVDiagnostics/TVDiagnostics.apk'] = (B/'TVDiagnostics.apk').read_bytes()
shutil.copyfile(OLD/'system.experimental.bin', IMAGE)
payload = B/'overlay'; payload.mkdir(exist_ok=False)
commands = ['mkdir /system/app/TVDiagnostics', 'set_inode_field /system/app/TVDiagnostics mode 040755',
            'ea_set /system/app/TVDiagnostics security.selinux u:object_r:system_file:s0']
for index,(path,data) in enumerate(changes.items()):
    local=payload/f'{index:02d}.bin'; local.write_bytes(data)
    try: src.get(path); exists=True
    except FileNotFoundError: exists=False
    if exists: commands.append(f'rm {path}')
    label = 'u:object_r:adb_keys_file:s0' if path=='/adb_keys' else 'u:object_r:system_file:s0'
    commands += [f'write {local} {path}',f'set_inode_field {path} mode 0100644',
                 f'set_inode_field {path} uid 0',f'set_inode_field {path} gid 0',
                 f'ea_set {path} security.selinux {label}']
cmd=B/'overlay.commands'; cmd.write_text('\n'.join(commands)+'\n')
for args,name,codes in [(['debugfs','-w','-f',str(cmd),str(IMAGE)],'debugfs.log',(0,)),
                        (['e2fsck','-fy',str(IMAGE)],'fsck-fix.log',(0,1)),
                        (['e2fsck','-fn',str(IMAGE)],'fsck-final.log',(0,))]:
    args[0]='/opt/homebrew/opt/e2fsprogs/sbin/'+args[0]
    p=subprocess.run(args,capture_output=True,text=True); (B/name).write_text(p.stdout+p.stderr)
    assert p.returncode in codes, name
dst=ExtFS(IMAGE.open('rb'))
for path,data in changes.items():
    n=dst.get(path); assert n.open().read()==data, path
    assert n.inode.i_mode==0o100644 and n.inode.i_uid==0 and n.inode.i_gid==0
    label='u:object_r:adb_keys_file:s0' if path=='/adb_keys' else 'u:object_r:system_file:s0'
    assert dict((a.name,a.value.rstrip(b'\0')) for a in n.xattr)['security.selinux']==label.encode()
# Exhaustive unchanged-file comparison; fail if anything outside the declared overlay changed.
def inventory(fs):
    out={}
    def walk(n,path):
        attrs={a.name:a.value.hex() for a in n.xattr}
        base=[n.filetype,n.inode.i_mode,n.inode.i_uid,n.inode.i_gid,attrs]
        if n.filetype==stat.S_IFDIR:
            for child in n.iterdir():
                if child.filename not in ('.','..'): walk(child,path+'/'+child.filename)
        elif n.filetype==stat.S_IFREG: base.append(hashlib.sha256(n.open().read()).hexdigest())
        elif n.filetype==stat.S_IFLNK: base.append(n.link)
        out[path]=base
    walk(fs.root,''); return out
before,after=inventory(src),inventory(dst)
delta=sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k))
assert set(delta)==set(changes)|{'/system/app/TVDiagnostics'}, delta
for name in ['vendor.experimental.bin','install-CtvUpgrade.bin.candidate','restore-CtvUpgrade.bin.candidate']:
    shutil.copyfile(OLD/name,B/name); assert sha(B/name)==expected[name]
record={'purpose':'Android 9 diagnostic experiment, not a confirmed repair',
 'runtime_verified':False,'flash_authorized':False,'device_or_usb_written':False,
 'base_v1_sha256':expected,'system_file_delta':delta,'unchanged_entries_checked':len(before)-1,
 'files':{n:{'bytes':(B/n).stat().st_size,'sha256':sha(B/n)} for n in ['system.experimental.bin','vendor.experimental.bin','install-CtvUpgrade.bin.candidate','restore-CtvUpgrade.bin.candidate','TVDiagnostics.apk']},
 'limitations':['No confirmed cause of v1 black screen','Network and remote functionality unverified',
 'Boot receiver cannot recover a failed Android framework or unavailable input driver',
 'Google login and Play downloads unverified','Native boot, bootloader, table and policy unchanged from v1',
 'ADB requires matching private key; no private key included; networking still required',
 'Persistent logcat has 16 rotated 1 MiB files plus active file; reading requires privileges',
 'Setup wizard may cover the diagnostic screen; HOME may show a launcher chooser']}
(B/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
(B/'SHA256SUMS').write_text(''.join(f"{v['sha256']}  {n}\n" for n,v in record['files'].items()))
print(json.dumps(record,indent=2))
