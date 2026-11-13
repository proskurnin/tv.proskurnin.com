/* Proskurnin TV site: language, time-of-day background, clock, screenshots from the
   build manifest, detail dialog and arrow-key (TV remote style) navigation. */
(() => {
  'use strict';
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  let data = {};
  try { data = JSON.parse($('#site-data').textContent || '{}'); } catch (e) { data = {}; }
  const screens = data.screens || {};
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } },
  };

  // ── Language: saved choice > #en/#ru > browser (EN only without Russian) > RU ──
  const EN = {
    m1: 'Features', m2: 'Remote', m3: 'How it was built', m4: 'Limits', menu: 'Sections',
    kicker: 'Launcher for Android TV',
    h1: 'A home screen of my own for an ordinary TV',
    lead: 'Proskurnin TV replaces the stock home screen: six favourite apps, weather, exchange rates, YouTube, AI movie picks and a remote on the phone. Built for one specific TV.',
    cta1: 'What it does', cta2: 'Source on GitHub ↗', 'cap-home': 'Proskurnin TV home screen',
    facts: 'Project in numbers', f1: 'launcher releases in the changelog', f2: 'days from the first experiments to the current version',
    f3: 'current version · remote <span id="f-remote">—</span>', f4: 'API keys inside the app — they live on the server',
    s1k: 'Home screen', s1h: 'Everything you need in one row', s1p: 'Pick a tile with the mouse or the arrow keys and press Enter — just like on the remote.',
    't-apps': 'Top six', 't-apps-s': 'Favourite apps in one row', 't-apps-d': 'The main row holds up to six apps; the rest are one press of the down arrow away. A long OK on a tile opens a menu: move, replace, remove from the home screen or hide in the “Other” folder. The order is kept.',
    't-other': '“Other”', 't-other-s': 'A folder for the clutter', 't-other-d': 'System and rarely used apps go to “Other”: they stay installed and working but no longer clutter the lists. An app can be brought back from the same folder.',
    't-weather': 'Weather', 't-weather-s': 'With a freshness stamp', 't-weather-d': 'Weather comes from Open-Meteo, falling back to wttr.in, each over its own route. It shows the provider’s data time, not the request time, so you can see how fresh it is.',
    't-rates': 'Rates', 't-rates-s': 'USD, EUR, CNY and BTC', 't-rates-d': 'Dollar, euro, yuan and bitcoin in dollars: change against the previous day and 7-day charts right on the home screen.',
    't-yt': 'YouTube', 't-yt-s': 'Counter and quick launch', 't-yt-d': 'A subscriber counter for the channel on the home screen, with read-only YouTube access. SmartTube starts from the main row; if it is missing, the launcher says so.',
    't-movies': 'What to watch', 't-movies-s': 'Describe a movie in words', 't-movies-d': 'Describe what you feel like watching, in words or by voice. AI together with TMDB suggests three cards with year, rating and runtime, with the full list on request. “Where to watch” shows streaming services from TMDB and JustWatch data.',
    't-ai': 'AI chat', 't-ai-s': 'Ask by voice, read on screen', 't-ai-d': 'A conversation with AI on the TV screen. Questions come from the phone remote, by voice or text. API keys are kept on the server, not in the app.',
    't-bg': 'Backgrounds', 't-bg-s': 'Morning, day, evening, night', 't-bg-d': 'Landscapes follow the time of day with a smooth transition: “Mountains and lakes” and “Sea” sets, a custom schedule or a fixed period. The photos are built into the app and work offline. This site’s background changes the same way.',
    't-dream': 'Screensaver', 't-dream-s': 'Video without internet', 't-dream-d': 'The screensaver keeps up to five clips in a local cache (up to 300 MB) and refreshes them in the background, so it starts instantly and does not depend on the network.',
    't-power': 'Power', 't-power-s': 'A three-action menu of its own', 't-power-d': 'Holding Power opens the launcher’s own three-action menu instead of the system window. It can be switched off in settings to bring the system one back.',
    't-home': 'Home button', 't-home-s': 'Its own screen and the old one', 't-home-d': 'A short Home press opens Proskurnin TV, a long one opens the stock Google TV home screen. The usual system screens stay within reach.',
    't-boot': 'Boot', 't-boot-s': 'PROSKURNIN · TV SYSTEM', 't-boot-d': 'The TV starts with its own boot screen: white background, PROSKURNIN · TV SYSTEM and seven coloured squares that fade in and blink in turn.',
    s2k: 'Phone remote', s2h: 'A remote in the phone’s browser', s2p: 'No extra app: the page opens from a QR code on the TV screen.',
    r1: 'Home network only: no port is exposed to the internet, no cloud.', r2: 'Pairing by QR code and an on-screen code; the phone is confirmed on the TV.',
    r3: 'Arrows, OK, volume, quick app launch and typing into a field on the TV.', r4: 'Voice is recorded only while you press, up to 30 seconds. You can fix the recognised phrase before sending.',
    r5: 'Three voice modes: “Let’s talk”, “Find a movie” and “Into the TV field”.',
    'cap-remote1': 'Buttons and quick launch', 'cap-remote2': 'Voice: the phrase can be edited',
    s3k: 'How it was built', s3h: 'Every change: a version, checks and a rollback', s3p: 'The log below is built automatically from the project changelog. Use ← → to browse, Enter for details.',
    p1: '<b>Keys stay on the server.</b> The app has no API keys at all: requests go through its own gateway.',
    p2: '<b>The UI never waits for the network.</b> Background, weather and rates load in the background and stop when the screen is hidden.',
    p3: '<b>Read first, change later.</b> Any change to the TV starts with read-only diagnostics and a copy of the original state.',
    p4: '<b>Tested means tested on the TV.</b> Emulation is never passed off as a check with the physical remote.',
    releases: 'Releases',
    s4k: 'Limits', s4h: 'Honest about what is missing',
    l1: 'Built for one TV on Android 9 (m7332 board). It is not a firmware for everyone: do not run it on another model.',
    l2: 'The UI runs in Full HD and the 4K panel gets an upscaled picture. Real 4K is still being researched.',
    l3: 'Power-off from its own menu works, but after a reboot the TV still waits for the physical Power button.',
    l4: 'There is no direct jump to a movie in a streaming app yet — the launcher shows where it is available.',
    s5k: 'Next', s5h: 'What is planned',
    n1: 'A 4K interface with a Full HD / 4K switch and automatic fallback.', n2: 'Reboot without the physical Power button.',
    n3: 'A catalogue of downloadable backgrounds with licences and a storage limit.', n4: 'Jump from a movie pick straight to the movie in a streaming app.',
    n5: 'Better picks: negations, runtime, language, animated or live action.',
    foot1: 'Proskurnin TV is a personal project for a home TV. <a class="nav" href="https://github.com/proskurnin/tv.proskurnin.com" target="_blank" rel="noopener">GitHub ↗</a> · <a class="nav" href="https://proskurnin.ru/" target="_blank" rel="noopener">proskurnin.ru ↗</a>',
    hint1: 'select', hint2: 'open', hint3: 'back', close: 'Back',
  };
  const META = {
    ru: { title: document.title, desc: $('meta[name="description"]').content },
    en: { title: 'Proskurnin TV — a home screen of my own for Android TV', desc: 'Proskurnin TV is a custom launcher for a home Android TV: six main apps, weather, rates, YouTube, AI movie picks and a remote on the phone.' },
  };
  const ruText = new Map();
  $$('[data-t]').forEach((el) => ruText.set(el, el.innerHTML));
  const ruAria = new Map();
  $$('[data-t-aria]').forEach((el) => ruAria.set(el, el.getAttribute('aria-label')));

  function detectLang() {
    const saved = store.get('tv.lang');
    if (saved === 'ru' || saved === 'en') return saved;
    if (location.hash === '#en' || location.hash === '#ru') return location.hash.slice(1);
    const langs = (navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || '']).map((l) => String(l).toLowerCase());
    return langs.some((l) => l.startsWith('en')) && !langs.some((l) => l.startsWith('ru')) ? 'en' : 'ru';
  }
  let lang = detectLang();

  function applyLang() {
    document.documentElement.lang = lang;
    ruText.forEach((ru, el) => { const en = EN[el.dataset.t]; el.innerHTML = lang === 'en' && en ? en : ru; });
    ruAria.forEach((ru, el) => { el.setAttribute('aria-label', lang === 'en' ? (EN[el.dataset.tAria] || ru) : ru); });
    document.title = META[lang].title;
    $('meta[name="description"]').content = META[lang].desc;
    const btn = $('#lang');
    btn.textContent = lang === 'en' ? 'RU' : 'EN';
    btn.setAttribute('aria-label', lang === 'en' ? 'Русский' : 'English');
    renderFacts(); renderShots(); renderReleases(); renderCredit(); tick();
  }
  $('#lang').addEventListener('click', () => { lang = lang === 'en' ? 'ru' : 'en'; store.set('tv.lang', lang); applyLang(); });

  const T = (ru, en) => (lang === 'en' ? en : ru);

  // ── Facts from the changelog ──
  function renderFacts() {
    const s = data.stats || {};
    const set = (id, v) => { const el = $('#' + id); if (el && v !== undefined && v !== null && v !== '') el.textContent = v; };
    set('f-releases', s.releases); set('f-days', s.days); set('f-version', s.version); set('f-remote', s.remote);
  }

  // ── Background by time of day (same default hours as the launcher) ──
  const hours = Array.isArray(data.hours) && data.hours.length === 4 ? data.hours : [6, 11, 17, 22];
  const periodOf = (h) => (h >= hours[0] && h < hours[1] ? 'morning' : h >= hours[1] && h < hours[2] ? 'day' : h >= hours[2] && h < hours[3] ? 'evening' : 'night');
  let period = '';
  function renderBg() {
    const p = periodOf(new Date().getHours());
    if (p === period) return;
    period = p;
    const bg = (data.bg || {})[p];
    if (bg) $('.bg').style.backgroundImage = `url("${bg.src}")`;
    renderCredit();
  }
  function renderCredit() {
    const bg = (data.bg || {})[period];
    const el = $('#bg-credit');
    if (!bg || !el) return;
    const names = { morning: T('утро', 'morning'), day: T('день', 'day'), evening: T('вечер', 'evening'), night: T('ночь', 'night') };
    el.textContent = '';
    el.append(T('Фон сейчас', 'Background now'), ` (${names[period]}): `);
    const a = document.createElement('a');
    a.href = bg.source; a.target = '_blank'; a.rel = 'noopener'; a.className = 'nav'; a.textContent = bg.title;
    const l = document.createElement('a');
    l.href = bg.licenseUrl; l.target = '_blank'; l.rel = 'noopener license'; l.className = 'nav'; l.textContent = bg.license;
    el.append(a, ` — ${bg.author}, `, l, T(', затемнено', ', darkened'));
  }

  // ── Clock ──
  function tick() {
    const now = new Date();
    const loc = lang === 'en' ? 'en-GB' : 'ru-RU';
    const c = $('#clock');
    c.dateTime = now.toISOString();
    c.innerHTML = `${now.toLocaleTimeString(loc, { hour: '2-digit', minute: '2-digit' })}<small>${now.toLocaleDateString(loc, { weekday: 'short', day: 'numeric', month: 'short' })}</small>`;
    renderBg();
  }
  setInterval(tick, 15000);

  // ── Screenshots: real image when the manifest has it, otherwise an honest empty frame ──
  function shotNode(id) {
    const s = screens[id];
    if (s) {
      const img = document.createElement('img');
      img.src = s.src; img.width = s.w; img.height = s.h; img.loading = 'lazy'; img.decoding = 'async';
      if (s.srcSmall) { img.srcset = `${s.srcSmall} ${s.wSmall}w, ${s.src} ${s.w}w`; img.sizes = s.h > s.w ? '260px' : '(max-width: 900px) 100vw, 60vw'; }
      img.alt = s.title || '';
      return img;
    }
    const d = document.createElement('div');
    d.className = 'empty';
    d.innerHTML = '<span class="squares" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></span>';
    d.append(T('Снимок экрана появится скоро', 'Screenshot coming soon'));
    return d;
  }
  function renderShots() {
    $$('[data-shot]').forEach((el) => { el.replaceChildren(shotNode(el.dataset.shot)); });
  }

  // ── Releases strip (changelog text stays in Russian) ──
  const fmtDate = (iso) => (iso ? new Date(iso + 'T12:00:00').toLocaleDateString(lang === 'en' ? 'en-GB' : 'ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }) : '');
  function renderReleases() {
    const box = $('#releases');
    if (!box) return;
    box.replaceChildren();
    (data.releases || []).forEach((r, i) => {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'rel nav'; b.setAttribute('role', 'listitem'); b.dataset.rel = i;
      const v = document.createElement('span');
      v.className = 'v' + (r.version ? '' : ' word-v');
      v.textContent = r.version || r.title;
      const d = document.createElement('span'); d.className = 'd'; d.textContent = r.dateText || fmtDate(r.date);
      const p = document.createElement('p'); p.lang = 'ru'; p.textContent = r.items[0] || '';
      b.append(v, d, p);
      box.append(b);
    });
  }

  // ── Detail dialog ──
  const dlg = $('#dlg');
  let lastFocus = null;
  function openDialog(title, bodyNodes, shotId) {
    lastFocus = document.activeElement;
    $('#dlg-title').textContent = title;
    $('.dlg-text', dlg).replaceChildren(...bodyNodes);
    const box = $('.dlg-shot', dlg);
    box.replaceChildren(); box.className = 'dlg-shot';
    if (shotId) {
      const s = screens[shotId];
      const tall = shotId.startsWith('remote-') || (s && s.h > s.w);
      const scr = document.createElement('div');
      scr.className = 'screen' + (tall ? ' tall' : '');
      scr.append(shotNode(shotId));
      if (tall) {
        box.classList.add('phone-shot');
        const ph = document.createElement('div'); ph.className = 'phone';
        const fr = document.createElement('div'); fr.className = 'phone-frame';
        fr.append(scr); ph.append(fr); box.append(ph);
      } else box.append(scr);
    }
    dlg.showModal();
    $('#dlg-close').focus();
    $('.hint').classList.add('off');
  }
  dlg.addEventListener('close', () => { if (lastFocus) lastFocus.focus({ preventScroll: true }); });
  dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
  $('#dlg-close').addEventListener('click', () => dlg.close());

  $$('.tile').forEach((t) => t.addEventListener('click', () => {
    const p = document.createElement('p');
    p.innerHTML = $('.more', t).innerHTML;
    openDialog($('b', t).textContent, [p], t.dataset.shotId);
  }));
  $('#releases').addEventListener('click', (e) => {
    const b = e.target.closest('.rel');
    if (!b) return;
    const r = (data.releases || [])[+b.dataset.rel];
    if (!r) return;
    const ul = document.createElement('ul'); ul.lang = 'ru';
    r.items.forEach((t) => { const li = document.createElement('li'); li.textContent = t; ul.append(li); });
    const nodes = [ul];
    const meta = document.createElement('p'); meta.className = 'note';
    meta.textContent = [r.dateText || fmtDate(r.date), lang === 'en' ? 'Release notes are kept in Russian.' : ''].filter(Boolean).join(' · ');
    nodes.push(meta);
    openDialog(r.version ? `Proskurnin TV ${r.version}` : r.title, nodes, null);
  });

  // ── Arrow keys: spatial navigation between focusable things, like a TV launcher ──
  const SEL = '.nav, .tile, .rel';
  const visible = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden'; };
  function candidates() {
    const scope = dlg.open ? dlg : document;
    return $$(SEL, scope).filter((el) => visible(el) && (dlg.open || !dlg.contains(el)));
  }
  function move(dir) {
    const items = candidates();
    if (!items.length) return;
    const cur = items.includes(document.activeElement) ? document.activeElement : null;
    if (!cur) {
      const inView = items.find((el) => { const r = el.getBoundingClientRect(); return r.top >= 60 && r.bottom <= innerHeight; });
      (inView || items[0]).focus();
      return;
    }
    const a = cur.getBoundingClientRect();
    const ax = a.left + a.width / 2, ay = a.top + a.height / 2;
    let best = null, bestScore = Infinity;
    for (const el of items) {
      if (el === cur) continue;
      const b = el.getBoundingClientRect();
      const bx = b.left + b.width / 2, by = b.top + b.height / 2;
      const dx = bx - ax, dy = by - ay;
      let along, cross;
      if (dir === 'ArrowRight') { if (b.left < a.right - 4 || dx <= 0) continue; along = b.left - a.right; cross = Math.abs(dy); }
      else if (dir === 'ArrowLeft') { if (b.right > a.left + 4 || dx >= 0) continue; along = a.left - b.right; cross = Math.abs(dy); }
      else if (dir === 'ArrowDown') { if (b.top < a.bottom - 4 || dy <= 0) continue; along = b.top - a.bottom; cross = Math.abs(dx); }
      else { if (b.bottom > a.top + 4 || dy >= 0) continue; along = a.top - b.bottom; cross = Math.abs(dx); }
      const score = Math.max(0, along) + cross * 2;
      if (score < bestScore) { bestScore = score; best = el; }
    }
    if (best) {
      best.focus({ preventScroll: true });
      best.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
      const r = best.getBoundingClientRect();
      if (r.top < 80 || r.bottom > innerHeight - 60) best.scrollIntoView({ block: 'center', behavior: 'auto' });
    }
  }
  document.addEventListener('keydown', (e) => {
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    const tag = (document.activeElement && document.activeElement.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
      e.preventDefault();
      move(e.key);
      $('.hint').classList.add('off');
    } else if (e.key === 'Backspace' && dlg.open) {
      e.preventDefault(); dlg.close();
    }
  });

  applyLang();
  setTimeout(() => $('.hint').classList.add('off'), 12000);
})();
