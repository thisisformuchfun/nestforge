"""R5 Dragon Guard: structural CadQuery crown + adapted Artec sculpt mesh.
The structural STEP intentionally excludes the sculpt. The printable STL/3MF
and mesh ornament preserve its detailed surface. Run after preparing assets.
"""
from pathlib import Path
import json,os,sys,shutil,hashlib
import numpy as np
import trimesh
import manifold3d as mf
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
ASSET=HERE/'assets/artec-dragon-printable.stl'
CREDIT={'title':'Dragon (Fantasy Dragon)','creator':'Artec Group inc. / Artec 3D','source_url':'https://www.artec3d.com/3d-models/fantasy-dragon','license':'CC BY 3.0 Unported (license supplied with downloaded archive)','license_url':'https://creativecommons.org/licenses/by/3.0/','modifications':'Reduced scan mesh; uniformly scaled to 24.5%; 0.30 mm voxel remesh and outward thickening; integrated into the snap crown. Original supplied license retained. The source page also offers CC BY 4.0.','applies_to':'Dragon sculpt on the weather crown; no endorsement implied.'}
def manifold(mesh):
 mesh.merge_vertices();mesh.update_faces(mesh.unique_faces());mesh.update_faces(mesh.nondegenerate_faces());mesh.remove_unreferenced_vertices()
 result=mf.Manifold(mf.Mesh(np.asarray(mesh.vertices,dtype=np.float32),np.asarray(mesh.faces,dtype=np.uint32)))
 if str(result.status())!='Error.NoError':raise ValueError(str(result.status()))
 return result

def export_mesh(s,path):
 m=s.to_mesh();t=trimesh.Trimesh(m.vert_properties[:,:3],m.tri_verts,process=True)
 assert t.is_watertight and t.is_winding_consistent and t.volume>0
 t.export(path);return t

def build():
 import castles,common
 if not ASSET.exists():raise FileNotFoundError('Dragon sculpt asset missing. Download the complete NestForge-CAD-Source.zip from the gallery print library, or copy dragon-ornament-assembly.stl from its hybrid CAD download to assets/artec-dragon-printable.stl.')
 # Existing snap interfaces and improved masonry remain parametric CAD.
 original=castles.dragon_relief
 castles.dragon_relief=lambda:castles.C(10,2,140,0,42)
 base_export=common.export_design
 def export_base(*args,**kwargs):
  args[4][3]['color']=castles.GOLD
  return base_export(*args,**kwargs)
 common.export_design=export_base
 try:castles.castle('dragon-guard-citadel')
 finally:
  castles.dragon_relief=original;common.export_design=base_export
 folder=common.ROOT/'dragon-guard-citadel';d=json.loads((folder/'design.json').read_text());p=d['parts'][2]
 structural=trimesh.load_mesh(folder/p['file']);sculpt=trimesh.load_mesh(ASSET)
 sculpt.apply_translation([0,0,141-sculpt.bounds[0,2]])
 a=manifold(structural);b=manifold(sculpt);whole=a+b
 if len(whole.decompose())!=1:raise ValueError('Dragon is not connected to the crown')
 roof=export_mesh(whole,folder/p['file']);basefile='03-snap-weather-crown-region-01.stl';sculptfile='03-snap-weather-crown-region-02.stl'
 base=export_mesh(a,folder/basefile);ornament=export_mesh(b-a,folder/sculptfile)
 # Supply the full transformed ornament for reuse separately from its fused crown.
 sculpt.export(folder/'dragon-ornament-assembly.stl')
 p.update(bounds=roof.bounds.reshape(-1).tolist(),volume_mm3=float(roof.volume),regions=[dict(name='Structural snap crown',file=basefile,color=castles.DARK,volume_mm3=float(base.volume)),dict(name='Artec dragon sculpture',file=sculptfile,color=castles.RED,volume_mm3=float(ornament.volume))],support='Tree supports beneath dragon wings, jaw and overhangs; crown upright. Review support contacts carefully.',cad_representation='STEP contains structural crown only; complete sculpted crown is STL/3MF. Sculpt source mesh supplied.',step_roundtrip_relative_volume_error=None)
 # Keep this build to four filament colors: the removable seed well is gold.
 d['parts'][3]['color']=castles.GOLD
 for region in d['parts'][3]['regions']:region['color']=castles.GOLD
 d['colors']=list(dict.fromkeys(r['color'] for part in d['parts'] for r in part['regions']));d['color_count']=len(d['colors'])
 d['description']='A carved octagonal citadel crowned by a detailed scanned dragon: textured scales, curved neck, claws and folded wing membranes. The guardian is fused into the removable weather crown.'
 d['revision']='R5';d['detail_revision']='R5';d['attributions']=[CREDIT];d['cad_format_note']='Hybrid CAD: editable STEP for the mechanical structure; the detailed dragon is supplied as a sculpt mesh. Complete printable geometry is in the STL and 3MF files.'
 d['detail_features']=[x for x in d['detail_features'] if 'Sculptural winged' not in x]+['Artec scanned dragon with real scales, wing membranes, claws and coiled tail','Sculpt thickened and fused into the crown; no extra decorative assembly part','Four-color build: dark crown, stone masonry, gold trim and red dragon']
 d['notes'].append(d['cad_format_note']);d['notes'].append('Dragon by Artec Group inc. / Artec 3D, CC BY 3.0 supplied license; adapted as documented in ATTRIBUTION.txt.')
 (folder/'design.json').write_text(json.dumps(d,indent=2)+'\n')
 shutil.copy2(HERE/'assets/ARTEC-LICENSE.txt',folder/'ARTEC-LICENSE.txt')
 (folder/'ATTRIBUTION.txt').write_text('\n'.join(f'{k}: {v}' for k,v in CREDIT.items())+'\n'+d['cad_format_note']+'\n')
 print('SCULPTED DRAGON',len(roof.faces),'triangles',d['color_count'],'colors',roof.extents,flush=True)
if __name__=='__main__':build()
