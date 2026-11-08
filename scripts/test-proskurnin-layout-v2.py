import subprocess,time,pathlib,json
A=['/Users/roman/Library/Android/sdk/platform-tools/adb','-s','192.168.178.105:5555'];P='local.proskurnin.preview';O=pathlib.Path('reports/proskurnin-layout-v2');result={}
def sh(s):return subprocess.check_output(A+['shell',s],timeout=40).decode()
def focus():return sh('dumpsys window windows').split('mCurrentFocus=')[-1].split('\n')[0]
def key(n):assert P in focus(),'Other screen active, stop';sh('input keyevent '+str(n));time.sleep(.2)
def shot(n):
 d=subprocess.check_output(A+['exec-out','screencap -p'],timeout=15);(O/(n+'.png')).write_bytes(d[d.index(b'\x89PNG'):])
def start():print(sh('am start -W -n '+P+'/.MainActivity'),flush=True);time.sleep(1)
result['home_before']=sh('cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME')
start();shot('main');key(20);shot('all-apps');key(22);key(21);key(20);shot('apps-down');key(19);key(19);shot('return-main');key(19);key(23);time.sleep(1);result['network']=focus();shot('network')
start();key(22);key(23);shot('settings-menu');key(4);key(22);key(23);time.sleep(3);result['google']=focus()
result['home_after']=sh('cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME');(O/'results.json').write_text(json.dumps(result,indent=2));print(result,flush=True)
