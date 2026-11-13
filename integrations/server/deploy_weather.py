#!/usr/bin/env python3
"""Deploy ONLY weather API to RU. Never transmit the file containing provider keys."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import shlex
import subprocess
from datetime import datetime, timezone
from settings import ROOT, load

RU = 'root@188.120.240.175'
STAMP = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

def remote(command, text=None):
    r = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', RU, command],
                       input=text, text=True, capture_output=True, timeout=60)
    if r.returncode:
        raise RuntimeError('Remote operation failed: ' + r.stderr[-1500:])
    return r.stdout.strip()

def put(path, content, mode=0o644):
    # Content enters SSH stdin, not a command argument or tool output.
    command = 'umask 077; cat > ' + shlex.quote(path) + '; chmod ' + oct(mode)[2:] + ' ' + shlex.quote(path)
    remote(command, content)

def main():
    s = load()
    for provider in ('OPEN_METEO', 'WTTR'):
        if s.api_routes[provider] not in ('direct', 'ru') or s.api_fallback_routes[provider] not in ('', 'direct', 'ru'):
            raise ValueError('US weather worker not implemented; refusing to silently use RU')
    token_file = ROOT / 'private/weather-device-token'
    if token_file.is_symlink():
        raise ValueError('Refusing symlink')
    if not token_file.exists():
        fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(secrets.token_urlsafe(32))
    token = token_file.read_text().strip()
    assert len(token) >= 32
    config = {'base_url': 'https://ru01.firstvds.proskurn.in/tv-api/v1/weather/',
              'token': token, 'providers': list(s.weather_providers),
              'routes': {p: s.api_routes[{'open_meteo':'OPEN_METEO','wttr':'WTTR'}[p]] for p in s.weather_providers},
              'fallback_routes': {p: s.api_fallback_routes[{'open_meteo':'OPEN_METEO','wttr':'WTTR'}[p]] for p in s.weather_providers}}
    target = ROOT / 'private/weather-routing.json'
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f: json.dump(config, f)
    backup = '/var/backups/proskurnin-api/' + STAMP
    remote('install -d -m 700 ' + backup + '; cp -a /etc/nginx/sites-available/ru01-placeholder.conf ' + backup + '/nginx.conf; getent passwd tv-api >/dev/null || useradd --system --no-create-home --shell /usr/sbin/nologin tv-api')
    remote('install -d -m 755 /opt/proskurnin-api /etc/proskurnin-api; install -d -m 700 -o tv-api -g tv-api /var/lib/proskurnin-api')
    put('/opt/proskurnin-api/device_auth.py', (ROOT / 'device_auth.py').read_text())
    put('/opt/proskurnin-api/weather_gateway.py', (ROOT / 'weather_gateway.py').read_text())
    extra_devices=json.loads(remote("python3 -c 'import json,pathlib;p=pathlib.Path(\"/etc/proskurnin-api/weather.json\");print(json.dumps(json.loads(p.read_text()).get(\"device_token_hashes\",{}) if p.exists() else {}))'"))
    put('/etc/proskurnin-api/weather.json', json.dumps({'device_token_hashes':extra_devices,'device_token_sha256': hashlib.sha256(token.encode()).hexdigest(),
                                                      'cache_seconds': s.weather_cache_seconds}), 0o640)
    remote('chown root:tv-api /etc/proskurnin-api/weather.json')
    put('/etc/systemd/system/proskurnin-weather-api.service', '''[Unit]
Description=Proskurnin TV weather API only
After=network-online.target
Wants=network-online.target
[Service]
User=tv-api
Group=tv-api
ExecStart=/usr/bin/python3 /opt/proskurnin-api/weather_gateway.py
Restart=on-failure
RestartSec=3
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/lib/proskurnin-api
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
MemoryMax=96M
TasksMax=32
UMask=0077
[Install]
WantedBy=multi-user.target
''')
    put('/etc/nginx/conf.d/proskurnin-weather-limits.conf', 'limit_req_zone $binary_remote_addr zone=proskurnin_weather:1m rate=30r/m;\n')
    put('/etc/nginx/snippets/proskurnin-weather-api.conf', '''location ^~ /tv-api/v1/weather/ {
    limit_req zone=proskurnin_weather burst=10 nodelay;
    limit_req_status 429;
    proxy_pass http://127.0.0.1:18787;
    proxy_set_header Host $host;
    proxy_set_header Authorization $http_authorization;
    proxy_read_timeout 12s;
    proxy_connect_timeout 2s;
    access_log off;
}
''')
    remote('python3 -', "from pathlib import Path\np=Path('/etc/nginx/sites-available/ru01-placeholder.conf')\ns=p.read_text()\nneedle='    ssl_protocols TLSv1.2 TLSv1.3;'\nline='    include /etc/nginx/snippets/proskurnin-weather-api.conf;'\nassert s.count(needle)==1\nif line not in s: p.write_text(s.replace(needle,needle+'\\n'+line))\n")
    try:
        remote('nginx -t && systemctl daemon-reload && systemctl enable proskurnin-weather-api && systemctl restart proskurnin-weather-api && systemctl reload nginx')
        remote('sleep 1; systemctl is-active --quiet proskurnin-weather-api')
    except Exception:
        remote('cp -a ' + backup + '/nginx.conf /etc/nginx/sites-available/ru01-placeholder.conf; nginx -t && systemctl reload nginx; systemctl stop proskurnin-weather-api')
        raise
    report = ROOT.parent.parent / 'reports/weather-api-v1'
    report.mkdir(exist_ok=True)
    (report / 'deployment.json').write_text(json.dumps({'ru': RU, 'backup': backup,
        'routes': config['routes'], 'fallback_routes': config['fallback_routes'],
        'only_weather_device_token_used': True, 'provider_keys_uploaded': False}, indent=2) + '\n')
    print('Weather API deployed; client config prepared privately; no provider API keys uploaded.')

if __name__ == '__main__': main()
