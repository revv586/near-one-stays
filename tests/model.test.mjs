import {test} from 'node:test';import assert from 'node:assert/strict';import {filterProperties,priceFor,filterPriceFor,compareSet,safeUrl} from '../dist/assets/model.mjs';
const base={id:'a',name:'A',address:'',subtitle:'',station:'สามย่าน',category:'short',availability:'advertised',offers:[{months:3,price:11000},{months:6,price:10000}],rank:1};const f={budget:10000,tab:'all',sort:'recommended'};
test('annual/indicative rates never become short term rates',()=>assert.equal(priceFor({...base,offers:[],indicativePrice:5000}),null));
test('3 month budget does not silently use six month discount',()=>assert.equal(filterProperties([base],{...f,tab:'short'}).length,0));
test('unknown walking distance never passes verified filter',()=>assert.equal(filterProperties([base],{...f,walk:'verified500'}).length,0));
test('full properties excluded from default results',()=>assert.equal(filterProperties([{...base,availability:'full'}],f).length,0));
test('comparison caps at 3 and toggle removes',()=>{assert.deepEqual(compareSet(['a','b','c'],'d'),['a','b','c']);assert.deepEqual(compareSet(['a','b'],'a'),['b']);});
test('reject javascript source URL',()=>assert.equal(safeUrl('javascript:alert(1)'),'#'));
test('search works with Thai station names',()=>assert.equal(filterProperties([base],{...f,query:'สามย่าน'}).length,1));

test('budget includes indicative rates and excludes leads above the slider',()=>{
 const lead={...base,offers:[],category:'lead',indicativePrice:6500};
 assert.equal(filterProperties([lead],{...f,budget:6000}).length,0);
 assert.equal(filterProperties([lead],{...f,budget:6500}).length,1);
 assert.equal(priceFor(lead),null);
});
test('sort mixes contract and indicative prices with unknown prices last',()=>{
 const known={...base,id:'known',offers:[{months:3,price:7000}]};
 const lead={...base,id:'lead',offers:[],category:'lead',indicativePrice:5000};
 const unknown={...lead,id:'unknown',indicativePrice:null};
 const list=[unknown,known,lead];
 assert.deepEqual(filterProperties(list,{...f,sort:'asc'}).map(p=>p.id),['lead','known','unknown']);
 assert.deepEqual(filterProperties(list,{...f,sort:'desc'}).map(p=>p.id),['known','lead','unknown']);
});
test('confirmed contract price takes precedence over indicative rate',()=>{
 const p={...base,indicativePrice:5000};
 assert.equal(filterPriceFor(p,'short'),11000);
 assert.equal(filterProperties([p],{...f,tab:'short'}).length,0);
});
test('short-price-only and lease filters still exclude indicative-only leads',()=>{
 const lead={...base,category:'lead',offers:[],indicativePrice:5000};
 assert.equal(filterProperties([lead],{...f,onlyKnown:true}).length,0);
 assert.equal(filterProperties([lead],{...f,term:'short'}).length,0);
 for(const value of [0,-1,'5000',NaN,Infinity])assert.equal(filterPriceFor({...lead,indicativePrice:value}),null);
});
