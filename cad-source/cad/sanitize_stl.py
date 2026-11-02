"""Remove only zero-area tessellation fragments; never fill holes or heal geometry.
Poles of analytic surfaces can emit triangles with zero mathematical area.
Each operation records the before/after hashes and requires unchanged volume.
"""
from pathlib import Path
import argparse,json,hashlib,os
import numpy as np
import trimesh
ROOT=Path(os.environ.get('NESTFORGE_EXPORTS',str(Path(__file__).resolve().parents[1]/'exports')))
def run(folder):
 p=folder/'design.json';d=json.loads(p.read_text());changes=[]
 names={p['file'] for p in d['parts']}|{r['file'] for p in d['parts'] for r in p.get('regions',[p])}
 for name in sorted(names):
  path=folder/name;mesh=trimesh.load_mesh(path,process=True);area=mesh.area_faces;keep=area>1e-10;n=int((~keep).sum())
  if not n:continue
  before=float(mesh.volume);sha=hashlib.sha256(path.read_bytes()).hexdigest()
  mesh.update_faces(keep);mesh.remove_unreferenced_vertices()
  after=float(mesh.volume)
  if abs(after-before)>max(1e-7,abs(before)*1e-10):raise ValueError(f'Unexpected volume change {name}')
  temp=path.with_suffix('.normalizing.stl');mesh.export(temp,file_type='stl');temp.replace(path)
  changes.append({'file':name,'removed_zero_area_facets':n,'area_threshold_mm2':1e-10,'original_sha256':sha,'normalized_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'volume_change_mm3':after-before,'hole_filling':False})
 if changes:
  d.setdefault('mesh_export_normalization',[]).extend(changes);p.write_text(json.dumps(d,indent=2))
 print(d['id'],'removed',sum(x['removed_zero_area_facets'] for x in changes),'zero-area facets',flush=True)
 return changes
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('slugs',nargs='*');a=parser.parse_args()
 for p in ROOT.glob('*/design.json'):
  if (not a.slugs or p.parent.name in a.slugs) and json.loads(p.read_text()).get('revision') in ('R2','R5','R6','R7'):run(p.parent)
