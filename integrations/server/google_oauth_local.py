#!/usr/bin/env python3
"""User-driven Desktop OAuth with PKCE. Local callback; tokens saved only on US worker."""
import base64,hashlib,hmac,html,json,os,secrets,shlex,subprocess,time,urllib.parse
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
ROOT=Path(__file__).resolve().parent
CHANNEL='UCIJ1iB_5TQf-NUCkzrvXn4w'
SCOPE='https://www.googleapis.com/auth/youtube.readonly'

EXCHANGE='''import sys,json,time,os,pwd,urllib.request,urllib.parse,urllib.error
data=json.load(sys.stdin)
try:
 request=urllib.request.Request('https://oauth2.googleapis.com/token',data=urllib.parse.urlencode(data).encode(),headers={'Content-Type':'application/x-www-form-urlencoded'})
 with urllib.request.urlopen(request,timeout=20) as response:tokens=json.load(response)
 with urllib.request.urlopen(urllib.request.Request('https://www.googleapis.com/youtube/v3/channels?part=id&mine=true',headers={'Authorization':'Bearer '+tokens['access_token']}),timeout=15) as response:channels=json.load(response)
 if not any(c.get('id')=='UCIJ1iB_5TQf-NUCkzrvXn4w' for c in channels.get('items',[])):print(json.dumps({'ok':False,'error':'wrong_channel'}));sys.exit(0)
 if 'https://www.googleapis.com/auth/youtube.readonly' not in tokens.get('scope','').split() or not tokens.get('refresh_token'):print(json.dumps({'ok':False,'error':'missing_scope_or_refresh_token'}));sys.exit(0)
 tokens['expires_at']=time.time()+tokens.get('expires_in',3600)
 tokens['client_id']=data['client_id'];tokens['client_secret']=data['client_secret']
 path='/var/lib/proskurnin-worker/oauth-token.json';fd=os.open(path+'.new',os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
 with os.fdopen(fd,'w') as f:json.dump(tokens,f)
 user=pwd.getpwnam('tv-api-worker');os.chown(path+'.new',user.pw_uid,user.pw_gid);os.replace(path+'.new',path)
 print(json.dumps({'ok':True,'channel_id':'UCIJ1iB_5TQf-NUCkzrvXn4w'}))
except urllib.error.HTTPError as error:print(json.dumps({'ok':False,'error':'oauth_exchange_http_'+str(error.code)}))
except Exception as error:print(json.dumps({'ok':False,'error':type(error).__name__}))
'''

def main():
    client=json.loads((ROOT/'private/oauth-client.json').read_text())['installed']
    state=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(48)
    challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    status_file=ROOT/'private/oauth-status.json';done={'value':False}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,text,status=200):
            body=('<!doctype html><meta charset="utf-8"><meta name="referrer" content="no-referrer"><title>Proskurnin TV</title><body style="font:20px system-ui;background:#10141d;color:#e1e6ef;padding:48px;max-width:800px"><h1>Proskurnin TV · Google OAuth</h1>'+text+'</body>').encode()
            self.send_response(status);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('Referrer-Policy','no-referrer');self.end_headers();self.wfile.write(body)
        def do_GET(self):
            if self.headers.get('Host')!='127.0.0.1:'+str(self.server.server_port):self.reply('Недопустимый адрес.',400);return
            parsed=urllib.parse.urlsplit(self.path)
            if parsed.path=='/' and not parsed.query:
                self.reply('<p>Войдите в аккаунт, управляющий каналом <b>@ProskurninLife</b>. Запрашивается только чтение данных YouTube.</p><p>Имена доступны только для публичных подписок; новые подписчики могут появляться с задержкой. Токены останутся на вашем сервере США.</p><p><a style="color:#b9d5ff" href="'+html.escape(auth_url,quote=True)+'">Продолжить вход в Google</a></p>');return
            if parsed.path!='/callback':self.reply('Страница не найдена',404);return
            q=urllib.parse.parse_qs(parsed.query)
            if len(q.get('state',[]))!=1 or not hmac.compare_digest(q['state'][0],state):self.reply('Неверный код сеанса. Начните вход заново.',400);return
            if q.get('error'):
                error=q['error'][0]
                if error not in ('access_denied','invalid_request','unauthorized_client','unsupported_response_type','invalid_scope','server_error','temporarily_unavailable'):error='oauth_authorization_failed'
                fd=os.open(status_file,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
                with os.fdopen(fd,'w') as f:json.dump({'ok':False,'error':error},f)
                done['value']=True;self.reply('Вход не завершён: '+html.escape(error)+'. Сообщите только этот статус, без кодов и секретов.');return
            if len(q.get('code',[]))!=1:self.reply('Не получен код авторизации.',400);return
            payload={'grant_type':'authorization_code','client_id':client['client_id'],'client_secret':client['client_secret'],'redirect_uri':redirect,'code':q['code'][0],'code_verifier':verifier}
            try:
                r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','ProxyJump=root@188.120.240.175','ubuntu@40.160.252.24','sudo -n python3 -c '+shlex.quote(EXCHANGE)],input=json.dumps(payload),text=True,capture_output=True,timeout=50)
                result=json.loads(r.stdout) if r.returncode==0 else {'ok':False,'error':'ssh_failed'}
            except subprocess.TimeoutExpired:result={'ok':False,'error':'oauth_exchange_timeout'}
            except ValueError:result={'ok':False,'error':'invalid_exchange_response'}
            fd=os.open(status_file,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
            with os.fdopen(fd,'w') as f:json.dump(result,f)
            done['value']=True
            self.reply('<p>Готово. Канал подтверждён, токены сохранены на сервере. Можно закрыть страницу.</p>' if result.get('ok') else '<p>Вход не завершён: '+html.escape(result.get('error','unknown'))+'. Сообщите этот статус в чат, без кодов и секретов.</p>')
    server=HTTPServer(('127.0.0.1',0),Handler);server.timeout=1
    redirect='http://127.0.0.1:'+str(server.server_port)+'/callback'
    auth_url='https://accounts.google.com/o/oauth2/v2/auth?'+urllib.parse.urlencode({'client_id':client['client_id'],'redirect_uri':redirect,'response_type':'code','scope':SCOPE,'state':state,'code_challenge':challenge,'code_challenge_method':'S256','access_type':'offline','prompt':'consent'})
    public={'local_url':'http://127.0.0.1:'+str(server.server_port)+'/','expires_in_seconds':600}
    (ROOT/'private/oauth-session.json').write_text(json.dumps(public));(ROOT/'private/oauth-session.json').chmod(0o600)
    print(json.dumps(public),flush=True)
    deadline=time.monotonic()+600
    while not done['value'] and time.monotonic()<deadline:server.handle_request()
    server.server_close()
    if done['value']:print('OAuth browser step finished; inspect safe status file.',flush=True)
    else:print('OAuth session expired without completion.',flush=True)

if __name__=='__main__':main()
