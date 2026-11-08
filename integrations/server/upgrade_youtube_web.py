#!/usr/bin/env python3
"""Update only the existing US API worker, preserving credentials and routes."""
import argparse,json
from datetime import datetime,timezone
from deploy_api import remote,put,US,ROOT

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
 if not args.apply:print('Use --apply after tests.');return
 backup='/var/backups/proskurnin-youtube-web/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 remote(US,'sudo -n install -d -m 700 '+backup)
 remote(US,'sudo -n cp -a /opt/proskurnin-worker/us_api_worker.py '+backup+'/us_api_worker.py')
 try:
  put(US,'/opt/proskurnin-worker/transcription.py',(ROOT/'transcription.py').read_text());put(US,'/opt/proskurnin-worker/us_api_worker.py',(ROOT/'us_api_worker.py').read_text())
  remote(US,'sudo -n python3 -m py_compile /opt/proskurnin-worker/us_api_worker.py && sudo -n systemctl restart proskurnin-us-api && sudo -n systemctl is-active proskurnin-us-api')
 except Exception:
  remote(US,'sudo -n cp -a '+backup+'/us_api_worker.py /opt/proskurnin-worker/us_api_worker.py && sudo -n systemctl restart proskurnin-us-api');raise
 report=ROOT.parent.parent/'reports/youtube-web-v124/backend-deployment.json'
 report.write_text(json.dumps({'backup':backup,'changed':'US API worker only','keys_changed':False,'vpn_changed':False},indent=2)+'\n');print('Updated worker; backup:',backup)
if __name__=='__main__':main()
