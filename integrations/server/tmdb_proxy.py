"""Fixed TMDB metadata/poster requests; never an arbitrary URL proxy."""
import collections,json,re,threading,time,urllib.parse,urllib.request,urllib.error
class TmdbError(Exception):pass
class InvalidRequest(ValueError):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args):return None

def validate(path,query):
 poster=re.fullmatch(r'/poster/([A-Za-z0-9_-]+\.jpg)',path)
 if poster:
  if query:raise InvalidRequest()
  return 'https://image.tmdb.org/t/p/w342/'+poster[1],True
 if not re.fullmatch(r'/(search/movie|discover/movie|movie/[0-9]{1,10})',path):raise InvalidRequest()
 try:q=urllib.parse.parse_qs(query,keep_blank_values=True,strict_parsing=True,max_num_fields=12)
 except ValueError:raise InvalidRequest() from None
 allowed={'language','include_adult','query','year','sort_by','vote_count.gte','with_genres','without_genres','with_runtime.lte','with_original_language'}
 if set(q)-allowed or any(len(v)!=1 or len(v[0])>180 for v in q.values()):raise InvalidRequest()
 for k,v in q.items():
  value=v[0]
  if k=='language' and value!='ru-RU':raise InvalidRequest()
  if k=='include_adult' and value!='false':raise InvalidRequest()
  if k=='sort_by' and value!='popularity.desc':raise InvalidRequest()
  if k in ('year','vote_count.gte','with_runtime.lte') and not re.fullmatch(r'[0-9]{1,4}',value):raise InvalidRequest()
  if k in ('with_genres','without_genres') and not re.fullmatch(r'(?:[0-9]{1,5}(?:,[0-9]{1,5})*)?',value):raise InvalidRequest()
  if k=='with_original_language' and not re.fullmatch('[a-z]{2}',value):raise InvalidRequest()
 if path=='/search/movie' and not q.get('query',[''])[0].strip():raise InvalidRequest()
 return 'https://api.themoviedb.org/3'+path+'?'+urllib.parse.urlencode({k:v[0] for k,v in q.items()}),False

class Tmdb:
 def __init__(self,credential,relay_authorization=None):
  self.credential=credential;self.relay=relay_authorization;self.cache=collections.OrderedDict();self.lock=threading.Lock();self.retry={}
 def get(self,path,query):
  url,poster=validate(path,query);key=(path,query);now=time.monotonic()
  with self.lock:
   saved=self.cache.get(key)
   if saved and now<saved[0]:self.cache.move_to_end(key);return saved[1:]
  headers={'User-Agent':'ProskurninTV/1.18'}
  if not poster:
   if re.fullmatch('[0-9a-fA-F]{32}',self.credential):url+='&'+urllib.parse.urlencode({'api_key':self.credential})
   else:headers['Authorization']='Bearer '+self.credential
  route='ru' if self.relay else 'us'
  try:
   if now<self.retry.get(poster,0):raise TmdbError()
   body,kind=self.fetch(url,headers,poster,4)
  except TmdbError:
   if not self.relay:raise
   self.retry[poster]=now+60
   fallback='http://127.0.0.1:18888/v1/tmdb'+path+('?' +query if query else '')
   body,kind=self.fetch(fallback,{'Authorization':self.relay},poster,10);route='us'
  with self.lock:
   self.cache[key]=(time.monotonic()+(86400 if poster else 3600),body,kind,route)
   while len(self.cache)>128 or sum(len(v[1]) for v in self.cache.values())>16777216:self.cache.popitem(last=False)
  return body,kind,route
 @staticmethod
 def fetch(url,headers,poster,timeout):
  try:
   with urllib.request.build_opener(NoRedirect).open(urllib.request.Request(url,headers=headers),timeout=timeout) as r:
    b=r.read(1048577)
   if len(b)>1048576:raise TmdbError()
   if poster:
    if not b.startswith(b'\xff\xd8\xff'):raise TmdbError()
   else:
    data=json.loads(b)
    if not isinstance(data,dict):raise TmdbError()
   return b,'image/jpeg' if poster else 'application/json; charset=utf-8'
  except (OSError,ValueError):raise TmdbError() from None
