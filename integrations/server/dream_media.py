"""Authenticated, fixed local screensaver media; no URLs or filesystem paths from clients."""
import json,re
from pathlib import Path
ROOT=Path('/opt/proskurnin-api/dream-media')
def resolve(path,root=ROOT):
 catalog=json.loads((root/'catalog.json').read_text())
 clips=[{k:v for k,v in x.items() if k in ('id','name','bytes','sha256','duration_seconds','fps')} for x in catalog['clips']]
 if path=='/tv-api/v1/dream/catalog':return json.dumps({'version':1,'clips':clips}).encode(),'application/json'
 m=re.fullmatch(r'/tv-api/v1/dream/clip/([a-z0-9]{1,40})\.mp4',path)
 if not m or m[1] not in {c['id'] for c in clips}:raise FileNotFoundError()
 file=root/(m[1]+'.mp4')
 if file.is_symlink() or not file.is_file() or file.stat().st_size>40000000:raise FileNotFoundError()
 return file,'video/mp4'
