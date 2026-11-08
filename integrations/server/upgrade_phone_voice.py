#!/usr/bin/env python3
"""Add bounded dictation API only. Backup and restore touched files on failure."""
from deploy_api import ROOT,RU,US,remote,put
from datetime import datetime,timezone
import json

def main():
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');backup='/var/backups/proskurnin-api/phone-voice-'+stamp
 remote(RU,'install -d -m 700 '+backup+' && cp -a /opt/proskurnin-api/api_relay.py '+backup+'/ && cp -a /etc/nginx/snippets/proskurnin-api-relay.conf '+backup+'/nginx.conf')
 remote(US,'sudo -n mkdir -p '+backup+' && sudo -n cp -a /opt/proskurnin-worker/us_api_worker.py '+backup+'/')
 try:
  for host,folder,file in [(RU,'/opt/proskurnin-api','api_relay.py'),(US,'/opt/proskurnin-worker','us_api_worker.py')]:
   put(host,folder+'/transcription.py',(ROOT/'transcription.py').read_text());put(host,folder+'/'+file,(ROOT/file).read_text());remote(host,('sudo -n ' if host==US else '')+'python3 -m py_compile '+folder+'/'+file+' '+folder+'/transcription.py')
  snippet=remote(RU,'cat /etc/nginx/snippets/proskurnin-api-relay.conf')
  if 'location = /tv-api/v1/ai/transcribe ' not in snippet:
   snippet+='''\nlocation = /tv-api/v1/ai/transcribe {
    limit_req zone=proskurnin_ai burst=3 nodelay;
    limit_req_status 429;
    client_max_body_size 1m;
    limit_except POST { deny all; }
    proxy_pass http://127.0.0.1:18788;
    proxy_set_header Authorization $http_authorization;
    proxy_read_timeout 50s;
    proxy_connect_timeout 2s;
    access_log off;
}
'''
  put(RU,'/etc/nginx/snippets/proskurnin-api-relay.conf',snippet);remote(RU,'nginx -t');remote(US,'sudo -n systemctl restart proskurnin-us-api && sudo -n systemctl is-active proskurnin-us-api');remote(RU,'systemctl restart proskurnin-api-relay && systemctl reload nginx && systemctl is-active proskurnin-api-relay')
 except Exception:
  remote(US,'sudo -n cp -a '+backup+'/us_api_worker.py /opt/proskurnin-worker/us_api_worker.py && sudo -n systemctl restart proskurnin-us-api');remote(RU,'cp -a '+backup+'/api_relay.py /opt/proskurnin-api/api_relay.py && cp -a '+backup+'/nginx.conf /etc/nginx/snippets/proskurnin-api-relay.conf && nginx -t && systemctl restart proskurnin-api-relay && systemctl reload nginx');raise
 report=ROOT.parent.parent/'reports/release-v131/backend.json';report.write_text(json.dumps({'backup':backup,'scope':'API transcription only; no VPN/routes changed'},indent=2)+'\n');print('Dictation API deployed; backup:',backup)
if __name__=='__main__':main()
