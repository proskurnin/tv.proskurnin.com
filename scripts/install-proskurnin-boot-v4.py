#!/usr/bin/env python3
"""SDX-43U4123B only. Install/restore approved artwork; never reboot or edit MBOOT/ENV.
Requires the verified v3 snapshot captured in reports/boot-branding-v4/before.json.
Default is local preparation. --apply explicitly enables TV writes.
"""
from pathlib import Path
import argparse, hashlib, json, shlex, struct, subprocess, time, zlib

ROOT=Path(__file__).resolve().parents[1]
BLOCK='/dev/block/platform/mstar_mci.0/by-name/MPOOL'
PREFIX_SIZE=49664
LOGO_OFFSET=244
SOURCE_SHA='0fbd8e9168fa07ef3377446f565d9633855ca96e5632db510f0e94def09d2101'
FILES=[('/vendor/tvconfig/boot0.jpg','bootlogo.jpg','boot0-before.jpg','tv_config_file'),('/vendor/tvconfig/bootlogo.jpg','bootlogo.jpg','bootlogo-before.jpg','tv_config_file'),('/system/media/bootanimation.zip','bootanimation.zip','bootanimation-before.zip','system_file')]

def sha(data):return hashlib.sha256(data).hexdigest()

def candidate(original,jpeg):
    if len(original)!=3145728 or sha(original)!=SOURCE_SHA:raise ValueError('MPOOL source is not the verified v3 image')
    if not jpeg.startswith(b'\xff\xd8') or not jpeg.endswith(b'\xff\xd9') or len(jpeg)>PREFIX_SIZE-LOGO_OFFSET:raise ValueError('Invalid JPEG/slot size')
    result=bytearray(original)
    result[LOGO_OFFSET:PREFIX_SIZE]=jpeg+bytes(PREFIX_SIZE-LOGO_OFFSET-len(jpeg))
    struct.pack_into('<I',result,8,zlib.crc32(result[LOGO_OFFSET:PREFIX_SIZE]))
    struct.pack_into('<I',result,240,zlib.crc32(result[:240]))
    assert result[PREFIX_SIZE:]==original[PREFIX_SIZE:]
    return bytes(result)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial',default='192.168.18.247:5555')
    parser.add_argument('--adb',default=str(Path.home()/'Library/Android/sdk/platform-tools/adb'))
    parser.add_argument('--color',choices=['ruby','copper','emerald','sapphire','amethyst'],default='ruby')
    parser.add_argument('--build',type=Path,default=ROOT/'builds/proskurnin-boot-v4')
    parser.add_argument('--backup',type=Path,default=ROOT/'reports/boot-branding-v4')
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--restore',action='store_true')
    args=parser.parse_args();build=args.build/args.color;report=args.backup
    baseline=json.loads((report/'before.json').read_text());manifest=json.loads((args.build/'manifest.json').read_text())
    original=(report/'MPOOL-before.bin').read_bytes()
    assert sha(original)==baseline['mpool_sha256']==SOURCE_SHA
    for remote,source,backup,context in FILES:
        assert sha((report/backup).read_bytes())==baseline['files'][remote]['sha256']
        assert sha((build/source).read_bytes())==manifest['colors'][args.color]['files'][source]
    updated=candidate(original,(build/'bootlogo.jpg').read_bytes())
    (build/'MPOOL.prefix.bin').write_bytes(updated[:PREFIX_SIZE]);(build/'MPOOL.candidate.bin').write_bytes(updated)
    (report/'MPOOL-prefix-before.bin').write_bytes(original[:PREFIX_SIZE])
    print('Prepared',args.color,'MPOOL',sha(updated),'tail unchanged from byte',PREFIX_SIZE,flush=True)
    if not args.apply:return
    adb=[args.adb,'-s',args.serial]
    def run(*command):
        p=subprocess.run(adb+list(command),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
        if p.returncode:raise RuntimeError('ADB failed: '+str(command[:2])+' '+p.stderr.decode(errors='replace'))
        return p.stdout
    def shell(command):return run('shell',command)
    def readpool():
        data=run('exec-out','cat '+BLOCK)
        if len(data)!=len(original):raise RuntimeError('Wrong MPOOL read size; stop')
        return data
    def filehash(path):return shell('sha256sum '+shlex.quote(path)).decode().split()[0]
    def replace(local,remote,context):
        tmp=remote+'.proskurnin-v4-new'
        run('push',str(local),tmp)
        shell('chown 0:0 '+tmp+' && chmod 0644 '+tmp+' && chcon u:object_r:'+context+':s0 '+tmp)
        if filehash(tmp)!=sha(local.read_bytes()):raise RuntimeError('Staged artwork hash mismatch')
        shell('mv '+tmp+' '+remote)
        if filehash(remote)!=sha(local.read_bytes()):raise RuntimeError('Installed artwork hash mismatch')
    def writeprefix(local):
        remote='/data/local/tmp/proskurnin-boot-v4/prefix-write.bin'
        run('push',str(local),remote)
        if filehash(remote)!=sha(local.read_bytes()):raise RuntimeError('Staged prefix hash mismatch')
        # This TV's dd disables conv options. The target is a block device, never
        # a regular file: bounded writes do not truncate its remaining sectors.
        shell('test -b '+BLOCK+' && dd if='+remote+' of='+BLOCK+' bs=512 count=97 && sync')
    def restore():
        current=readpool()
        if current[PREFIX_SIZE:]!=original[PREFIX_SIZE:]:raise RuntimeError('Unrelated MPOOL bytes changed; refuse rollback')
        if current!=original:writeprefix(report/'MPOOL-prefix-before.bin')
        if readpool()!=original:raise RuntimeError('Original MPOOL not restored')
        for remote,source,backup,context in FILES:replace(report/backup,remote,context)
        shell('sync')
    root=False;mounted=False;mutation=False
    status={'version':4,'color':args.color,'installed':False,'readback_verified':False,'rebooted':False,'runtime_verified':False}
    try:
        run('root');root=True;time.sleep(2);run('connect',args.serial)
        assert b'uid=0' in shell('id')
        assert shell('getprop ro.product.device').decode().strip()=='m7332_eu'
        current=readpool()
        if args.restore:
            if current[PREFIX_SIZE:]!=original[PREFIX_SIZE:]:raise RuntimeError('MPOOL tail changed; stop')
        elif current!=original:raise RuntimeError('MPOOL no longer matches before snapshot; stop')
        for remote,source,backup,context in FILES:
            allowed={baseline['files'][remote]['sha256']}
            if args.restore:allowed.add(manifest['colors'][args.color]['files'][source])
            if filehash(remote) not in allowed:raise RuntimeError('Existing artwork changed: '+remote)
        mounts=shell('cat /proc/mounts').decode().splitlines()
        root_options=next(line.split()[3].split(',') for line in mounts if line.split()[1]=='/')
        assert 'ro' in root_options,'Unexpected root mount state'
        assert any(line.split()[1]=='/vendor' and 'rw' in line.split()[3].split(',') for line in mounts),'Unexpected vendor mount state'
        shell('mkdir -p /data/local/tmp/proskurnin-boot-v4')
        # Keep a second copy of all rollback artifacts on the TV before any artwork write.
        for name in ['MPOOL-prefix-before.bin','boot0-before.jpg','bootlogo-before.jpg','bootanimation-before.zip']:
            dest='/data/local/tmp/proskurnin-boot-v4/'+name
            run('push',str(report/name),dest)
            assert filehash(dest)==sha((report/name).read_bytes())
        shell('mount -o remount,rw /');mounted=True
        if args.restore:
            mutation=True;restore();status['restored']=True;status['readback_verified']=True
        else:
            mutation=True
            for remote,source,backup,context in FILES:replace(build/source,remote,context)
            assert readpool()==original,'MPOOL changed during file staging'
            writeprefix(build/'MPOOL.prefix.bin')
            actual=readpool()
            (report/'MPOOL-after.bin').write_bytes(actual)
            assert actual==updated,'MPOOL readback mismatch'
            for remote,source,backup,context in FILES:assert filehash(remote)==manifest['colors'][args.color]['files'][source]
            shell('sync');status.update(installed=True,readback_verified=True,mpool_sha256=sha(actual),files=manifest['colors'][args.color]['files'])
        print('RESTORED' if args.restore else 'INSTALLED',args.color,'verified; NO REBOOT',flush=True)
    except Exception:
        if mutation and not args.restore:
            try:restore();status['automatic_rollback_verified']=True
            except Exception as error:status['rollback_error']=str(error)
        raise
    finally:
        if mounted:
            try:shell('sync && mount -o remount,ro /')
            except Exception as error:status['remount_error']=str(error)
        if root:
            try:run('unroot')
            except Exception as error:status['unroot_error']=str(error)
        (report/('restore-status.json' if args.restore else 'install-status.json')).write_text(json.dumps(status,indent=2)+'\n')

if __name__=='__main__':main()
