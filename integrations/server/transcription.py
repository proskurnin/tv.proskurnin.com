"""Bounded phone dictation; no recording/transcript persistence or payload logging."""
import base64,json,secrets,threading,time,urllib.request,urllib.error
from pathlib import Path
MIMES={'audio/webm':'webm','audio/mp4':'mp4'}
def validate(body):
    if not isinstance(body,dict) or set(body)!={'audio','mime'} or body['mime'] not in MIMES or not isinstance(body['audio'],str) or len(body['audio'])>1000000:raise ValueError('invalid_audio')
    data=base64.b64decode(body['audio'],validate=True)
    if not 256<=len(data)<=750000:raise ValueError('invalid_audio')
    if body['mime']=='audio/webm' and not data.startswith(b'\x1aE\xdf\xa3'):raise ValueError('invalid_audio')
    if body['mime']=='audio/mp4' and data[4:8]!=b'ftyp':raise ValueError('invalid_audio')
    return data
lock=threading.Lock();last=0
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args):return None

def transcribe(config,directory,body):
    global last
    data=validate(body)
    if not lock.acquire(blocking=False):raise ValueError('rate_limit')
    try:
        if time.monotonic()-last<3:raise ValueError('rate_limit')
        last=time.monotonic();path=Path(directory)/'transcription-budget.json';day=time.strftime('%Y-%m-%d',time.gmtime())
        try:budget=json.loads(path.read_text())
        except (OSError,ValueError):budget={}
        if budget.get('day')!=day:budget={'day':day,'count':0}
        if budget.get('count',0)>=100:raise ValueError('daily_limit')
        budget['count']=budget.get('count',0)+1;tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(budget));tmp.replace(path)
        boundary='tv-'+secrets.token_hex(16);parts=[]
        for name,value in [('model',config.get('transcription_model','gpt-4o-mini-transcribe')),('language','ru'),('response_format','json')]:parts.append(('--'+boundary+'\r\nContent-Disposition: form-data; name="'+name+'"\r\n\r\n'+value+'\r\n').encode())
        parts.append(('--'+boundary+'\r\nContent-Disposition: form-data; name="file"; filename="voice.'+MIMES[body['mime']]+'"\r\nContent-Type: '+body['mime']+'\r\n\r\n').encode()+data+b'\r\n');parts.append(('--'+boundary+'--\r\n').encode())
        request=urllib.request.Request('https://api.openai.com/v1/audio/transcriptions',data=b''.join(parts),headers={'Authorization':'Bearer '+config['openai_api_key'],'Content-Type':'multipart/form-data; boundary='+boundary})
        try:
            with urllib.request.build_opener(NoRedirect).open(request,timeout=35) as response:raw=response.read(8193)
            if len(raw)>8192:raise ValueError('transcription_unavailable')
            text=json.loads(raw).get('text','').strip()
            if not text or len(text)>512:raise ValueError('speech_empty_or_long')
            return {'text':text}
        except urllib.error.HTTPError as e:raise ValueError('quota_or_rate_limit' if e.code==429 else 'transcription_unavailable') from None
        except (OSError,KeyError,json.JSONDecodeError):raise ValueError('transcription_unavailable') from None
    finally:lock.release()
