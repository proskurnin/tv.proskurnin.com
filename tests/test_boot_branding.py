"""Guard the device-specific logo patch: never change panel/other MPOOL data."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import unittest
from unittest.mock import patch
import zlib

spec=importlib.util.spec_from_file_location('boot_v4',Path(__file__).resolve().parents[1]/'scripts/install-proskurnin-boot-v4.py')
boot=importlib.util.module_from_spec(spec);spec.loader.exec_module(boot)

class BootBrandingTest(unittest.TestCase):
    def setUp(self):
        self.original=bytes(range(256))*12288
        self.digest=hashlib.sha256(self.original).hexdigest()
        self.jpg=b'\xff\xd8'+b'example'*4000+b'\xff\xd9'

    def test_only_logo_and_two_checksums_change(self):
        with patch.object(boot,'SOURCE_SHA',self.digest):
            result=boot.candidate(self.original,self.jpg)
        self.assertEqual(len(result),len(self.original))
        self.assertEqual(result[49664:],self.original[49664:])
        self.assertEqual(result[:8],self.original[:8])
        self.assertEqual(result[12:240],self.original[12:240])
        self.assertEqual(result[244:244+len(self.jpg)],self.jpg)
        self.assertEqual(struct.unpack_from('<I',result,8)[0],zlib.crc32(result[244:49664]))
        self.assertEqual(struct.unpack_from('<I',result,240)[0],zlib.crc32(result[:240]))

    def test_changed_snapshot_is_rejected(self):
        with patch.object(boot,'SOURCE_SHA',self.digest):
            with self.assertRaises(ValueError):boot.candidate(b'X'+self.original[1:],self.jpg)
            with self.assertRaises(ValueError):boot.candidate(self.original[:-1],self.jpg)

    def test_oversized_or_incomplete_jpeg_is_rejected(self):
        with patch.object(boot,'SOURCE_SHA',self.digest):
            for bad in (b'\xff\xd8'+bytes(49420)+b'\xff\xd9',self.jpg[:-2],b'not jpeg'):
                with self.assertRaises(ValueError):boot.candidate(self.original,bad)

if __name__=='__main__':unittest.main()
