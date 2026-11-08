#!/usr/bin/env python3
import sys,io,hashlib,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'integrations/server'))
import speed_probe
from api_relay import Handler
class Fake:
 def __init__(self):self.headers={};self.status=None;self.wfile=io.BytesIO();self.connection=SimpleNamespace(settimeout=lambda n:None)
 def reply(self,status,data):self.status=status
 def send_response(self,status):self.status=status
 def send_header(self,k,v):self.headers[k]=v
 def end_headers(self):pass
class Tests(unittest.TestCase):
 def test_finite_body_and_cooldown(self):
  with patch.object(speed_probe,'_next',0):
   first=Fake();speed_probe.serve(first)
   self.assertEqual(first.status,200);self.assertEqual(len(first.wfile.getvalue()),16*1024*1024);self.assertNotIn('Content-Encoding',first.headers)
   second=Fake();speed_probe.serve(second);self.assertEqual(second.status,429);self.assertEqual(len(second.wfile.getvalue()),0)
 def test_auth_precedes_probe(self):
  for auth,status,called in [('bad',401,False),('test-device',None,True)]:
   f=Fake();f.headers={'Authorization':auth};f.server=SimpleNamespace(config={'device_auth_sha256':hashlib.sha256(b'test-device').hexdigest()});f.path='/tv-api/v1/network/speed'
   with patch('api_relay.speed_probe') as probe:
    Handler.dispatch(f,'GET');self.assertEqual(probe.called,called);self.assertEqual(f.status,status)
 def test_no_query_or_post(self):
  for method,path,status in [('GET','/tv-api/v1/network/speed?url=https://example.com',400),('POST','/tv-api/v1/network/speed',404)]:
   f=Fake();f.headers={'Authorization':'test-device'};f.server=SimpleNamespace(config={'device_auth_sha256':hashlib.sha256(b'test-device').hexdigest()});f.path=path
   with patch('api_relay.speed_probe') as probe:Handler.dispatch(f,method);self.assertFalse(probe.called);self.assertEqual(f.status,status)
 def test_cancel_releases_lock(self):
  class Broken:
   def write(self,chunk):raise BrokenPipeError()
  with patch.object(speed_probe,'_next',0):
   f=Fake();f.wfile=Broken();speed_probe.serve(f);self.assertFalse(speed_probe._lock.locked())
if __name__=='__main__':unittest.main()
