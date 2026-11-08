#!/usr/bin/env python3
"""Disable only the weather API service and its nginx location."""
import argparse
from deploy_weather import remote

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--apply', action='store_true')
    if not p.parse_args().apply:
        print('First disable Server weather in launcher settings. --apply then disables only the RU weather API, leaving other server services untouched.')
        return
    remote('python3 -', "from pathlib import Path\np=Path('/etc/nginx/sites-available/ru01-placeholder.conf')\ns=p.read_text()\np.write_text(s.replace('    include /etc/nginx/snippets/proskurnin-weather-api.conf;\\n',''))\n")
    remote('nginx -t && systemctl reload nginx && systemctl disable --now proskurnin-weather-api')
    print('Weather API disabled. Provider keys, other APIs, VPN and TV Home not changed.')

if __name__ == '__main__': main()
