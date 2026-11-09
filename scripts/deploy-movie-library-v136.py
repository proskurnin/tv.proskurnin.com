#!/usr/bin/env python3
"""Targeted movie validation update; retains keys, API routing and other services."""
import sys,json,hashlib,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'integrations/server'))
from deploy_api import remote as base_remote,put,RU,US
import deploy_api,time
def remote(host,command,body=None):
 for attempt in range(3):
  try:return base_remote(host,command,body)
  except RuntimeError as e:
   if attempt==2 or not any(t in str(e) for t in ("timed out","Connection reset","Connection closed")):raise
   time.sleep(1)
deploy_api.remote=remote
report=ROOT/'reports/movies-v136';backup='/var/backups/proskurnin-api/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-v136'
files=[(US,'/opt/proskurnin-worker','us_api_worker.py'),(US,'/opt/proskurnin-worker','movie_contract.py'),(RU,'/opt/proskurnin-api','api_relay.py'),(RU,'/opt/proskurnin-api','movie_contract.py')]
for host,folder,name in files:
 assert remote(host,'sha256sum '+folder+'/'+name).split()[0]==hashlib.sha256((report/'before'/name).read_bytes()).hexdigest(),'Source changed'
for host in (US,RU):remote(host,('sudo -n ' if host==US else '')+'install -d -m 700 '+backup)
for host,folder,name in files:remote(host,('sudo -n ' if host==US else '')+'cp -a '+folder+'/'+name+' '+backup+'/'+name)
conf=remote(RU,'cat /etc/nginx/snippets/proskurnin-api-relay.conf')+'\n'
(report/'before/nginx-api.conf').write_text(conf)
remote(RU,'cp -a /etc/nginx/snippets/proskurnin-api-relay.conf '+backup+'/nginx-api.conf')
try:
 for host,folder,name in files:
  source=ROOT/'integrations/server'/name;put(host,folder+'/'+name,source.read_text())
  assert remote(host,'sha256sum '+folder+'/'+name).split()[0]==hashlib.sha256(source.read_bytes()).hexdigest()
 for host,folder,service in [(US,'/opt/proskurnin-worker','proskurnin-us-api'),(RU,'/opt/proskurnin-api','proskurnin-api-relay')]:
  prefix='sudo -n ' if host==US else ''
  remote(host,prefix+'python3 -m compileall -q '+folder+' && '+prefix+'systemctl restart '+service+' && '+prefix+'systemctl is-active '+service)
 import re
 revised,n=re.subn(r'(location = /tv-api/v1/ai/movies \{[^}]*client_max_body_size )[^;]+;',r'\g<1>96k;',conf)
 assert n==1
 put(RU,'/etc/nginx/snippets/proskurnin-api-relay.conf',revised)
 remote(RU,'nginx -t && systemctl reload nginx')

except Exception:
 remote(RU,'cp -a '+backup+'/nginx-api.conf /etc/nginx/snippets/proskurnin-api-relay.conf; nginx -t && systemctl reload nginx')
 for host,folder,name in files:remote(host,('sudo -n ' if host==US else '')+'cp -a '+backup+'/'+name+' '+folder+'/'+name)
 remote(US,'sudo -n systemctl restart proskurnin-us-api');remote(RU,'systemctl restart proskurnin-api-relay');raise
(report/'backend-deployment.json').write_text(json.dumps({'backup':backup,'files':files,'verified':True},indent=2)+'\n')
print('Movie validation deployed; sources verified; backup:',backup)
