import fs from 'node:fs/promises';
import zlib from 'node:zlib';
import * as THREE from '../dist/vendor/build/three.module.js';
const stlSource=(await fs.readFile(new URL('../dist/vendor/jsm/loaders/STLLoader.js',import.meta.url),'utf8')).replace("from 'three'",`from '${new URL('../dist/vendor/build/three.module.js',import.meta.url).href}'`);
const {STLLoader}=await import('data:text/javascript;base64,'+Buffer.from(stlSource).toString('base64'));
const app=await fs.readFile(new URL('../dist/app.js',import.meta.url),'utf8');
const fn=app.slice(app.indexOf('function smoothSculpt('),app.indexOf('async function getGeometry('));
const smooth=new Function('THREE',fn+';return smoothSculpt;')(THREE);
const catalog=JSON.parse(await fs.readFile(new URL('../dist/catalog.json',import.meta.url)));
let count=0;
for(const d of catalog){for(const p of d.parts){for(const r of p.regions){
 if(process.argv.includes('--available')&&!r.file.endsWith('.gz'))continue;
 const packed=await fs.readFile(new URL('../dist/models/'+d.id+'/'+r.file,import.meta.url));const b=zlib.gunzipSync(packed);if(count===0){const browserBytes=new Uint8Array(await new Response(new Blob([packed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());if(!Buffer.from(browserBytes).equals(b))throw Error('Browser decompression mismatch');}let g=new STLLoader().parse(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength));
 if(d.id==='dragon-guard-citadel'&&r.file.includes('crown-region-02')){const before=g.getAttribute('position').count;g=smooth(g);if(g.index.count!==before)throw Error('Sculpt triangles changed');if(!g.getAttribute('normal').array.every(Number.isFinite))throw Error('Invalid normals');console.log('Sculpt smoothing',before,'triangle vertices →',g.getAttribute('position').count,'shared vertices');}
 g.computeBoundingBox();if(!Number.isFinite(g.boundingBox.min.x))throw Error(r.file);g.dispose();count++;
}}}
console.log('Three.js parsed',count,'compressed display meshes. WebGL/browser visual QA not performed.');
