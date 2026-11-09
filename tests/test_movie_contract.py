import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'integrations/server'))
from movie_contract import validate,verified
from tmdb_proxy import validate as tmdb_validate,InvalidRequest
class MovieContract(unittest.TestCase):
 def candidate(self):return dict(id=1,title='Черепаха',original_title='Turtle',year='2009',runtime=80,overview='A sea turtle travels across the ocean.',keywords=['sea turtle'],genres=['Documentary'],original_language='en')
 def test_no_invented_or_duplicate_ids(self):
  for ids in ([2],[1,1]):
   with self.assertRaises(ValueError):verified({'matches':[dict(id=i,reason='Фильм про черепаху',evidence='sea turtle') for i in ids]},[self.candidate()])
 def test_unsupported_evidence_removed_not_replaced(self):
  self.assertEqual(verified({'matches':[dict(id=1,reason='Про черепах',evidence='a completely invented description')]},[self.candidate()])['matches'],[])
 def test_accept_real_evidence_and_allow_fewer_than_three(self):
  result=verified({'matches':[dict(id=1,reason='Главный герой — морская черепаха',evidence='A sea turtle travels')]},[self.candidate()]);self.assertEqual(len(result['matches']),1)
  self.assertEqual(verified({'matches':[]},[self.candidate()])['matches'],[])
 def test_reject_unbounded_or_injected_metadata(self):
  for body in [dict(query='черепахи',url='http://x'),dict(query='черепахи',candidates=[dict(self.candidate(),overview='x'*2501)]),dict(query='черепахи',candidates=[self.candidate()]*7)]:
   with self.assertRaises(ValueError):validate(body)
 def test_tmdb_append_restricted(self):
  self.assertIn('append_to_response=keywords',tmdb_validate('/movie/1','language=ru-RU&append_to_response=keywords')[0])
  for path,q in [('/movie/1','append_to_response=videos'),('/search/movie','query=x&append_to_response=keywords')]:
   with self.assertRaises(InvalidRequest):tmdb_validate(path,q)
if __name__=='__main__':unittest.main()
