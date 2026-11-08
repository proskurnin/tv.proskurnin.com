import os,subprocess,time,json,re,xml.etree.ElementTree as E,ssl,urllib.request,urllib.error
from pathlib import Path
import sys
if '--live' not in sys.argv:raise SystemExit('Explicit --live required: changes TV screen and creates a test pairing.')
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/release-v131';URL='https://192.168.178.105:8766';ADB=['/Users/roman/Library/Android/sdk/platform-tools/adb','-s','192.168.178.105:5555']
def sh(c):return subprocess.check_output(ADB+['shell',c],text=True,timeout=35)
def ui():
 for attempt in range(4):
  path='/data/local/tmp/remote-v11-'+str(time.monotonic_ns())+'.xml';sh('uiautomator dump '+path+' >/dev/null')
  try:return list(E.fromstring(sh('cat '+path)).iter('node'))
  except Exception:time.sleep(.4)
 raise RuntimeError('TV UI unavailable')
def tvclick(text):
 n=next(n for n in ui() if text.lower() in n.get('text','').lower() and n.get('clickable')=='true');b=list(map(int,re.findall(r'\d+',n.get('bounds'))));sh('input tap %d %d'%((b[0]+b[2])//2,(b[1]+b[3])//2))
def get_code():
 for n in ui():
  m=re.fullmatch(r'(\d{3}) (\d{3})\n\d+ с',n.get('text',''))
  if m:return m[1]+m[2]
 tvclick('Подключить телефон');return get_code()
sh('am start -n local.proskurnin.remote/.RemoteActivity');time.sleep(2)
results={};sslctx=ssl.create_default_context(cafile=str(ROOT/'integrations/remote/private/ca.pem'))
with urllib.request.urlopen(URL,context=sslctx,timeout=5) as r:assert r.status==200;results['tls_verified']=True
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/Users/roman/Library/Caches/ms-playwright/chromium-1217/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing',args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture=/private/tmp/remote-voice.wav'])
 context=browser.new_context(**p.devices['Pixel 7'],ignore_https_errors=True,permissions=['microphone']);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(URL,wait_until='networkidle');page.locator('#pairing').wait_for(state='visible')
 sh('am start -n local.proskurnin.remote/.RemoteActivity');time.sleep(1);tvclick('Подключить телефон');page.locator('#pin').fill(get_code());page.locator('#phoneName').fill('Проверка HTTPS 1.1');page.locator('#pairButton').click();page.get_by_text('Подтвердите «Разрешить» на телевизоре.').wait_for();time.sleep(1);tvclick('Разрешить');page.locator('#controls').wait_for(state='visible',timeout=15000)
 assert not errors,errors;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert any(c['secure'] and c['httpOnly'] for c in context.cookies(URL+'/api/state'));results['secure_pairing']=True
 def api(path,body=None):return page.evaluate('''async ([path,body])=>{const r=await fetch('/api/'+path,{method:body===null?'GET':'POST',headers:body===null?{}:{'Content-Type':'application/json','X-TV-Request':'1'},body:body===null?undefined:JSON.stringify(body)});return {status:r.status,body:await r.json()};}''',[path,body])
 assert api('text',{'id':'stale','revision':0,'text':'test'})['status']==409;results['stale_field_rejected']=True
 assert api('voice',{'mime':'text/html','audio':'bad'})['status']==503;results['bad_audio_rejected']=True
 # Phone microphone capture through MediaRecorder, real TV and real transcription API.
 page.locator('#voiceToggle').click();time.sleep(2);print('Voice status:',page.locator('#voiceStatus').inner_text(),'JS errors:',errors,flush=True);page.get_by_text('Говорите в телефон… До 30 секунд.').wait_for(timeout=10000);time.sleep(7);page.locator('#voiceToggle').click();page.get_by_text('Проверьте фразу и нажмите «Отправить на ТВ».').wait_for(timeout=60000);text=page.locator('#voiceText').input_value();assert len(text)>3;results['microphone_fixture_to_api']=True;print('Transcription returned text; content omitted',flush=True)
 # Browser sends request to launcher via signature-protected receiver.
 page.locator('#voiceMode').select_option('chat');page.locator('#voiceSend').click();time.sleep(4);assert '.AssistantActivity' in sh('dumpsys activity activities | grep mResumedActivity');results['phone_opens_chat']=True
 # Focus actual standard EditText, type Cyrillic, compare on-TV contents, then clear.
 n=next(n for n in ui() if n.get('class')=='android.widget.EditText');b=list(map(int,re.findall(r'\d+',n.get('bounds'))));sh('input tap %d %d'%((b[0]+b[2])//2,(b[1]+b[3])//2));page.locator('#textPanel').wait_for(state='visible',timeout=12000);page.locator('#tvText').fill('Привет с телефона 123');page.get_by_text('Передано на ТВ',exact=True).wait_for();assert any(n.get('text')=='Привет с телефона 123' for n in ui());results['cyrillic_mirroring']=True
 field=api('field')['body']['field'];assert api('text',{'id':field['id'],'revision':field['revision']-1,'text':'outdated'})['status']==409;results['stale_revision_rejected']=True
 page.locator('#tvText').fill('');time.sleep(.8);page.screenshot(path=str(OUT/'phone-https.png'),full_page=True)
 # Changing screen must invalidate old field ID.
 api('command',{'action':'home'});time.sleep(1);assert api('text',{'id':field['id'],'revision':field['revision'],'text':'stale'})['status']==409;results['navigation_invalidates_field']=True
 page.reload(wait_until='networkidle');page.locator('#controls').wait_for(state='visible');results['reload_reconnect']=True
 results['js_errors']=errors;assert not errors
 api('logout',{});browser.close()
(OUT/'remote-tests.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(results),flush=True)
