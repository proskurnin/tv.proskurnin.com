#!/usr/bin/env python3
"""Read regular backup files only. Never opens devices or writes to a TV.
Sizes/partition geometry are from the read-only SDX-43U4123B snapshot.
Does not certify restore compatibility or authenticity of the source device.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / 'reports/full-firmware-readonly-20261107-184246/partition-map.csv'
EMMC_BYTES = 7818182656
BOOT_BYTES = 4194304


def check_file(path, expected):
    path = path.resolve(strict=True)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f'{path.name}: only regular files allowed, no device access')
    if info.st_size != expected:
        raise ValueError(f'{path.name}: {info.st_size} bytes, expected {expected}; '
                         'do not pad a truncated dump')
    return path


def digest(path, offset, length):
    h = hashlib.sha256()
    with path.open('rb') as f:
        f.seek(offset)
        while length:
            data = f.read(min(length, 8 * 1024 * 1024))
            if not data:
                raise ValueError('Unexpected end of file')
            h.update(data)
            length -= len(data)
    return h.hexdigest()


def load_map(path):
    with path.open() as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 33 or len({r['name'] for r in rows}) != 33:
        raise ValueError('Expected 33 unique partitions')
    end = 0
    for r in sorted(rows, key=lambda x: int(x['offset_bytes'])):
        start, length = int(r['offset_bytes']), int(r['size_bytes'])
        if start < end or length <= 0 or start + length > EMMC_BYTES:
            raise ValueError('Invalid partition geometry')
        end = start + length
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emmc', type=Path, required=True)
    parser.add_argument('--boot1', type=Path, required=True)
    parser.add_argument('--boot2', type=Path, required=True)
    args = parser.parse_args()
    try:
        paths = [check_file(p, n) for p, n in
                 [(args.emmc, EMMC_BYTES), (args.boot1, BOOT_BYTES), (args.boot2, BOOT_BYTES)]]
        if len(set(paths)) != 3:
            raise ValueError('Three distinct input files required')
        rows = load_map(MAP)
        result = {'status': 'sizes-and-hashes-only', 'restore_verified': False,
                  'warning': 'Partition ranges use the prior TV snapshot; on-disk partition table and '
                             'device identity still need independent validation.',
                  'files': [], 'partitions': []}
        for role, path in zip(['emmc', 'boot1', 'boot2'], paths):
            size = path.stat().st_size
            result['files'].append({'role': role, 'path': str(path), 'bytes': size,
                                    'sha256': digest(path, 0, size)})
        for r in rows:
            offset, size = int(r['offset_bytes']), int(r['size_bytes'])
            result['partitions'].append({'name': r['name'], 'offset': offset, 'bytes': size,
                                         'sha256': digest(paths[0], offset, size)})
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError) as e:
        parser.exit(2, f'REJECTED: {e}\n')


if __name__ == '__main__':
    main()
