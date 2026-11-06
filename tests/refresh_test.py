import unittest,sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from refresh import extract_renthub,extract_zmyhome,apply,discovery_candidates,discovery
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
class ZmyHomeTests(unittest.TestCase):
 def test_property_rates_are_not_short_contract_offers(self):
  html='<h1>ห้องพัก A</h1><h5>14 พระราม4</h5><h3>ข้อมูลอพาร์ทเม้นท์</h3>ระยะเวลาในการเช่า รายเดือน ค่าน้ำ 21บาท ต่อหน่วย ค่าไฟ 8บาท ต่อหน่วย ค่าบริการอื่นๆ 0.00<h3>ประเภทห้อง</h3>1 Bedroom 20 ตร.ม. 1 นอน 1 น้ำ 6,500 - 8,500 บาท/เดือน<h3>Facility</h3>MRT ศูนย์ฯสิริกิติ์ (0.2 กม.)<h3>อพาร์ทเม้นท์ใกล้เคียง</h3><h2>ห้องอื่น</h2>500 บาท/เดือน'
  out=extract_zmyhome(html)
  self.assertEqual(out['indicativePrice'],6500);self.assertEqual(out['rates'],[])
  self.assertEqual(out['distances'],[{'station':'ศูนย์ฯ สิริกิติ์','websiteMeters':200}])
  self.assertEqual(out['fees']['electric'],'8บาท ต่อหน่วย')
  self.assertNotIn('ห้องอื่น',out['roomText'])
 def test_zmyhome_discovery_queues_unverified_leads_only(self):
  html='<article><a href="/apartment/12"><img></a><h2>ห้องพัก A</h2><span class="current">6,000 - 8,000</span></article><article><a href="/apartment/13"></a><h2>หอพักสตรี</h2><span class="current">4,000</span></article><article><a href="/apartment/14"></a><h2>ห้องเกินงบ</h2><span class="current">12,000</span></article>'
  out=discovery_candidates(html,{'parser':'zmyhome','source':'ZmyHome','station':'คลองเตย','url':'https://zmyhome.com/search/apartment'})
  self.assertEqual(len(out),1);self.assertEqual(out[0]['url'],'https://zmyhome.com/apartment/12')
  self.assertFalse(out[0]['verified']);self.assertTrue(out[0]['geographyUnverified'])
  self.assertNotIn('websiteMeters',out[0])
 def test_women_only_is_detected_from_property_not_nearby_ad(self):
  html='<h1>หอพัก A</h1><h3>ข้อมูลอพาร์ทเม้นท์</h3>ประเภทโครงการ หอพัก<h3>ประเภทห้อง</h3>Studio 5,000บาท/เดือน<h3>Facility</h3><h3>อพาร์ทเม้นท์ใกล้เคียง</h3>หอพักสตรี'
  self.assertFalse(extract_zmyhome(html)['womenOnly'])
  self.assertTrue(extract_zmyhome(html.replace('หอพัก A','หอพักสตรี A'))['womenOnly'])
if __name__=='__main__':unittest.main()
