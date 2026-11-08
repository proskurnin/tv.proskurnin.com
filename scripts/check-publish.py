#!/usr/bin/env python3
"""Check Git index for private paths, credential patterns and known local credentials.
Print only filenames and categories, never matching secret values.
"""
import json,re,subprocess,sys
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
 for name,reason in issues:print(name+': '+reason)
 print('Publication check:',len(files),'files;',len(issues),'findings')
 return bool(issues)
if __name__=='__main__':sys.exit(main())
