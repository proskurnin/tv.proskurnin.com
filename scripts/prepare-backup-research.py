#!/usr/bin/env python3
"""Offline-only audit and draft builder. Does not contact a TV or removable media.
Outputs .candidate files, NOT approved upgrade files. No safety claim about MBOOT.
"""
import hashlib
import json
from pathlib import Path
import struct
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'reports/full-firmware-readonly-20261107-184246/backup-script-audit'
HEADER = 16384
ARCHIVE_HASH = 'ee6f53f522c2560ef1f7524b5eae8943569decee3900e7d9132d402114e58ffc'
ALLOWED = {
    'boot_backup': ['usb start 0', 'emmcbootbin 0 boot1', 'emmcbootbin 0 boot2'],
    'emmc_backup': ['usb start 0', 'mmc dd mmc2usb 0'],
}
REMOVE = {'saveenv', 'setenv LetvUpgrade_complete 1', 'setenv ForcePowerOn 0'}


def pack(text):
    raw = text.encode('ascii')
    if len(raw) > HEADER:
        raise ValueError('Header too long')
    head = raw.ljust(HEADER, b'\xff')
    first = head + b'12345678' + struct.pack('<I', zlib.crc32(head))
    return first + struct.pack('<I', zlib.crc32(first)) + head[:16]


def unpack(data):
    if len(data) != HEADER + 32 or data[HEADER:HEADER+8] != b'12345678':
        raise ValueError('Unexpected container format')
    head = data[:HEADER]
    if struct.unpack_from('<I', data, HEADER+8)[0] != zlib.crc32(head):
        raise ValueError('CRC1 mismatch')
    if struct.unpack_from('<I', data, HEADER+12)[0] != zlib.crc32(data[:HEADER+12]):
        raise ValueError('CRC2 mismatch')
    if data[-16:] != head[:16]:
        raise ValueError('Header copy mismatch')
    raw = head.split(b'\xff', 1)[0]
    if head[len(raw):] != b'\xff' * (HEADER-len(raw)):
        raise ValueError('Unexpected header padding')
    text = raw.decode('ascii')
    if not text.rstrip().endswith('% <- this is end of file symbol'):
        raise ValueError('Unexpected terminator')
    return text


def commands(text):
    return [s.strip() for s in text.splitlines() if s.strip() and not s.strip().startswith(('#', '%'))]


def main():
    archive = (AUDIT / 'BACKUP.zip').read_bytes()
    if hashlib.sha256(archive).hexdigest() != ARCHIVE_HASH:
        raise ValueError('Input archive changed')
    dest = AUDIT / 'offline-drafts-NOT-FOR-TV'
    dest.mkdir(exist_ok=True)
    results = []
    with zipfile.ZipFile(AUDIT / 'BACKUP.zip') as z:
        for name, allowed in ALLOWED.items():
            original = z.read(f'BACKUP/{name}/CtvUpgrade.bin')
            text = unpack(original)
            if pack(text) != original:
                raise ValueError('Original round-trip failed')
            draft = '\n'.join(line for line in text.split('\n') if line.strip() not in REMOVE)
            if commands(draft) != allowed:
                raise ValueError('Unexpected executable command')
            data = pack(draft)
            if unpack(data) != draft:
                raise ValueError('Draft round-trip failed')
            for offset in (100, HEADER, HEADER+8, HEADER+12, HEADER+16):
                broken = bytearray(data)
                broken[offset] ^= 1
                try:
                    unpack(bytes(broken))
                except ValueError:
                    pass
                else:
                    raise ValueError('Corruption not detected')
            (dest / (name + '.candidate')).write_bytes(data)
            (dest / (name + '.txt')).write_text(draft)
            results.append({'name':name, 'sha256':hashlib.sha256(data).hexdigest(),
                            'bytes':len(data), 'commands':allowed,
                            'original_byte_identical_roundtrip':True,
                            'corruption_checks':5, 'approved_for_tv':False})
    (dest / 'manifest.json').write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
