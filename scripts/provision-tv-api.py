#!/usr/bin/env python3
"""Provision private device credential and TMDB route; provider keys remain on servers."""
import importlib.util,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('provision_weather',ROOT/'scripts/provision-tv-weather.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def main():
    files=[ROOT/'integrations/server/private'/name for name in ('api-client.json','tmdb-client.json')]
    for p in files:
        if p.is_symlink() or p.stat().st_mode&0o077:raise ValueError('Configuration must be private')
        json.loads(p.read_text())
    root='uid=0(' in module.adb('shell','id')
    try:
        if not root:module.adb('root');module.connect()
        uid=module.adb('shell','stat -c %u /data/user/0/local.proskurnin.preview').strip();assert uid.isdigit()
        directory='/data/user/0/local.proskurnin.preview/files'
        module.adb('shell',f'mkdir -p {directory}; chown {uid}:{uid} {directory}; chmod 700 {directory}')
        for p in files:
            target=directory+'/'+p.name
            module.adb('push',str(p),target+'.new')
            module.adb('shell',f'chown {uid}:{uid} {target}.new; chmod 600 {target}.new; mv {target}.new {target}; restorecon {target}')
        print('Private API access and TMDB route provisioned; all provider keys remain off the TV.')
    finally:
        if not root:module.adb('unroot');module.connect()
if __name__=='__main__':main()
