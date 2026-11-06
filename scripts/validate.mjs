import {createHash} from 'node:crypto';
import fs from 'node:fs';import assert from 'node:assert/strict';import {stations,validOffer} from '../dist/assets/model.mjs';
const data=JSON.parse(fs.readFileSync(new URL('../dist/data/listings.json',import.meta.url)));const ids=new Set();for(const p of data.properties){assert(!ids.has(p.id),'Duplicate canonical property '+p.id);ids.add(p.id);assert(stations.includes(p.station),'Station outside 3-stop corridor');assert(Math.abs(stations.indexOf(p.station)-3)===p.stops);assert(p.ownerConfirmed===false,'Owner confirmation must be explicit');assert(p.walkingVerified===false||Number.isFinite(p.walkingMeters));for(const o of p.offers)assert(validOffer(o),'Invalid contract rate');assert(new URL(p.sourceUrl).protocol==='https:');if(p.walkingVerified&&p.walkingMeters>800)assert(p.category==='excluded');for(const photo of p.photos||[])assert(fs.existsSync('dist/'+photo.url),'Missing image');}assert(data.schemaVersion===1);const sources=JSON.parse(fs.readFileSync('dist/data/sources.json'));assert(new Set(sources.sources.map(s=>s.id)).size===sources.sources.length);for(const s of sources.sources){assert(['manual','metadata','structured'].includes(s.mode));if(s.url)assert(new URL(s.url).protocol==='https:');}const pages=JSON.parse(fs.readFileSync('scripts/discovery-sources.json'));assert(pages.length>=21);assert(pages.every(p=>['renthub','hongpak','zmyhome'].includes(p.parser))); console.log('Validated '+ids.size+' properties, contract rates, corridor and image paths.');

// Give browser modules content-based filenames so a deployment cannot reuse stale code.
const digest=text=>createHash('sha256').update(text).digest('hex').slice(0,12);
const model=fs.readFileSync('dist/assets/model.mjs','utf8');
const modelName=`model-${digest(model)}.mjs`;
const app=fs.readFileSync('dist/assets/app.js','utf8').replace("'./model.mjs'",`'./${modelName}'`);
const appName=`app-${digest(app)}.js`;
fs.writeFileSync('dist/assets/'+modelName,model);
fs.writeFileSync('dist/assets/'+appName,app);
const style=fs.readFileSync('dist/assets/style.css','utf8');
const styleName=`style-${digest(style)}.css`;
fs.writeFileSync('dist/assets/'+styleName,style);
const indexPath='dist/index.html';const index=fs.readFileSync(indexPath,'utf8');
assert(/\.\/assets\/app(?:-[a-f0-9]{12})?\.js/.test(index),'Application entry missing');
assert(/\.\/assets\/style(?:-[a-f0-9]{12})?\.css/.test(index),'Stylesheet entry missing');
fs.writeFileSync(indexPath,index.replace(/\.\/assets\/app(?:-[a-f0-9]{12})?\.js/g,'./assets/'+appName).replace(/\.\/assets\/style(?:-[a-f0-9]{12})?\.css/g,'./assets/'+styleName));
for(const name of fs.readdirSync('dist/assets')){
 if(/^(?:app-[a-f0-9]{12}\.js|model-[a-f0-9]{12}\.mjs|style-[a-f0-9]{12}\.css)$/.test(name)&&![modelName,appName,styleName].includes(name))fs.unlinkSync('dist/assets/'+name);
}
console.log('Built versioned browser modules:',appName,modelName,styleName);
