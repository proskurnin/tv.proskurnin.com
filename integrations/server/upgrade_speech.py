#!/usr/bin/env python3
"""Deploy only the speech API extension; never touch keys, OAuth, VPN or SSH tunnel."""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from deploy_api import remote,put,RU,US,ROOT

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
 if not args.apply:print('Use --apply to deploy the prepared, tested speech endpoint.');return
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');backup='/var/backups/proskurnin-speech/'+stamp
 for host,directory,filename in [(US,'/opt/proskurnin-worker','us_api_worker.py'),(RU,'/opt/proskurnin-api','api_relay.py')]:
  prefix='sudo -n ' if host==US else ''
  remote(host,prefix+'install -d -m 700 '+backup)
  remote(host,prefix+'cp -a '+directory+'/'+filename+' '+backup+'/'+filename)
 remote(RU,'cp -a /etc/nginx/snippets/proskurnin-api-relay.conf '+backup+'/nginx-snippet.conf')
 def rollback():
  remote(US,'sudo -n cp -a '+backup+'/us_api_worker.py /opt/proskurnin-worker/us_api_worker.py && sudo -n systemctl restart proskurnin-us-api')
  remote(RU,'cp -a '+backup+'/api_relay.py /opt/proskurnin-api/api_relay.py && cp -a '+backup+'/nginx-snippet.conf /etc/nginx/snippets/proskurnin-api-relay.conf && nginx -t && systemctl restart proskurnin-api-relay && systemctl reload nginx')
 try:
  for host,directory,filename in [(US,'/opt/proskurnin-worker','us_api_worker.py'),(RU,'/opt/proskurnin-api','api_relay.py')]:
   put(host,directory+'/transcription.py',(ROOT/'transcription.py').read_text());put(host,directory+'/chat_contract.py',(ROOT/'chat_contract.py').read_text());put(host,directory+'/'+filename,(ROOT/filename).read_text())
   remote(host,('sudo -n ' if host==US else '')+'python3 -m py_compile '+directory+'/'+filename+' '+directory+'/chat_contract.py')
  snippet=remote(RU,'cat /etc/nginx/snippets/proskurnin-api-relay.conf')
  if 'location = /tv-api/v1/ai/speech ' not in snippet:
   snippet+='''
location = /tv-api/v1/ai/speech {
    limit_req zone=proskurnin_ai burst=3 nodelay;
    limit_req_status 429;
    client_max_body_size 32k;
    limit_except POST { deny all; }
    proxy_pass http://127.0.0.1:18788;
    proxy_set_header Authorization $http_authorization;
    proxy_read_timeout 50s;
    proxy_connect_timeout 2s;
    access_log off;
}
'''
  put(RU,'/etc/nginx/snippets/proskurnin-api-relay.conf',snippet)
  remote(RU,'nginx -t')
  remote(US,'sudo -n systemctl restart proskurnin-us-api && sudo -n systemctl is-active proskurnin-us-api')
  remote(RU,'systemctl restart proskurnin-api-relay && systemctl reload nginx && systemctl is-active proskurnin-api-relay')
 except Exception:
  rollback();raise
 report=ROOT.parent.parent/'reports/layout-speech-v123/backend-deployment.json';report.write_text(json.dumps({'backup':backup,'endpoint':'/tv-api/v1/ai/speech','keys_changed':False,'vpn_changed':False,'scope':'speech API extension only'},indent=2)+'\n');print('Speech endpoint deployed. Backup:',backup)
if __name__=='__main__':main()
