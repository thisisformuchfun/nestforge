"""Install verified R6 Vegas designs and camera adapters, preserving R5 models."""
from pathlib import Path
import gzip, json, os, shutil, zipfile, importlib.util
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist';CAD=ROOT/'cad-source/cad'
STAGE=Path(os.environ.get('NESTFORGE_R6',str(ROOT/'cad-source/r6')))

def archive(path,entries):
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for f,name in entries:z.write(f,name)
 with zipfile.ZipFile(path) as z:assert z.testzip() is None

def install(src,dest):
 d=json.loads((src/'design.json').read_text());slug=d['id'];checks=json.loads((src/'checks.json').read_text())
 assert checks['passed'] and checks['native_bambu_studio_roundtrip'],slug
 assert (src/'.r6-packaged').exists(),slug
 dest.mkdir(parents=True,exist_ok=True);(dest/'plates').mkdir(exist_ok=True)
 for name in ['preview.png','PRINT-GUIDE.html','checks.json','assembly-checks.json','plate-layout.json','service-checks.json','camera-service-audit.json']:
  if (src/name).exists():shutil.copy2(src/name,dest/name)
 guide=dest/'PRINT-GUIDE.html'
 s=guide.read_text().replace('STL parts in assembly coordinates; STEP solids and assembly; color-assigned 3MF plates;','STL parts in assembly coordinates; color-assigned 3MF plates;').replace('<b>assembly.glb</b> for viewing.','Editable assembly STEP is supplied in the separate CAD ZIP.').replace('The GLB follows standard glTF units: metres, Y up.','')
 guide.write_text(s)
 d['cad_download']=slug+'-STEP.zip';archive(dest/d['cad_download'],[(src/(slug+'.step'),slug+'.step')])
 # Store each 3MF once. The site extracts individual entries losslessly on demand.
 names={'design.json','preview.png','PRINT-GUIDE.html','plate-layout.json','checks.json','assembly-checks.json','service-checks.json','camera-service-audit.json'}|{p['file'] for p in d['parts']}
 entries=[(dest/n if n=='PRINT-GUIDE.html' else src/n,str(Path(slug)/n)) for n in sorted(names) if (src/n).exists()]
 entries += [(f,str(Path(slug)/f.relative_to(src))) for f in sorted((src/'plates').glob('*.3mf'))]
 entries += [(f,str(Path(slug)/'sources'/f.name)) for f in CAD.iterdir() if f.suffix in ['.py','.html','.md']]
 archive(dest/(slug+'-X1C.zip'),entries)
 for p in d['parts']:
  single=any(r['file']==p['file'] for r in p.get('regions',[p]))
  p['download']=p['file']+'.gz' if single else slug+'-X1C.zip'
  if not single:p['download_scope']='build'
  for r in p['regions']:
   file=r['file'];gz=file+'.gz';(dest/gz).write_bytes(gzip.compress((src/file).read_bytes(),compresslevel=9,mtime=0));r['file']=gz
 layout=json.loads((dest/'plate-layout.json').read_text())
 for plate in layout['plates']:
  for obj in plate['objects']:
   for r in obj['regions']:r['file'] += '.gz'
 (dest/'plate-layout.json').write_text(json.dumps(layout,separators=(',',':')))
 (dest/'design.json').write_text(json.dumps(d,separators=(',',':')))
 return d

def main():
 spec=importlib.util.spec_from_file_location('plans',ROOT/'scripts/render-print-plans.py');plans=importlib.util.module_from_spec(spec);spec.loader.exec_module(plans)
 coupon_src=STAGE/'coupons/vegas-fit-coupon'
 coupon=install(coupon_src,DIST/'models/vegas-fit-coupon');plans.build(coupon)
 adapters=[]
 for src in sorted((STAGE/'adapters').glob('*/design.json')):
  folder=src.parent;d=install(folder,DIST/'models/camera-adapters'/folder.name)
  fake=dict(d,id='camera-adapters/'+d['id']);plan=plans.build(fake)
  adapters.append(dict(id=d['id'],label=d['name'],file=f'models/camera-adapters/{d["id"]}/{d["id"]}-X1C.zip',plate_image=f'models/camera-adapters/{d["id"]}/plates/plate-01-preview.webp',plate_count=plan['plate_count'],time_hours=plan['total_time_hours'],part=d['parts'][0],camera_mount=d['camera_mount']))
 assert len(adapters)==3,len(adapters)
 cat=json.loads((DIST/'catalog.json').read_text());old=[d for d in cat if d.get('family')!='Vegas camera hotels'];new=[]
 summary=json.loads((DIST/'print-plan-summary.json').read_text())
 for src in sorted((STAGE/'exports').glob('*/design.json')):
  if src.parent.name=='vegas-fit-prototype':continue
  d=install(src.parent,DIST/'models'/src.parent.name);d['camera_adapters']=adapters
  d['fit_coupon']={'file':'models/vegas-fit-coupon/vegas-fit-coupon-X1C.zip','plate_image':'models/vegas-fit-coupon/plates/plate-01-preview.webp','plate_count':1}
  new.append(d);summary[d['id']]=plans.build(d)
  (DIST/'models'/d['id']/'design.json').write_text(json.dumps(d,separators=(',',':')))
 assert len(new)==12,len(new)
 # Put the most recognizable architectural silhouettes first in the collection.
 order=['vegas-excalibur','vegas-luxor','vegas-venetian','vegas-paris','vegas-bellagio','vegas-caesars','vegas-newyork-newyork','vegas-flamingo','vegas-wynn','vegas-mirage','vegas-strat','vegas-circus-circus']
 new.sort(key=lambda d:order.index(d['id']))
 (DIST/'catalog.json').write_text(json.dumps(new+old,separators=(',',':')))
 (DIST/'print-plan-summary.json').write_text(json.dumps(summary,indent=2))
 archive(DIST/'downloads/NestForge-CAD-Source.zip',[(f,str(Path('cad')/f.relative_to(CAD))) for f in CAD.rglob('*') if f.is_file() and '__pycache__' not in str(f) and f.suffix not in ['.pyc','.png']])
 # Verify every old native plate is byte-identical in its pack, then deduplicate.
 removed=0
 for d in old:
  folder=DIST/'models'/d['id']
  with zipfile.ZipFile(folder/(d['id']+'-X1C.zip')) as z:
   for file in (folder/'plates').glob('*.3mf'):
    assert file.read_bytes()==z.read(d['id']+'/plates/'+file.name)
    removed+=file.stat().st_size;file.unlink()
 print('Installed',len(new),'Vegas hotels and',len(adapters),'adapters; deduplicated MiB',round(removed/1048576,2))
 print('Site MiB',round(sum(f.stat().st_size for f in DIST.rglob('*') if f.is_file())/1048576,2))

if __name__=='__main__':main()
