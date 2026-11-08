#!/usr/bin/env python3
"""TV OAuth device flow: codes shown locally, exchange and tokens only on US."""
import html,json,os,queue,shlex,subprocess,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
ROOT=Path(__file__).resolve().parent
REMOTE=r'''
import json,sys,time,urllib.request,urllib.parse,urllib.error,os,pwd
client=json.load(sys.stdin)
scope='https://www.googleapis.com/auth/youtube.readonly'
def post(path,data):
 req=urllib.request.Request('https://oauth2.googleapis.com/'+path,data=urllib.parse.urlencode(data).encode(),headers={'Content-Type':'application/x-www-form-urlencoded'})
 try:
  with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)
 except urllib.error.HTTPError as e:
  try:data=json.load(e)
  except Exception:data={}
  allowed=['authorization_pending','slow_down','access_denied','expired_token','invalid_client','invalid_grant','invalid_scope','unauthorized_client']
  return {'error':data.get('error') if data.get('error') in allowed else 'oauth_http_'+str(e.code)}
def run():
 device=post('device/code',{'client_id':client['client_id'],'scope':scope})
 if 'error' in device:print(json.dumps({'ok':False,'error':device['error']}),flush=True);return
 url=device['verification_url']
 if urllib.parse.urlsplit(url).hostname not in ('www.google.com','google.com','accounts.google.com'):raise ValueError('verification_host')
 expires=min(600,int(device['expires_in']));interval=max(5,int(device.get('interval',5)))
 print(json.dumps({'user_code':device['user_code'],'verification_url':url,'expires_in':expires}),flush=True)
 deadline=time.monotonic()+expires
 while time.monotonic()+interval<deadline:
  time.sleep(interval)
  tokens=post('token',{'client_id':client['client_id'],'client_secret':client['client_secret'],'device_code':device['device_code'],'grant_type':'urn:ietf:params:oauth:grant-type:device_code'})
  error=tokens.get('error')
  if error=='authorization_pending':continue
  if error=='slow_down':interval+=5;continue
  if error:print(json.dumps({'ok':False,'error':error}),flush=True);return
  req=urllib.request.Request('https://www.googleapis.com/youtube/v3/channels?part=id&mine=true',headers={'Authorization':'Bearer '+tokens['access_token']})
  with urllib.request.urlopen(req,timeout=15) as response:channels=json.load(response)
  if not any(c.get('id')=='UCIJ1iB_5TQf-NUCkzrvXn4w' for c in channels.get('items',[])):print(json.dumps({'ok':False,'error':'wrong_channel'}),flush=True);return
  if scope not in tokens.get('scope','').split() or not tokens.get('refresh_token'):print(json.dumps({'ok':False,'error':'missing_scope_or_refresh_token'}),flush=True);return
  tokens.update(expires_at=time.time()+tokens.get('expires_in',3600),client_id=client['client_id'],client_secret=client['client_secret'])
  path='/var/lib/proskurnin-worker/oauth-token.json';fd=os.open(path+'.new',os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
  with os.fdopen(fd,'w') as f:json.dump(tokens,f)
  u=pwd.getpwnam('tv-api-worker');os.chown(path+'.new',u.pw_uid,u.pw_gid);os.replace(path+'.new',path)
  print(json.dumps({'ok':True,'channel_id':'UCIJ1iB_5TQf-NUCkzrvXn4w'}),flush=True);return
 print(json.dumps({'ok':False,'error':'session_expired'}),flush=True)
try:run()
except Exception as e:print(json.dumps({'ok':False,'error':type(e).__name__}),flush=True)
'''
def save_status(data):
 p=ROOT/'private/oauth-status.json';fd=os.open(p,os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
 with os.fdopen(fd,'w') as f:json.dump(data,f)
def main():
 client=json.loads((ROOT/'private/oauth-client.json').read_text())['installed']
 p=subprocess.Popen(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','ProxyJump=root@188.120.240.175','ubuntu@40.160.252.24','sudo -n python3 -u -c '+shlex.quote(REMOTE)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
 p.stdin.write(json.dumps(client));p.stdin.close()
 messages=queue.Queue()
 def read():
  for line in p.stdout:
   try:messages.put(json.loads(line))
   except ValueError:messages.put({'ok':False,'error':'invalid_response'})
 threading.Thread(target=read,daemon=True).start()
 try:initial=messages.get(timeout=40)
 except queue.Empty:p.terminate();raise RuntimeError('Device authorization unavailable')
 if 'user_code' not in initial:save_status(initial);print(json.dumps(initial));return
 state={'result':None}
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):
   if self.headers.get('Host')!='127.0.0.1:'+str(self.server.server_port) or self.path!='/':self.send_error(404);return
   result=state['result']
   content=('<h2>Готово: канал подтверждён</h2>' if result.get('ok') else '<h2>Вход не завершён: '+html.escape(result.get('error','unknown'))+'</h2>') if result else '<p>Откройте <a target="_blank" rel="noreferrer" href="'+html.escape(initial['verification_url'],quote=True)+'">страницу Google</a> и введите код:</p><p style="font-size:38px;letter-spacing:3px">'+html.escape(initial['user_code'])+'</p><p>Выберите аккаунт канала @ProskurninLife. Разрешение: только чтение YouTube. Коды и секреты в чат не отправляйте.</p><p>Токены будут сохранены только на вашем сервере США. Эта страница обновляется автоматически.</p>'
   body=('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="5"><meta name="referrer" content="no-referrer"><title>Proskurnin TV — вход по коду</title><body style="font:20px system-ui;background:#10141d;color:#e1e6ef;padding:48px"><h1>Proskurnin TV · Google OAuth</h1>'+content+'</body>').encode()
   self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 server=HTTPServer(('127.0.0.1',0),Handler);server.timeout=1
 safe={'local_url':'http://127.0.0.1:'+str(server.server_port)+'/','expires_in_seconds':initial['expires_in'],'flow':'device'}
 fd=os.open(ROOT/'private/oauth-session.json',os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
 with os.fdopen(fd,'w') as f:json.dump(safe,f)
 print(json.dumps(safe),flush=True);deadline=time.monotonic()+initial['expires_in']+30;done_at=None
 try:
  while time.monotonic()<deadline:
   if not messages.empty():
    result=messages.get();state['result']=result;save_status(result);print(json.dumps(result),flush=True);done_at=time.monotonic()
   server.handle_request()
   if done_at and time.monotonic()>done_at+60:break
 finally:
  server.server_close()
  if p.poll() is None:p.terminate()
if __name__=='__main__':main()
