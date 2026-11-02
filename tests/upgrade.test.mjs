import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';
import {filterCatalog,plural,designIdFromHash} from '../dist/catalog-tools.js';
import {matchColors,buildShoppingSummary,cameraKit,safeStoreUrl,snapshotDate} from '../dist/sourcing-model.js';
import {validShortlist,toggleShortlist} from '../dist/shortlist-state.js';
import {crc32,extractZipEntry} from '../dist/zip-download.js';
import {setupNatureAudio} from '../dist/nature-audio.js';
const root=new URL('../dist/',import.meta.url);
const read=async file=>JSON.parse(await fs.readFile(new URL(file,root),'utf8'));
const catalog=await read('catalog.json'),summary=await read('print-plan-summary.json'),evidence=await read('sourcing-data.json'),editorial=await read('editorial-data.json');

test('Default discovery shows all 37 no-camera designs, and no camera kits',()=>{const d=filterCatalog(catalog,summary);assert.equal(d.length,37);assert(d.every(x=>!x.camera_system));});
test('Explicit camera opt-in preserves all 47 existing designs',()=>{assert.equal(filterCatalog(catalog,summary,{includeCameras:true}).length,47);});
test('Every family filter is exact and does not introduce cameras',()=>{for(const family of new Set(catalog.map(d=>d.family))){assert(filterCatalog(catalog,summary,{family}).every(d=>d.family===family&&!d.camera_system));}});
test('Search is case-insensitive and matches multiple terms',()=>{assert.deepEqual(filterCatalog(catalog,summary,{query:' SCANDINAVIAN  CABIN '}).map(d=>d.id),['scandinavian-cabin']);});
test('One-plate and two-plate budgets use actual source counts',()=>{for(const n of [1,2]){const found=filterCatalog(catalog,summary,{maxPlates:n});assert(found.length>0);assert(found.every(d=>summary[d.id].plate_count<=n));}});
test('Unknown plate counts never satisfy a one-plate promise',()=>{assert.equal(filterCatalog(catalog,{}, {maxPlates:1}).length,0);});
test('Empty searches yield an empty state instead of unrelated products',()=>{assert.equal(filterCatalog(catalog,summary,{query:'no-such-design-xyz'}).length,0);});
test('Sorting is deterministic and does not mutate the catalog',()=>{const before=catalog.map(d=>d.id);const d=filterCatalog(catalog,summary,{sort:'plates'});assert(d.every((x,i)=>!i||summary[d[i-1].id].plate_count<=summary[x.id].plate_count));assert.deepEqual(catalog.map(d=>d.id),before);});
test('Grammar and malformed hash handling do not fail the collection',()=>{assert.equal(plural(1,'plate'),'1 plate');assert.equal(plural(2,'piece'),'2 pieces');assert.equal(designIdFromHash('#bad%zz'),'');assert.equal(designIdFromHash('#fairy-tale-turret'),'fairy-tale-turret');});
test('Every design has robust full-spool sourcing with dated direct links',()=>{for(const d of catalog){const matches=matchColors(d,evidence);assert(matches.length>0);for(const m of matches){assert(m.primary);assert(safeStoreUrl(m.primary.url));assert.equal(m.primary.material,'ASA');assert.equal(m.primary.filament_weight_kg,1);assert.match(snapshotDate(m.primary,evidence),/^2026-10-(20|23)$/);}}});
test('No available ASA does not crash or fabricate an estimate',()=>{const copy=structuredClone(evidence);for(const b of copy.filaments.brands)for(const v of b.variants)v.available=false;const matches=matchColors(catalog[0],copy);assert(matches.every(m=>m.primary===null));const sum=buildShoppingSummary(matches,null);assert.equal(sum.complete,false);assert.equal(sum.total,null);});
test('Reinforced and non-1kg offers are never silently substituted',()=>{const copy=structuredClone(evidence);for(const b of copy.filaments.brands)for(const v of b.variants){v.material='ASA-CF';v.filament_weight_kg=3;}assert(matchColors(catalog[0],copy).every(m=>m.primary===null));});
test('Missing camera prices make the total incomplete, not cheaper',()=>{const d=catalog.find(d=>d.camera_system),matches=matchColors(d,evidence);assert.equal(buildShoppingSummary(matches,null,true).complete,false);});
test('Required lens cost comes from data, never the old hard-coded $9.98',()=>{const c=structuredClone(evidence.camera_evidence.cameras.find(c=>c.id==='wyze-battery-cam-pro'));c.optics.usd=17.25;assert.equal(cameraKit(c).total,89.98+17.25);c.optics.usd=null;assert.equal(cameraKit(c).total,null);});
test('Duplicate matched spools count once, not once per design color',()=>{const matches=matchColors(catalog[0],evidence);const m=matches[0];const sum=buildShoppingSummary([m,m],null);assert.equal(sum.spools.length,1);assert.equal(sum.total,m.primary.price_usd);});
test('Unknown, negative, non-finite and unsafe offers are rejected',()=>{assert.equal(safeStoreUrl('javascript:alert(1)'),null);assert.equal(safeStoreUrl('https://user:secret@example.com'),null);const copy=structuredClone(evidence);for(const b of copy.filaments.brands)for(const v of b.variants)v.price_usd=-1;assert(matchColors(catalog[0],copy).every(m=>m.primary===null));});
test('All four concepts remain distinct from printable catalog records',()=>{assert.equal(editorial.concepts.length,4);for(const c of editorial.concepts){assert(!catalog.some(d=>d.id===c.id));assert(c.tests.length>=3);assert(c.related.every(id=>catalog.some(d=>d.id===id&&!d.camera_system)));}assert.equal(new Set(editorial.concepts.map(c=>c.feeding)).size,4);});
test('Shortlist rejects corrupt storage and unknown IDs; toggles without duplicates',()=>{const ids=editorial.concepts.map(c=>c.id);assert.deepEqual(validShortlist('bad json',ids),[]);assert.deepEqual(validShortlist(JSON.stringify([ids[0],ids[0],'fake']),ids),[ids[0]]);assert.deepEqual(toggleShortlist([ids[0]],ids[0],ids),[]);assert.deepEqual(toggleShortlist([],'fake',ids),[]);});
function zipStored(payload,name='plate.3mf'){
 const enc=new TextEncoder(),n=enc.encode(name),size=payload.length;const bytes=new Uint8Array(30+n.length+size+46+n.length+22),v=new DataView(bytes.buffer),central=30+n.length+size,end=central+46+n.length;
 v.setUint32(0,0x04034b50,true);v.setUint32(14,crc32(payload),true);v.setUint32(18,size,true);v.setUint32(22,size,true);v.setUint16(26,n.length,true);bytes.set(n,30);bytes.set(payload,30+n.length);
 v.setUint32(central,0x02014b50,true);v.setUint32(central+16,crc32(payload),true);v.setUint32(central+20,size,true);v.setUint32(central+24,size,true);v.setUint16(central+28,n.length,true);bytes.set(n,central+46);
 v.setUint32(end,0x06054b50,true);v.setUint16(end+8,1,true);v.setUint16(end+10,1,true);v.setUint32(end+12,46+n.length,true);v.setUint32(end+16,central,true);return bytes.buffer;
}
test('CRC32 agrees with the standard check vector',()=>{assert.equal(crc32(new TextEncoder().encode('123456789')),0xcbf43926);});
test('Stored ZIP extraction preserves the exact original bytes',async()=>{const payload=new TextEncoder().encode('native plate bytes');assert.deepEqual(await extractZipEntry(zipStored(payload),'plate.3mf'),payload);});
test('Corrupt same-length plate bytes are blocked before download',async()=>{const buffer=zipStored(new TextEncoder().encode('unchanged'));new Uint8Array(buffer)[41]^=1;await assert.rejects(extractZipEntry(buffer,'plate.3mf'),/checksum/);});
test('Truncated and missing ZIP entries fail safely',async()=>{await assert.rejects(extractZipEntry(new ArrayBuffer(5),'x'),/missing/);await assert.rejects(extractZipEntry(zipStored(new Uint8Array([1])),'absent'),/not found/);});

test('Actual selectDesign source cannot overwrite new sourcing after a delayed old model',async()=>{
 const code=await fs.readFile(new URL('app.js',root),'utf8');const fn=code.slice(code.indexOf('async function selectDesign'),code.indexOf('async function downloadSTL'));
 const elements=new Map(),el=key=>{if(!elements.has(key))elements.set(key,{hidden:false,textContent:'',href:'',innerHTML:'',checked:false,replaceChildren(){},append(){},focus(){this.focused=true;}});return elements.get(key);};
 const a={id:'first',name:'First',family:'Originals',description:'First',parts:[{}]},b={id:'second',name:'Second',family:'Originals',description:'Second',parts:[{}]};
 const pending=new Map(),sourceCalls=[],noop=()=>{},state={catalog:[a,b],includeCameras:false};
 const context={state,$:el,clearPrintPlates:noop,experience:{classList:{add:noop}},renderAvailable:false,renderCredits:noop,bounds:()=>({size:[1,2,3]}),printSummary:{},plural,colors:()=>[],renderParts:noop,renderAssembly:noop,renderPrintPlates:noop,url:(d,f)=>`${d.id}/${f}`,setPane:noop,productPageIds:[],renderCards:noop,history:{replaceState:noop},renderSourcing:d=>sourceCalls.push(d.id),showScene:ds=>new Promise(resolve=>pending.set(ds[0].id,resolve)),renderFamilies:noop};
 vm.createContext(context);vm.runInContext(fn+'\nthis.selectDesign=selectDesign;',context);
 const first=context.selectDesign('first');const second=context.selectDesign('second');pending.get('second')();await second;pending.get('first')();await first;
 assert.deepEqual(sourceCalls,['first','second']);assert.equal(state.selected.id,'second');assert.equal(el('#detail-name').textContent,'Second');
});
test('Nature audio stays silent on ordinary interaction and preserves zero volume',async()=>{
 const old={document:globalThis.document,Audio:globalThis.Audio,localStorage:globalThis.localStorage};const nodes=new Map(['#sound-toggle','#sound-volume','#sound-status'].map(id=>[id,{setAttribute(){}}])),listeners=[];let played=0;
 globalThis.document={querySelector:s=>nodes.get(s),addEventListener:type=>listeners.push(type),hidden:false};globalThis.localStorage={getItem:k=>k==='nestforge-volume'?'0':null,setItem(){}};globalThis.Audio=class{constructor(){this.volume=1;}async play(){played++;}pause(){}addEventListener(){}};
 try{const audio=setupNatureAudio();assert.equal(audio.audio.volume,0);assert.equal(played,0);assert(!listeners.includes('pointerdown')&&!listeners.includes('keydown'));nodes.get('#sound-toggle').onclick();await Promise.resolve();assert.equal(played,1);assert.equal(audio.enabled,true);}finally{Object.assign(globalThis,old);}
});
