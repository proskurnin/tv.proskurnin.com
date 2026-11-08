#!/usr/bin/env python3
"""Check the authenticated relay's media resolver against unsafe paths."""
import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'integrations/server'))
from dream_media import resolve
class MediaTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  (self.root/'catalog.json').write_text(json.dumps({'clips':[{'id':'landscape01','name':'Landscape','bytes':3,'sha256':'a'*64,'source':'https://not-for-client/','fps':30}]}))
  (self.root/'landscape01.mp4').write_bytes(b'abc')
 def tearDown(self):self.tmp.cleanup()
 def test_catalog_does_not_expose_source_urls(self):
  data,kind=resolve('/tv-api/v1/dream/catalog',self.root)
  self.assertEqual(kind,'application/json');self.assertNotIn('source',json.loads(data)['clips'][0])
 def test_only_catalogued_files(self):
  file,kind=resolve('/tv-api/v1/dream/clip/landscape01.mp4',self.root)
  self.assertEqual(file.read_bytes(),b'abc');self.assertEqual(kind,'video/mp4')
  for path in ['../catalog.json','/tv-api/v1/dream/clip/../catalog.json','/tv-api/v1/dream/clip/unknown.mp4','/tv-api/v1/dream/clip/landscape01.mp4?x=1']:
   with self.assertRaises(FileNotFoundError):resolve(path,self.root)
 def test_symlink_is_rejected(self):
  file=self.root/'landscape01.mp4';file.unlink();file.symlink_to(self.root/'catalog.json')
  with self.assertRaises(FileNotFoundError):resolve('/tv-api/v1/dream/clip/landscape01.mp4',self.root)
 def test_oversized_file_is_rejected(self):
  with (self.root/'landscape01.mp4').open('wb') as f:f.truncate(40000001)
  with self.assertRaises(FileNotFoundError):resolve('/tv-api/v1/dream/clip/landscape01.mp4',self.root)
if __name__=='__main__':unittest.main()
