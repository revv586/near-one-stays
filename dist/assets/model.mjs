export const stations=['หัวลำโพง','สามย่าน','สีลม','ลุมพินี','คลองเตย','ศูนย์ฯ สิริกิติ์','สุขุมวิท'];
export const kinds={apartment:'หอพัก / อพาร์ตเมนต์',condo:'คอนโด',capsule:'แคปซูล',hostel:'ห้องพัก / โฮสเทล'};
export function validOffer(o){return Number.isInteger(o.months)&&o.months>0&&Number.isFinite(o.price)&&o.price>0;}
export function offersFor(p,term='all'){return (p.offers||[]).filter(o=>validOffer(o)&&(term==='all'||term==='short'&&o.months<=4||term==='six'&&o.months===6));}
export function priceFor(p,term='all'){const a=offersFor(p,term);return a.length?Math.min(...a.map(o=>o.price)):null;}
export function bestOffer(p,term='all'){return offersFor(p,term).sort((a,b)=>a.price-b.price)[0]||null;}
export function eligible(p){return p.category!=='excluded'&&p.availability!=='full';}
export function filterProperties(list,f){return list.filter(p=>{
 if(f.tab==='excluded'?!(!eligible(p)):!eligible(p))return false;
 if(f.tab==='lead'&&p.category!=='lead')return false;
 if(f.tab==='short'&&!offersFor(p,'short').length)return false;
 if(f.tab==='six'&&!offersFor(p,'six').length)return false;
 if(f.tab==='alternative'&&p.category!=='alternative')return false;
 const term=['short','six'].includes(f.tab)?f.tab:f.term||'all';
 const price=priceFor(p,term);
 if(price!==null&&price>f.budget)return false;
 if(f.onlyKnown&&price===null)return false;
 if(f.term&&f.term!=='all'&&!offersFor(p,f.term).length)return false;
 if(f.station&&p.station!==f.station)return false;
 if(f.privateOnly&&p.bathroom!=='private')return false;
 if(f.kinds?.length&&!f.kinds.includes(p.kind))return false;
 if(f.walk==='verified500'&&!(p.walkingVerified&&p.walkingMeters<=500))return false;
 if(f.walk==='verified800'&&!(p.walkingVerified&&p.walkingMeters<=800))return false;
 if(f.query&&!`${p.name} ${p.address} ${p.station} ${p.subtitle}`.toLowerCase().includes(f.query.toLowerCase()))return false;
 return true;
 }).sort((a,b)=>f.sort==='asc'?(priceFor(a,['short','six'].includes(f.tab)?f.tab:f.term)||Infinity)-(priceFor(b,['short','six'].includes(f.tab)?f.tab:f.term)||Infinity):f.sort==='desc'?(priceFor(b,['short','six'].includes(f.tab)?f.tab:f.term)||-Infinity)-(priceFor(a,['short','six'].includes(f.tab)?f.tab:f.term)||-Infinity):f.sort==='stops'?a.stops-b.stops||a.rank-b.rank:a.rank-b.rank);}
export function safeUrl(url){try{const u=new URL(url);return u.protocol==='https:'||u.protocol==='http:'?u.href:'#';}catch{return '#';}}
export function compareSet(ids,id){if(ids.includes(id))return ids.filter(x=>x!==id);return ids.length>=3?ids:[...ids,id];}
