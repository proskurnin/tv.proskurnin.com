"""Public cinema card lookup, never account history or a subscription entitlement check."""
import re,urllib.parse,unicodedata,json
from html.parser import HTMLParser
PROVIDERS={
 'kinopoisk':{'hd.kinopoisk.ru':r'/film/[A-Za-z0-9-]+/?'},
 'ivi':{'ivi.tv':r'/watch/[A-Za-z0-9_-]+/?','www.ivi.tv':r'/watch/[A-Za-z0-9_-]+/?','www.ivi.ru':r'/watch/[A-Za-z0-9_-]+/?','ivi.ru':r'/watch/[A-Za-z0-9_-]+/?'},
 'okko':{'okko.tv':r'/movie/[A-Za-z0-9_-]+/?'},
 'premier':{'premier.one':r'/show/[A-Za-z0-9_-]+/?'},
 'kion':{'kion.ru':r'/(?:video|film|movie)/[A-Za-z0-9_/-]+/?'},
 'wink':{'wink.ru':r'/movies/[A-Za-z0-9_-]+/?'},
 'zona':{'www.kinopoisk.ru':r'/film/[0-9]+/?'},
}
SCHEMA={'type':'object','properties':{'url':{'type':'string'},'title':{'type':'string'},'year':{'type':'string'}},'required':['url','title','year'],'additionalProperties':False}
def validate(body):
 if not isinstance(body,dict) or set(body)!={'id','title','original_title','year','provider'}:raise ValueError('fields')
 if type(body['id']) is not int or not 0<body['id']<10**10 or body['provider'] not in PROVIDERS:raise ValueError('provider')
 if any(not isinstance(body[k],str) or not 1<=len(body[k])<=160 for k in ('title','original_title')):raise ValueError('title')
 if not isinstance(body['year'],str) or not re.fullmatch(r'(18|19|20|21)[0-9]{2}',body['year']):raise ValueError('year')
 return body

def safe_url(url,provider):
 try:
  u=urllib.parse.urlsplit(url);port=u.port
 except (ValueError,TypeError):return False
 return (isinstance(url,str) and len(url)<=1000 and u.scheme=='https' and not u.username and not u.password and port in (None,443)
         and not u.query and not u.fragment and u.hostname in PROVIDERS.get(provider,{}) and bool(re.fullmatch(PROVIDERS[provider][u.hostname],u.path)))
def normalize(text):return re.sub(r'[^\w]','',unicodedata.normalize('NFKC',text).casefold().replace('ё','е'))
def verified(body,data,response):
 if not isinstance(data,dict) or set(data)!={'url','title','year'}:raise ValueError('result')
 if not all(isinstance(data[k],str) for k in data):raise ValueError('result')
 url=data['url']
 if not url:return {'found':False}
 sources=set();searched=False
 for item in response.get('output',[]):
  if item.get('type')=='web_search_call' and item.get('status')=='completed':
   searched=True
   for source in item.get('action',{}).get('sources',[]):
    if isinstance(source,dict):sources.add(source.get('url',''))
  for part in item.get('content',[]):
   for annotation in part.get('annotations',[]):
    if annotation.get('type')=='url_citation':sources.add(annotation.get('url',''))
 if not searched or url not in sources or not safe_url(url,body['provider']):return {'found':False}
 if data['year']!=body['year'] or normalize(data['title']) not in {normalize(body['title']),normalize(body['original_title'])}:return {'found':False}
 return {'found':True,'url':url,'title':data['title'],'year':data['year'],'provider':body['provider'],'source':'public_web','entitlement_checked':False}

class MovieMetadata(HTMLParser):
 def __init__(self):super().__init__();self.active=False;self.parts=[];self.blocks=[]
 def handle_starttag(self,tag,attrs):
  if tag=='script':self.active=dict(attrs).get('type','').lower()=='application/ld+json';self.parts=[]
 def handle_data(self,data):
  if self.active:self.parts.append(data)
 def handle_endtag(self,tag):
  if tag=='script' and self.active:self.blocks.append(''.join(self.parts));self.active=False

def page_matches(body,html):
 parser=MovieMetadata();parser.feed(html)
 # Ivi exposes VideoObject without release date; use its explicit film heading,
 # never uploadDate (which is when the file reached the service).
 heading=re.search(r'<title>Фильм (.*?) \(([0-9]{4})\):',html,re.I)
 ivi_heading=body.get('provider')=='ivi' and heading and heading[2]==body['year'] and normalize(heading[1]) in {normalize(body['title']),normalize(body['original_title'])}
 def walk(value,depth=0):
  if depth>20:return False
  if isinstance(value,list):return any(walk(v,depth+1) for v in value)
  if not isinstance(value,dict):return False
  kind=value.get('@type');kinds=kind if isinstance(kind,list) else [kind]
  if 'VideoObject' in kinds and ivi_heading and normalize(str(value.get('name',''))) in {normalize(body['title']),normalize(body['original_title'])}:return True
  if 'Movie' in kinds:
   names=[value.get('name',''),value.get('alternateName','')];year=str(value.get('datePublished',''))[:4]
   if year==body['year'] and any(isinstance(n,str) and normalize(n) in {normalize(body['title']),normalize(body['original_title'])} for n in names):return True
  return any(walk(v,depth+1) for v in value.values() if isinstance(v,(dict,list)))
 for block in parser.blocks:
  try:
   if walk(json.loads(block)):return True
  except (ValueError,TypeError,RecursionError):pass
 return False
