import subprocess,time,pathlib,json
A=['/Users/roman/Library/Android/sdk/platform-tools/adb','-s','192.168.178.105:5555'];P='local.proskurnin.preview';O=pathlib.Path('reports/proskurnin-preview-tests')
def sh(s):return subprocess.check_output(A+['shell',s],timeout=35).decode()
print(sh('am start -W -n '+P+'/.MainActivity'),flush=True);time.sleep(2)
before=sh('dumpsys gfxinfo '+P+' framestats');(O/'navigation-before.txt').write_text(before)
for n in [20,22,21,22,21,19,20,22,21]:
 assert P in sh('dumpsys window windows').split('mCurrentFocus=')[-1].split('\n')[0],'Focus left preview; stopping'
 sh('input keyevent '+str(n));time.sleep(.2)
after=sh('dumpsys gfxinfo '+P+' framestats');(O/'navigation-after.txt').write_text(after);(O/'memory-final.txt').write_text(sh('dumpsys meminfo '+P))
def frames(s):
 out={}
 for l in s.splitlines():
  if l.startswith('0,'):
   a=l.split(',')
   if len(a)>=14:
    try:out[int(a[1])]=(int(a[13])-int(a[1]))/1000000
    except:pass
 return out
b=frames(before);a=frames(after);v=sorted(v for k,v in a.items() if k not in b and 0<v<10000);j={'new_frame_count':len(v),'frame_ms':v,'note':'Actual vsync-to-frame-completed timestamps; includes focus changes, excludes nonzero flags.'};(O/'navigation-measurement.json').write_text(json.dumps(j,indent=2));print(j,flush=True)
d=subprocess.check_output(A+['exec-out','screencap -p']);(O/'final-preview.png').write_bytes(d[d.index(b'\x89PNG'):])
