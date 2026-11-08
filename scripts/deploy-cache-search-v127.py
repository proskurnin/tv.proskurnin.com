#!/usr/bin/env python3
"""Targeted API update: optional web search and authenticated local video files."""
import sys,json,shlex,hashlib,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'integrations/server'))
from deploy_api import remote,put,RU,US
report=ROOT/'reports/apps-cache-search-v127';stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');backup='/var/backups/proskurnin-api/'+stamp+'-v127'
files=[(US,'/opt/proskurnin-worker','us_api_worker.py'),(US,'/opt/proskurnin-worker','chat_contract.py'),(RU,'/opt/proskurnin-api','chat_contract.py'),(RU,'/opt/proskurnin-api','api_relay.py')]
for host,folder,name in files:
 expected=hashlib.sha256((report/'before'/name).read_bytes()).hexdigest();actual=remote(host,'sha256sum '+folder+'/'+name).split()[0]
 if expected!=actual:raise RuntimeError('Remote source changed: '+name)
for host in [RU,US]:remote(host,('sudo -n ' if host==US else '')+'install -d -m 700 '+backup)
for host,folder,name in files:remote(host,('sudo -n ' if host==US else '')+'cp -a '+folder+'/'+name+' '+backup+'/'+name)
remote(RU,'cp -a /etc/nginx/snippets/proskurnin-api-relay.conf '+backup+'/nginx-api.conf; install -d -m 755 /opt/proskurnin-api/dream-media')
clips=ROOT/'downloads/dream-clips-v1';catalog=json.loads((clips/'catalog.json').read_text());assert len(catalog['clips'])>=6
for x in catalog['clips']:
 assert x['bytes']<40000000
 subprocess.run(['scp','-q',str(clips/(x['id']+'.mp4')),RU+':/opt/proskurnin-api/dream-media/'],check=True)
 actual=remote(RU,'sha256sum /opt/proskurnin-api/dream-media/'+x['id']+'.mp4').split()[0]
 assert actual==x['sha256']
put(RU,'/opt/proskurnin-api/dream-media/catalog.json',(clips/'catalog.json').read_text())
try:
 for host,folder,name in files:put(host,folder+'/'+name,(ROOT/'integrations/server'/name).read_text())
 put(RU,'/opt/proskurnin-api/dream_media.py',(ROOT/'integrations/server/dream_media.py').read_text())
 conf=(report/'before/nginx-api.conf').read_text();assert 'location ^~ /tv-api/v1/dream/' not in conf
 conf+='''\nlocation ^~ /tv-api/v1/dream/ {
    limit_except GET { deny all; }
    proxy_pass http://127.0.0.1:18788;
    proxy_set_header Authorization $http_authorization;
    proxy_buffering off;
    proxy_read_timeout 30s;
    proxy_connect_timeout 2s;
    access_log off;
}
'''
 put(RU,'/etc/nginx/snippets/proskurnin-api-relay.conf',conf)
 remote(US,'sudo -n python3 -m py_compile /opt/proskurnin-worker/us_api_worker.py /opt/proskurnin-worker/chat_contract.py; sudo -n systemctl restart proskurnin-us-api; sudo -n systemctl is-active proskurnin-us-api')
 remote(RU,'python3 -m py_compile /opt/proskurnin-api/api_relay.py /opt/proskurnin-api/chat_contract.py /opt/proskurnin-api/dream_media.py; nginx -t && systemctl restart proskurnin-api-relay && systemctl reload nginx && systemctl is-active proskurnin-api-relay')
except Exception:
 for host,folder,name in files:remote(host,('sudo -n ' if host==US else '')+'cp -a '+backup+'/'+name+' '+folder+'/'+name)
 remote(RU,'cp -a '+backup+'/nginx-api.conf /etc/nginx/snippets/proskurnin-api-relay.conf; nginx -t && systemctl restart proskurnin-api-relay && systemctl reload nginx')
 remote(US,'sudo -n systemctl restart proskurnin-us-api');raise
(report/'backend-deployment.json').write_text(json.dumps({'backup':backup,'clips':len(catalog['clips']),'endpoints':['ai/chat','dream/catalog','dream/clip/<id>.mp4']},indent=2));print('Updated API and verified',len(catalog['clips']),'clips; backup:',backup)
