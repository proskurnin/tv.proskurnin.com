import importlib.util,json,os,sys,tempfile,unittest,urllib.request,urllib.error,threading
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'integrations/server'))
from launcher_profiles import universal_manifest,ANDROID as A
import portable_server
spec=importlib.util.spec_from_file_location('universal_setup',ROOT/'scripts/provision-universal.py');setup=importlib.util.module_from_spec(spec);spec.loader.exec_module(setup)
class UniversalTests(unittest.TestCase):
 def config(self):return {'version':1,'base_url':'https://api.example.org/tv-api/v1/','api_token':'a'*43,'weather_token':'b'*43}
 def test_https_only_without_credentials_or_paths(self):
  setup.validate(self.config())
  for url in ['http://api.example.org/tv-api/v1/','https://user:pass@api.example.org/tv-api/v1/','https://api.example.org/tv-api/v1/?token=x','https://api.example.org/tv-api/v1/#fragment','https://api.example.org/','https://api.example.org:0/tv-api/v1/']:
   with self.assertRaises(ValueError):setup.validate(dict(self.config(),base_url=url))
  with self.assertRaises(ValueError):setup.validate(dict(self.config(),api_token='b'*43))
 def test_private_file_refuses_public_and_symlink(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'cfg';p.write_text('{}');p.chmod(0o644)
   with self.assertRaises(ValueError):setup.private_file(p,1024)
   p.chmod(0o600);self.assertEqual(setup.private_file(p,1024),b'{}')
   link=Path(d)/'link';link.symlink_to(p)
   with self.assertRaises(ValueError):setup.private_file(link,1024)
 def test_no_boot_receiver_or_power_takeover(self):
  root=ET.fromstring(universal_manifest((ROOT/'builds/proskurnin-preview-v1/app/AndroidManifest.xml').read_text()));app=root.find('application')
  names={x.get(A+'name') for x in app};self.assertNotIn('.BootHomeReceiver',names);self.assertNotIn('.PowerMenuActivity',names)
  self.assertIn('.CachedDreamService',names);self.assertIn('.AssistantActivity',names);self.assertIn('.MovieActivity',names)
  self.assertEqual(app.find('provider').get(A+'permission'),'android.permission.DUMP')
  self.assertEqual(root.get('package'),'local.proskurnin.preview')
 def test_home_service_has_no_screen_content_access(self):
  service=ET.parse(ROOT/'builds/proskurnin-preview-v1/app/res/xml/home_keys.xml').getroot()
  self.assertEqual(service.get(A+'canRetrieveWindowContent'),'false')
  self.assertEqual(service.get(A+'accessibilityEventTypes'),'typeWindowStateChanged')
  self.assertEqual(service.get(A+'canRequestFilterKeyEvents'),'true')
 def test_backend_auth_and_allowlist_without_external_requests(self):
  with tempfile.TemporaryDirectory() as tmp:
   directory=Path(tmp)/'private';portable_server.initialize(directory,'https://api.example.org/tv-api/v1/')
   device=json.loads((directory/'device.json').read_text());self.assertIn('tv-primary',json.loads((directory/'relay.json').read_text())['device_auth_hashes']);self.assertEqual((directory/'device.json').stat().st_mode&0o777,0o600)
   running=portable_server.servers(directory,'all')
   for server in running:threading.Thread(target=server.serve_forever,daemon=True).start()
   try:
    cases=[(18788,'/tv-api/v1/no-such-api','wrong',401),(18788,'/tv-api/v1/no-such-api',device['api_token'],404),(18787,'/tv-api/v1/weather/unknown',device['weather_token'],404),(18787,'/tv-api/v1/weather/unknown',device['api_token'],401),(18888,'/v1/ai/chat','wrong',401)]
    for port,path,token,status in cases:
     request=urllib.request.Request('http://127.0.0.1:'+str(port)+path,headers={'Authorization':'Bearer '+token})
     with self.assertRaises(urllib.error.HTTPError) as result:urllib.request.urlopen(request,timeout=3)
     self.assertEqual(result.exception.code,status)
   finally:
    for server in running:server.shutdown();server.server_close()
if __name__=='__main__':unittest.main()
