"""Validate the delivered catalog, compressed meshes and download archive links."""
from pathlib import Path
import json,gzip,struct,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
cat=json.loads((DIST/'catalog.json').read_text());assert len(cat)==37
parts=plates=0
for d in cat:
 folder=DIST/'models'/d['id'];assert d['revision']=='R5'
 checks=json.loads((folder/'checks.json').read_text());assert checks['passed'] and checks['native_bambu_studio_roundtrip']
 assert (folder/'preview.png').stat().st_size>1000
 assert len(set(r['color'] for p in d['parts'] for r in p['regions']))<=7
 for p in d['parts']:
  parts+=1
  for r in p['regions']:
   b=gzip.decompress((folder/r['file']).read_bytes());n=struct.unpack_from('<I',b,80)[0];assert len(b)==84+50*n and n>0
   assert hashlib.sha256(b).hexdigest()==checks['input_sha256'][r['file'].removesuffix('.gz')]
  if p['download'].endswith('.zip'):
   with zipfile.ZipFile(folder/p['download']) as z:assert z.testzip() is None and any(x.endswith('.stl') for x in z.namelist())
  else:assert len(gzip.decompress((folder/p['download']).read_bytes()))>84
 for name in [d['cad_download'],d['id']+'-X1C.zip']:
  with zipfile.ZipFile(folder/name) as z:
   assert z.testzip() is None
   if d.get('attributions'):assert any(x.endswith('ARTEC-LICENSE.txt') for x in z.namelist())
 plan=json.loads((folder/'print-plan.json').read_text());assert plan['plate_count']==checks['plate_count']
 for plate in plan['plates']:
  plates+=1;assert len(plate['colors'])<=4
  assert (folder/plate['preview']).exists()
  with zipfile.ZipFile(folder/plate['file']) as z:
   assert z.testzip() is None
   settings=json.loads(z.read('Metadata/project_settings.config'));assert settings['printer_model']=='Bambu Lab X1 Carbon'
assert sum(d['color_count']>4 for d in cat)<=10
assert 'linkedin.com' in (DIST/'index.html').read_text()
assert 'setupNatureAudio' in (DIST/'downloads/index.html').read_text()
size=sum(p.stat().st_size for p in DIST.rglob('*') if p.is_file());assert size<=256*1024**2,f'Site exceeds size cap: {size}'
print(json.dumps(dict(designs=len(cat),parts=parts,plates=plates,size_MiB=round(size/1024**2,1),native_roundtrips='passed',browser_visual_QA='not available',physical_print_trials=False),indent=2))
