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
def focus_probe(index):
 nodes=[n for n in ui() if n.get('class')=='android.widget.EditText'];n=nodes[index];b=list(map(int,re.findall(r'\d+',n.get('bounds'))));sh('input tap %d %d'%((b[0]+b[2])//2,(b[1]+b[3])//2))
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
 # Independent probe app verifies native text fields and password exclusion.
 sh('am start -n local.proskurnin.fieldprobe/.FieldProbe');time.sleep(1);focus_probe(0);time.sleep(.5);page.locator('#textPanel').wait_for(state='visible',timeout=10000);field=api('field')['body']['field'];assert field['active'];assert field['package']=='local.proskurnin.fieldprobe'
 page.locator('#tvText').fill('Кириллица — второй экран');page.get_by_text('Передано на ТВ',exact=True).wait_for();assert api('field')['body']['field']['text']=='Кириллица — второй экран';results['independent_app_text']=True
 focus_probe(1);time.sleep(1);new=api('field')['body']['field'];assert new['active'] and new['id']!=field['id'];assert api('text',{'id':field['id'],'revision':field['revision'],'text':'STALE'})['status']==409;results['new_field_rejects_old_request']=True
 focus_probe(2);time.sleep(1);protected=api('field')['body']['field'];assert not protected.get('active');assert 'TEST_PASSWORD_SENTINEL' not in json.dumps(api('state'));page.locator('#textPanel').wait_for(state='hidden');results['password_not_exposed']=True
 # Check that a late update cannot write after navigation into a password.
 assert api('text',{'id':new['id'],'revision':new['revision'],'text':'BAD'})['status']==409
 assert api('command',{'action':'home'})['body']['ok'];time.sleep(1)
 page.screenshot(path=str(OUT/'phone-controls.png'),full_page=True);results['helper_ready']=api('state')['body']['control_ready'];assert results['helper_ready']
 # Stop listeners through TV UI, then restart and retain only this test cookie.
 sh('am start -n local.proskurnin.remote/.RemoteActivity');time.sleep(1);tvclick('Сервер: включён');time.sleep(.5)
 try:urllib.request.urlopen(URL,context=sslctx,timeout=3);raise AssertionError('HTTPS still open')
 except urllib.error.URLError:pass
 tvclick('Сервер: выключен');time.sleep(1);page.reload(wait_until='networkidle');page.locator('#controls').wait_for(state='visible');results['off_and_reconnect']=True
 api('logout',{});assert not errors;results['js_errors']=errors;browser.close()
(OUT/'field-security-tests.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(results),flush=True)
sh('am start -n local.proskurnin.preview/.MainActivity')
