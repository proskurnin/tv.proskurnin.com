#!/usr/bin/env python3
import sys,json,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'integrations/server'))
from us_api_worker import Worker,web_answer,ApiError

def at(date):return datetime.fromisoformat(date).replace(tzinfo=timezone.utc).timestamp()
def sample(date,count=6500):return {'subscriber_count':count,'fetched_at':at(date)}
class Tests(unittest.TestCase):
 def test_yesterday_rollover_restart_zero_and_negative(self):
  with tempfile.TemporaryDirectory() as d:
   w=Worker({},d);a=w.youtube_trend(sample('2026-12-31T22:00:00'),at('2026-12-31T22:00:00'));self.assertIsNone(a['subscriber_delta'])
   w.youtube_trend(sample('2026-12-31T23:59:00',6510),at('2026-12-31T23:59:00'))
   w=Worker({},d);a=w.youtube_trend(sample('2027-01-01T00:00:00',6520),at('2027-01-01T00:00:00'));self.assertEqual(a['subscriber_delta'],10);self.assertEqual(a['baseline_day'],'2026-12-31')
   self.assertEqual(w.youtube_trend(sample('2027-01-01T01:00:00',6510),at('2027-01-01T01:00:00'))['subscriber_delta'],0)
   self.assertEqual(w.youtube_trend(sample('2027-01-01T02:00:00',6500),at('2027-01-01T02:00:00'))['subscriber_delta'],-10)
 def test_missing_day_and_stale_not_zero(self):
  with tempfile.TemporaryDirectory() as d:
   w=Worker({},d);w.youtube_trend(sample('2026-11-01T20:00:00'),at('2026-11-01T20:00:00'))
   self.assertIsNone(w.youtube_trend(sample('2026-11-01T20:00:00'),at('2026-11-02T01:00:00'))['subscriber_delta'])
   self.assertIsNone(w.youtube_trend(sample('2026-11-03T20:00:00'),at('2026-11-03T20:00:00'))['subscriber_delta'])
 def test_cache_and_offline_preserve_yesterday(self):
  with tempfile.TemporaryDirectory() as d:
   now=at('2026-11-02T00:01:00');old=sample('2026-11-01T23:59:00')
   Path(d,'youtube.json').write_text(json.dumps({'data':old,'fetched_at':old['fetched_at']}))
   w=Worker({'youtube_api_key':'fake'},d)
   with patch('us_api_worker.time.time',return_value=now),patch('us_api_worker.request_json',side_effect=ApiError('provider_unavailable')) as api:
    self.assertIsNone(w.youtube(300)['subscriber_delta']);api.assert_not_called()
   with patch('us_api_worker.time.time',return_value=now+300),patch('us_api_worker.request_json',side_effect=ApiError('provider_unavailable')):
    value=w.youtube(300);self.assertTrue(value['stale']);self.assertIsNone(value['subscriber_delta'])
   self.assertEqual(json.loads(Path(d,'youtube-days.json').read_text())['2026-11-01']['count'],6500)
 def test_citations_utf16_and_voice(self):
  raw='🌍 Факт. [source]';start=raw.index('[source]')
  r={'output':[{'content':[{'type':'output_text','text':raw,'annotations':[{'type':'url_citation','start_index':start,'end_index':len(raw),'url':'https://example.org/fact','title':'Факт'}]}]}]}
  answer,speech,cites,sources=web_answer(r);self.assertEqual(answer,'🌍 Факт. [1]');self.assertEqual(speech,'🌍 Факт.');self.assertEqual(cites[0]['start'],9);self.assertEqual(sources[0]['url'],'https://example.org/fact')
  r['output'][0]['content'][0]['annotations'][0]['url']='javascript:alert(1)';self.assertEqual(web_answer(r)[2],[])
 def test_missing_search_fails_instead_of_unverified_answer(self):
  with tempfile.TemporaryDirectory() as d:
   w=Worker({'openai_api_key':'fake'},d)
   with patch('us_api_worker.request_json',return_value={'status':'completed','output':[]}):
    with self.assertRaises(ApiError) as e:w.chat({'query':'Курс сегодня?','history':[]})
    self.assertEqual(e.exception.code,'web_search_unavailable')
if __name__=='__main__':unittest.main()
