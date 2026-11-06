import {test} from 'node:test';import assert from 'node:assert/strict';import {filterProperties,priceFor,compareSet,safeUrl} from '../dist/assets/model.mjs';
const base={id:'a',name:'A',address:'',subtitle:'',station:'สามย่าน',category:'short',availability:'advertised',offers:[{months:3,price:11000},{months:6,price:10000}],rank:1};const f={budget:10000,tab:'all',sort:'recommended'};
test('annual/indicative rates never become short term rates',()=>assert.equal(priceFor({...base,offers:[],indicativePrice:5000}),null));
test('3 month budget does not silently use six month discount',()=>assert.equal(filterProperties([base],{...f,tab:'short'}).length,0));
test('unknown walking distance never passes verified filter',()=>assert.equal(filterProperties([base],{...f,walk:'verified500'}).length,0));
test('full properties excluded from default results',()=>assert.equal(filterProperties([{...base,availability:'full'}],f).length,0));
test('comparison caps at 3 and toggle removes',()=>{assert.deepEqual(compareSet(['a','b','c'],'d'),['a','b','c']);assert.deepEqual(compareSet(['a','b'],'a'),['b']);});
test('reject javascript source URL',()=>assert.equal(safeUrl('javascript:alert(1)'),'#'));
test('search works with Thai station names',()=>assert.equal(filterProperties([base],{...f,query:'สามย่าน'}).length,1));
