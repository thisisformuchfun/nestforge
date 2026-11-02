"""Static and artifact checks; these do not claim browser or physical QA."""
from pathlib import Path
from lxml import html
import json,re,hashlib,math,subprocess
R=Path(__file__).resolve().parents[1];D=R/'dist';catalog=json.loads((D/'catalog.json').read_text());ids={d['id'] for d in catalog}
new_pages=[D/'themes/index.html',D/'concepts/index.html',*sorted((D/'concepts').glob('*/index.html')),*sorted((D/'designs').glob('*/index.html'))]
errors=[];local_links=0;image_links=0
# Scan all top-level, library, and newly generated pages. Embedded legacy print
# guides are already protected by unchanged-artifact checks below.
for page in [D/'index.html',D/'downloads/index.html',*new_pages]:
 tree=html.fromstring(page.read_text());pageids=[x.get('id') for x in tree.xpath('//*[@id]')]
 if len(pageids)!=len(set(pageids)):errors.append(f'{page}: duplicate IDs')
 for el in tree.xpath('//*[@href or @src]'):
  for attr in ['href','src']:
   value=el.get(attr)
   if not value or value.startswith(('http:','https:','data:','blob:')):continue
   path,_,fragment=value.partition('#');path=path.split('?')[0];target=(page.parent/path).resolve() if path else page.resolve()
   if target.is_dir():target=target/'index.html'
   local_links+=1
   if not target.exists():errors.append(f'{page.relative_to(D)} -> missing {value}')
   if fragment and target.exists() and target.suffix=='.html':
    known={x.get('id') for x in html.fromstring(target.read_text()).xpath('//*[@id]')}
    if target==D/'index.html':known|=ids
    if fragment not in known:errors.append(f'{page.relative_to(D)} -> missing anchor {value}')
 for img in tree.xpath('//img'):
  image_links+=1
  if not img.get('alt'):errors.append(f'{page}: image missing alt')
 if page in new_pages:
  assert tree.get('lang')=='en',page
  assert len(tree.xpath('//h1'))==1,page
  assert tree.xpath('//meta[@name="viewport"]'),page
  assert tree.xpath('//main[@id="content"]'),page
  for a in tree.xpath('//a[@target="_blank"]'):assert 'noopener' in a.get('rel',''),page
  if '/concepts/' in str(page):
   assert not tree.xpath('//a[@download]'),page
   assert 'CONCEPT ONLY' in page.read_text() or 'design studies' in page.read_text(),page
# Resolve stylesheet asset imports and local JavaScript modules.
for css in D.glob('*.css'):
 for ref in re.findall(r'url\([\'"]?([^\'"\)\s;]+)',css.read_text()) + re.findall(r'@import\s+[\'"]([^\'"]+)',css.read_text()):
  if ref.startswith(('http','data:','#','var(')):continue
  assert (css.parent/ref).exists(),(css,ref)
for js in D.glob('*.js'):
 for ref in re.findall(r'(?:from\s*|import\s*)[\'"]([^\'"]+)[\'"]',js.read_text()):
  if ref.startswith('.'):assert (js.parent/ref).exists(),(js,ref)
# Preserve every original model/guide/print artifact, not just the main zip.
original=json.loads((R/'review/baseline-artifact-hashes.json').read_text());changed=[]
for rel,digest in original.items():
 p=D/rel
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:changed.append(rel)
assert not changed,changed
# The public repository and source ZIP do not carry hosted Site identity.
# Check the exact retained catalog bytes even without Git, and never mistake an
# ancestor workspace checkout for this project's repository.
publication=json.loads((R/'review/publication-integrity.json').read_text())
for rel,digest in publication['files'].items():
 assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==digest, f'Publication baseline changed: {rel}'
try:
 git_root=subprocess.run(['git','rev-parse','--show-toplevel'],cwd=R,text=True,capture_output=True)
except FileNotFoundError:
 git_root=None
if git_root is not None and git_root.returncode==0 and Path(git_root.stdout.strip()).resolve()==R:
 assert subprocess.check_output(['git','diff','--','dist/catalog.json'],cwd=R,text=True)=='','Unstaged CAD catalog metadata changes'
# Generate twice: authoring sources must reproduce the same pages.
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in new_pages}
subprocess.run(['python','scripts/build-editorial-pages.py'],cwd=R,check=True,capture_output=True)
assert before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in new_pages},'Non-deterministic editorial output'
# Metadata-only camera orientation sanity check, not a focus/occlusion test.
cameras=[]
for d in catalog:
 if not d.get('camera_system'):continue
 v=[0,-1,0]
 rx,ry,rz=[math.radians(x) for x in d['camera_pose']['rotation']]
 x,y,z=v;y,z=y*math.cos(rx)-z*math.sin(rx),y*math.sin(rx)+z*math.cos(rx)
 x,z=x*math.cos(ry)+z*math.sin(ry),-x*math.sin(ry)+z*math.cos(ry)
 x,y=x*math.cos(rz)-y*math.sin(rz),x*math.sin(rz)+y*math.cos(rz)
 delta=[t-o for t,o in zip(d['feeding_target'],d['camera_pose']['translation'])];forward_mm=sum(a*b for a,b in zip([x,y,z],delta))
 assert forward_mm>0,(d['id'],forward_mm)
 assert d['camera_service'],d['id']
 cameras.append({'id':d['id'],'feeding_target_in_forward_halfspace':True,'forward_projection_mm':round(forward_mm,2),'service_instructions_present':True})
assert not errors,'\n'.join(errors)
result={'new_editorial_pages':len(new_pages),'local_html_references_checked':local_links,'images_with_alt_text':image_links,'unchanged_original_artifacts':len(original),'publication_baseline_files_checked':len(publication['files']),'catalog_designs_preserved':len(catalog),'camera_free_designs':sum(not d.get('camera_system',False) for d in catalog),'source_generation_deterministic':True,'duplicate_ids':0,'missing_local_links':0,'camera_metadata_sanity_checks':cameras,'mobile_checks':'Static responsive rules only; no browser layout checks in this command.','browser_patch_QA':'Not performed by this static checking command.','physical_validation':'Not performed; no claim added.'}
print(json.dumps(result,indent=2))
