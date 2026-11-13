import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('launcher_profiles', ROOT / 'scripts/launcher_profiles.py')
profiles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profiles)
A = profiles.ANDROID


class PreviewManifestTest(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / 'builds/proskurnin-preview-v1/app/AndroidManifest.xml'
        self.original = self.path.read_text()
        self.preview = ET.fromstring(profiles.preview_manifest(self.original))

    def test_preview_cannot_be_home_or_background_service(self):
        self.assertEqual(self.preview.get('package'), 'local.proskurnin.xiaomipreview')
        app = self.preview.find('application')
        self.assertEqual([c.tag for c in app], ['activity', 'activity', 'activity', 'meta-data', 'provider'])
        self.assertEqual({a.get(A+'name') for a in app.findall('activity')},
                         {'local.proskurnin.preview.MainActivity', 'local.proskurnin.preview.MovieActivity',
                          'local.proskurnin.preview.AssistantActivity'})
        for a in app.findall('activity')[1:]:
            self.assertEqual(a.get(A+'exported'), 'false')
        activity = app.find('activity')
        self.assertEqual(activity.get(A+'name'), 'local.proskurnin.preview.MainActivity')
        self.assertEqual({c.get(A+'name') for c in activity.findall('.//category')},
                         {'android.intent.category.LAUNCHER', 'android.intent.category.LEANBACK_LAUNCHER'})
        self.assertEqual(app.find('meta-data').get(A+'value'), 'true')
        self.assertEqual(app.get(A+'allowBackup'), 'false')

    def test_no_privileged_permissions_or_secret_assets_added(self):
        self.assertEqual({c.get(A+'name') for c in self.preview.findall('uses-permission')},
                         {'android.permission.INTERNET', 'android.permission.RECORD_AUDIO', 'android.permission.ACCESS_NETWORK_STATE',
                          'android.permission.ACCESS_WIFI_STATE'})
        self.assertFalse(self.preview.findall('permission'))
        self.assertEqual(self.preview.find('uses-sdk').get(A+'minSdkVersion'), '28')

    def test_configuration_provider_requires_shell_permission(self):
        provider = self.preview.find('application/provider')
        self.assertEqual(provider.get(A+'permission'), 'android.permission.DUMP')
        self.assertEqual(provider.get(A+'grantUriPermissions'), 'false')
        self.assertEqual(provider.get(A+'authorities'), 'local.proskurnin.xiaomipreview.configuration')
        self.assertNotIn('android.permission.DUMP',
                         {p.get(A+'name') for p in self.preview.findall('uses-permission')})

    def test_standard_manifest_is_not_modified(self):
        self.assertEqual(self.path.read_text(), self.original)
        normal = ET.fromstring(self.original)
        self.assertEqual(normal.get('package'), 'local.proskurnin.preview')
        self.assertTrue(normal.findall('.//service'))
        self.assertTrue(normal.findall('.//receiver'))


if __name__ == '__main__':
    unittest.main()
