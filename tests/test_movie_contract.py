import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'integrations/server'))
from movie_contract import validate,verified,permits_alternative
from tmdb_proxy import validate as tmdb_validate,InvalidRequest
class MovieContract(unittest.TestCase):
 def candidate(self):return dict(id=1,title='Черепаха',original_title='Turtle',year='2009',runtime=80,overview='A sea turtle travels across the ocean.',keywords=['sea turtle'],genres=['Documentary'],original_language='en')
 def test_no_invented_or_duplicate_ids(self):
  for ids in ([2],[1,1]):
   with self.assertRaises(ValueError):verified({'matches':[dict(topic_role='central',id=i,reason='Фильм про черепаху',evidence='sea turtle') for i in ids]},[self.candidate()])
 def test_unsupported_evidence_removed_not_replaced(self):
  self.assertEqual(verified({'matches':[dict(topic_role='central',id=1,reason='Про черепах',evidence='a completely invented description')]},[self.candidate()])['matches'],[])
 def test_accept_real_evidence_and_allow_fewer_than_three(self):
  result=verified({'matches':[dict(topic_role='central',id=1,reason='Главный герой — морская черепаха',evidence='A sea turtle travels')]},[self.candidate()]);self.assertEqual(len(result['matches']),1)
  self.assertEqual(verified({'matches':[]},[self.candidate()])['matches'],[])
 def test_reject_unbounded_or_injected_metadata(self):
  for body in [dict(query='черепахи',url='http://x'),dict(query='черепахи',candidates=[dict(self.candidate(),overview='x'*2501)]),dict(query='черепахи',candidates=[dict(self.candidate(),id=i+1) for i in range(13)])]:
   with self.assertRaises(ValueError):validate(body)
 def test_full_pool_kept_for_gallery(self):
  candidates=[dict(self.candidate(),id=i+1) for i in range(12)]
  self.assertEqual(len(validate(dict(query='Фильмы про черепах',candidates=candidates,requested_type='film',type_override='none'))[1]),12)
  result=verified({'matches':[dict(topic_role='central',id=i+1,reason='Черепаха — главный герой фильма',evidence='sea turtle') for i in range(12)]},candidates)
  self.assertEqual(len(result['matches']),12)
 def test_alternative_and_exclusions_bounded(self):
  self.assertEqual(validate({'query':'Фильмы про черепах','type_override':'animation','exclude_titles':['Teenage Mutant Ninja Turtles']})[0],'Фильмы про черепах')
  for body in [{'query':'Фильмы про черепах','type_override':'series'}, {'query':'Фильмы про черепах','exclude_titles':['x']*61}]:
   with self.assertRaises(ValueError):validate(body)
 def test_secondary_topic_is_not_a_match(self):
  self.assertEqual(verified({'matches':[dict(id=1,reason='Черепаха появляется во второстепенной сцене',evidence='sea turtle',topic_role='supporting')]},[self.candidate()])['matches'],[])
 def test_requested_type_does_not_forbid_alternative_offer(self):
  for q in ['Фильмы про черепах','Мультфильмы про черепах']:
   self.assertTrue(permits_alternative(q))
  for q in ['Фильмы про подводный мир, не мультфильмы','Только мультфильмы','Никаких мультфильмов','cartoons only','no animation']:
   self.assertFalse(permits_alternative(q))
 def test_availability_endpoint_is_bounded(self):
  self.assertIn('/movie/105/watch/providers?',tmdb_validate('/movie/105/watch/providers','')[0])
  for path,q in [('/movie/105/watch/providers','url=https://example.com'),('/movie/105/watch/providers/other',''),('/movie/-1/watch/providers','')]:
   with self.assertRaises(InvalidRequest):tmdb_validate(path,q)
 def test_tmdb_append_restricted(self):
  self.assertIn('append_to_response=keywords',tmdb_validate('/movie/1','language=ru-RU&append_to_response=keywords')[0])
  for path,q in [('/movie/1','append_to_response=videos'),('/search/movie','query=x&append_to_response=keywords')]:
   with self.assertRaises(InvalidRequest):tmdb_validate(path,q)
class MovieWorkerCache(unittest.TestCase):
 def test_verified_cache_preserves_only_central_matches(self):
  import tempfile,json
  from unittest.mock import patch
  from us_api_worker import Worker
  c=MovieContract().candidate();body=dict(query='Фильмы про черепах',candidates=[c],requested_type='film')
  response={'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps({'matches':[dict(id=1,reason='Главная героиня — черепаха',evidence='sea turtle',topic_role='central')]})}]}]}
  with tempfile.TemporaryDirectory() as folder, patch('us_api_worker.request_json',return_value=response) as call:
   worker=Worker({'openai_api_key':'test-placeholder'},folder)
   first=worker.verify_movies(body);second=worker.verify_movies(body)
   self.assertEqual(first,second);self.assertEqual(len(first['matches']),1);self.assertEqual(call.call_count,1)
   self.assertEqual(call.call_args.args[2]['model'],'gpt-4.1')

if __name__=='__main__':unittest.main()
