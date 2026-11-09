#!/usr/bin/env python3
"""RU API gateway forwarding only named API operations to an authenticated US worker."""
from transcription import validate as validate_audio
from movie_contract import validate as validate_movies
import hashlib,hmac,json,time,urllib.request,urllib.error,urllib.parse
from tmdb_proxy import Tmdb,TmdbError,InvalidRequest
from chat_contract import validate_chat,validate_speech
from dream_media import resolve as dream_media
from speed_probe import serve as speed_probe
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def reply(self,status,data):
        body=json.dumps(data,ensure_ascii=False).encode();self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
    def dispatch(self,method):
        auth=self.headers.get('Authorization','')
        if not hmac.compare_digest(hashlib.sha256(auth.encode()).hexdigest(),self.server.config['device_auth_sha256']):
            self.reply(401,{'error':'unauthorized'});return
        u=urllib.parse.urlsplit(self.path);body=None
        if method=='GET' and u.path=='/tv-api/v1/network/speed':
            if u.query:self.reply(400,{'error':'invalid_parameters'})
            else:speed_probe(self)
            return
        if method=='GET' and u.path.startswith('/tv-api/v1/dream/'):
            try:
                if u.query:raise FileNotFoundError()
                data,kind=dream_media(u.path)
                self.send_response(200);self.send_header('Content-Type',kind)
                self.send_header('Content-Length',str(len(data) if isinstance(data,bytes) else data.stat().st_size));self.send_header('Cache-Control','private, no-store');self.end_headers()
                if isinstance(data,bytes):self.wfile.write(data)
                else:
                    with data.open('rb') as source:
                        while True:
                            chunk=source.read(65536)
                            if not chunk:break
                            self.wfile.write(chunk)
            except (BrokenPipeError,ConnectionResetError):pass
            except (OSError,ValueError,KeyError):self.reply(404,{'error':'media_unavailable'})
            return
        if method=='GET' and u.path.startswith('/tv-api/v1/tmdb/'):
            try:
                raw,kind,route=self.server.tmdb.get(u.path[len('/tv-api/v1/tmdb'):],u.query)
                self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','private, max-age=3600');self.send_header('X-API-Egress',route);self.end_headers();self.wfile.write(raw)
            except InvalidRequest:self.reply(400,{'error':'invalid_parameters'})
            except TmdbError:self.reply(503,{'error':'tmdb_unavailable'})
            return
        allowed={('POST','/tv-api/v1/ai/transcribe'):'/v1/ai/transcribe',('GET','/tv-api/v1/youtube/channel'):'/v1/youtube/channel',('POST','/tv-api/v1/ai/movies'):'/v1/ai/movies',('POST','/tv-api/v1/ai/chat'):'/v1/ai/chat',('POST','/tv-api/v1/ai/speech'):'/v1/ai/speech'}
        path=allowed.get((method,u.path))
        if path is None:self.reply(404,{'error':'unknown_api'});return
        try:
            if method=='GET':
                q=urllib.parse.parse_qs(u.query,strict_parsing=True)
                if set(q)-{'interval'} or any(len(v)!=1 for v in q.values()):raise ValueError()
                interval=int(q.get('interval',['300'])[0])
                if interval not in (300,600,900,1800,3600):raise ValueError()
                path+='?interval='+str(interval)
            else:
                if u.query:raise ValueError()
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=(1010000 if path.endswith("/transcribe") else 32768 if path.endswith(("/chat","/movies")) else 4096):raise ValueError()
                data=json.loads(self.rfile.read(length))
                if path.endswith('/transcribe'):validate_audio(data)
                elif path.endswith('/speech'):validate_speech(data)
                elif path.endswith('/chat'):validate_chat(data)
                else:validate_movies(data)
                body=json.dumps(data).encode()
        except (ValueError,TypeError):self.reply(400,{'error':'invalid_parameters'});return
        start=time.monotonic();status=503;result={'error':'us_worker_unavailable'}
        try:
            request=urllib.request.Request('http://127.0.0.1:18888'+path,data=body,headers={'Authorization':self.server.config['relay_authorization'],'Content-Type':'application/json'},method=method)
            with urllib.request.urlopen(request,timeout=45) as response:
                limit=1500000 if path.endswith("/speech") else 1048576
                raw=response.read(limit+1)
                if len(raw)>limit:raise ValueError()
                result=json.loads(raw);status=200
        except urllib.error.HTTPError as e:
            status=503
            try:result={'error':json.load(e).get('error','worker_error')}
            except Exception:pass
        except (OSError,ValueError):pass
        self.reply(status,result)
        print(json.dumps({'device_id':'tv-sdx43','api':u.path,'egress':'us','status':status,'ms':round((time.monotonic()-start)*1000)}),flush=True)
    def do_GET(self):self.dispatch('GET')
    def do_POST(self):self.dispatch('POST')

if __name__=='__main__':
    server=ThreadingHTTPServer(('127.0.0.1',18788),Handler)
    server.config=json.loads(Path('/etc/proskurnin-api/relay.json').read_text());server.tmdb=Tmdb(server.config['tmdb_credential'],server.config['relay_authorization']);server.serve_forever()
