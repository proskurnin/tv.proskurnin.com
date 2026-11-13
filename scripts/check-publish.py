#!/usr/bin/env python3
"""Check Git index for private paths, credential patterns and known local credentials.
Print only filenames and categories, never matching secret values.
"""
import hashlib,json,re,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 files=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0');files=[p for p in files if p];issues=[];values=set()
 def collect(v,key=''):
  if isinstance(v,dict):
   for k,x in v.items():collect(x,k)
  elif isinstance(v,list):
   for x in v:collect(x,key)
  elif isinstance(v,str) and len(v)>18 and key.lower() in ('token','access_token','refresh_token','client_secret','api_key','openai_api_key','youtube_api_key','tmdb_credential','password','relay_authorization'):values.add(v)
 for p in (ROOT/'integrations').glob('**/private/*'):
  if p.suffix=='.json':
   try:collect(json.loads(p.read_text()))
   except (ValueError,OSError):pass
  if p.name in ('api-keys.env','api-device-token','api-relay-token','weather-device-token'):
   for line in p.read_text().splitlines():
    if line.startswith('#'):continue
    key,sep,val=line.partition('=')
    if sep and any(k in key for k in ['KEY','TOKEN','SECRET']) and len(val.strip())>18:values.add(val.strip().strip('"'))
    elif not sep and len(line.strip())>18:values.add(line.strip())
 patterns=[r'sk-(?:proj-)?[A-Za-z0-9_-]{20,}',r'AIza[0-9A-Za-z_-]{30,}',r'gh[pousr]_[A-Za-z0-9_]{20,}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'ya29\.[A-Za-z0-9_-]{20,}',r'1//[A-Za-z0-9_-]{25,}',r'GOCSPX-[A-Za-z0-9_-]{20,}']
 for name in files:
  if any(part in ['private','reports','downloads','snapshots','artifacts','upstream'] for part in Path(name).parts):issues.append((name,'private path'))
  data=subprocess.check_output(['git','show',':'+name],cwd=ROOT)
  if len(data)>3000000:issues.append((name,'large file'))
  if any(re.search(p.encode(),data) for p in patterns):issues.append((name,'secret pattern'))
  if any(v.encode() in data for v in values):issues.append((name,'matches local credential'))
 # Screenshot-specific publication checks read only the Git index, just like
 # the secret scan above. Never print image contents or metadata values.
 shot_names=[n for n in files if n.startswith('docs/screenshots/')]
 if shot_names:
  def staged(path):return subprocess.check_output(['git','show',':'+path],cwd=ROOT)
  try:
   catalog=json.loads(staged('docs/screenshots/catalog.json'))
   manifest=json.loads(staged('docs/screenshots/manifest.json'))
   private_keys={'ip','serial','ssid','mac','address'}
   if private_keys.intersection(k.lower() for k in catalog.get('device',{})):
    issues.append(('docs/screenshots/catalog.json','private network/device identifier in catalog'))
   if private_keys.intersection(k.lower() for k in manifest.get('device',{})):
    issues.append(('docs/screenshots/manifest.json','private network/device identifier in manifest'))
   specs={x['id']:x for x in catalog['screens']}
   entries=manifest.get('screens',{})
   for name in shot_names:
    if not name.endswith('.png'):continue
    sid=Path(name).stem
    entry=entries.get(sid)
    spec=specs.get(sid)
    if not entry or not spec:issues.append((name,'not declared in catalog and manifest'));continue
    raw=staged(name)
    if len(raw)>3000000:issues.append((name,'screenshot exceeds 3 MB'))
    if not raw.startswith(b'\x89PNG\r\n\x1a\n'):issues.append((name,'invalid PNG'))
    else:
     pos=8;width=height=None;exif=False
     while pos+12<=len(raw):
      size=struct.unpack('>I',raw[pos:pos+4])[0];kind=raw[pos+4:pos+8]
      if pos+12+size>len(raw):break
      if kind==b'IHDR':width,height=struct.unpack('>II',raw[pos+8:pos+16])
      if kind==b'eXIf':exif=True
      if kind==b'IEND':break
      pos+=12+size
     if exif:issues.append((name,'EXIF metadata present'))
     if width is None or height is None:issues.append((name,'invalid PNG dimensions'))
     elif spec.get('kind') in ('tv','manual') and [width,height]!=catalog['device'].get('resolution'):issues.append((name,'TV dimensions mismatch'))
    if hashlib.sha256(raw).hexdigest()!=entry.get('sha256'):issues.append((name,'SHA256 does not match manifest'))
    if any(m.get('rect',[0,0,0,0])[2]<=0 or m.get('rect',[0,0,0,0])[3]<=0 for m in spec.get('masks',[])):issues.append((name,'privacy mask coordinates not configured'))
   for sid,entry in entries.items():
    if 'docs/screenshots/'+entry.get('file','') not in shot_names:issues.append(('docs/screenshots/'+sid+'.png','manifest image is not staged'))
  except Exception:
   issues.append(('docs/screenshots','catalog or manifest could not be validated'))
 for name,reason in issues:print(name+': '+reason)
 print('Publication check:',len(files),'files;',len(issues),'findings')
 return bool(issues)
if __name__=='__main__':sys.exit(main())
