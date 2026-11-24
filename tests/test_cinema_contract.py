import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'integrations/server'))
from cinema_contract import validate,verified,safe_url
class CinemaContractTest(unittest.TestCase):
 def setUp(self):
  self.body=dict(id=105,title='Назад в будущее',original_title='Back to the Future',year='1985',provider='ivi')
  self.url='https://www.ivi.ru/watch/90324'
  self.data=dict(url=self.url,title='Назад в будущее',year='1985')
  self.response={'output':[{'type':'web_search_call','status':'completed','action':{'sources':[{'url':self.url}]}}]}
 def test_real_source_and_identity_required(self):
  self.assertTrue(verified(self.body,self.data,self.response)['found'])
  self.assertFalse(verified(self.body,self.data,{'output':[]})['found'])
  self.assertFalse(verified(self.body,dict(self.data,year='1989'),self.response)['found'])
  self.assertFalse(verified(self.body,dict(self.data,title='Другой фильм'),self.response)['found'])
 def test_auth_redirects_and_unknown_hosts_rejected(self):
  for url in ['http://ivi.ru/watch/1','https://ivi.ru.evil.test/watch/1','https://ivi.ru@evil.test/watch/1','https://ivi.ru/watch/1?redirect=http://evil.test','https://ivi.ru/auth','intent://movie','https://ivi.ru:bad/watch/1']:
   self.assertFalse(safe_url(url,'ivi'),url)
 def test_no_unbounded_or_account_payload(self):
  for body in [dict(self.body,history=['private']),dict(self.body,provider='arbitrary'),dict(self.body,title='x'*161)]:
   with self.assertRaises(ValueError):validate(body)

class OfficialPageTest(unittest.TestCase):
 def test_movie_identity_must_match(self):
  from cinema_contract import page_matches
  import json
  body=dict(title='Назад в будущее',original_title='Back to the Future',year='1985')
  def html(**changes):
   data=dict({'@type':'Movie','name':'Back to the Future','datePublished':'1985-07-03'},**changes)
   return '<script type="application/ld+json">'+json.dumps(data)+'</script>'
  self.assertTrue(page_matches(body,html()))
  self.assertFalse(page_matches(body,html(datePublished='1989')))
  self.assertFalse(page_matches(body,html(name='Another film')))
  self.assertFalse(page_matches(body,html(**{'@type':'Article'})))
  self.assertFalse(page_matches(body,'Back to the Future 1985'))

 def test_ivi_video_upload_date_is_not_release_year(self):
  from cinema_contract import page_matches
  body=dict(title='Назад в будущее',original_title='Back to the Future',year='1985',provider='ivi')
  page='<title>Фильм Назад в будущее (1985): описание</title><script type="application/ld+json">{"@type":"VideoObject","name":"Назад в будущее","uploadDate":"2019-04-01"}</script>'
  self.assertTrue(page_matches(body,page))
  self.assertFalse(page_matches(body,page.replace('(1985)','(1989)')))
  self.assertFalse(page_matches(dict(body,provider='wink'),page))
