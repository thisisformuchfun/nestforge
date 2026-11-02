"""Validate the installed R7 collection, native print packs and retained originals."""
from pathlib import Path
import gzip,hashlib,io,json,struct,zipfile
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'dist'
catalog=json.loads((D/'catalog.json').read_text());assert len(catalog)==47
new=[d for d in catalog if d.get('camera_system')];assert len(new)==10
assert len({d['architecture']['form'] for d in new})==10
assert len({d['architecture']['seed_system'] for d in new})==10
assert not any(d['id'].startswith('vegas-') for d in catalog)
parts=plates=0;new_plates=0;plans=[]
for d in catalog:
 folder=D/'models'/d['id'];c=json.loads((folder/'checks.json').read_text())
 assert c['passed'] and c['native_bambu_studio_roundtrip'],d['id']
 assert (folder/'preview.png').stat().st_size>1000
 assert d['revision'] in ('R5','R7')
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
  assert d['revision']=='R7' and d['material']=='ASA' and len(d['parts'])<=5 and d['color_count']<=4
  assert d['camera_profiles']==[d['camera_default']]
  assert 0<=d['camera_part_index']<len(d['parts'])
  assert len(d['camera_pose']['translation'])==3 and len(d['camera_pose']['rotation'])==3
  assert d['mounting']['type'] in ('hanging','post','wall')
  if d['mounting']['type']=='hanging':assert len(d['hanger'])==3
  else:assert not d['hanger']
  assert d['camera_service'] and len(d['feeding_target'])==3
  camera_file=folder/'camera-clearance.json';assert camera_file.exists(),d['id']
  audit=json.loads(camera_file.read_text());assert audit.get('passed'),(d['id'],audit)
  assert audit['design_json_sha256']==c['input_sha256']['design.json'],(d['id'],'camera metadata check stale')
  assert all(c['input_sha256'][f]==h for f,h in audit['step_sha256'].items()),(d['id'],'camera STEP check stale')
  new_plates+=plan['plate_count'];plans.append({'id':d['id'],'parts':len(d['parts']),'plates':plan['plate_count'],'planning_hours':plan['total_time_hours'],'camera':d['camera_default'],'mounting':d['mounting']['type']})
assert sum(d['color_count']>4 for d in catalog)<=10
source=json.loads((D/'sourcing-data.json').read_text())
assert '2026-10-20' in json.dumps(source)
assert all(brand in json.dumps(source).lower() for brand in ('bambu','polymaker','esun','eryone','overture'))
for camera in source['camera_evidence']['cameras']:
 for p in camera['prices']:
  if 'amazon' in p['seller'].lower():assert p['usd'] is None
page=(D/'index.html').read_text();assert 'linkedin.com/in/stephenshaffer-rd/' in page
app=(D/'app.js').read_text();assert 'setupNatureAudio' in app and 'setupNatureAudio' in (D/'downloads/index.html').read_text()
assert 'new BirdVisit' in app and 'new PartAnnotations' in app
assert not any(word in page.lower() for word in ['vegas','hotel'])
size=sum(f.stat().st_size for f in D.rglob('*') if f.is_file());assert size<256*1024**2,size
print(json.dumps(dict(designs=len(catalog),unique_camera_feeders=len(new),printed_parts=parts,native_X1C_plates=plates,new_camera_plates=new_plates,ASA=True,size_MiB=round(size/1048576,2),camera_print_plans=plans,browser_QA='Not performed by this artifact-checking command',physical_print_test=False),indent=2))
