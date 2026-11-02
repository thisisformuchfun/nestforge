import fs from 'node:fs/promises';
import {extractZipEntry} from '../dist/zip-download.js';
const root=new URL('../dist/',import.meta.url);const catalog=JSON.parse(await fs.readFile(new URL('catalog.json',root)));
let count=0;
for(const d of catalog){
 const folder=new URL(`models/${d.id}/`,root);const plan=JSON.parse(await fs.readFile(new URL('print-plan.json',folder)));
 const archive=await fs.readFile(new URL(`${d.id}-X1C.zip`,folder));const buffer=archive.buffer.slice(archive.byteOffset,archive.byteOffset+archive.byteLength);
 for(const p of plan.plates){
  const plate=await extractZipEntry(buffer,`${d.id}/${p.file}`);
  const settings=JSON.parse(new TextDecoder().decode(await extractZipEntry(plate.buffer,'Metadata/project_settings.config')));
  if(settings.printer_model!=='Bambu Lab X1 Carbon')throw Error('Plate mismatch');
  if(d.camera_system&&!settings.filament_type.every(t=>t==='ASA'))throw Error('ASA preset missing');
  count++;
 }
}
console.log(`${count} native 3MF plates extracted successfully using the website download code.`);
