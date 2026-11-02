"""Remove redundant STEP/GLB copies from web print packs; CAD has its own link."""
from pathlib import Path
import json,os,zipfile,html
ROOT=Path(__file__).resolve().parents[1]/'dist'
old='STL parts in assembly coordinates; STEP solids and assembly; color-assigned 3MF plates;'
new='STL parts in assembly coordinates; color-assigned 3MF plates;'
old2='<b>assembly.glb</b> for viewing.'
new2='Editable assembly STEP is a separate CAD download in the gallery. The complete collection bundle also contains all individual STEP solids.'
def guide(data):
 return data.decode().replace(old,new).replace(old2,new2).encode()
catalog=json.loads((ROOT/'catalog.json').read_text())
for d in catalog:
 folder=ROOT/'models'/d['id'];target=folder/(d['id']+'-X1C.zip');temp=target.with_suffix('.web.zip')
 step=folder/(d['id']+'.step');cad=folder/(d['id']+'-STEP.zip')
 if step.exists():
  with zipfile.ZipFile(cad,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:z.write(step,step.name)
  with zipfile.ZipFile(cad) as z:assert z.testzip() is None and z.read(step.name)==step.read_bytes()
  step.unlink()
 assert cad.is_file()
 d['cad_download']=cad.name
 # A multicolor part is displayed from its region meshes. Compress its
 # separate full-part STL download instead of storing the same surface twice.
 for part in d['parts']:
  if any(r['file']==part['file'] for r in part.get('regions',[part])):continue
  stl=folder/part['file'];partzip=folder/(Path(part['file']).stem+'-STL.zip')
  if stl.exists():
   with zipfile.ZipFile(partzip,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:z.write(stl,stl.name)
   with zipfile.ZipFile(partzip) as z:assert z.testzip() is None and z.read(stl.name)==stl.read_bytes()
   stl.unlink()
  assert partzip.is_file()
  part['download']=partzip.name
 with zipfile.ZipFile(target) as source,zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as out:
  for entry in source.infolist():
   if Path(entry.filename).suffix in ['.step','.glb']:continue
   data=source.read(entry.filename)
   if Path(entry.filename).name=='PRINT-GUIDE.html':data=guide(data)
   out.writestr(entry.filename,data)
 with zipfile.ZipFile(temp) as z:assert z.testzip() is None
 os.replace(temp,target)
 p=folder/'PRINT-GUIDE.html';p.write_bytes(guide(p.read_bytes()))
for target in (ROOT/'downloads').glob('NestForge-*-Prints-R2.zip'):target.unlink()
(ROOT/'catalog.json').write_text(json.dumps(catalog,separators=(',',':')))
# This old collection is unlinked and superseded by the six R2 downloads.
(ROOT/'downloads/NestForge-Collection-R1.zip').unlink(missing_ok=True)
order=['Castles','Originals','World architecture','Game day','Whimsical','Future habitats']
cards=''
for family in order:
 links=''.join('<li><a href="../models/'+d['id']+'/'+d['id']+'-X1C.zip" download>'+html.escape(d['name'])+' <span>Print pack ↓</span></a> <a class="cad" href="../models/'+d['id']+'/'+d['cad_download']+'" download>STEP ZIP ↓</a></li>' for d in catalog if d['family']==family)
 cards+='<article><h2>'+html.escape(family)+'</h2><ul>'+links+'</ul></article>'
(ROOT/'downloads/index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NestForge R2 — print library</title><style>body{max-width:1100px;margin:60px auto;padding:0 24px;font:16px/1.6 system-ui;background:#0b211e;color:#e9eddc}h1{font-size:48px;line-height:1.1}a{color:inherit}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}article{padding:25px;border:1px solid #4b6458;border-radius:18px;background:#17392e}ul{list-style:none;padding:0}li{padding:12px 0;border-top:1px solid #345448}li>a:first-child{display:flex;justify-content:space-between;gap:12px;text-decoration:none}span,.cad{font-size:12px;color:#94e0c0;white-space:nowrap}.cad{display:block;margin-top:3px}a:hover{color:#b8ffdd}small{color:#adbbb2}</style><body><a href="../">← Back to the 3D garden</a><h1>Print a little world.</h1><p>37 rebuilt designs. Print packs contain arranged native X1C plates, STL parts, assembly notes and source. Editable assembly STEP is a separate ZIP download.</p><section>'+cards+'</section><p><a href="NestForge-CAD-Source.zip" download>Download all editable CadQuery source ↓</a></p><small>R2 digital prototypes · At most four colors per plate · Open and slice in Bambu Studio. Physical snap/load/seed-flow trials remain required.</small></body></html>')
print('Prepared 37 web print packs and compressed STEP downloads; duplicate family archives removed.')
