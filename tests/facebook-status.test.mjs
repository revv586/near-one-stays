import {test} from 'node:test';
import assert from 'node:assert/strict';
import {facebookSyncStatus} from '../dist/assets/model.mjs';
const now=Date.parse('2026-11-06T12:30:00Z');
const feed={lastRun:{status:'success'},groups:[{status:'ok',lastCheckedAt:'2026-11-06T12:00:00Z'},{status:'ok',lastCheckedAt:'2026-11-06T12:05:00Z'}]};
test('freshness requires both groups, not a newer global timestamp',()=>{
 assert.equal(facebookSyncStatus(feed,now).state,'fresh');
 const stale={...feed,checkedAt:'2026-11-06T12:30:00Z',groups:[feed.groups[0],{status:'ok',lastCheckedAt:'2026-11-06T10:00:00Z'}]};
 assert.equal(facebookSyncStatus(stale,now).state,'stale');
});
test('failed collection cannot display the previous success as current',()=>{
 assert.equal(facebookSyncStatus({...feed,lastRun:{status:'blocked'}},now).state,'blocked');
 assert.equal(facebookSyncStatus({...feed,groups:[feed.groups[0],{...feed.groups[1],lastRun:{status:'blocked'}}]},now).state,'blocked');
 assert.equal(facebookSyncStatus({...feed,groups:[feed.groups[0],{status:'login_required',lastCheckedAt:feed.groups[1].lastCheckedAt}]},now).state,'blocked');
});
test('missing and future group timestamps do not produce a fresh result',()=>{
 assert.equal(facebookSyncStatus({},now).state,'pending');
 assert.equal(facebookSyncStatus({...feed,groups:[feed.groups[0]]},now).state,'pending');
 assert.equal(facebookSyncStatus({...feed,groups:[feed.groups[0],{status:'ok',lastCheckedAt:'2026-11-07T12:05:00Z'}]},now).state,'pending');
});
