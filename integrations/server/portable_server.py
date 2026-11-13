#!/usr/bin/env python3
"""Portable loopback-only backend. No SSH, remote deployment or system changes."""
import argparse,hashlib,json,os,secrets,signal,threading
from pathlib import Path
from http.server import ThreadingHTTPServer
import api_relay,us_api_worker,weather_gateway,dream_media
from tmdb_proxy import Tmdb

def digest(value):return hashlib.sha256(value.encode()).hexdigest()
def save(path,value):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as out:json.dump(value,out,ensure_ascii=False,indent=2)

def initialize(directory,base):
    from urllib.parse import urlsplit
    u=urlsplit(base)
    if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment or u.path!='/tv-api/v1/':raise ValueError('Invalid HTTPS base')
    directory.mkdir(parents=True,mode=0o700,exist_ok=False)
    api,weather,relay=(secrets.token_urlsafe(32) for _ in range(3))
    save(directory/'device.json',{'version':1,'base_url':base,'api_token':api,'weather_token':weather})
    save(directory/'relay.json',{'device_auth_sha256':digest(secrets.token_urlsafe(32)),'device_auth_hashes':{'tv-primary':digest('Bearer '+api)},'relay_authorization':'Bearer '+relay,'tmdb_credential':''})
    save(directory/'weather.json',{'device_token_sha256':digest(secrets.token_urlsafe(32)),'device_token_hashes':{'tv-primary':digest(weather)},'cache_seconds':1800})
    save(directory/'worker.json',{'relay_auth_sha256':digest('Bearer '+relay),'openai_api_key':'','youtube_api_key':'','tmdb_credential':'','model':'gpt-4.1-mini','movie_model':'gpt-4.1','transcription_model':'gpt-4o-mini-transcribe'})
    (directory/'dream-media').mkdir(mode=0o700)
    save(directory/'dream-media/catalog.json',{'version':1,'clips':[]})
    print('Private configuration created. Fill provider keys locally; never copy worker/relay files to TV.')

def load(directory,name):
    path=directory/name
    if path.is_symlink() or path.stat().st_mode&0o077:raise ValueError('Private configuration permissions required')
    return json.loads(path.read_text())

def servers(directory,role):
    result=[]
    if role in ('all','worker'):
        cfg=load(directory,'worker.json')
        s=ThreadingHTTPServer(('127.0.0.1',18888 if role=='all' else 18889),us_api_worker.Handler)
        s.auth_hash=cfg['relay_auth_sha256'];s.worker=us_api_worker.Worker(cfg,directory/'cache-worker');s.tmdb=Tmdb(cfg['tmdb_credential']);result.append(s)
    if role in ('all','gateway'):
        cfg=load(directory,'relay.json');s=ThreadingHTTPServer(('127.0.0.1',18788),api_relay.Handler)
        s.config=cfg;s.tmdb=Tmdb(cfg['tmdb_credential'],cfg['relay_authorization']);result.append(s)
        api_relay.dream_media=lambda path:dream_media.resolve(path,directory/'dream-media')
        cfg=load(directory,'weather.json');s=ThreadingHTTPServer(('127.0.0.1',18787),weather_gateway.Handler)
        s.token_hash=cfg['device_token_sha256'];s.device_hashes=cfg.get('device_token_hashes',{});s.cache=weather_gateway.WeatherCache(directory/'cache-weather',cfg['cache_seconds']);result.append(s)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',required=True,type=Path);p.add_argument('--init',action='store_true');p.add_argument('--base-url');p.add_argument('--role',choices=['all','worker','gateway'],default='all');args=p.parse_args()
    os.umask(0o077)
    if args.init:
        if not args.base_url:p.error('--base-url required with --init')
        initialize(args.directory,args.base_url);return
    running=servers(args.directory,args.role)
    for server in running:threading.Thread(target=server.serve_forever,daemon=True).start()
    def stop(*_):
        for server in running:server.shutdown();server.server_close()
        raise SystemExit(0)
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    print('API ready on loopback only; configure HTTPS reverse proxy separately.',flush=True)
    signal.pause()
if __name__=='__main__':main()
