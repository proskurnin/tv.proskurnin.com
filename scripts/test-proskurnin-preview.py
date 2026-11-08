from pathlib import Path
import subprocess,time,json
O=Path('reports/proskurnin-preview-tests');O.mkdir(exist_ok=True);A=['/Users/roman/Library/Android/sdk/platform-tools/adb','-s','192.168.178.105:5555'];P='local.proskurnin.preview';report={}
def sh(s):return subprocess.check_output(A+['shell',s],timeout=30).decode()
def focus():return sh('dumpsys window windows').split('mCurrentFocus=')[-1].split('\n')[0]
def own():assert P in focus(),'TV focus changed; stop injecting keys'
def key(n):own();sh('input keyevent '+str(n));time.sleep(.15)
def shot(name):
 d=subprocess.check_output(A+['exec-out','screencap -p'],timeout=15);(O/(name+'.png')).write_bytes(d[d.index(b'\x89PNG'):])
def start():report['launch']=sh('am start -W -n '+P+'/.MainActivity');time.sleep(1);own()
report['home_before']=sh('cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME')
start();shot('start');(O/'gfx-before.txt').write_text(sh('dumpsys gfxinfo '+P))
for n in [22]*6+[21]*6+[19,20]:key(n)
shot('arrows');key(23);time.sleep(3);report['okko_launch_focus']=focus();shot('okko-open')
start();key(22);key(23);time.sleep(2);report['kinopoisk_launch_focus']=focus();shot('kinopoisk-open')
start();key(22);key(23);time.sleep(2);report['ivi_launch_focus']=focus();shot('ivi-open')
start();key(22);key(23);time.sleep(2);report['youtube_launch_focus']=focus();shot('youtube-open')
start();key(19);key(23);shot('settings');key(23);shot('design-off');key(19);key(23);key(23);shot('design-on');key(20)
(O/'meminfo.txt').write_text(sh('dumpsys meminfo '+P));(O/'gfx-after.txt').write_text(sh('dumpsys gfxinfo '+P));(O/'focus-events.txt').write_text(sh('logcat -d -s ProskurninPreview:I *:S'))
key(4);time.sleep(.3);report['back_focus']=focus();report['home_after']=sh('cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME');assert report['home_before']==report['home_after'];(O/'results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print(json.dumps(report,ensure_ascii=False))
