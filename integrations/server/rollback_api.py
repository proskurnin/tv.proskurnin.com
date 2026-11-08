#!/usr/bin/env python3
"""Disable only the new movie/YouTube API services; preserve weather and all VPN services."""
import argparse,shlex
from deploy_api import remote,RU,US
PLAN='''Stops US proskurnin-us-api + proskurnin-api-tunnel and RU proskurnin-api-relay.
Removes only the proskurnin-api-relay nginx include; validates nginx before reload.
Disables the dedicated tv-api-relay SSH authorization. Keeps configs, keys and caches
for recovery. Does not revoke Google OAuth or provider keys at their providers.
Weather API, nginx other sites, VPN/Happ and launcher Home are not changed.'''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
 if not a.apply:print(PLAN+'\nRun with --apply to execute.');return
 remote(US,'sudo -n systemctl disable --now proskurnin-api-tunnel.service proskurnin-us-api.service')
 code="""from pathlib import Path
import subprocess,time
p=Path('/etc/nginx/sites-available/ru01-placeholder.conf');s=p.read_text()
b=Path('/var/backups/proskurnin-api/rollback-'+str(int(time.time())));b.mkdir(parents=True,mode=0o700);(b/'nginx.conf').write_text(s)
p.write_text(s.replace('    include /etc/nginx/snippets/proskurnin-api-relay.conf;',''))
if subprocess.run(['nginx','-t'],capture_output=True).returncode:
 p.write_text(s);raise SystemExit('nginx validation failed; original config restored')
subprocess.run(['systemctl','reload','nginx'],check=True)
k=Path('/etc/proskurnin-api/relay_authorized_keys')
if k.exists():(b/'relay_authorized_keys').write_bytes(k.read_bytes());k.write_text('')
subprocess.run(['systemctl','disable','--now','proskurnin-api-relay.service'],check=True)
print('Scoped API services disabled; weather retained.')
"""
 print(remote(RU,'python3 -c '+shlex.quote(code)))
if __name__=='__main__':main()
