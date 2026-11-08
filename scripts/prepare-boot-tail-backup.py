#!/usr/bin/env python3
"""Offline builder for the reviewed installed MBOOT. Does not access USB or TV."""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'reports/full-firmware-readonly-20261107-184246'
spec=importlib.util.spec_from_file_location('container',ROOT/'scripts/prepare-backup-research.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
b=(R/'device-dump/emmc-stage2/extracted/MBOOT.bin').read_bytes()
assert hashlib.sha256(b).hexdigest()=='1f63d4e2cf20effe4ea06f23a8742ad034f57f8b6b607a67e0a72912315b5623'
lines=['usb start 0']
for part in [1,2]:
 for suffix,fill in [('A','a5'),('B','5a')]:
  lines += [f'mw.b 0x50000000 0x{fill} 0x400',
            f'mmc read.boot {part} 0x50000000 0x1ffe 0x400',
            f'fatwrite usb 0:1 0x50000000 B{part}T{suffix}.BIN 0x400']
lines += ['setenv LetvUpgrade_complete 1','setenv ForcePowerOn 0','saveenv']
assert 0x1ffe*512==4193280 and (0x1ffe*512+0x400)==4194304
text='#-------------USB Upgrade Bin Info----------------\n# Device : m7332_eu\n# Boot tail backup; read eMMC, write USB files only. ENV completion flags retained.\n\n'+'\n'.join(lines)+'\n\n% <- this is end of file symbol\n'
data=m.pack(text);assert m.unpack(data)==text
out=R/'device-dump/boot-tail-analysis/prepared';out.mkdir(exist_ok=True)
(out/'CtvUpgrade.bin').write_bytes(data);(out/'script.txt').write_text(text)
(out/'manifest.json').write_text(json.dumps({'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'commands':lines,'container_roundtrip_passed':True,'runtime_tested':False,'eMMC_data_writes':False,'ENV_completion_writes':True,'RAM_scratch_write':True,'usb_output_files':['B1TA.BIN','B1TB.BIN','B2TA.BIN','B2TB.BIN'],'each_output_bytes':1024},indent=2))
print(hashlib.sha256(data).hexdigest(),len(data))
