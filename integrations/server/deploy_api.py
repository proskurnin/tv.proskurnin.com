#!/usr/bin/env python3
"""Install API-only RU relay and US worker; no VPN or default route changes."""
import hashlib,json,os,secrets,shlex,subprocess
from pathlib import Path
from datetime import datetime,timezone
from settings import ROOT,load

RU='root@188.120.240.175';US='ubuntu@40.160.252.24'
def remote(host,command,body=None):
    args=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10']
    if host==US:args+=['-o','ProxyJump='+RU]
    r=subprocess.run(args+[host,command],input=body,text=True,capture_output=True,timeout=60)
    if r.returncode:raise RuntimeError('Remote command failed on '+host+': '+r.stderr[-800:])
    return r.stdout.strip()
def put(host,path,content,mode=0o644):
    code="import os,sys\np="+repr(path)+"\nt=p+'.new'\nfd=os.open(t,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,"+str(mode)+")\nwith os.fdopen(fd,'w') as f:f.write(sys.stdin.read())\nos.chmod(t,"+str(mode)+")\nos.replace(t,p)"
    remote(host,('sudo -n ' if host==US else '')+'python3 -c '+shlex.quote(code),content)
def secret(name):
    p=ROOT/'private'/name
    if p.is_symlink():raise ValueError('Refusing symlink')
    if not p.exists():
        fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as f:f.write(secrets.token_urlsafe(32))
    return p.read_text().strip()
def private_json(path,data):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as f:json.dump(data,f)
def main():
    settings=load()
    if any(settings.api_routes[k]!='us' for k in ('OPENAI','YOUTUBE_DATA')):raise ValueError('This deploy requires US routes for OpenAI and YouTube Data API')
    device=secret('api-device-token');relay=secret('api-relay-token')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');backup='/var/backups/proskurnin-api/'+stamp
    remote(RU,'install -d -m 700 '+backup+'; cp -a /etc/nginx/sites-available/ru01-placeholder.conf '+backup+'/nginx.conf; getent passwd tv-api-relay >/dev/null || useradd --system --no-create-home --shell /usr/sbin/nologin tv-api-relay')
    remote(US,"sudo -n sh -eu -c 'getent passwd tv-api-worker >/dev/null || useradd --system --create-home --home-dir /var/lib/proskurnin-worker --shell /usr/sbin/nologin tv-api-worker; chmod 700 /var/lib/proskurnin-worker; install -d -m 755 /etc/proskurnin-worker /opt/proskurnin-worker; if test ! -f /var/lib/proskurnin-worker/id_ed25519; then runuser -u tv-api-worker -- ssh-keygen -q -t ed25519 -N \"\" -C proskurnin-api-only -f /var/lib/proskurnin-worker/id_ed25519; fi'")
    pub=remote(US,'sudo -n cat /var/lib/proskurnin-worker/id_ed25519.pub');assert pub.startswith('ssh-ed25519 ')
    hostkey=remote(RU,'cat /etc/ssh/ssh_host_ed25519_key.pub').split()
    put(US,'/var/lib/proskurnin-worker/known_hosts','188.120.240.175 '+' '.join(hostkey[:2])+'\n')
    put(RU,'/etc/proskurnin-api/relay_authorized_keys','restrict,port-forwarding,permitlisten="127.0.0.1:18888" '+pub+'\n')
    put(RU,'/etc/ssh/sshd_config.d/71-proskurnin-api-relay.conf','''Match User tv-api-relay
    AuthorizedKeysFile /etc/proskurnin-api/relay_authorized_keys
    AuthenticationMethods publickey
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    AllowTcpForwarding remote
    PermitListen 127.0.0.1:18888
    AllowStreamLocalForwarding no
    GatewayPorts no
    X11Forwarding no
    AllowAgentForwarding no
    PermitTTY no
    MaxSessions 0
Match all
''')
    remote(RU,'/usr/sbin/sshd -t && systemctl reload ssh')
    put(US,'/opt/proskurnin-worker/tmdb_proxy.py',(ROOT/'tmdb_proxy.py').read_text())
    put(US,'/opt/proskurnin-worker/transcription.py',(ROOT/'transcription.py').read_text())
    put(US,'/opt/proskurnin-worker/chat_contract.py',(ROOT/'chat_contract.py').read_text())
    put(US,'/opt/proskurnin-worker/us_api_worker.py',(ROOT/'us_api_worker.py').read_text())
    put(US,'/etc/proskurnin-worker/api.json',json.dumps({'openai_api_key':settings.secrets['OPENAI_API_KEY'],'youtube_api_key':settings.secrets['YOUTUBE_API_KEY'],
        'tmdb_credential':settings.secrets['TMDB_READ_ACCESS_TOKEN'],'model':'gpt-4.1-mini','relay_auth_sha256':hashlib.sha256(('Bearer '+relay).encode()).hexdigest()}),0o640)
    remote(US,'sudo -n chown root:tv-api-worker /etc/proskurnin-worker/api.json')
    put(US,'/etc/systemd/system/proskurnin-us-api.service','''[Unit]
Description=Proskurnin YouTube and AI API worker
After=network-online.target
[Service]
User=tv-api-worker
Group=tv-api-worker
ExecStart=/usr/bin/python3 /opt/proskurnin-worker/us_api_worker.py
Restart=on-failure
NoNewPrivileges=yes
PrivateTmp=yes
ProtectHome=yes
ProtectSystem=strict
ReadWritePaths=/var/lib/proskurnin-worker
MemoryMax=160M
TasksMax=32
UMask=0077
[Install]
WantedBy=multi-user.target
''')
    put(US,'/etc/systemd/system/proskurnin-api-tunnel.service','''[Unit]
Description=Proskurnin API-only reverse tunnel (fixed worker port)
After=network-online.target proskurnin-us-api.service
Wants=network-online.target
StartLimitIntervalSec=0
[Service]
User=tv-api-worker
Group=tv-api-worker
ExecStart=/usr/bin/ssh -4 -F /dev/null -N -T -o BatchMode=yes -o IdentitiesOnly=yes -o ExitOnForwardFailure=yes -o ConnectTimeout=15 -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/var/lib/proskurnin-worker/known_hosts -i /var/lib/proskurnin-worker/id_ed25519 -R 127.0.0.1:18888:127.0.0.1:18889 tv-api-relay@188.120.240.175
Restart=always
RestartSec=5
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
MemoryMax=96M
[Install]
WantedBy=multi-user.target
''')
    remote(US,'sudo -n systemctl daemon-reload && sudo -n systemctl enable proskurnin-us-api proskurnin-api-tunnel && sudo -n systemctl restart proskurnin-us-api proskurnin-api-tunnel')
    put(RU,'/opt/proskurnin-api/tmdb_proxy.py',(ROOT/'tmdb_proxy.py').read_text())
    put(RU,'/opt/proskurnin-api/transcription.py',(ROOT/'transcription.py').read_text())
    put(RU,'/opt/proskurnin-api/chat_contract.py',(ROOT/'chat_contract.py').read_text())
    put(RU,'/opt/proskurnin-api/speed_probe.py',(ROOT/'speed_probe.py').read_text())
    put(RU,'/opt/proskurnin-api/dream_media.py',(ROOT/'dream_media.py').read_text())
    put(RU,'/opt/proskurnin-api/api_relay.py',(ROOT/'api_relay.py').read_text())
    put(RU,'/etc/proskurnin-api/relay.json',json.dumps({'device_auth_sha256':hashlib.sha256(('Bearer '+device).encode()).hexdigest(),'relay_authorization':'Bearer '+relay,'tmdb_credential':settings.secrets['TMDB_READ_ACCESS_TOKEN']}),0o640)
    remote(RU,'chown root:tv-api /etc/proskurnin-api/relay.json')
    put(RU,'/etc/systemd/system/proskurnin-api-relay.service','''[Unit]
Description=Proskurnin allowlisted API relay
After=network-online.target
[Service]
User=tv-api
Group=tv-api
ExecStart=/usr/bin/python3 /opt/proskurnin-api/api_relay.py
Restart=on-failure
NoNewPrivileges=yes
PrivateTmp=yes
ProtectHome=yes
ProtectSystem=strict
MemoryMax=96M
TasksMax=32
[Install]
WantedBy=multi-user.target
''')
    put(RU,'/etc/nginx/conf.d/proskurnin-api-limits.conf','limit_req_zone $binary_remote_addr zone=proskurnin_yt:1m rate=30r/m;\nlimit_req_zone $binary_remote_addr zone=proskurnin_ai:1m rate=6r/m;\nlimit_req_zone $binary_remote_addr zone=proskurnin_tmdb:1m rate=120r/m;\n')
    snippet=''
    for path,zone in [('youtube/channel','proskurnin_yt'),('ai/movies','proskurnin_ai'),('ai/chat','proskurnin_ai'),('ai/speech','proskurnin_ai'),('ai/transcribe','proskurnin_ai')]:
        snippet+='''location = /tv-api/v1/'''+path+''' {
    limit_req zone='''+zone+''' burst=3 nodelay;
    limit_req_status 429;
    client_max_body_size '''+('1m' if path=='ai/transcribe' else '32k')+''';
    proxy_pass http://127.0.0.1:18788;
    proxy_set_header Authorization $http_authorization;
    proxy_read_timeout 50s;
    proxy_connect_timeout 2s;
    access_log off;
}
'''
    snippet+='location ^~ /tv-api/v1/tmdb/ {\n    limit_req zone=proskurnin_tmdb burst=20 nodelay;\n    limit_req_status 429;\n    client_max_body_size 1k;\n    limit_except GET { deny all; }\n    proxy_pass http://127.0.0.1:18788;\n    proxy_set_header Authorization $http_authorization;\n    proxy_read_timeout 20s;\n    proxy_connect_timeout 2s;\n    access_log off;\n}\n'
    snippet+='location ^~ /tv-api/v1/dream/ {\n    limit_except GET { deny all; }\n    proxy_pass http://127.0.0.1:18788;\n    proxy_set_header Authorization $http_authorization;\n    proxy_buffering off;\n    proxy_read_timeout 30s;\n    proxy_connect_timeout 2s;\n    access_log off;\n}\n'
    snippet+='location = /tv-api/v1/network/speed {\n    limit_except GET { deny all; }\n    proxy_pass http://127.0.0.1:18788;\n    proxy_set_header Authorization $http_authorization;\n    proxy_buffering off;\n    gzip off;\n    proxy_read_timeout 12s;\n    proxy_connect_timeout 2s;\n    access_log off;\n}\n'
    put(RU,'/etc/nginx/snippets/proskurnin-api-relay.conf',snippet)
    remote(RU,'python3 -',"from pathlib import Path\np=Path('/etc/nginx/sites-available/ru01-placeholder.conf')\ns=p.read_text()\nneedle='    ssl_protocols TLSv1.2 TLSv1.3;'\nline='    include /etc/nginx/snippets/proskurnin-api-relay.conf;'\nassert s.count(needle)==1\nif line not in s:p.write_text(s.replace(needle,needle+'\\n'+line))\n")
    try:
        remote(RU,'nginx -t && systemctl daemon-reload && systemctl enable proskurnin-api-relay && systemctl restart proskurnin-api-relay && systemctl reload nginx')
    except Exception:
        remote(RU,'cp -a '+backup+'/nginx.conf /etc/nginx/sites-available/ru01-placeholder.conf; nginx -t && systemctl reload nginx; systemctl stop proskurnin-api-relay')
        raise
    private_json(ROOT/'private/api-client.json',{'base_url':'https://ru01.firstvds.proskurn.in/tv-api/v1/','token':device})
    # TMDB metadata/posters use approved RU with US fallback; provider key stays on servers.
    private_json(ROOT/'private/tmdb-client.json',{'route':'ru','fallback':'us'})
    report=ROOT.parent.parent/'reports/api-integration-v1';report.mkdir(exist_ok=True)
    (report/'deployment.json').write_text(json.dumps({'backup_ru':backup,'ru_relay':'188.120.240.175','us_worker':'40.160.252.24',
        'ports':{'ru_relay_loopback':18788,'ru_tunnel_loopback':18888,'us_worker_loopback':18889},
        'scope':['youtube_data_api','openai_api','tmdb_metadata_and_posters'],'vpn_changed':False,'openai_youtube_keys_only_on_us':True},indent=2)+'\n')
    print('API-only relay and worker deployed; private TV configuration generated. No VPN changes.')

if __name__=='__main__':main()
