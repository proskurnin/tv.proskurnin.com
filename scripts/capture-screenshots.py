#!/usr/bin/env python3
"""Capture and verify the curated Proskurnin TV screenshot set.

TV interaction is limited to navigation. Synthetic text is sourced only from
catalog.json and is never printed. Unmasked frames are kept in memory or in
private/screenshots during capture, never in the public output directory.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "docs" / "screenshots"
CATALOG = PUBLIC / "catalog.json"
MANIFEST = PUBLIC / "manifest.json"
PRIVATE = ROOT / "private" / "screenshots"
MAX_BYTES = 3_000_000
ADB = os.environ.get("ADB", "/Users/roman/Library/Android/sdk/platform-tools/adb")
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
SYNTHETIC_KEYS = {"movie_space", "assistant_evening", "remote_voice_space", "keyboard_space"}


def catalog():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    ids = [s["id"] for s in data["screens"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate screenshot id")
    for s in data["screens"]:
        if s.get("priority") not in ("P1", "P2", "P3"):
            raise ValueError("invalid priority: " + s["id"])
        if s.get("kind") == "tv" and any(x.startswith("SYNTHETIC:") and x.split(":", 1)[1] not in data["syntheticInputs"] for x in s.get("steps", [])):
            raise ValueError("unknown synthetic input: " + s["id"])
    return data


def run(args, timeout=20, check=True, quiet=False):
    p = subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if check and p.returncode:
        detail = p.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError((detail[:250] if detail else "command failed"))
    return p.stdout.decode("utf-8", "replace")


def adb(serial, *args, timeout=20, check=True):
    return run([ADB, "-s", serial, *args], timeout=timeout, check=check)


def png_info(path):
    raw = path.read_bytes()
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("not a PNG")
    width = height = None
    pos = 8
    chunks = []
    while pos + 12 <= len(raw):
        size = int.from_bytes(raw[pos:pos + 4], "big")
        kind = raw[pos + 4:pos + 8]
        body = raw[pos + 8:pos + 8 + size]
        if len(body) != size:
            raise ValueError("truncated PNG")
        chunks.append(kind.decode("ascii", "replace"))
        if kind == b"IHDR":
            width, height = int.from_bytes(body[:4], "big"), int.from_bytes(body[4:8], "big")
        if kind == b"IEND":
            break
        pos += size + 12
    if width is None or height is None or "eXIf" in chunks:
        raise ValueError("invalid PNG or EXIF metadata")
    return raw, width, height, chunks


def mask_png(src, dest, rects):
    try:
        from PIL import Image, ImageDraw
    except ImportError as e:
        raise RuntimeError("Pillow is required to apply the catalog privacy masks") from e
    im = Image.open(src).convert("RGB")
    draw = ImageDraw.Draw(im)
    for mask in rects:
        x, y, w, h = mask["rect"]
        if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > im.width or y + h > im.height:
            raise ValueError("invalid privacy mask coordinates")
        # Sample adjacent flat background, then cover opaquely; no blur/alpha.
        sx, sy = max(0, x - 2), max(0, y - 2)
        fill = im.getpixel((sx, sy))
        draw.rectangle((x, y, x + w - 1, y + h - 1), fill=fill)
    im.save(dest, format="PNG", optimize=True)


def validate_public(path, expected_size=None):
    raw, w, h, chunks = png_info(path)
    if len(raw) > MAX_BYTES:
        raise ValueError("PNG exceeds 3 MB: " + path.name)
    if expected_size and (w, h) != tuple(expected_size):
        raise ValueError("unexpected image dimensions: " + path.name)
    if w < 640 or h < 360:
        raise ValueError("image is too small: " + path.name)
    try:
        from PIL import Image, ImageStat
        im = Image.open(path).convert("RGB")
        if ImageStat.Stat(im).stddev == [0, 0, 0]:
            raise ValueError("blank image: " + path.name)
    except ImportError:
        pass
    return hashlib.sha256(raw).hexdigest(), w, h


def effective_masks(spec, data):
    launcher_backdrop = {"home", "home-app-menu", "rates", "settings", "settings-background", "weather", "settings-appearance", "home-move"}
    common = list(data.get("commonMasks", [])) if spec.get("id") in launcher_backdrop else []
    return common + list(spec.get("masks", []))


def manifest_data():
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"schemaVersion": 1, "device": catalog()["device"], "screens": {}}


def verify():
    c = catalog(); m = manifest_data(); errors = []
    for sid, entry in m.get("screens", {}).items():
        spec = next((x for x in c["screens"] if x["id"] == sid), None)
        path = PUBLIC / entry.get("file", sid + ".png")
        if not spec or not path.is_file():
            errors.append(sid + ": catalog or PNG missing"); continue
        try:
            digest, w, h = validate_public(path, c["device"]["resolution"] if spec["kind"] in ("tv", "manual") else None)
            if digest != entry.get("sha256"): errors.append(sid + ": SHA256 mismatch")
            if entry.get("width") != w or entry.get("height") != h: errors.append(sid + ": dimensions mismatch")
            masks = effective_masks(spec, c)
            if entry.get("masks", []) != masks: errors.append(sid + ": manifest mask record differs from catalog")
            if any(x["rect"][2] <= 0 or x["rect"][3] <= 0 for x in masks): errors.append(sid + ": privacy mask coordinates are not configured")
        except Exception as e: errors.append(sid + ": " + str(e))
    return errors


def update_manifest(spec, path, data, source="tv"):
    digest, w, h = validate_public(path, data["device"]["resolution"] if spec["kind"] in ("tv", "manual") else None)
    m = manifest_data()
    m["device"] = data["device"]
    m["screens"][spec["id"]] = {"file": path.name, "sha256": digest, "width": w, "height": h,
        "capturedAt": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "source": source,
        "launcherVersion": data["device"]["launcherVersion"], "launcherVersionCode": data["device"]["launcherVersionCode"],
        "remoteVersion": data["device"]["remoteVersion"], "remoteVersionCode": data["device"]["remoteVersionCode"],
        "masks": effective_masks(spec, data)}
    tmp = MANIFEST.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, MANIFEST)


def type_synthetic(serial, key, data):
    if key not in SYNTHETIC_KEYS or key not in data["syntheticInputs"]:
        raise RuntimeError("synthetic input is not allowlisted")
    # ADB input's argv is intentionally neither logged nor echoed.
    value = data["syntheticInputs"][key].replace(" ", "%s")
    adb(serial, "shell", "input", "text", value, timeout=8)


def nav_step(serial, step, data):
    if step == "HOME": adb(serial, "shell", "input", "keyevent", "KEYCODE_HOME")
    elif step == "BACK": adb(serial, "shell", "input", "keyevent", "KEYCODE_BACK")
    elif step in ("UP", "DOWN", "LEFT", "RIGHT", "OK"):
        code = {"UP":"DPAD_UP", "DOWN":"DPAD_DOWN", "LEFT":"DPAD_LEFT", "RIGHT":"DPAD_RIGHT", "OK":"DPAD_CENTER"}[step]
        adb(serial, "shell", "input", "keyevent", "KEYCODE_" + code)
    elif step.startswith("WAIT:"): time.sleep(min(30, int(step.split(":",1)[1])))
    elif step.startswith("SYNTHETIC:"): type_synthetic(serial, step.split(":",1)[1], data)
    elif step == "LONG_OK": adb(serial, "shell", "input", "keyevent", "--longpress", "KEYCODE_DPAD_CENTER")
    elif step.startswith("OPEN_"):
        # The TV routes below use only DPAD/OK navigation; activities are never force-started.
        nav_open(serial, step)
    elif step.startswith("EXPECT_TEXT:"): pass
    else: raise RuntimeError("unsupported navigation step")


def nav_open(serial, step):
    # These sequences are intentionally conservative. We stop at screens that
    # require selecting a setting or a profile; no toggle/save action is sent.
    seq = {
        "OPEN_MOVIE": ["UP", "OK"],
        "OPEN_ASSISTANT": ["UP", "LONG_OK"],
        "OPEN_SETTINGS": ["UP"] + ["RIGHT"] * 4 + ["OK"],
        # These routes start inside the launcher settings dialog opened by
        # OPEN_SETTINGS; do not repeat its Home toolbar navigation.
        "OPEN_BACKGROUND": ["DOWN", "OK", "DOWN", "OK"],
        "OPEN_APPEARANCE": ["DOWN", "OK"],
        "OPEN_WEATHER_SOURCES": ["UP"] + ["RIGHT"] * 4 + ["OK", "DOWN", "DOWN", "OK", "DOWN", "DOWN", "OK"],
        "OPEN_APP_KEYS": ["UP"] + ["RIGHT"] * 4 + ["OK"] + ["DOWN"] * 11 + ["OK"],
        "OPEN_REMOTE_SETTINGS": ["UP"] + ["RIGHT"] * 4 + ["OK"] + ["DOWN"] * 10 + ["OK"],
        "OPEN_OTHER": ["DOWN"] + ["DOWN"] * 16 + ["OK"]
    }.get(step)
    if seq is None: raise RuntimeError("unknown navigation route")
    for key in seq:
        nav_step(serial, key, {})
        time.sleep(.15)


def hierarchy(serial):
    PRIVATE.mkdir(parents=True, exist_ok=True)
    remote = "/sdcard/proskurnin-capture-window.xml"
    local = PRIVATE / "window.xml"
    try:
        adb(serial, "shell", "uiautomator", "dump", remote, timeout=15)
        adb(serial, "pull", remote, str(local), timeout=20)
        return local.read_text(encoding="utf-8", errors="replace")
    finally:
        adb(serial, "shell", "rm", "-f", remote, check=False)
        try: local.unlink()
        except FileNotFoundError: pass


def device_frame(serial, dest):
    remote = "/sdcard/proskurnin-capture.png"
    adb(serial, "shell", "screencap", "-p", remote, timeout=15)
    try: adb(serial, "pull", remote, str(dest), timeout=20)
    finally: adb(serial, "shell", "rm", "-f", remote, check=False)


def baseline_snapshot(serial, xml, data):
    """Save private UI hierarchy and home/folder frames once per capture run."""
    PRIVATE.mkdir(parents=True, exist_ok=True)
    if re.search(r"выключить|перезагрузить|сделать скриншот", xml, re.I):
        return
    home = PRIVATE / "baseline-home.png"
    if home.exists():
        return
    time.sleep(2)
    device_frame(serial, home)
    (PRIVATE / "baseline-window.xml").write_text(xml, encoding="utf-8")
    # The Canvas UI has no virtual tile nodes. Keep the XML dump plus a private
    # visual record for manual app-order comparison; public files stay masked.
    for key in ["DOWN"] + ["DOWN"] * 16 + ["OK"]:
        nav_step(serial, key, data)
        time.sleep(.12)
    other_xml = hierarchy(serial)
    device_frame(serial, PRIVATE / "baseline-other.png")
    (PRIVATE / "baseline-other-window.xml").write_text(other_xml, encoding="utf-8")
    nav_step(serial, "BACK", data)
    nav_step(serial, "HOME", data)


def assert_layout_unchanged(serial):
    baseline = PRIVATE / "baseline-home.png"
    if not baseline.exists():
        return
    time.sleep(2)
    current = PRIVATE / "current-home-check.png"
    device_frame(serial, current)
    try:
        from PIL import Image, ImageChops, ImageStat
        with Image.open(baseline) as a, Image.open(current) as b:
            a = a.convert("RGB")
            b = b.convert("RGB")
            # Compare the six tile interiors only. Focus rings, captions, and
            # rotating wallpaper can change between captures without changing
            # the user's app order or tile artwork.
            tiles = [(120, 725, 375, 860), (402, 725, 662, 860),
                     (688, 725, 947, 860), (972, 725, 1233, 860),
                     (1258, 725, 1517, 860), (1543, 725, 1802, 860)]
            deltas = [statistics.mean(ImageStat.Stat(ImageChops.difference(a.crop(box), b.crop(box))).mean)
                      for box in tiles]
        if max(deltas) > 8.0:
            raise RuntimeError("CRITICAL: home tile region differs from private baseline; screenshot withheld")
    except ImportError as e:
        raise RuntimeError("Pillow is required to compare home tile layout with baseline") from e


def check_device(serial, data):
    adb(serial, "get-state", timeout=5)
    product = adb(serial, "shell", "getprop", "ro.product.model").strip()
    device = adb(serial, "shell", "getprop", "ro.product.device").strip()
    if product not in data["device"]["productModelAliases"] or device not in data["device"]["deviceAliases"]:
        raise RuntimeError("connected device does not match Sber SDX-43U4123B profile")
    if ":" in serial and not serial.startswith("emulator-"):
        target_host = serial.rsplit(":", 1)[0]
        wlan = adb(serial, "shell", "ip", "-o", "-4", "addr", "show", "wlan0", check=False)
        if target_host not in re.findall(r"\binet\s+(\d{1,3}(?:\.\d{1,3}){3})/", wlan):
            raise RuntimeError("ADB target IP does not match the connected Sber Wi-Fi address")
    version = adb(serial, "shell", "dumpsys", "package", data["device"]["package"])
    if not re.search(r"versionName=" + re.escape(data["device"]["launcherVersion"]) + r"\b", version) or not re.search(r"versionCode=" + str(data["device"]["launcherVersionCode"]) + r"\b", version):
        raise RuntimeError("installed launcher version differs from catalog")
    activities = adb(serial, "shell", "dumpsys", "activity", "activities")
    if data["device"]["package"] not in activities:
        raise RuntimeError("current screen is not the Proskurnin launcher; no capture performed")
    # Store the original hierarchy privately for audit; never publish it.
    baseline = hierarchy(serial)
    baseline_snapshot(serial, baseline, catalog())
    return baseline


def capture_tv(serial, spec, data, dry_run=False):
    if dry_run:
        print(spec["id"] + ": navigation plan valid")
        return False
    for attempt in range(1, 4):
        try:
            for step in spec.get("steps", []): nav_step(serial, step, data)
            xml = hierarchy(serial)
            if any(t.lower() in xml.lower() for t in spec.get("forbidden", [])):
                raise RuntimeError("forbidden screen state")
            for expected in spec.get("expected", []):
                if expected not in xml: raise RuntimeError("expected UI text not exposed to accessibility")
            raw_path = PRIVATE / (spec["id"] + ".raw.png")
            adb(serial, "shell", "screencap", "-p", "/sdcard/proskurnin-capture.png", timeout=15)
            adb(serial, "pull", "/sdcard/proskurnin-capture.png", str(raw_path), timeout=20)
            adb(serial, "shell", "rm", "-f", "/sdcard/proskurnin-capture.png", check=False)
            candidate = PRIVATE / (spec["id"] + ".candidate.png")
            masks = effective_masks(spec, data)
            if masks:
                if any(m["rect"][2] <= 0 or m["rect"][3] <= 0 for m in masks):
                    raise RuntimeError("privacy mask coordinates require visual calibration; frame withheld")
                mask_png(raw_path, candidate, masks)
            else:
                shutil.copyfile(raw_path, candidate)
            # Return to launcher using Back then Home and ensure the current
            # activity remains ours. The full private baseline XML is retained.
            nav_step(serial, "BACK", data)
            nav_step(serial, "HOME", data)
            state = adb(serial, "shell", "dumpsys", "activity", "activities")
            if data["device"]["package"] not in state:
                raise RuntimeError("failed to return to Proskurnin Home")
            assert_layout_unchanged(serial)
            dest = PUBLIC / (spec["id"] + ".png")
            shutil.copyfile(candidate, dest)
            update_manifest(spec, dest, data)
            print(spec["id"] + ": captured")
            return True
        except Exception as e:
            print(spec["id"] + ": attempt " + str(attempt) + " skipped (" + str(e)[:160] + ")")
            try: nav_step(serial, "BACK", data); nav_step(serial, "HOME", data)
            except Exception: pass
            if attempt < 3: time.sleep(1)
    return False


def capture_manual_power(serial, spec, data):
    check_device(serial, data)
    xml = hierarchy(serial)
    if not re.search(r"выключ|перезагруз|питани|сон", xml, re.I):
        raise RuntimeError("power menu text was not recognized; frame withheld")
    PRIVATE.mkdir(parents=True, exist_ok=True)
    raw_path = PRIVATE / "power-menu.raw.png"
    adb(serial, "shell", "screencap", "-p", "/sdcard/proskurnin-capture.png", timeout=15)
    adb(serial, "pull", "/sdcard/proskurnin-capture.png", str(raw_path), timeout=20)
    adb(serial, "shell", "rm", "-f", "/sdcard/proskurnin-capture.png", check=False)
    # Validate the physical frame before publishing. No POWER key is sent.
    dest = PUBLIC / "power-menu.png"
    masks = effective_masks(spec, data)
    if masks: mask_png(raw_path, dest, masks)
    else: shutil.copyfile(raw_path, dest)
    update_manifest(spec, dest, data, "owner-opened-menu")
    print("power-menu: captured; owner may close it with Back")


def render_boot(spec, data):
    source = ROOT / "builds" / "proskurnin-boot-v7" / "preview-animation.png"
    metadata = ROOT / "builds" / "proskurnin-boot-v7" / "manifest.json"
    if not source.is_file() or not metadata.is_file():
        raise RuntimeError("boot renderer output or manifest is missing")
    info = json.loads(metadata.read_text(encoding="utf-8"))
    expected = info.get("files", {}).get("preview-animation.png")
    if not expected or hashlib.sha256(source.read_bytes()).hexdigest() != expected:
        raise RuntimeError("existing boot preview does not match its renderer manifest")
    shutil.copyfile(source, PUBLIC / "boot.png")
    update_manifest(spec, PUBLIC / "boot.png", data, "render-proskurnin-boot-v7")
    print("boot: copied hash-verified preview from the v7 renderer output")


def capture_remote(spec, data):
    """Render the shipped remote UI with deterministic local-only mock state."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sync_playwright = None
    assets = ROOT / "builds" / "proskurnin-remote-v1" / "app" / "assets"
    with tempfile.TemporaryDirectory(prefix="proskurnin-remote-shot-") as td:
        temp = Path(td)
        shutil.copyfile(assets / "style.css", temp / "style.css")
        html = (assets / "index.html").read_text(encoding="utf-8")
        html = html.replace('href="/style.css"', 'href="style.css"')
        html = re.sub(r'<script src="/app\.js" defer></script>', '', html)
        phrase = json.dumps(data["syntheticInputs"].get(spec.get("input", ""), ""), ensure_ascii=False)
        page_mode = spec.get("page")
        fixture = """
<script>
const $=id=>document.getElementById(id);
document.querySelector('#pairing').hidden=true;document.querySelector('#controls').hidden=false;
document.querySelector('#offline').hidden=true;document.querySelector('#dot').classList.add('ready');
document.querySelector('#status').textContent='Подключён';
document.querySelector('#volumeValue').textContent='18 / 30';
document.querySelector('#quickApps').innerHTML='<button>Кинопоиск</button><button>Иви</button><button>Okko</button><button>YouTube</button>';
document.querySelector('#allApps').innerHTML='<button>Кинопоиск</button><button>Иви</button><button>Okko</button><button>YouTube</button>';
document.querySelector('#feedback').textContent='Локальный макет · команды отключены';
document.querySelector('#voiceMode').value='movie';
document.querySelector('#httpsSetup').hidden=true;
document.querySelector('#voiceToggle').disabled=false;document.querySelector('#voiceMode').disabled=false;
document.querySelector('#voiceText').value=__PHRASE__;
document.querySelector('#tvText').value=__PHRASE__;
if(__PAGE__==='remote-voice'){document.querySelector('#voicePanel').hidden=false;document.querySelector('#voiceStatus').textContent='Проверьте фразу и нажмите «Отправить на ТВ».';document.querySelector('#voiceSend').disabled=false;}
if(__PAGE__==='remote-keyboard'){document.querySelector('#textPanel').hidden=false;document.querySelector('#tvText').disabled=false;document.querySelector('#textStatus').textContent='Локальный пример активного поля ТВ';}
if(__PAGE__==='remote-pair'){document.querySelector('#controls').hidden=true;document.querySelector('#pairing').hidden=false;document.querySelector('#status').textContent='Нужно сопряжение';document.querySelector('#phoneName').value='';}
</script>
""".replace("__PHRASE__", phrase).replace("__PAGE__", json.dumps(page_mode))
        html = html.replace("</body>", fixture + "</body>")
        path = temp / "index.html"
        path.write_text(html, encoding="utf-8")
        out = PRIVATE / (spec["id"] + ".remote.png")
        PRIVATE.mkdir(parents=True, exist_ok=True)
        if sync_playwright:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
                page.goto(path.as_uri(), wait_until="networkidle", timeout=20000)
                page.screenshot(path=str(out), full_page=False, animations="disabled")
                browser.close()
        elif Path(CHROME).is_file():
            profile = temp / "chrome-profile"
            run([CHROME, "--headless=new", "--disable-gpu", "--disable-background-networking", "--disable-sync",
                 "--no-first-run", "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=1920,1080",
                 "--user-data-dir=" + str(profile), "--screenshot=" + str(out), path.as_uri()], timeout=60)
        else:
            raise RuntimeError("local remote-page capture needs Playwright or Chrome")
        masks = effective_masks(spec, data)
        if masks: mask_png(out, PUBLIC / (spec["id"] + ".png"), masks)
        else: shutil.copyfile(out, PUBLIC / (spec["id"] + ".png"))
        update_manifest(spec, PUBLIC / (spec["id"] + ".png"), data, "local-remote-mock")
        print(spec["id"] + ": rendered from local remote assets with mock data")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--serial")
    p.add_argument("--list", action="store_true")
    p.add_argument("--id", dest="sid")
    p.add_argument("--priority", choices=("P1", "P2", "P3"))
    p.add_argument("--all", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--manual", action="store_true")
    p.add_argument("--verify", action="store_true")
    p.add_argument("--remote", action="store_true")
    p.add_argument("--render", action="store_true")
    a = p.parse_args()
    try:
        data = catalog()
        if a.list:
            for s in data["screens"]: print(f"{s['priority']} {s['id']} [{s['kind']}] {s['title']}")
            return 0
        if a.verify:
            errors = verify()
            for error in errors: print(error)
            print("Screenshot verification:", "FAILED" if errors else "passed")
            return bool(errors)
        if not (a.sid or a.priority or a.all): p.error("select --id, --priority or --all")
        chosen = [s for s in data["screens"] if a.all or s["id"] == a.sid or s["priority"] == a.priority]
        if a.sid and not chosen: p.error("unknown screenshot id")
        for s in chosen:
            if s["kind"] == "owner": print(s["id"] + ": owner-supplied image required; skipped")
            elif s["kind"] == "deferred": print(s["id"] + ": deferred — " + s.get("reason", "owner action required"))
            elif s["kind"] == "manual":
                if a.manual and (a.sid == s["id"] or a.all or a.priority == s["priority"]):
                    if not a.serial: p.error("--serial is required for manual TV capture")
                    capture_manual_power(a.serial, s, data)
                else: print(s["id"] + ": use --manual --id " + s["id"])
            elif s["kind"] == "render":
                if a.render: render_boot(s, data)
                else: print(s["id"] + ": pass --render to generate from the local renderer")
            elif s["kind"] == "remote":
                if a.remote: capture_remote(s, data)
                else: print(s["id"] + ": pass --remote to render from a local mock")
            elif s["kind"] == "tv":
                if not a.dry_run and not a.serial: p.error("--serial is required for TV captures")
                if not a.dry_run: check_device(a.serial, data)
                capture_tv(a.serial, s, data, a.dry_run)
        return 0
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as e:
        print("capture-screenshots:", str(e)[:250], file=sys.stderr)
        return 2


if __name__ == "__main__": sys.exit(main())
