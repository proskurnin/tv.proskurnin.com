"""Site builder: changelog parsing, credits and numbers. No Pillow, no network."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_site', ROOT / 'scripts' / 'build-site.py')
build_site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_site)

SAMPLE = """# Журнал

## 1.39 (code 51) — 2026-11-09

- Фоны: **«Горы и озёра»** и `Море`, см. [документ](docs/X.md).
- Второй пункт.

## Исследование 4K — 2026-11-09, лаунчер остаётся 1.38

Абзац без маркеров.

## Более ранние этапы — 2026-11-07–08

- Первые опыты.
"""


class ChangelogTest(unittest.TestCase):
    def test_sample(self):
        entries = build_site.parse_changelog(SAMPLE)
        self.assertEqual([e['title'] for e in entries], ['Более ранние этапы', 'Исследование 4K', '1.39 (code 51)'])
        early, research, release = entries
        self.assertEqual(early['dateText'], '7–8 ноября 2026')
        self.assertEqual(early['version'], '')
        self.assertEqual(research['items'], ['Абзац без маркеров.'])
        self.assertEqual(release['version'], '1.39')
        self.assertEqual(release['code'], 51)
        self.assertEqual(release['items'][0], 'Фоны: «Горы и озёра» и Море, см. документ.')
        s = build_site.stats(entries, '1.39', '1.1.1')
        self.assertEqual((s['releases'], s['days'], s['first'], s['last']), (1, 3, '2026-11-07', '2026-11-09'))

    def test_real_changelog(self):
        entries = build_site.parse_changelog((ROOT / 'CHANGELOG.md').read_text(encoding='utf-8'))
        self.assertGreater(len(entries), 10)
        self.assertTrue(all(e['items'] for e in entries))
        self.assertTrue(all(len(t) <= 321 for e in entries for t in e['items']))
        dates = [e['date'] for e in entries if e['date']]
        self.assertEqual(dates, sorted(dates))

    def test_clip(self):
        self.assertEqual(build_site.clip('слово ' * 100, 20), 'слово слово слово…')


class CreditsTest(unittest.TestCase):
    def test_mountain_backgrounds_have_attribution(self):
        credits = build_site.parse_credits((build_site.BACKGROUNDS / 'CREDITS.txt').read_text(encoding='utf-8'))
        for period in build_site.PERIODS:
            c = credits[('mountains', period)]
            self.assertTrue(c['author'] and c['license'].startswith('CC BY'))
            self.assertTrue(c['licenseUrl'].startswith('https://creativecommons.org/'))
            self.assertTrue(c['source'].startswith('https://commons.wikimedia.org/'))
            self.assertTrue((build_site.BACKGROUNDS / 'mountains' / f'{period}.jpg').is_file())

    def test_versions(self):
        self.assertRegex(build_site.version_name(build_site.LAUNCHER_MANIFEST), r'^\d+\.\d+')
        self.assertRegex(build_site.version_name(build_site.REMOTE_MANIFEST), r'^\d+\.\d+')


if __name__ == '__main__':
    unittest.main()
