import base64,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'integrations/server'))
from transcription import validate
class AudioContract(unittest.TestCase):
 def body(self,raw=b'\x1aE\xdf\xa3'+bytes(300),mime='audio/webm'):return {'audio':base64.b64encode(raw).decode(),'mime':mime}
 def test_webm(self):self.assertEqual(len(validate(self.body())),304)
 def test_mp4(self):self.assertEqual(len(validate(self.body(bytes(4)+b'ftyp'+bytes(300),'audio/mp4'))),308)
 def test_rejects_bad_or_extra_fields(self):
  for value in [None,{},self.body(mime='text/html'),self.body(b'hello'),{**self.body(),'url':'http://untrusted'},self.body(b'x'*751000),{'audio':'%%%','mime':'audio/webm'},self.body(bytes(400),'audio/mp4')]:
   with self.assertRaises(ValueError):validate(value)
if __name__=='__main__':unittest.main()
