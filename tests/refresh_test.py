import unittest,sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from refresh import extract_renthub,apply,discovery_candidates,discovery
from unittest.mock import patch
class RefreshTests(unittest.TestCase):
 def page(self,t):
  return '<script id="__NEXT_DATA__">'+json.dumps({'props':{'pageProps':{'listing':{'id':1,'price':{'monthly':{'minPrice':5000},'shortTerm':t},'rooms':[],'description':'ห้องพัก'}}}})+'</script>'
 def test_annual_only_never_becomes_short_rate(self):self.assertEqual(extract_renthub(self.page({'shortContract':False}))['rates'],[])
 def test_explicit_contracts_only(self):
  r=extract_renthub(self.page({'shortContract':True,'oneMonth':{'shortContract':True,'minPrice':11000},'sixMonth':{'shortContract':True,'minPrice':9000}}))
  self.assertEqual([(x['months'],x['price']) for x in r['rates']],[(1,11000),(6,9000)])
 def test_changed_source_requires_review(self):
  p={'id':'x','offers':[{'months':6,'price':5000}],'sourceFingerprint':'old','availability':'full'};changes=[]
  apply(p,{'fingerprint':'new','rates':[],'allFull':False},'2026-11-06',changes)
  self.assertTrue(p['needsReview']);self.assertEqual(p['availability'],'full');self.assertEqual(p['offers'][0]['price'],5000);self.assertEqual(len(changes),1)
 def test_empty_rooms_not_treated_as_full(self):self.assertFalse(extract_renthub(self.page({}))['allFull'])
 def test_discovery_rejects_far_overbudget_and_women_only(self):
  def listing(id,name,price,distance):return {'id':id,'name':name,'slug':str(id),'coverPicture':'/photo.jpg','price':{'monthly':{'minPrice':price}},'distance':distance}
  entries=[listing(1,'ห้อง A',7000,450),listing(2,'ไกล',5000,801),listing(3,'แพง',12000,200),listing(4,'หอพักหญิง',4000,200),listing(5,'ไม่ระบุราคา',0,200)]
  page='<script id="__NEXT_DATA__">'+json.dumps({'props':{'pageProps':entries}})+'</script>'
  result=discovery_candidates(page,{'source':'RentHub','parser':'renthub','station':'ลุมพินี'})
  self.assertEqual([v['listingId'] for v in result],['1']);self.assertFalse(result[0]['verified']);self.assertTrue(result[0]['geographyUnverified'])
 def test_same_building_alias_does_not_reappear_in_queue(self):
  data={'properties':[{'name':'PS House','sourceUrl':'https://www.renthub.in.th/ps','sourceListingId':'1','additionalSources':[{'url':'https://www.renthub.in.th/other-name','listingId':'2'}]}]}
  candidates=[{'name':'other-name','url':'https://www.renthub.in.th/changed-slug','listingId':'2'}]
  with patch('refresh.allowed_by_robots',return_value=True),patch('refresh.fetch',return_value='page'),patch('refresh.discovery_candidates',return_value=candidates):discovery(data)
  self.assertEqual(data['reviewQueue'],[])
 def test_hongpak_links_are_leads_not_verified_rooms(self):
  result=discovery_candidates('<article><a href="/rooms/123-room">ห้องพัก A</a><span class="distance">ใกล้ MRT สามย่าน 0.5 กม.</span><div class="price">7,000 บาท/เดือน</div></article><article><a href="/rooms/999">โฆษณาไกล</a><span class="distance">2.3 กม.</span><div class="price">6,000 บาท/เดือน</div></article>',{'parser':'hongpak','source':'Hongpak','url':'https://www.hongpak.in.th/search','station':'สามย่าน'})
  self.assertEqual(len(result),1);self.assertEqual(result[0]['url'],'https://www.hongpak.in.th/rooms/123-room');self.assertFalse(result[0]['verified'])
if __name__=='__main__':unittest.main()
