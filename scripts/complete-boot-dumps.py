#!/usr/bin/env python3
"""Validate double-read tails and overlap before producing full boot images locally."""
import argparse,hashlib,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'reports/full-firmware-readonly-20261107-184246/device-dump'

def merge(old,a,b):
    if len(old)!=4193792 or len(a)!=1024 or len(b)!=1024:
        raise ValueError('Unexpected size: preserve all original files')
    if a!=b:
        raise ValueError('Independent reads differ')
    if a[:512]!=old[-512:]:
        raise ValueError('Overlap does not match original boot copy')
    if a==bytes([0xa5])*1024 or a==bytes([0x5a])*1024:
        raise ValueError('RAM initialization pattern returned instead of a read')
    result=old+a[512:]
    if len(result)!=4194304:
        raise ValueError('Wrong final size')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tails',type=Path,required=True);args=p.parse_args()
    originals=R/'boot-stage1';manifest=json.loads((originals/'manifest.json').read_text());pending=[]
    for i in [1,2]:
        name=f'BOOT{i}.BIN';old=(originals/name).read_bytes();expected=next(x for x in manifest['files'] if x['name']==name)
        if hashlib.sha256(old).hexdigest()!=expected['sha256']:
            raise ValueError('Original boot copy changed')
        a=(args.tails/f'B{i}TA.BIN').read_bytes();b=(args.tails/f'B{i}TB.BIN').read_bytes()
        pending.append((name,merge(old,a,b)))
    dest=R/'boot-complete'
    if dest.exists():raise ValueError('Output directory already exists; refusing overwrite')
    dest.mkdir(mode=0o700);records=[]
    for name,b in pending:
        path=dest/name;path.write_bytes(b);os.chmod(path,0o600)
        records.append({'file':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'tail_double_read_matches':True,'512_byte_overlap_matches':True})
    (dest/'manifest.json').write_text(json.dumps(records,indent=2))
    print(json.dumps(records,indent=2))

if __name__=='__main__':main()
