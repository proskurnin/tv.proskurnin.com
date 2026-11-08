#!/usr/bin/env python3
import sys,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'integrations/server'))
from deploy_api import remote,put,RU
r=ROOT/'reports/layout-speed-v128';folder='/opt/proskurnin-api';conf='/etc/nginx/snippets/proskurnin-api-relay.conf'
expected=hashlib.sha256((r/'before/api_relay.py').read_bytes()).hexdigest()
assert remote(RU,'sha256sum '+folder+'/api_relay.py').split()[0]==expected,'Remote code changed'
oldconf=remote(RU,'cat '+conf)+'\n';(r/'before/nginx-api.conf').write_text(oldconf)
assert 'location = /tv-api/v1/network/speed' not in oldconf
backup='/var/backups/proskurnin-api/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-v128'
remote(RU,'install -d -m 700 '+backup+'; cp -a '+folder+'/api_relay.py '+backup+'/api_relay.py; cp -a '+conf+' '+backup+'/nginx-api.conf')
try:
 for name in ['speed_probe.py','api_relay.py']:put(RU,folder+'/'+name,(ROOT/'integrations/server'/name).read_text())
 put(RU,conf,oldconf+'\n'+(r/'speed-nginx.conf').read_text())
 remote(RU,'python3 -m py_compile '+folder+'/api_relay.py '+folder+'/speed_probe.py && nginx -t && systemctl restart proskurnin-api-relay && systemctl reload nginx && systemctl is-active proskurnin-api-relay')
except Exception:
 remote(RU,'cp -a '+backup+'/api_relay.py '+folder+'/api_relay.py; cp -a '+backup+'/nginx-api.conf '+conf+'; nginx -t && systemctl restart proskurnin-api-relay && systemctl reload nginx');raise
(r/'server-deployment.json').write_text(json.dumps(dict(backup=backup,node='188.120.240.175',limit_bytes=16*1024*1024),indent=2));print('RU speed endpoint deployed; backup:',backup)
