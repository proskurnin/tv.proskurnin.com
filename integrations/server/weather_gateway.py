#!/usr/bin/env python3
"""Fixed weather API adapters, not an HTTP proxy. No provider keys required."""
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from device_auth import identify

URLS = {
    'open_meteo': 'https://api.open-meteo.com/v1/forecast?latitude=55.75&longitude=37.62&current=temperature_2m,weather_code,is_day,wind_speed_10m&wind_speed_unit=ms&timeformat=unixtime',
    'wttr': 'https://wttr.in/55.75,37.62?format=j1&lang=ru',
}
MAX_BODY = 262144

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def upstream(provider):
    request = urllib.request.Request(URLS[provider], headers={'User-Agent': 'ProskurninTVWeather/1.0'})
    with urllib.request.build_opener(NoRedirect).open(request, timeout=4) as response:
        body = response.read(MAX_BODY + 1)
        if response.status != 200 or len(body) > MAX_BODY:
            raise ValueError('Invalid weather response')
    data = json.loads(body)
    if provider == 'open_meteo':
        current = data['current']
        temperature = float(current['temperature_2m'])
        age = time.time() - float(current['time'])
        if not -3600 <= age <= 21600:
            raise ValueError('Old forecast')
        int(current['weather_code'])
    else:
        current = data['current_condition'][0]
        temperature = float(current['temp_C'])
        if not (current.get('lang_ru') or current.get('weatherDesc')):
            raise ValueError('Missing condition')
    if not math.isfinite(temperature) or not -90 <= temperature <= 65:
        raise ValueError('Invalid temperature')
    return data

class WeatherCache:
    def __init__(self, directory, ttl=1800, fetch=upstream, clock=time.time):
        self.directory, self.ttl, self.fetch, self.clock = Path(directory), ttl, fetch, clock
        self.directory.mkdir(parents=True, exist_ok=True)
        self.locks = {key: threading.Lock() for key in URLS}
        self.retry_after = {}

    def get(self, provider):
        if provider not in URLS:
            raise ValueError('Unknown provider')
        with self.locks[provider]:
            now = self.clock()
            path = self.directory / (provider + '.json')
            saved = None
            try:
                saved = json.loads(path.read_text())
                age = now - saved['fetched_at']
                if not 0 <= age <= 21600 or not isinstance(saved['payload'], dict):
                    saved = None
            except (OSError, ValueError, TypeError, KeyError):
                saved = None
            stale = False
            if saved is None or now - saved['fetched_at'] >= self.ttl:
                try:
                    if now < self.retry_after.get(provider, 0):
                        raise ValueError('Provider cooldown')
                    saved = {'fetched_at': self.clock(), 'payload': self.fetch(provider)}
                    tmp = path.with_suffix('.tmp')
                    tmp.write_text(json.dumps(saved))
                    os.replace(tmp, path)
                except Exception:
                    if now >= self.retry_after.get(provider, 0):
                        self.retry_after[provider] = now + 60
                    if saved is None:
                        raise ValueError('Weather unavailable') from None
                    stale = True
            result = dict(saved['payload'])
            result['_proskurnin'] = {'provider': provider, 'stale': stale,
                                    'age_seconds': max(0, int(now - saved['fetched_at']))}
            return result

class Handler(BaseHTTPRequestHandler):
    server_version = 'ProskurninWeather/1.0'

    def log_message(self, fmt, *args):
        pass  # Never log HTTP headers, arbitrary paths, or credentials.

    def reply(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        auth = self.headers.get('Authorization', '')
        supplied = auth[7:] if auth.startswith('Bearer ') else ''
        device_id = identify(supplied, self.server.token_hash, getattr(self.server, 'device_hashes', {}))
        if device_id is None:
            self.reply(401, {'error': 'unauthorized'})
            return
        routes = {'/tv-api/v1/weather/' + provider: provider for provider in URLS}
        provider = routes.get(self.path)
        if provider is None:
            self.reply(404, {'error': 'unknown_api'})
            return
        started = time.monotonic()
        try:
            data = self.server.cache.get(provider)
            self.reply(200, data)
            status = 200
        except Exception:
            self.reply(503, {'error': 'weather_unavailable'})
            status = 503
        print(json.dumps({'device_id': device_id, 'api': 'weather.' + provider,
                          'status': status, 'ms': round((time.monotonic() - started) * 1000)}), flush=True)

def main():
    config = json.loads(Path('/etc/proskurnin-api/weather.json').read_text())
    server = ThreadingHTTPServer(('127.0.0.1', 18787), Handler)
    server.token_hash = config['device_token_sha256']
    server.device_hashes = config.get('device_token_hashes', {})
    server.cache = WeatherCache('/var/lib/proskurnin-api/weather', config['cache_seconds'])
    server.serve_forever()

if __name__ == '__main__':
    main()
