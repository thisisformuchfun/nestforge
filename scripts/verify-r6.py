"""Check shipped geometry, unchanged plate ZIP entries, sourcing and web links."""
from pathlib import Path
import gzip,hashlib,io,json,struct,zipfile
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'dist'
catalog=json.loads((D/'catalog.json').read_text());assert len(catalog)==49
vegas=[d for d in catalog if d.get('camera_system')];assert len(vegas)==12
parts=plates=0
for d in catalog:
 folder=D/'models'/d['id'];c=json.loads((folder/'checks.json').read_text())
 assert c['passed'] and c['native_bambu_studio_roundtrip'],d['id']
 assert (folder/'preview.png').stat().st_size>1000
 assert d['revision'] in ('R5','R6')
 for p in d['parts']:
  parts+=1
  for r in p['regions']:
   raw=gzip.decompress((folder/r['file']).read_bytes());n=struct.unpack_from('<I',raw,80)[0]
   assert len(raw)==84+50*n and n>0
   assert hashlib.sha256(raw).hexdigest()==c['input_sha256'][r['file'].removesuffix('.gz')]
  assert (folder/p['download']).exists()
 for archive in (d['cad_download'],d['id']+'-X1C.zip'):
  with zipfile.ZipFile(folder/archive) as z:
   assert z.testzip() is None
   if d.get('attributions'):assert any(n.endswith('ARTEC-LICENSE.txt') for n in z.namelist())
 plan=json.loads((folder/'print-plan.json').read_text());assert plan['plate_count']==c['plate_count']
 with zipfile.ZipFile(folder/(d['id']+'-X1C.zip')) as pack:
  for plate in plan['plates']:
   plates+=1;assert len(plate['colors'])<=4 and (folder/plate['preview']).exists()
   with zipfile.ZipFile(io.BytesIO(pack.read(d['id']+'/'+plate['file']))) as z:
    assert z.testzip() is None
    s=json.loads(z.read('Metadata/project_settings.config'))
    assert s['printer_model']=='Bambu Lab X1 Carbon'
    if d.get('camera_system'):assert all(v=='ASA' for v in s['filament_type'])
 if d.get('camera_system'):
  assert d['revision']=='R6' and d['material']=='ASA' and len(d['parts'])==3 and d['color_count']<=4
  assert plan['plate_count']==2 and len(d['camera_adapters'])==3
  assert d['camera_default']=='wyze-battery-cam-pro'
  for adapter in d['camera_adapters']:
   assert (D/adapter['file']).exists() and (D/adapter['plate_image']).exists()
   assert adapter['plate_count']==1
   mount=adapter['camera_mount']
   if adapter['id']=='birdfy-cam-2k':assert mount['front_y']==118
assert sum(d['color_count']>4 for d in catalog)<=10
source=json.loads((D/'sourcing-data.json').read_text())
assert '2026-10-20' in json.dumps(source)
assert all(brand in json.dumps(source).lower() for brand in ('bambu','polymaker','esun','eryone','overture'))
for c in source['camera_evidence']['cameras']:
 for p in c['prices']:
  if 'amazon' in p['seller'].lower():assert p['usd'] is None
page=(D/'index.html').read_text();assert 'linkedin.com/in/stephenshaffer-rd/' in page
assert 'setupNatureAudio' in (D/'app.js').read_text() and 'setupNatureAudio' in (D/'downloads/index.html').read_text()
assert 'new BirdVisit' in (D/'app.js').read_text() and 'new PartAnnotations' in (D/'app.js').read_text()
size=sum(f.stat().st_size for f in D.rglob('*') if f.is_file());assert size<256*1024**2,size
print(json.dumps(dict(designs=len(catalog),vegas_hotels=len(vegas),printed_parts=parts,native_X1C_plates=plates,alternative_camera_plates=3,ASA=True,size_MiB=round(size/1048576,2),browser_QA='Blocked by managed preview bwrap proc mount; not performed',physical_print_test=False),indent=2))
