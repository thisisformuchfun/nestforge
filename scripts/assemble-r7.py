"""Install ten distinct R7 camera feeders; retain the original 37 designs."""
from pathlib import Path
import gzip,hashlib,json,os,shutil,zipfile,importlib.util,html
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist';CAD=ROOT/'cad-source/cad'
STAGE=Path(os.environ.get('NESTFORGE_R7',os.environ.get('NESTFORGE_EXPORTS',str(ROOT/'cad-source/exports'))))
ORDER=['orchard-hopper','meadow-lantern','fern-wall-pocket','pebble-pod','bottle-bough','drift-platform','ridge-aframe','acorn-column','woven-arch','willow-screen']
def archive(path,entries):
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for f,name in entries:z.write(f,name)
 with zipfile.ZipFile(path) as z:assert z.testzip() is None

def install(src):
 d=json.loads((src/'design.json').read_text());slug=d['id'];dest=DIST/'models'/slug
 checks=json.loads((src/'checks.json').read_text())
 assert checks['passed'] and checks['native_bambu_studio_roundtrip'],slug
 assert d['revision']=='R7' and d['camera_system'] and d['color_count']<=4
 for n,h in checks['input_sha256'].items():assert hashlib.sha256((src/n).read_bytes()).hexdigest()==h,(slug,n,'stale checks')
 dest.mkdir(parents=True,exist_ok=True);(dest/'plates').mkdir(exist_ok=True)
 for name in ['preview.png','PRINT-GUIDE.html','checks.json','assembly-checks.json','plate-layout.json','camera-clearance.json','finger-release-checks.json','seed-bowl-service.json']:
  if (src/name).exists():shutil.copy2(src/name,dest/name)
 guide=dest/'PRINT-GUIDE.html';s=guide.read_text().replace('STL parts in assembly coordinates; STEP solids and assembly; color-assigned 3MF plates;','STL parts in assembly coordinates; color-assigned 3MF plates;').replace('<b>assembly.glb</b> for viewing.','Editable assembly STEP is supplied in the separate CAD ZIP.').replace('The GLB follows standard glTF units: metres, Y up.','')
 if d.get('camera_system'):s=s.replace('<h2>Files included</h2>','<p>Catalog renders include an illustrative purchased camera. Camera contours, lens locations and Birdfy body height are approximate. Purchased hardware is excluded from every STL, STEP and 3MF file.</p><h2>Files included</h2>')
 guide.write_text(s)
 d['cad_download']=slug+'-STEP.zip';archive(dest/d['cad_download'],[(src/(slug+'.step'),slug+'.step'),(CAD/'R7-GUIDE.md','R7-GUIDE.md')])
 names={'design.json','preview.png','PRINT-GUIDE.html','plate-layout.json','checks.json','assembly-checks.json','camera-clearance.json','finger-release-checks.json','seed-bowl-service.json'}|{p['file'] for p in d['parts']}
 entries=[(dest/n if n=='PRINT-GUIDE.html' else src/n,str(Path(slug)/n)) for n in sorted(names) if (src/n).exists()]
 entries += [(f,str(Path(slug)/f.relative_to(src))) for f in sorted((src/'plates').glob('*.3mf'))]
 entries += [(f,str(Path(slug)/'sources'/f.name)) for f in CAD.iterdir() if f.suffix in ['.py','.html','.md']]
 archive(dest/(slug+'-X1C.zip'),entries)
 for p in d['parts']:
  single=any(r['file']==p['file'] for r in p.get('regions',[p]))
  p['download']=p['file']+'.gz' if single else slug+'-X1C.zip'
  if not single:p['download_scope']='build'
  for r in p['regions']:
   f=r['file'];gz=f+'.gz';(dest/gz).write_bytes(gzip.compress((src/f).read_bytes(),compresslevel=9,mtime=0));r['file']=gz
 layout=json.loads((dest/'plate-layout.json').read_text())
 for plate in layout['plates']:
  for obj in plate['objects']:
   for r in obj['regions']:r['file'] += '.gz'
 (dest/'plate-layout.json').write_text(json.dumps(layout,separators=(',',':')))
 (dest/'design.json').write_text(json.dumps(d,separators=(',',':')))
 return d

def download_library(catalog):
 esc=html.escape;groups=list(dict.fromkeys(d['family'] for d in catalog));sections=[]
 for family in groups:
  items=[]
  for d in [d for d in catalog if d['family']==family]:
   p=f'../models/{d["id"]}/';items.append(f'<li><a href="{p}{d["id"]}-X1C.zip" download>{esc(d["name"])}<span>Print pack ↓</span></a><a class="cad" href="{p}{d["cad_download"]}" download>{"CAD + sculpt ZIP" if d.get("attributions") else "STEP ZIP"} ↓</a><a class="cad" href="../#{d["id"]}">3D, plates & ASA sources ↗</a></li>')
  sections.append(f'<article><h2>{esc(family)}</h2><ul>{"".join(items)}</ul></article>')
 doc='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="../style.css"><title>NestForge R7 | Print library</title><style>body{max-width:1100px;margin:60px auto;padding:0 24px;font:16px/1.6 system-ui;background:#0b211e;color:#e9eddc}h1{font-size:48px;line-height:1.1}a{color:inherit}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}article{padding:25px;border:1px solid #4b6458;border-radius:18px;background:#17392e}ul{list-style:none;padding:0}li{padding:12px 0;border-top:1px solid #345448}li>a:first-child{display:flex;justify-content:space-between;gap:12px;text-decoration:none}span,.cad{font-size:12px;color:#94e0c0;white-space:nowrap}.cad{display:block;margin-top:3px}a:hover{color:#b8ffdd}small{color:#adbbb2}</style><body><a href="../">← Back to the 3D garden</a><h1>Made for your backyard.</h1><p>47 designs, including ten individually designed camera feeders. Print packs contain native X1C plates, individual STL parts, assembly notes and parametric source. Editable STEP is a separate download. Open a design to compare its actual plate count, color loads and unsliced print-time estimate.</p><p>The camera collection uses ASA and a specified camera for each design. Wyze Battery Cam Pro builds need its official close-up lens; Birdfy builds leave room for the antenna. Cameras, mounting hardware and the reused bottle are not printed. Read each build’s service and mounting instructions.</p><section>'''+''.join(sections)+'''</section><p><a href="NestForge-CAD-Source.zip" download>Download the editable CadQuery source ↓</a></p><small>R7 digital prototypes. At most four colors per plate. Open and slice in Bambu Studio. Physical fit, snap, load, focus and seed-flow trials remain required.</small><p><a href="https://www.linkedin.com/in/stephenshaffer-rd/" target="_blank" rel="noopener noreferrer">Made by Stephen Shaffer · LinkedIn ↗</a></p><div id="nature-audio" aria-label="Nature audio controls"><button id="sound-toggle" aria-pressed="false">♪ Sound off</button><label for="sound-volume" class="sr-only">Nature sound volume</label><input id="sound-volume" type="range" min="0" max="100" value="32" aria-label="Nature sound volume"><small id="sound-status">Tap to hear the garden</small></div><script type="module">import {setupNatureAudio} from '../nature-audio.js';setupNatureAudio();</script></body></html>'''
 (DIST/'downloads/index.html').write_text(doc)

def main():
 spec=importlib.util.spec_from_file_location('plans',ROOT/'scripts/render-print-plans.py');plans=importlib.util.module_from_spec(spec);spec.loader.exec_module(plans)
 cat=json.loads((DIST/'catalog.json').read_text());old=[d for d in cat if not d.get('camera_system')];assert len(old)==37,len(old)
 new=[install(STAGE/slug) for slug in ORDER];summary=json.loads((DIST/'print-plan-summary.json').read_text())
 for d in new:summary[d['id']]=plans.build(d)
 catalog=new+old;ids={d['id'] for d in catalog};summary={k:v for k,v in summary.items() if k in ids}
 (DIST/'catalog.json').write_text(json.dumps(catalog,separators=(',',':')))
 (DIST/'print-plan-summary.json').write_text(json.dumps(summary,indent=2))
 archive(DIST/'downloads/NestForge-CAD-Source.zip',[(f,str(Path('cad')/f.relative_to(CAD))) for f in CAD.rglob('*') if f.is_file() and '__pycache__' not in str(f) and f.suffix not in ['.pyc','.png']])
 download_library(catalog)
 # Rejected models remain in source history, outside the active public collection.
 for folder in list((DIST/'models').glob('vegas-*'))+[DIST/'models/camera-adapters']:
  if folder.is_dir():shutil.rmtree(folder)
 print('Installed',len(new),'distinct camera feeders; retained',len(old),'original designs')
 print('Site MiB',round(sum(f.stat().st_size for f in DIST.rglob('*') if f.is_file())/1048576,2))
if __name__=='__main__':main()
