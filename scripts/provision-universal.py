#!/usr/bin/env python3
"""Explicit root-free import; never installs, starts apps or changes system settings."""
import argparse,base64,json,os,re,shlex,stat,subprocess
from pathlib import Path
from urllib.parse import urlsplit

def private_file(path,limit):
    path=Path(path)
    st=path.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or st.st_mode&0o077 or st.st_size>limit:
        raise ValueError('Expected an owned private regular file (chmod 600) within size limit')
    return path.read_bytes()

def validate(value):
    if set(value)!={'version','base_url','api_token','weather_token'} or type(value['version']) is not int or value['version']!=1:
        raise ValueError('Invalid configuration structure')
    u=urlsplit(value['base_url'])
    if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment or u.path!='/tv-api/v1/' or (u.port is not None and not 0<u.port<65536):
        raise ValueError('Expected HTTPS base URL ending /tv-api/v1/')
    for key in ('api_token','weather_token'):
        if not isinstance(value[key],str) or not re.fullmatch('[A-Za-z0-9_-]{32,128}',value[key]):raise ValueError('Invalid device token')
    if value['api_token']==value['weather_token']:raise ValueError('Use distinct API and weather tokens')
    return value

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--device',required=True);p.add_argument('--adb',default='adb');p.add_argument('--config',required=True,type=Path);p.add_argument('--remote',action='store_true');p.add_argument('--remote-tls',type=Path);args=p.parse_args()
    value=validate(json.loads(private_file(args.config,1024)))
    prefix=[args.adb,'-s',args.device]
    state=subprocess.run(prefix+['get-state'],capture_output=True,text=True,timeout=15)
    if state.returncode or state.stdout.strip()!='device':raise RuntimeError('ADB not ready; stop, do not bypass authorization')
    if args.remote:
        data={'api-client.json':json.dumps({'base_url':value['base_url'],'token':value['api_token']}).encode()}
        if args.remote_tls:
            for name in ['remote.p12','tls-password','ca.cer','remote-ca.mobileconfig']:data[name]=private_file(args.remote_tls/name,16384)
        payload={'version':1,'files':{k:base64.b64encode(v).decode() for k,v in data.items()}};authority='local.proskurnin.remote.configuration'
    else:
        if args.remote_tls:raise ValueError('--remote-tls requires --remote')
        payload=value;authority='local.proskurnin.preview.configuration'
    # Sensitive payload through stdin only, never subprocess argv, shell history or logs.
    command='content call --uri content://'+authority+' --method configure --extra '+shlex.quote('payload:s:'+json.dumps(payload,separators=(',',':')))+'\n'
    result=subprocess.run(prefix+['shell','sh'],input=command,capture_output=True,text=True,timeout=30)
    if result.returncode or 'configured=true' not in result.stdout or 'Exception' in result.stdout:raise RuntimeError('Import not confirmed; no retry or root fallback. Device may need updated APK.')
    print('Configuration imported into application private storage. No system settings changed.')
if __name__=='__main__':
    try:main()
    except Exception as exc:raise SystemExit(type(exc).__name__+': setup failed; inspect arguments, permissions and device connection (secret contents suppressed)')
