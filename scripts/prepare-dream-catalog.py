#!/usr/bin/env python3
"""Prepare local media catalog from user-owned MP4 files; never downloads videos."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);a=p.parse_args()
clips=[]
for f in sorted(a.directory.glob('*.mp4')):
 if f.is_symlink() or not re.fullmatch('[a-z0-9]{1,40}',f.stem) or f.stat().st_size>40000000:raise SystemExit('MP4 needs lowercase alphanumeric name and size <= 40 MB')
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(f)]))
 video=next(s for s in info['streams'] if s['codec_type']=='video');n,d=map(int,video['avg_frame_rate'].split('/'));fps=n/d
 if video['codec_name']!='h264' or video['width']>1920 or video['height']>1080 or not 0<fps<=30 or not 1<=float(info['format']['duration'])<=300:raise SystemExit('Use H.264 <=1920x1080 <=30 FPS')
 clips.append({'id':f.stem,'name':f.stem,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'duration_seconds':float(info['format']['duration']),'fps':fps})
if len(clips)<5:raise SystemExit('Provide at least 5 clips')
(a.directory/'catalog.json').write_text(json.dumps({'version':1,'clips':clips},indent=2)+'\n');print('Catalog ready:',len(clips),'clips')
