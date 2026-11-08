"""API-only settings. Parse data without shell evaluation; never display secrets."""
import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
API_ROUTE_DEFAULTS = {
    'OPENAI': 'us', 'YOUTUBE_DATA': 'us', 'GOOGLE_OAUTH': 'us',
    'TMDB': 'ru', 'OPEN_METEO': 'ru', 'WTTR': 'direct',
    'CBR': 'direct', 'COINBASE': 'direct',
}
SECRET_NAMES = ('OPENAI_API_KEY', 'YOUTUBE_API_KEY', 'TMDB_READ_ACCESS_TOKEN')

def read_env(path):
    result = {}
    for number, line in enumerate(Path(path).read_text(encoding='utf-8-sig').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            raise ValueError(f'Invalid assignment on line {number}; value hidden')
        key, value = line.split('=', 1)
        key, value = key.strip(), value.strip()
        if not re.fullmatch(r'[A-Z][A-Z0-9_]*', key):
            raise ValueError(f'Invalid variable name on line {number}')
        if key in result:
            raise ValueError(f'Duplicate variable on line {number}; value hidden')
        if value.startswith(('"', "'")):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError(f'Unclosed quote on line {number}')
            value = value[1:-1]
        result[key] = value
    return result

@dataclass(frozen=True)
class Settings:
    api_servers: dict
    api_routes: dict
    api_fallback_routes: dict
    weather_providers: tuple
    weather_cache_seconds: int
    secrets: dict = field(repr=False)
    oauth_file: Path = field(repr=False)

    def route_for(self, service, fallback=False):
        # All selectors apply ONLY to the named API adapter, never to an app/VPN.
        name = service.upper()
        if name not in self.api_routes:
            raise ValueError('Unknown API service')
        route = self.api_fallback_routes[name] if fallback else self.api_routes[name]
        if not route:
            return None
        if route == 'direct':
            return {'mode': 'direct', 'caller': 'tv', 'via': [], 'worker_ip': None}
        return {'mode': route, 'caller': 'backend',
                'via': [self.api_servers['ru']], 'worker_ip': self.api_servers[route]}

    def safe_status(self):
        oauth_kind = None
        if self.oauth_file.exists():
            try:
                data = json.loads(self.oauth_file.read_text())
                oauth_kind = next((k for k in ('installed', 'web') if k in data), None)
                if not oauth_kind or not all(data[oauth_kind].get(k) for k in ('client_id', 'client_secret')):
                    raise ValueError()
            except (ValueError, TypeError, KeyError):
                raise ValueError('OAuth JSON invalid; contents hidden') from None
        return {'scope': 'tv_api_only', 'api_servers': self.api_servers,
                'api_routes': self.api_routes,
                'api_fallback_routes': self.api_fallback_routes,
                'credentials_present': {key: bool(value) for key, value in self.secrets.items()},
                'oauth_json_format': oauth_kind, 'oauth_authorization_status': 'check_us_worker',
                'weather_providers': self.weather_providers,
                'weather_cache_seconds': self.weather_cache_seconds}

def load(path=ROOT / 'private/api-keys.env'):
    values = read_env(path)
    retired = {'TV_API_ENTRY_SERVER', 'OPENAI_SERVER', 'YOUTUBE_SERVER',
               'GOOGLE_OAUTH_SERVER', 'TMDB_SERVER', 'WEATHER_SERVER', 'RATES_SERVER'}
    if retired.intersection(values):
        raise ValueError('Retired ambiguous SERVER settings; use per-provider API_ROUTE')
    servers = {'ru': values.get('API_RU_RELAY_IP', '188.120.240.175'),
               'us': values.get('API_US_WORKER_IP', '40.160.252.24')}
    if servers != {'ru': '188.120.240.175', 'us': '40.160.252.24'}:
        raise ValueError('API server address has not been approved')
    routes = {service: values.get(service + '_API_ROUTE', default)
              for service, default in API_ROUTE_DEFAULTS.items()}
    if any(route not in ('direct', 'ru', 'us') for route in routes.values()):
        raise ValueError('API route must be direct, ru or us')
    fallbacks = {service: values.get(service + '_API_FALLBACK_ROUTE', 'ru' if service == 'WTTR' else 'us' if service == 'TMDB' else '')
                 for service in API_ROUTE_DEFAULTS}
    if any(route not in ('', 'direct', 'ru', 'us') for route in fallbacks.values()):
        raise ValueError('API fallback must be empty, direct, ru or us')
    if any(route and route == routes[service] for service, route in fallbacks.items()):
        raise ValueError('API fallback must differ from the primary route')
    providers = tuple(p.strip() for p in values.get('WEATHER_PROVIDERS', 'open_meteo,wttr').split(','))
    if not providers or len(set(providers)) != len(providers) or any(p not in ('open_meteo', 'wttr') for p in providers):
        raise ValueError('Invalid weather providers; allowed: open_meteo,wttr')
    try:
        interval = int(values.get('WEATHER_CACHE_SECONDS', '1800'))
    except ValueError:
        raise ValueError('Weather interval must be an integer; value hidden') from None
    if not 900 <= interval <= 21600:
        raise ValueError('Weather cache interval must be 900..21600 seconds')
    return Settings(servers, routes, fallbacks, providers, interval,
                    {key: values.get(key, '') for key in SECRET_NAMES},
                    ROOT / 'private/oauth-client.json')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=Path, default=ROOT / 'private/api-keys.env')
    args = parser.parse_args()
    try:
        print(json.dumps(load(args.env).safe_status(), ensure_ascii=False, indent=2))
    except (ValueError, OSError) as error:
        # Do not print provider responses, env contents or exception local variables.
        parser.exit(1, f'Configuration validation failed ({type(error).__name__}); no values displayed.\n')
