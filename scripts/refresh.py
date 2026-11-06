#!/usr/bin/env python3
"""Read public listings. Never infer short-contract rates from annual prices."""
import concurrent.futures,datetime,functools,hashlib,html,json,os,pathlib,re,sys,time,urllib.request,urllib.parse,urllib.robotparser
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/'dist/data/listings.json'
UA='NearOneListingMonitor/1.0 (public listing research; no login)'
ALLOWED={'www.renthub.in.th','www.livinginsider.com','www.hongpak.in.th','www.thaiapartment.com','propertyhub.in.th','www.ddproperty.com','www.hipflat.co.th','zmyhome.com','www.dotproperty.co.th','baan.kaidee.com','www.ennxo.com','www.condothai.co.th'}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',s or ''))).strip()
def fetch(url,limit=6_000_000):
 p=urllib.parse.urlsplit(url)
 if p.scheme!='https' or p.hostname not in ALLOWED and not p.hostname.endswith(('renthub.in.th','livinginsider.com')):raise ValueError('URL not on public-source allowlist')
 url=urllib.parse.quote(url,safe=':/?=&%+#')
 req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/json'})
 with urllib.request.urlopen(req,timeout=22) as r:
  if urllib.parse.urlsplit(r.url).hostname!=p.hostname:raise ValueError('Unexpected cross-domain redirect')
  body=r.read(limit+1)
  if len(body)>limit:raise ValueError('Page too large')
  return body.decode('utf-8','replace')
def extract_renthub(s):
 m=re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',s,re.S)
 if not m:raise ValueError('RentHub data schema missing; review needed')
 d=json.loads(m[1])['props']['pageProps']['listing']
 rates=[]
 # Explicit shortTerm fields only; monthly is usually annual and MUST NOT be substituted.
 t=d.get('price',{}).get('shortTerm',{}) or {}
 if t.get('shortContract'):
  for k,months in [('oneMonth',1),('threeMonth',3),('sixMonth',6)]:
   v=t.get(k) or {};lo=v.get('minPrice');hi=v.get('maxPrice')
   if v.get('shortContract') and isinstance(lo,(int,float)) and lo>0:
    rates.append({'months':months,'price':lo,**({'maxPrice':hi} if hi and hi!=lo else {}),'evidence':'explicit_short_term_field'})
 rooms=d.get('rooms') or []
 cover=d.get('coverPicture')
 pictures=[v.get('pictureUrl') for v in d.get('pictures',[]) if v.get('pictureUrl')]
 if cover:pictures=[cover]+[p for p in pictures if p!=cover]
 pictures=['https://bcdn.renthub.in.th'+p if p.startswith('/') else p for p in pictures[:3]]
 stable={'rates':rates,'descriptionHash':hashlib.sha256(clean(d.get('description','')).encode()).hexdigest(),'fee':d.get('fee'),'rooms':[{'name':v.get('roomName'),'availability':v.get('availability'),'price':v.get('price')} for v in rooms]}
 return {'rates':rates,'photos':pictures,'allFull':bool(rooms) and all(v.get('availability') is False for v in rooms),'posterUpdated':d.get('updatedAt'),'fingerprint':hashlib.sha256(json.dumps(stable,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'listingId':str(d['id'])}
def extract_generic(s):
 if len(s)<2000 or re.search(r'<title>\s*(?:Access denied|Just a moment|Login)',s,re.I):raise ValueError('Blocked or login page; retaining prior facts')
 # Capture only metadata, not a guessed rent/contract from unrelated cards.
 metas=re.findall(r'<meta\b[^>]*>',s,re.I)
 photos=[]
 for tag in metas:
  if re.search(r'(?:property|name)=["\']og:image["\']',tag,re.I):
   m=re.search(r'content=["\'](.*?)["\']',tag,re.I)
   if m:photos.append(html.unescape(m[1]))
 # LivingInsider primary description metadata excludes view counts/related ads.
 descriptions=[]
 for tag in metas:
  if re.search(r'(?:property|name)=["\'](?:og:description|description)["\']',tag,re.I):
   m=re.search(r'content=["\'](.*?)["\']',tag,re.I)
   if m:descriptions.append(clean(m[1]))
 if not photos:
  photos=re.findall(r'''<img[^>]+src=["'](https://images\.thaiapartment\.com/Apartment/[^"']+)["']''',s,re.I)[:3]
 return {'photos':photos[-1:] if len(photos)==1 else photos[:3],'fingerprint':hashlib.sha256('|'.join(descriptions).encode()).hexdigest() if descriptions else None,'rates':[],'allFull':None}
def extract_zmyhome(s):
 # Read the property's own facts, excluding nearby-property cards and navigation.
 heading=re.search(r'<h[12]\b[^>]*>(.*?)</h[12]>',s,re.S|re.I)
 if not heading:raise ValueError('ZmyHome property heading missing')
 core=s[heading.start():]
 core=re.split(r'อพาร์ทเม้นท์ใกล้เคียง|อพาร์ทเมนท์ใกล้เคียง',core)[0]
 text=clean(re.sub(r'<(script|style)\b.*?</\1>','',core,flags=re.S|re.I)).split('หมายเหตุ :')[0]
 name=clean(heading[1]);address=re.search(r'<h5\b[^>]*>(.*?)</h5>',core,re.S|re.I)
 info=text.split('ข้อมูลอพาร์ทเม้นท์')[-1]
 rooms=info.split('ประเภทห้อง',1)[-1].split('Facility',1)[0]
 amounts=[int(v.replace(',','')) for v in re.findall(r'([\d,]+)\s*บาท/เดือน',rooms)]
 # A range's lower bound belongs to the same room's annual/unspecified rate.
 lows=[int(v.replace(',','')) for v in re.findall(r'([\d,]+)\s*(?:-\s*[\d,]+)?\s*บาท/เดือน',rooms)]
 nearby=re.findall(r'MRT\s*([^()]+?)\s*\(([\d.]+)\s*กม\.\)',info)
 stations={'ลุมพินี':'ลุมพินี','คลองเตย':'คลองเตย','สามย่าน':'สามย่าน','สีลม':'สีลม','หัวลำโพง':'หัวลำโพง','ศูนย์ฯสิริกิติ์':'ศูนย์ฯ สิริกิติ์','สุขุมวิท':'สุขุมวิท'}
 distances=[{'station':stations[k.strip()],'websiteMeters':round(float(v)*1000)} for k,v in nearby if k.strip() in stations]
 fees={}
 for label,key in [('ค่าน้ำ','water'),('ค่าไฟ','electric'),('ค่าอินเตอร์เน็ต','internet'),('ค่าบริการอื่นๆ','service')]:
  m=re.search(re.escape(label)+r'\s*(.*?)(?=ค่าน้ำ|ค่าไฟ|ค่าอินเตอร์เน็ต|ค่าบริการอื่นๆ|ประเภทห้อง|$)',info)
  fees[key]=m[1].strip() if m else 'ต้องสอบถาม'
 photos=list(dict.fromkeys(html.unescape(u) for u in re.findall(r'<img[^>]+src=["\'](https://image\.zmyhome\.com/apartment/[^"\']+)',core,re.I)))[:3]
 return {'name':name,'address':clean(re.sub(r'<style\b.*?</style>','',address[1],flags=re.S)) if address else '', 'roomText':rooms,'indicativePrice':min(lows) if lows else None,'distances':distances,'fees':fees,'womenOnly':bool(re.search('หอพักสตรี|หอพักหญิง|หอหญิง|Her Dorm',text,re.I)),'photos':photos,'fingerprint':hashlib.sha256(info.encode()).hexdigest(),'rates':[],'allFull':None}

@functools.lru_cache(maxsize=40)
def read_robots(origin):
 robots=origin+'/robots.txt'
 try:
  req=urllib.request.Request(robots,headers={'User-Agent':UA})
  with urllib.request.urlopen(req,timeout=10) as r:txt=r.read(400000).decode('utf-8','replace')
  rp=urllib.robotparser.RobotFileParser();rp.parse(txt.splitlines())
  return rp
 except urllib.error.HTTPError as e:
  return e.code==404
 except Exception:
  return False

def allowed_by_robots(url):
 p=urllib.parse.urlsplit(url);rp=read_robots(urllib.parse.urlunsplit((p.scheme,p.netloc,'','','')))
 return rp if isinstance(rp,bool) else rp.can_fetch(UA,urllib.parse.quote(url,safe=':/?=&%'))

def check(p):
 try:
  if not allowed_by_robots(p['sourceUrl']):raise ValueError('robots.txt unavailable or does not permit automated access')
  s=fetch(p['sourceUrl'])
  out=extract_renthub(s) if 'renthub.in.th' in p['sourceUrl'] else extract_zmyhome(s) if 'zmyhome.com/apartment/' in p['sourceUrl'] else extract_generic(s)
  return p['id'],out,None
 except Exception as e:return p['id'],None,str(e)[:180]
def image_download(url,name):
 try:
  parsed=urllib.parse.urlsplit(url)
  if parsed.scheme!='https' or not parsed.hostname.endswith(('renthub.in.th','livinginsider.com','hongpak.in.th','thaiapartment.com','zmyhome.com')):return None
  path=ROOT/'dist/assets'/name
  if not path.exists():
   req=urllib.request.Request(url,headers={'User-Agent':UA})
   with urllib.request.urlopen(req,timeout=20) as r:blob=r.read(5_000_001)
   if len(blob)>5_000_000:return None
   if not (blob.startswith(b'\xff\xd8') or blob.startswith(b'\x89PNG') or blob.startswith(b'RIFF')):return None
   path.write_bytes(blob)
  return 'assets/'+name
 except Exception:return None

def apply(p,result,at,changes):
 previous=p.get('sourceFingerprint')
 if previous and result.get('fingerprint') and previous!=result['fingerprint']:
  p['needsReview']=True
  changes.append({'at':at,'propertyId':p['id'],'kind':'source_changed','summary':'ข้อมูลราคา สัญญา หรือรายละเอียดในต้นทางเปลี่ยน โปรดตรวจเงื่อนไขก่อนจอง'})
 if result.get('rates'):
  # Annual-only and manually interpreted text offers stay curated, never fabricated.
  p['offers']=result['rates'];p['autoRatesAsOf']=at
 if result.get('allFull') is True:p['availability']='full'
 elif result.get('allFull') is False and p['availability']=='full':
  p['needsReview']=True  # Do not declare vacancy based only on a page-level flag.
 if result.get('posterUpdated'):p['posterUpdated']=result['posterUpdated']
 if result.get('fingerprint'):p['sourceFingerprint']=result['fingerprint']
 p.update(lastFetchedAt=at,checkStatus='ok',checkError=None)

class ListingLinks(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.current=None
 def handle_starttag(self,tag,attrs):
  if tag=='a':
   href=dict(attrs).get('href','')
   self.current={'url':href,'name':''} if re.search(r'(?:^|hongpak\.in\.th)/rooms/\d+',href) else None
 def handle_data(self,text):
  if self.current is not None:self.current['name']+=text+' '
 def handle_endtag(self,tag):
  if tag=='a' and self.current is not None:
   self.current['name']=clean(self.current['name']);self.links.append(self.current);self.current=None

def discovery_candidates(s,page):
 found=[]
 if page['parser']=='renthub':
  m=re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>',s,re.S)
  if not m:raise ValueError('Category schema missing')
  def walk(v):
   if isinstance(v,dict):
    if v.get('slug') and v.get('name') and v.get('coverPicture') and v.get('id'):
     lo=((v.get('price') or {}).get('monthly') or {}).get('minPrice');distance=v.get('distance')
     if isinstance(lo,(int,float)) and 0<lo<=10000 and isinstance(distance,(int,float)) and distance<=800:
      found.append({'name':v['name'],'url':'https://www.renthub.in.th/'+v['slug'],'listingId':str(v['id']),'websiteMeters':distance})
    for x in v.values():walk(x)
   elif isinstance(v,list):
    for x in v:walk(x)
  walk(json.loads(m[1])['props']['pageProps'])
 elif page['parser']=='zmyhome':
  for card in re.findall(r'<article\b[^>]*>(.*?)</article>',s,re.S|re.I):
   link=re.search(r'href=["\'](/apartment/\d+)["\']',card)
   heading=re.search(r'<h2[^>]*>(.*?)</h2>',card,re.S|re.I)
   price=re.search(r'class=["\']current["\'][^>]*>(.*?)</span>',card,re.S)
   amount=re.search(r'[\d,]+',clean(price[1])) if price else None
   if link and heading and amount and 0<int(amount[0].replace(',',''))<=10000:
    found.append({'name':clean(heading[1]),'url':urllib.parse.urljoin(page['url'],link[1]),'indicativePrice':int(amount[0].replace(',',''))})
 else:
  # Parse actual result cards, excluding navigation and distant sponsored ads.
  for card in re.findall(r'<article\b[^>]*>(.*?)</article>',s,re.S|re.I):
   dm=re.search(r'class=["\']distance["\'][^>]*>(.*?)</',card,re.S)
   pm=re.search(r'class=["\']price["\'][^>]*>(.*?)</div>',card,re.S)
   distance=re.search(r'([\d.]+)\s*(กม\.|ม\.|เมตร)',clean(dm[1])) if dm else None
   price=re.search(r'[\d,]+',clean(pm[1])) if pm else None
   if not distance or not price or 'บาท/เดือน' not in clean(pm[1]):continue
   meters=round(float(distance[1])*(1000 if distance[2]=='กม.' else 1));amount=int(price[0].replace(',',''))
   if meters>800 or not 0<amount<=10000:continue
   parser=ListingLinks();parser.feed(card)
   links=[v for v in parser.links if len(v['name'])>3]
   if links:found.append({'name':links[0]['name'],'url':urllib.parse.urljoin(page['url'],links[0]['url']),'websiteMeters':meters})
 return [dict(v,source=page['source'],station=page['station'],discoveredAt=now(),verified=False,geographyUnverified=True) for v in found if not re.search('หญิง|สตรี',v['name'])]

def discovery(data):
 # Queue only: public category membership is not a verified MRT walking route.
 known=set();known_ids=set();known_names={clean(p['name']).casefold() for p in data['properties']}
 for p in data['properties']:
  for v in [{'url':p['sourceUrl'],'listingId':p.get('sourceListingId')},*p.get('additionalSources',[])]:
   known.add(urllib.parse.unquote(v['url']).rstrip('/'))
   if v.get('listingId'):known_ids.add(str(v['listingId']))
 previous={urllib.parse.unquote(v['url']).rstrip('/'):v for v in data.get('reviewQueue',[]) if urllib.parse.unquote(v['url']).rstrip('/') not in known}
 queue={}
 pages=json.loads((ROOT/'scripts/discovery-sources.json').read_text());runs=[]
 def read(page):
  try:
   if not allowed_by_robots(page['url']):raise ValueError('robots.txt unavailable or disallows automated access')
   return page,discovery_candidates(fetch(page['url']),page),None
  except Exception as e:return page,[],str(e)[:160]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for page,candidates,error in pool.map(read,pages):
   runs.append({'source':page['source'],'station':page['station'],'url':page['url'],'checkedAt':now(),'status':'error' if error else 'ok','candidates':len(candidates),**({'error':error} if error else {})})
   if error:
    for key,v in previous.items():
     if v.get('source','RentHub')==page['source'] and v.get('station')==page['station']:queue.setdefault(key,v)
   for v in candidates:
    key=urllib.parse.unquote(v['url']).rstrip('/')
    if key in known or str(v.get('listingId','')) in known_ids or clean(v['name']).casefold() in known_names:continue
    if key not in queue:queue[key]={**v,'discoveredAt':previous.get(key,{}).get('discoveredAt',v.get('discoveredAt',now()))}
 data['reviewQueue']=list(queue.values())[-300:]
 data['discoveryRuns']=runs

def main():
 data=json.loads(DATA.read_text());changes=data.get('changes',[]);ok=0;bad=0;at=now()
 from facebook_import import merge_facebook,is_automatic_source
 merge_facebook(data)
 automatic=[p for p in data['properties'] if is_automatic_source(p)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for id,result,error in pool.map(check,automatic):
   p=next(x for x in data['properties'] if x['id']==id)
   if error:
    bad+=1;p.update(checkStatus='error',checkError=error,lastAttemptAt=at);print(id+': source unavailable; retained prior facts')
    continue
   ok+=1;apply(p,result,at,changes)
   if not p.get('photos'):
    photos=[]
    for i,url in enumerate(result.get('photos',[])[:3]):
     local=image_download(url,f'{id}-{i}.jpg')
     if local:photos.append({'url':local,'sourceUrl':url,'credit':p['sourceName']})
    if photos:p['photos']=photos
 if '--discover' in sys.argv:discovery(data)
 # Secondary sources preserve independent evidence; never overwrite the canonical room's rent.
 secondary=[(p,v) for p in data['properties'] for v in p.get('additionalSources',[]) if v.get('url') and is_automatic_source(v)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  inputs=[{'id':str(i),'sourceUrl':v['url']} for i,(p,v) in enumerate(secondary)]
  for id,result,error in pool.map(check,inputs):
   p,v=secondary[int(id)];v['lastAttemptAt']=at
   if error:v.update(checkStatus='error',checkError=error);continue
   if v.get('fingerprint') and result.get('fingerprint') and v['fingerprint']!=result['fingerprint']:p['needsReview']=True
   v.update(checkStatus='ok',lastFetchedAt=at)
   if result.get('fingerprint'):v['fingerprint']=result['fingerprint']
 data['changes']=changes[-100:];data['generatedAt']=at
 data['lastRun']={'startedAt':at,'finishedAt':now(),'success':ok,'failed':bad,'manualSkipped':len(data['properties'])-len(automatic),'discoverySuccess':sum(v['status']=='ok' for v in data.get('discoveryRuns',[])),'discoveryFailed':sum(v['status']=='error' for v in data.get('discoveryRuns',[]))}
 if os.getenv('GITHUB_ACTIONS')=='true' or os.getenv('NEARONE_SCHEDULED')=='1':
  data['schedule']={'state':'active','frequency':'hourly','note':'GitHub Actions' if os.getenv('GITHUB_ACTIONS')=='true' else 'macOS LaunchAgent'}
 temp=DATA.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2));temp.replace(DATA)
 print(f'Checked {ok+bad} sources: {ok} accessible, {bad} unavailable. Unknown facts were not promoted.')
 if '--strict' in sys.argv and ok==0:sys.exit(1)
if __name__=='__main__':main()
