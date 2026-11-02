"""Install verified R5 export packages into the static site, with lossless mesh compression."""
from pathlib import Path
import json,zipfile,shutil,gzip,os,sys
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist';SOURCE=ROOT/'cad-source/cad'
EXPORT=Path(os.environ.get('NESTFORGE_EXPORTS',str(ROOT/'cad-source/exports')))
old=json.loads((DIST/'catalog.json').read_text());catalog=[]
def archive(path, entries):
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
  for f,name in entries:z.write(f,name)
 with zipfile.ZipFile(path) as z:assert z.testzip() is None
for previous in old:
 slug=previous['id'];src=EXPORT/slug
 if '--available' in sys.argv and not ((src/'.r5-packaged').exists() and (src/'.r5-rendered').exists()):
  catalog.append(previous);continue
 assert (src/'.r5-packaged').exists(),f'Not packaged: {slug}'
 assert (src/'preview.png').exists(),f'No render: {slug}'
 checks=json.loads((src/'checks.json').read_text())
 assert checks['passed'] and checks['native_bambu_studio_roundtrip'],slug
 d=json.loads((src/'design.json').read_text());assert d['revision']=='R5'
 dest=DIST/'models'/slug
 shutil.rmtree(dest);dest.mkdir()
 for name in ['preview.png','PRINT-GUIDE.html','checks.json','assembly-checks.json','plate-layout.json','ATTRIBUTION.txt','ARTEC-LICENSE.txt','hybrid-mesh-checks.json']:
  if (src/name).exists():shutil.copy2(src/name,dest/name)
 shutil.copytree(src/'plates',dest/'plates')
 guide=dest/'PRINT-GUIDE.html';g=guide.read_text().replace('R2 digital prototype','R5 digital prototype').replace('STL parts in assembly coordinates; STEP solids and assembly; color-assigned 3MF plates;','STL parts in assembly coordinates; color-assigned 3MF plates;').replace('<b>assembly.glb</b> for viewing.','Editable CAD and the complete collection source are separate gallery downloads. Color regions are embedded in the 3MF; source regeneration recreates individual region meshes.').replace('The GLB follows standard glTF units: metres, Y up.','')
 guide.write_text(g)
 # Separate editable CAD. The hybrid dragon also supplies the complete printable mesh.
 cadfiles=[(src/(slug+'.step'),slug+'.step')]
 if d.get('cad_format_note'):
  for name in ['dragon-ornament-assembly.stl','ATTRIBUTION.txt','ARTEC-LICENSE.txt']:
   cadfiles.append((src/name,name))
  note=src/'CAD-README.txt';note.write_text(d['cad_format_note']+'\nSee ATTRIBUTION.txt for the sculpt source and modifications.\n');cadfiles.append((note,note.name))
 d['cad_download']=slug+'-STEP.zip';archive(dest/d['cad_download'],cadfiles)
 # Build current print pack; exclude duplicated STEP/GLB and include licensed mesh source only for dragon.
 entries=[]
 names={'design.json','preview.png','PRINT-GUIDE.html','plate-layout.json','checks.json','assembly-checks.json','hybrid-mesh-checks.json','ATTRIBUTION.txt','ARTEC-LICENSE.txt'}
 names|={p['file'] for p in d['parts']}|{f.name for f in src.glob('*-validation.json')}
 for name in sorted(names):
  if (src/name).exists():entries.append((dest/name if name=='PRINT-GUIDE.html' else src/name,str(Path(slug)/name)))
 entries += [(f,str(Path(slug)/f.relative_to(src))) for f in (src/'plates').glob('*.3mf')]
 entries += [(f,str(Path(slug)/'sources'/f.name)) for f in SOURCE.iterdir() if f.suffix in ['.py','.html','.md']]
 # Complete community source asset is in the linked collection source ZIP and hybrid CAD download.
 if d.get('attributions'):
  entries.append((SOURCE/'assets/ARTEC-LICENSE.txt',str(Path(slug)/'sources/assets/ARTEC-LICENSE.txt')))
 archive(dest/(slug+'-X1C.zip'),entries)
 for p in d['parts']:
  single=any(r['file']==p['file'] for r in p.get('regions',[p]))
  p['download']=p['file']+'.gz' if single else slug+'-X1C.zip'
  if not single:p['download_scope']='build'
  for r in p.get('regions',[p]):
   name=r['file'];gz=name+'.gz'
   if not (dest/gz).exists():(dest/gz).write_bytes(gzip.compress((src/name).read_bytes(),compresslevel=7,mtime=0))
   r['file']=gz
 # Web plate layout matches losslessly compressed region files, native plate files remain standard 3MF.
 lp=dest/'plate-layout.json';layout=json.loads(lp.read_text())
 for plate in layout['plates']:
  for obj in plate['objects']:
   for region in obj['regions']:region['file'] += '.gz'
 lp.write_text(json.dumps(layout,separators=(',',':')))
 (dest/'design.json').write_text(json.dumps(d,separators=(',',':')))
 catalog.append(d)
 print('INSTALLED',slug,flush=True)
(DIST/'catalog.json').write_text(json.dumps(catalog,separators=(',',':')))
archive(DIST/'downloads/NestForge-CAD-Source.zip',[(f,str(Path('cad')/f.relative_to(SOURCE))) for f in SOURCE.rglob('*') if f.is_file() and '__pycache__' not in str(f) and f.suffix not in ['.pyc','.png']])
p=DIST/'downloads/index.html';s=p.read_text().replace('R2','R5').replace('37 rebuilt designs.','37 detailed designs.').replace('Editable assembly STEP is a separate ZIP download.','Editable assembly STEP is a separate ZIP download. Dragon Guard includes its credited sculpt mesh alongside the structural STEP.').replace('dragon-guard-citadel-STEP.zip" download>STEP ZIP','dragon-guard-citadel-STEP.zip" download>CAD + sculpt ZIP');p.write_text(s)
print('SIZE MiB',sum(f.stat().st_size for f in DIST.rglob('*') if f.is_file())/1048576)
