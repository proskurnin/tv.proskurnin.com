import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('provision', Path(__file__).resolve().parents[1] / 'scripts/provision-xiaomi-preview-api.py')
provision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provision)


class ProvisionTests(unittest.TestCase):
    def good(self):
        return {'version': 1, 'api_token': 'a'*43, 'weather_token': 'b'*43}

    def test_valid_device_config(self):
        self.assertIn('api_token', provision.validate(self.good()))

    def test_reject_keys_and_arbitrary_endpoints(self):
        for key in ('openai_api_key', 'base_url', 'command'):
            with self.assertRaises(ValueError):
                provision.validate(dict(self.good(), **{key: 'not-allowed'}))
        for bad in ('short', 'x'*129, 'x'*40+'\n', 'x'*40+"'", 'x'*40+';'):
            with self.assertRaises(ValueError):
                provision.validate(dict(self.good(), api_token=bad))
        with self.assertRaises(ValueError):
            provision.validate(dict(self.good(), version=True))
        with self.assertRaises(ValueError):
            provision.validate(dict(self.good(), weather_token='a'*43))

    def test_private_file_only(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/'config.json'
            p.write_text(provision.validate(self.good()))
            p.chmod(0o600)
            provision.read_private(p)
            p.chmod(0o644)
            with self.assertRaises(ValueError):
                provision.read_private(p)
            link = Path(directory)/'link'
            link.symlink_to(p)
            with self.assertRaises(OSError):
                provision.read_private(link)
