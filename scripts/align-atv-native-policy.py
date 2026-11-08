#!/usr/bin/env python3
"""Align an offline experimental system with the preserved native boot/vendor."""
import hashlib
import json
import stat
import subprocess
from pathlib import Path
from dissect.extfs import ExtFS
from dissect.util.stream import RangeStream

ROOT = Path(__file__).resolve().parents[1]
R = ROOT/'reports/full-firmware-readonly-20261107-184246'
OUT = ROOT/'builds/atv9-offline-prototype-v1'
assert not (OUT/'native-policy-manifest.json').exists()
image = OUT/'system.experimental.bin'
native = ExtFS(RangeStream((R/'device-dump/emmc-stage2/emmc.bin').open('rb'),606928896,786432000))
host = OUT/'native-bootstrap'
host.mkdir(exist_ok=False)
paths = []
def collect(node, path):
    if node.filetype == stat.S_IFDIR:
        for n in node.iterdir():
            if n.filename not in ('.','..'):
                collect(n,path+'/'+n.filename)
    elif node.filetype == stat.S_IFREG:
        paths.append(path)
collect(native.get('/system/etc/selinux'),'/system/etc/selinux')
for n in native.root.iterdir():
    if n.filetype == stat.S_IFREG and (n.filename == 'init' or n.filename.startswith('init.') or n.filename == 'ueventd.rc'):
        paths.append('/'+n.filename)
commands=[]
records=[]
for i,path in enumerate(paths):
    n=native.get(path)
    b=n.open().read()
    p=host/f'{i:03d}.bin'
    p.write_bytes(b)
    commands += [f'rm {path}',f'write {p} {path}',
                 f'set_inode_field {path} mode 0{n.inode.i_mode:o}',
                 f'set_inode_field {path} uid {n.inode.i_uid}',
                 f'set_inode_field {path} gid {n.inode.i_gid}']
    attrs={}
    for j,attr in enumerate(n.xattr):
        ap=host/f'{i:03d}-{j:02d}.xattr'
        ap.write_bytes(attr.value)
        commands.append(f'ea_set -f {ap} {path} {attr.name}')
        attrs[attr.name]=attr.value.hex()
    records.append({'path':path,'sha256':hashlib.sha256(b).hexdigest(),'mode':n.inode.i_mode,'xattrs':attrs})
cmd=OUT/'native-bootstrap.commands'
cmd.write_text('\n'.join(commands)+'\n')
for args,name,allowed in [(['debugfs','-w','-f',cmd,image],'native-bootstrap.log',(0,)),
                          (['e2fsck','-fy',image],'system-native-fsck-fix.log',(0,1)),
                          (['e2fsck','-fn',image],'system-native-fsck-final.log',(0,))]:
    args[0]='/opt/homebrew/opt/e2fsprogs/sbin/'+args[0]
    p=subprocess.run([str(x) for x in args],capture_output=True,text=True)
    (OUT/name).write_text(p.stdout+p.stderr)
    assert p.returncode in allowed,name
check=ExtFS(image.open('rb'))
for rec in records:
    n=check.get(rec['path'])
    assert hashlib.sha256(n.open().read()).hexdigest()==rec['sha256']
    assert n.inode.i_mode==rec['mode']
    attrs={a.name:a.value.hex() for a in n.xattr}
    assert all(attrs.get(k)==v for k,v in rec['xattrs'].items())
vendor=ExtFS((OUT/'vendor.experimental.bin').open('rb'))
assert check.get('/system/etc/selinux/plat_and_mapping_sepolicy.cil.sha256').open().read().strip() == vendor.get('/etc/selinux/precompiled_sepolicy.plat_and_mapping.sha256').open().read().strip()
with image.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
(OUT/'native-policy-manifest.json').write_text(json.dumps({'image_sha256':sha,'copied_native_files':records,'native_vendor_policy_digest_matches':True,'runtime_verified':False},indent=2))
m=json.loads((OUT/'manifest.json').read_text());m['image_sha256']=sha;m['native_bootstrap_overlay']='native-policy-manifest.json';(OUT/'manifest.json').write_text(json.dumps(m,indent=2))
print('Native bootstrap/policy alignment verified, SHA256',sha)
