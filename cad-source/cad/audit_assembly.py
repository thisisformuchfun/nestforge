"""Read-only CAD STEP interference audit; no meshes or solids are modified.

Run once geometry is final. --only ID ... rechecks selected designs. Results
include STEP hashes so downstream tools can distinguish stale checks.
"""
from pathlib import Path
import argparse,hashlib,itertools,json,os
import cadquery as cq
ROOT=Path(os.environ.get('NESTFORGE_EXPORTS',str(Path(__file__).resolve().parents[1]/'exports')))

def audit(file):
 d=json.loads(file.read_text());parts=[];pairs=[];hashes={}
 for p in d['parts']:
  path=file.parent/p['step'];hashes[p['step']]=hashlib.sha256(path.read_bytes()).hexdigest()
  s=cq.importers.importStep(str(path)).val();parts.append((p,s))
 for (a,sa),(b,sb) in itertools.combinations(parts,2):
  ba=sa.BoundingBox();bb=sb.BoundingBox()
  if ba.xmax<bb.xmin or bb.xmax<ba.xmin or ba.ymax<bb.ymin or bb.ymax<ba.ymin or ba.zmax<bb.zmin or bb.zmax<ba.zmin:continue
  try:
   # The true common is wholly inside the overlap of the two bounding boxes.
   # Exact clipping removes distant decorative faces before the costly common.
   lo=[max(getattr(ba,k+'min'),getattr(bb,k+'min')) for k in 'xyz']
   hi=[min(getattr(ba,k+'max'),getattr(bb,k+'max')) for k in 'xyz']
   dims=[hi[i]-lo[i] for i in range(3)]
   print('AUDIT PAIR',a['name'],'/',b['name'],flush=True)
   if min(dims)<=0:vol=0.0
   else:
    pad=.001
    roi=cq.Solid.makeBox(*(v+2*pad for v in dims),cq.Vector(*(v-pad for v in lo)))
    roi_volume=(dims[0]+2*pad)*(dims[1]+2*pad)*(dims[2]+2*pad)
    clipped=[]
    for shape,box in [(sa,ba),(sb,bb)]:
     box_volume=box.xlen*box.ylen*box.zlen
     local=shape.intersect(roi) if box_volume>roi_volume*1.2 else shape
     if local.Solids() and not local.isValid():raise ValueError('Invalid exact ROI clip')
     clipped.append(local)
    vol=clipped[0].intersect(clipped[1]).Volume() if all(x.Solids() for x in clipped) else 0.0
   pairs.append({'part_a':a['name'],'part_b':b['name'],'intersection_mm3':round(vol,6),'clearance_mm':None,'significant_interference':vol>0.05,'exact_brep_roi_clip':True})
  except Exception as e:pairs.append({'part_a':a['name'],'part_b':b['name'],'error':str(e)})
 result={'id':d['id'],'method':'Exact BREP common volume in assembly coordinates, bounded by exact BREP clipping to padded bounding-box intersection','interference_tolerance_mm3':0.05,'step_sha256':hashes,'pairs':pairs,'multi_solid_parts':[{'name':p['name'],'solids':len(s.Solids())} for p,s in parts if len(s.Solids())!=1]}
 result['passed']=not result['multi_solid_parts'] and all(not p.get('significant_interference') and not p.get('error') for p in pairs)
 (file.parent/'assembly-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
 return result

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--only',nargs='+');parser.add_argument('--changed-only',action='store_true');args=parser.parse_args()
 paths=[p for p in sorted(ROOT.glob('*/design.json')) if json.loads(p.read_text()).get('revision') in ('R2','R5','R6','R7')]
 if args.only:paths=[p for p in paths if p.parent.name in args.only]
 results=[]
 for f in paths:
  previous=f.parent/'assembly-checks.json'
  if args.changed_only and previous.exists():
   old=json.loads(previous.read_text());hashes=old.get('step_sha256',{})
   expected={p['step'] for p in json.loads(f.read_text())['parts']}
   if old.get('passed') and set(hashes)==expected and all(hashlib.sha256((f.parent/n).read_bytes()).hexdigest()==h for n,h in hashes.items()):
    results.append(old);print('UNCHANGED',f.parent.name,flush=True);continue
  results.append(audit(f));(ROOT/'assembly-audit.json').write_text(json.dumps(results,indent=2))
if __name__=='__main__':main()
