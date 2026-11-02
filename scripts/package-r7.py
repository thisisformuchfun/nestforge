"""Package only current, camera-audited R7 exports through native Bambu Studio."""
from pathlib import Path
import argparse,hashlib,json,os,sys
ROOT=Path(__file__).resolve().parents[1]
STAGE=Path(os.environ.get('NESTFORGE_R7',os.environ.get('NESTFORGE_EXPORTS',str(ROOT/'cad-source/exports'))))
os.environ['NESTFORGE_EXPORTS']=str(STAGE);sys.path.insert(0,str(ROOT/'cad-source/cad'))
from sanitize_stl import run
from package_collection import package_design
p=argparse.ArgumentParser();p.add_argument('--only',nargs='+');args=p.parse_args()
files=sorted(STAGE.glob('*/design.json'))
for path in files:
 if args.only and path.parent.name not in args.only:continue
 folder=path.parent;audit=json.loads((folder/'camera-clearance.json').read_text())
 assert audit.get('passed'),(folder.name,'camera review not passed')
 assert audit['design_json_sha256']==hashlib.sha256(path.read_bytes()).hexdigest(),(folder.name,'stale camera metadata check')
 for f,h in audit['step_sha256'].items():assert hashlib.sha256((folder/f).read_bytes()).hexdigest()==h,(folder.name,f,'stale camera STEP check')
 cpath=folder/'checks.json';checks=json.loads(cpath.read_text()) if cpath.exists() else {}
 if checks.get('passed') and checks.get('native_bambu_studio_roundtrip') and all(hashlib.sha256((folder/f).read_bytes()).hexdigest()==h for f,h in checks.get('input_sha256',{}).items()):
  print('CURRENT',folder.name,checks['plate_count'],'native plates',flush=True);continue
 run(folder);checks=package_design(path)
 assert checks['passed'] and checks['native_bambu_studio_roundtrip'],(folder.name,checks)
 (folder/'.r7-packaged').write_text('Current native Bambu Studio roundtrip passed')
