import hashlib
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'integrations/server'))
from device_auth import identify


class DeviceAuthTests(unittest.TestCase):
    def setUp(self):
        self.old = hashlib.sha256(b'Bearer old-device').hexdigest()
        self.devices = {'tv-xiaomi-nino': hashlib.sha256(b'Bearer new-device').hexdigest()}

    def test_both_devices_and_revoke(self):
        self.assertEqual(identify('Bearer old-device', self.old, self.devices), 'tv-sdx43')
        self.assertEqual(identify('Bearer new-device', self.old, self.devices), 'tv-xiaomi-nino')
        self.assertIsNone(identify('Bearer new-device', self.old, {}))
        self.assertEqual(identify('Bearer old-device', self.old, {}), 'tv-sdx43')

    def test_fail_closed(self):
        for value in ('', 'wrong', 'Bearer new-device\n', 'x'*257, None):
            self.assertIsNone(identify(value, self.old, self.devices))
        for mapping in (None, [], {'bad\nlabel': self.devices['tv-xiaomi-nino']}, {'tv-xiaomi-nino': 'short'}):
            self.assertIsNone(identify('Bearer new-device', self.old, mapping))
            self.assertEqual(identify('Bearer old-device', self.old, mapping), 'tv-sdx43')
