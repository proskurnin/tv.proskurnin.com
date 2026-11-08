#!/usr/bin/env python3
import sys,tempfile,time,json,unittest
from pathlib import Path
from unittest.mock import patch,MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'integrations/server'))
from chat_contract import validate_speech
from us_api_worker import Worker,ApiError
class Tests(unittest.TestCase):
 def test_only_generated_answer_id(self):
  self.assertEqual(validate_speech({'speech_id':'a'*32}),'a'*32)
  for body in [{'text':'Speak arbitrary text'},{'speech_id':'a'*32,'url':'https://x'}, {'speech_id':'../../secret'},[],{'speech_id':None}]:
   with self.assertRaises(ValueError):validate_speech(body)
 def test_unknown_and_expired_no_provider(self):
  with tempfile.TemporaryDirectory() as d:
   w=Worker({},d);w.speech_items['a'*32]={'at':time.time()-301,'text':'old'}
   with patch('us_api_worker.urllib.request.build_opener') as api:
    for ident in ['a'*32,'b'*32]:
     with self.assertRaises(ApiError) as e:w.speech({'speech_id':ident})
     self.assertEqual(e.exception.code,'speech_expired')
    api.assert_not_called()
 def test_duplicate_uses_memory_and_no_text_on_disk(self):
  with tempfile.TemporaryDirectory() as d:
   w=Worker({'openai_api_key':'fake'},d);w.speech_items['a'*32]={'at':time.time(),'text':'Добрый вечер'}
   response=MagicMock();response.__enter__.return_value=response;response.read.return_value=b'ID3'+b'a'*300;response.headers.get_content_type.return_value='audio/mpeg'
   with patch('us_api_worker.urllib.request.build_opener') as api:
    api.return_value.open.return_value=response
    first=w.speech({'speech_id':'a'*32});second=w.speech({'speech_id':'a'*32});self.assertEqual(first,second);self.assertEqual(api.return_value.open.call_count,1)
    req=api.return_value.open.call_args.args[0];payload=json.loads(req.data);self.assertEqual(payload['model'],'gpt-4o-mini-tts');self.assertEqual(payload['response_format'],'mp3')
   files=list(Path(d).iterdir());self.assertEqual([p.name for p in files],['speech-budget.json']);self.assertNotIn('Добрый',files[0].read_text())
 def test_bounded_cache(self):
  with tempfile.TemporaryDirectory() as d:
   w=Worker({},d);w.speech_items={str(i):{'at':time.time(),'text':'x'} for i in range(12)};w.prune_speech();self.assertLess(len(w.speech_items),8)
 def test_speech_budget(self):
  with tempfile.TemporaryDirectory() as d:
   w=Worker({},d);w.speech_items['a'*32]={'at':time.time(),'text':'x'};Path(d,'speech-budget.json').write_text(json.dumps({'day':time.strftime('%Y-%m-%d',time.gmtime()),'count':50}))
   with self.assertRaises(ApiError) as e:w.speech({'speech_id':'a'*32})
   self.assertEqual(e.exception.code,'daily_limit')
if __name__=='__main__':unittest.main()
