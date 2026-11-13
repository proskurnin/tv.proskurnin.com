#!/usr/bin/env python3
"""Build the static site https://tv.proskurnin.com/ into dist/site.

Inputs (all from this repository):
  site/                              page sources (index.html, assets/)
  docs/screenshots/manifest.json     screenshots; missing ones become empty frames on the page
  CHANGELOG.md                       release log, numbers on the page
  builds/*/AndroidManifest.xml       current launcher and remote versions
  builds/proskurnin-preview-v1/app/assets/backgrounds/mountains/*.jpg + CREDITS.txt
Output: dist/site with content-hashed files under assets/ (served as immutable).
Needs Pillow. Does not touch the TV or the network.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
SHOTS = ROOT / 'docs' / 'screenshots'
BACKGROUNDS = ROOT / 'builds' / 'proskurnin-preview-v1' / 'app' / 'assets' / 'backgrounds'
LAUNCHER_MANIFEST = ROOT / 'builds' / 'proskurnin-preview-v1' / 'app' / 'AndroidManifest.xml'
REMOTE_MANIFEST = ROOT / 'builds' / 'proskurnin-remote-v1' / 'app' / 'AndroidManifest.xml'
PERIODS = ('morning', 'day', 'evening', 'night')
HOURS = [6, 11, 17, 22]  # BackgroundConfig.DEFAULT_HOURS
MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']


def short_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:10]


def clean_md(text: str) -> str:
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = text.replace('**', '').replace('`', '')
    return re.sub(r'\s+', ' ', text).strip()


def clip(text: str, limit: int = 320) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(' ', 1)[0].rstrip(',;:—-')
    return cut + '…'


def parse_changelog(text: str) -> list[dict]:
    """Sections '## …' newest first → entries oldest first."""
    entries = []
    for block in re.split(r'^## ', text, flags=re.M)[1:]:
        lines = block.splitlines()
        heading = lines[0].strip()
        body = [l.rstrip() for l in lines[1:]]
        bullets = [clean_md(l[2:]) for l in body if l.startswith('- ')]
        paras = [clean_md(l) for l in body if l.strip() and not l.startswith(('- ', '#', '|', '```', '    '))]
        items = [clip(t) for t in (bullets or paras) if t][:6]
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', heading)
        version = re.match(r'(\d+\.\d+(?:\.\d+)?)\b', heading)
        code = re.search(r'\bcode (\d+)', heading)
        title = re.split(r' — ', heading, maxsplit=1)[0].strip()
        date = dates[0] if dates else ''
        span = re.search(r'(\d{4})-(\d{2})-(\d{2})–(\d{2})', heading)
        date_text = f'{int(span.group(3))}–{int(span.group(4))} {MONTHS[int(span.group(2)) - 1]} {span.group(1)}' if span else ''
        entries.append({
            'version': version.group(1) if version else '',
            'code': int(code.group(1)) if code else None,
            'title': title,
            'date': date,
            'dateText': date_text,
            'items': items,
        })
    entries.reverse()
    return entries


def stats(entries: list[dict], launcher: str, remote: str) -> dict:
    dates = sorted(e['date'] for e in entries if e['date'])
    days = (dt.date.fromisoformat(dates[-1]) - dt.date.fromisoformat(dates[0])).days + 1 if dates else None
    return {
        'releases': sum(1 for e in entries if e['version']),
        'first': dates[0] if dates else '',
        'last': dates[-1] if dates else '',
        'days': days,
        'version': launcher,
        'remote': remote,
    }


def catalog_titles() -> dict:
    """id -> title from docs/screenshots/catalog.json (the manifest does not repeat titles)."""
    path = SHOTS / 'catalog.json'
    if not path.exists():
        return {}
    screens = json.loads(path.read_text(encoding='utf-8')).get('screens', [])
    items = screens.values() if isinstance(screens, dict) else screens
    return {s['id']: s.get('title', '') for s in items if isinstance(s, dict) and 'id' in s}


def manifest_screens(manifest: dict, titles: dict) -> list:
    """Screens as a list of dicts with 'id'. Accepts both manifest layouts:
    a list of {id, ...} (docs/SCREENSHOTS.md 7.2) and a map {id: {...}} written by capture-screenshots.py."""
    screens = manifest.get('screens', [])
    if isinstance(screens, dict):
        screens = [{'id': sid, **entry} for sid, entry in screens.items() if isinstance(entry, dict)]
    out = []
    for s in screens:
        if isinstance(s, dict):
            s = dict(s)
            s.setdefault('title', titles.get(s.get('id', ''), ''))
            out.append(s)
    return out


def phone_crop(img: 'Image.Image') -> 'Image.Image':
    """Phone remote shots go into a 390x844 phone frame. A landscape capture of the remote page
    (centred column on an empty background) is cut to that aspect around its centre for the site only;
    the PNG in docs/screenshots stays untouched."""
    ratio = 390 / 844
    if img.width / img.height <= ratio:
        return img
    w = round(img.height * ratio)
    left = (img.width - w) // 2
    return img.crop((left, 0, left + w, img.height))


def version_name(manifest: Path) -> str:
    m = re.search(r'android:versionName="([^"]+)"', manifest.read_text(encoding='utf-8')) if manifest.exists() else None
    return m.group(1) if m else ''


def parse_credits(text: str) -> dict:
    """CREDITS.txt blocks: 'set / period', file title, 'Автор: …', 'LICENSE — url', source url."""
    out = {}
    for block in re.split(r'\n\s*\n', text.strip()):
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if len(lines) < 5 or ' / ' not in lines[0]:
            continue
        key = tuple(p.strip() for p in lines[0].split(' / ', 1))
        lic = lines[3].split(' — ', 1)
        out[key] = {
            'title': re.sub(r'\.(jpe?g|png)$', '', lines[1], flags=re.I),
            'author': lines[2].split(':', 1)[1].strip() if ':' in lines[2] else lines[2],
            'license': lic[0].strip(),
            'licenseUrl': lic[1].strip() if len(lic) > 1 else '',
            'source': lines[4],
        }
    return out


def webp(img, quality: int) -> bytes:
    buf = io.BytesIO()
    img.save(buf, 'WEBP', quality=quality, method=6)
    return buf.getvalue()


def write_hashed(out_dir: Path, stem: str, ext: str, data: bytes) -> str:
    name = f'{stem}.{short_hash(data)}.{ext}'
    (out_dir / name).write_bytes(data)
    return name


def build(out: Path) -> dict:
    from PIL import Image  # imported here so --help works without Pillow

    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(SITE, out)
    assets = out / 'assets'
    (assets / 'img').mkdir(parents=True, exist_ok=True)
    (assets / 'shots').mkdir(parents=True, exist_ok=True)

    # Backgrounds: the launcher's "Mountains and lakes" set, with attribution.
    credits = parse_credits((BACKGROUNDS / 'CREDITS.txt').read_text(encoding='utf-8'))
    bg = {}
    for period in PERIODS:
        src = BACKGROUNDS / 'mountains' / f'{period}.jpg'
        img = Image.open(src).convert('RGB')
        if img.width > 1920:
            img = img.resize((1920, round(img.height * 1920 / img.width)), Image.LANCZOS)
        name = write_hashed(assets / 'img', f'bg-{period}', 'webp', webp(img, 74))
        bg[period] = {'src': f'/assets/img/{name}', **credits[('mountains', period)]}

    # Screenshots listed in the manifest (docs/SCREENSHOTS.md); the page shows empty frames for the rest.
    screens = {}
    manifest_path = SHOTS / 'manifest.json'
    if manifest_path.exists():
        for s in manifest_screens(json.loads(manifest_path.read_text(encoding='utf-8')), catalog_titles()):
            sid, file = s.get('id', ''), SHOTS / s.get('file', '')
            if not re.fullmatch(r'[a-z0-9-]+', sid) or not file.is_file():
                continue
            img = Image.open(file).convert('RGB')
            if sid.startswith('remote-'):
                img = phone_crop(img)
            full = write_hashed(assets / 'shots', sid, 'webp', webp(img, 86))
            small_w = 960 if img.width >= img.height else max(1, img.width // 2)
            small_img = img.resize((small_w, round(img.height * small_w / img.width)), Image.LANCZOS) if img.width > small_w else img
            small = write_hashed(assets / 'shots', f'{sid}-s', 'webp', webp(small_img, 82))
            screens[sid] = {
                'src': f'/assets/shots/{full}', 'w': img.width, 'h': img.height,
                'srcSmall': f'/assets/shots/{small}', 'wSmall': small_img.width,
                'title': s.get('title', ''), 'version': s.get('launcherVersion', ''),
            }

    releases = parse_changelog((ROOT / 'CHANGELOG.md').read_text(encoding='utf-8'))
    data = {
        'screens': screens,
        'bg': bg,
        'hours': HOURS,
        'releases': releases,
        'stats': stats(releases, version_name(LAUNCHER_MANIFEST), version_name(REMOTE_MANIFEST)),
    }

    # Content-hashed CSS/JS/icon; index.html gets the data inline.
    index = (out / 'index.html').read_text(encoding='utf-8')
    for rel in ('assets/style.css', 'assets/app.js', 'assets/favicon.svg'):
        path = out / rel
        raw = path.read_bytes()
        stem, ext = path.name.rsplit('.', 1)
        name = write_hashed(path.parent, stem, ext, raw)
        path.unlink()
        assert index.count(f'/{rel}') == 1, rel
        index = index.replace(f'/{rel}', f'/assets/{name}')
    assert index.count('<!--DATA-->') == 1
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    index = index.replace('<!--DATA-->', payload)
    (out / 'index.html').write_text(index, encoding='utf-8')
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out', type=Path, default=ROOT / 'dist' / 'site')
    args = parser.parse_args()
    data = build(args.out)
    s = data['stats']
    print(f"Built {args.out}: {len(data['screens'])} screenshots, {len(data['releases'])} log entries, "
          f"{s['releases']} releases over {s['days']} days, launcher {s['version']}, remote {s['remote']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
