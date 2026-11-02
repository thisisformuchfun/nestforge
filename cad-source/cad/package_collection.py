#!/usr/bin/env python3
"""Validate exported CAD and pack color-assigned, UNSLICED X1C 3MF projects.

The source STL remains in assembly coordinates. Print rotations are XYZ degrees,
followed by any 90-degree Z turn chosen by the plate packer. Parts are then
translated to Z=0. No geometry is scaled and no repair is performed silently.
Run: python cad/package_collection.py [--only design-id ...]
"""
from __future__ import annotations
import argparse, hashlib, html, json, math, os, shutil, tempfile, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
import native_bambu
from read_3mf import read as read_3mf

ROOT=Path(__file__).resolve().parents[1]
EXPORT=Path(os.environ.get('NESTFORGE_EXPORTS',str(ROOT/'exports')))
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
BED=256.0; MARGIN=15.0; MAX_XY=240.0; GAP=8.0; MAX_Z=245.0
EXCLUSION=[0.,0.,18.,28.]
TOWER=[190.,190.,240.,240.]  # Reserved envelope, not a fake printable tower.
SOURCES={
 'x1c_profile':'https://github.com/bambulab/BambuStudio/blob/master/resources/profiles/BBL/machine/Bambu%20Lab%20X1%20Carbon%200.4%20nozzle.json',
 'machine_base':'https://github.com/bambulab/BambuStudio/blob/master/resources/profiles/BBL/machine/fdm_bbl_3dp_001_common.json',
 'bambu_serialization':'https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/Format/bbs_3mf.cpp',
 '3mf_core':'https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md',
 'asa':'https://us.store.bambulab.com/products/asa-filament',
 'cleaning':'https://www.allaboutbirds.org/news/how-to-clean-your-bird-feeder/'
}

def design_material(design):
    value=os.environ.get('NESTFORGE_MATERIAL') or design.get('material','PETG')
    if isinstance(value,dict):value=value.get('polymer',value.get('type','PETG'))
    value=str(value).upper().removeprefix('GENERIC ').strip()
    if value not in ('PETG','ASA'):raise ValueError(f'Unsupported project material: {value}')
    return value

def overlap(a,b,gap=GAP):
    return not (a[2]+gap<=b[0]+1e-5 or b[2]+gap<=a[0]+1e-5 or a[3]+gap<=b[1]+1e-5 or b[3]+gap<=a[1]+1e-5)

def rgb(color):
    color=color.lstrip('#')
    if len(color)==3:color=''.join(c*2 for c in color)
    return [int(color[i:i+2],16) for i in (0,2,4)]+[255]

def inspect_part(folder,p,index):
    mesh=trimesh.load_mesh(folder/p['file'],process=True)
    if not isinstance(mesh,trimesh.Trimesh): raise ValueError('STL is not a triangle mesh')
    r=Rotation.from_euler('xyz',p.get('print_rotation',[0,0,0]),degrees=True).as_matrix()
    v=mesh.vertices@r.T
    dims=v.max(axis=0)-v.min(axis=0)
    _,edge_counts=np.unique(np.sort(mesh.edges,axis=1),axis=0,return_counts=True)
    area=np.linalg.norm(np.cross(mesh.triangles[:,1]-mesh.triangles[:,0],mesh.triangles[:,2]-mesh.triangles[:,0]),axis=1)/2
    components=mesh.split(only_watertight=False,repair=False)
    # STL float precision can produce zero-area facets; count and report, do not hide.
    checks={
      'part_index':index,'name':p['name'],'file':p['file'],
      'vertices':len(mesh.vertices),'triangles':len(mesh.faces),
      'closed_edges':bool(np.all(edge_counts==2)),
      'boundary_edges':int(np.count_nonzero(edge_counts==1)),
      'nonmanifold_edges':int(np.count_nonzero(edge_counts>2)),
      'winding_consistent':bool(mesh.is_winding_consistent),
      'positive_volume':bool(mesh.volume>0), 'volume_mm3':round(float(mesh.volume),3),
      'components':len(components),'declared_solids':p.get('solids'),
      'single_connected_body':int(sum(c.volume>1e-8 for c in components))==1 and p.get('solids',1)==1,
      'positive_material_shells':int(sum(c.volume>1e-8 for c in components)),
      'enclosed_cavity_shells':int(sum(c.volume<(-1e-8) for c in components)),
      'shell_volumes_nonzero':all(abs(c.volume)>1e-8 for c in components),
      'all_shells_closed':all(c.is_watertight for c in components),
      'degenerate_triangles':int(np.count_nonzero(area<1e-10)),
      'print_size_mm':np.round(dims,3).tolist(),
      'print_height_ok':bool(dims[2]<=MAX_Z+1e-4),
      'print_footprint_ok':bool(dims[0]<=MAX_XY-MARGIN+1e-4 and dims[1]<=MAX_XY-MARGIN+1e-4),
    }
    region_checks=[]
    for region_record in p.get('regions',[p]):
        region=trimesh.load_mesh(folder/region_record['file'],process=True)
        region_checks.append(dict(name=region_record['name'],closed=bool(region.is_watertight),winding=bool(region.is_winding_consistent),positive_volume=bool(region.volume>0)))
    checks['material_regions']=region_checks
    checks['regions_passed']=all(all(r[k] for k in ['closed','winding','positive_volume']) for r in region_checks)
    checks['passed']=checks['regions_passed'] and all(checks[k] for k in ['closed_edges','winding_consistent','positive_volume','shell_volumes_nonzero','all_shells_closed','single_connected_body','print_height_ok','print_footprint_ok']) and checks['degenerate_triangles']==0
    return {'part':p,'part_index':index,'mesh':mesh,'rotated':v,'rotation':r,'size':dims,'checks':checks}

def part_colors(p):return {r['color'].upper() for r in p.get('regions',[p])}
def plate_colors(plate):return set().union(*(part_colors(o['part']) for o in plate))
def tower_clear(vertices):
    # The convex hull includes every projected triangle and overhang. Its
    # distance to the reserved tower is conservative even for hollow parts.
    points=np.unique(vertices[:,:2],axis=0);polygon=points[ConvexHull(points).vertices]
    x0,y0,x1,y1=TOWER
    tower=np.array([[x0-GAP,y0-GAP],[x1+GAP,y0-GAP],[x1+GAP,y1+GAP],[x0-GAP,y1+GAP]])
    edges=np.roll(polygon,-1,axis=0)-polygon
    axes=np.vstack([np.array([[1.,0.],[0.,1.]]),np.c_[-edges[:,1],edges[:,0]]])
    axes/=np.linalg.norm(axes,axis=1)[:,None]
    a=polygon@axes.T;b=tower@axes.T
    return bool(np.any((a.max(axis=0)<=b.min(axis=0)+1e-5)|(b.max(axis=0)<=a.min(axis=0)+1e-5)))
def find_placement(obj,plate):
    palette=plate_colors(plate)|part_colors(obj['part'])
    if len(palette)>4:return None
    mixed=len(palette)>1
    boxes=[x['rect'] for x in plate]
    if mixed:
        if any(not tower_clear(o['print_vertices']) for o in plate):return None
    boxes=boxes+[EXCLUSION]
    xs=sorted({MARGIN,EXCLUSION[2]+GAP,*[b[2]+GAP for b in boxes]})
    ys=sorted({MARGIN,EXCLUSION[3]+GAP,*[b[3]+GAP for b in boxes]})
    candidates=[]
    for turn in [0,90]:
        rz=Rotation.from_euler('z',turn,degrees=True).as_matrix()
        v=obj['rotated']@rz.T
        lo=v.min(axis=0);dims=v.max(axis=0)-lo
        for y in ys:
            for x in xs:
                rect=[x,y,x+dims[0],y+dims[1]]
                if rect[2]>MAX_XY+1e-4 or rect[3]>MAX_XY+1e-4:continue
                if any(overlap(rect,b) for b in boxes):continue
                if mixed and not tower_clear(v-lo+[x,y,0]):continue
                candidates.append((y*BED+x,turn,rect,v-lo+[x,y,0],rz@obj['rotation'],np.array([x,y,0])-lo))
    return min(candidates,key=lambda c:(c[0],c[1])) if candidates else None

def pack(objects):
    plates=[]
    for obj in sorted(objects,key=lambda x:(-max(x['size'][:2]),-np.prod(x['size'][:2]),x['part_index'])):
        placed=False
        # Prefer an existing same-color plate to avoid needless swaps.
        order=sorted(range(len(plates)),key=lambda i:len(plate_colors(plates[i])|part_colors(obj['part'])))
        for i in order+[len(plates)]:
            plate=plates[i] if i<len(plates) else []
            candidate=find_placement(obj,plate)
            if candidate is None:continue
            _,turn,rect,vertices,rotation,translation=candidate
            entry=dict(obj,turn=turn,rect=rect,print_vertices=vertices,final_rotation=rotation,translation=translation)
            if i==len(plates):plates.append([])
            plates[i].append(entry);placed=True;break
        if not placed:raise ValueError(f"{obj['part']['name']}: no safe bounding-box placement in X1C envelope")
    return plates

def xmlbytes(e):return ET.tostring(e,encoding='utf-8',xml_declaration=True)
def meta(parent,k,v):return ET.SubElement(parent,'metadata',{'key':k,'value':str(v)})

def plate_materials(plate,materials):
    used=plate_colors(plate)
    return [dict(m,extruder=i+1) for i,m in enumerate(m for m in materials if m['color'] in used)]

def make_3mf(path,design,plate,materials,number):
    model=ET.Element('model',{'unit':'millimeter','xml:lang':'en-US','xmlns':NS,'xmlns:BambuStudio':'http://schemas.bambulab.com/package/2021'})
    ET.SubElement(model,'metadata',{'name':'Application'}).text='NestForge R2'
    ET.SubElement(model,'metadata',{'name':'BambuStudio:3mfVersion'}).text='1'
    resources=ET.SubElement(model,'resources');base=ET.SubElement(resources,'basematerials',{'id':'1'})
    for mat in materials:ET.SubElement(base,'base',{'name':mat['name'],'displaycolor':mat['color']+'FF'})
    build=ET.SubElement(model,'build');config=ET.Element('config');oid=2;object_ids=[];counts=[]
    source=EXPORT/design['id']
    for obj in plate:
        p=obj['part'];region_ids=[];reg_records=[]
        for r in p.get('regions',[p]):
            mesh=trimesh.load_mesh(source/r['file'],process=True)
            vertices=mesh.vertices@obj['final_rotation'].T+obj['translation']
            ex=next(m['extruder'] for m in materials if m['color']==r['color'].upper())
            rid=oid;oid+=1;region_ids.append(rid);reg_records.append((rid,r,ex,len(mesh.faces)))
            o=ET.SubElement(resources,'object',{'id':str(rid),'type':'model','name':r['name'],'pid':'1','pindex':str(ex-1)})
            me=ET.SubElement(o,'mesh');vs=ET.SubElement(me,'vertices');fs=ET.SubElement(me,'triangles')
            for v in vertices:ET.SubElement(vs,'vertex',dict(zip(['x','y','z'],[f'{x:.6f}' for x in v])))
            for f in mesh.faces:ET.SubElement(fs,'triangle',dict(zip(['v1','v2','v3'],map(str,f))))
        aid=oid;oid+=1;object_ids.append(aid)
        assembly=ET.SubElement(resources,'object',{'id':str(aid),'type':'model','name':p['name']})
        components=ET.SubElement(assembly,'components')
        for rid in region_ids:ET.SubElement(components,'component',{'objectid':str(rid)})
        ET.SubElement(build,'item',{'objectid':str(aid),'printable':'1'})
        oc=ET.SubElement(config,'object',{'id':str(aid)});meta(oc,'name',p['name']);meta(oc,'extruder',reg_records[0][2] if len(reg_records)==1 else 1)
        ET.SubElement(oc,'metadata',{'face_count':str(sum(x[3] for x in reg_records))})
        for rid,r,ex,nfaces in reg_records:
            pc=ET.SubElement(oc,'part',{'id':str(rid),'subtype':'normal_part'})
            for k,v in [('name',r['name']),('extruder',ex),('matrix','1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'),('source_file',r['file']),('source_object_id',0),('source_volume_id',0)]:meta(pc,k,v)
            ET.SubElement(pc,'mesh_stat',{'face_count':str(nfaces),'edges_fixed':'0','degenerate_facets':'0','facets_removed':'0','facets_reversed':'0','backwards_edges':'0'})
        support=p.get('support','None; upright').lower()
        if not(support.startswith('none') or 'no support' in support or 'support-free' in support):
            meta(oc,'enable_support','1');meta(oc,'support_type','tree(auto)' if ('tree' in support or 'organic' in support) else 'normal(auto)')
    pl=ET.SubElement(config,'plate')
    for k,v in [('plater_id',1),('plater_name',f"{design['name']} / {number}"),('locked','false'),('bed_type','Textured PEI Plate'),('print_sequence','by layer')]:meta(pl,k,v)
    for i,aid in enumerate(object_ids):
        inst=ET.SubElement(pl,'model_instance')
        for k,v in [('object_id',aid),('instance_id',0),('identify_id',i+1)]:meta(inst,k,v)
    n=len(materials);mixed=n>1;polymer=design_material(design)
    settings={
      'printer_model':'Bambu Lab X1 Carbon','printer_variant':'0.4','printer_settings_id':'Bambu Lab X1 Carbon 0.4 nozzle',
      'nozzle_diameter':['0.4'],'printable_area':['0x0','256x0','256x256','0x256'],'printable_height':'250',
      'bed_exclude_area':['0x0','18x0','18x28','0x28'],
      'print_settings_id':'0.20mm Standard @BBL X1C','layer_height':'0.2','initial_layer_print_height':'0.2',
      'wall_loops':'4','top_shell_layers':'5','bottom_shell_layers':'5','sparse_infill_density':'15%',
      'sparse_infill_pattern':'gyroid','curr_bed_type':'Textured PEI Plate','print_sequence':'by layer',
      'filament_colour':[m['color'] for m in materials],'filament_type':[polymer]*n,'filament_diameter':['1.75']*n,
      'filament_settings_id':[f'Generic {polymer}']*n,'filament_ids':['GFG99' if polymer=='PETG' else 'GFB98']*n,
      'enable_prime_tower':'1' if mixed else '0','prime_tower_width':'35','prime_tower_brim_width':'3',
      'wipe_tower_x':['197.5'],'wipe_tower_y':['197.5'],'brim_type':'auto_brim','brim_width':'3',
      'enable_support':'0','support_type':'normal(auto)',
      'flush_volumes_matrix':['0' if i==j else '280' for i in range(n) for j in range(n)],
    }
    rel=ET.Element('Relationships',{'xmlns':'http://schemas.openxmlformats.org/package/2006/relationships'})
    ET.SubElement(rel,'Relationship',{'Target':'/3D/3dmodel.model','Id':'rel0','Type':'http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel'})
    types=ET.Element('Types',{'xmlns':'http://schemas.openxmlformats.org/package/2006/content-types'})
    for ext,ct in [('rels','application/vnd.openxmlformats-package.relationships+xml'),('model','application/vnd.ms-package.3dmanufacturing-3dmodel+xml'),('config','application/octet-stream')]:ET.SubElement(types,'Default',{'Extension':ext,'ContentType':ct})
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,blob in {'[Content_Types].xml':xmlbytes(types),'_rels/.rels':xmlbytes(rel),'3D/3dmodel.model':xmlbytes(model),'Metadata/model_settings.config':xmlbytes(config),'Metadata/project_settings.config':json.dumps(settings,indent=2)}.items():z.writestr(name,blob)
    return verify_3mf(path,plate,n)

def verify_3mf(path,plate,material_count):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        m=ET.fromstring(z.read('3D/3dmodel.model'));c=ET.fromstring(z.read('Metadata/model_settings.config'));settings=json.loads(z.read('Metadata/project_settings.config'))
        ns={'m':NS};build=m.findall('m:build/m:item',ns)
        assert len(build)==len(plate)==len(c.findall('object'))
        for o in c.findall('object'):
            for p in o.findall('part'):
                ex=int(p.find("metadata[@key='extruder']").attrib['value']);assert 1<=ex<=material_count<=4
        assert len(settings['filament_colour'])==material_count
        assert not any(x.endswith('.gcode') for x in z.namelist())
    scene=read_3mf(path);loaded=scene.to_geometry()
    expected=sum(p['mesh'].volume for p in plate)
    # Independently tessellated color boundaries can refine curved surface triangles.
    # The BREP partition is exact; retain a 0.1% mesh-volume approximation check.
    relative_error=abs(loaded.volume-expected)/expected
    assert relative_error<.001,(loaded.volume,expected,relative_error)
    return {'region_vs_full_mesh_relative_volume_error':relative_error,'zip_crc':True,'xml_parsed':True,'physical_objects':len(plate),'material_regions':len(scene.geometry),'extruder_assignments':True,'independent_3mf_volume_match':True,'contains_gcode':False}

def make_layout(plates,materials):
    records=[]
    for number,plate in enumerate(plates,1):
        local=plate_materials(plate,materials);objects=[]
        for o in plate:
            p=o['part'];v=o['print_vertices'];transform=np.eye(4);transform[:3,:3]=o['final_rotation'];transform[:3,3]=o['translation']
            objects.append({'part_index':o['part_index'],'name':p['name'],'file':p['file'],'extruder':next(m['extruder'] for m in local if m['color']==p['color'].upper()) if p['color'].upper() in [m['color'] for m in local] else 1,'color':p['color'].upper(),'regions':[dict(r,extruder=next(m['extruder'] for m in local if m['color']==r['color'].upper())) for r in p.get('regions',[p])],'position_mm':np.round(v.min(axis=0),6).tolist(),'bounds_mm':np.round(np.r_[v.min(axis=0),v.max(axis=0)],6).tolist(),'rotation_deg':p.get('print_rotation',[0,0,0]),'packing_z_rotation_deg':o['turn'],'assembly_to_plate_matrix':np.round(transform,9).tolist()})
        records.append({'number':number,'file':f'plates/plate-{number:02}.3mf','material_order':local,'prime_tower_reserved':TOWER if len(local)>1 else None,'tower_clearance_method':'Projected convex hull outside reserved tower expanded by 8 mm','objects':objects})
    return {'printer':'Bambu Lab X1 Carbon / 0.4 mm nozzle','status':'Color-assigned unsliced project; open and slice in Bambu Studio','bed_mm':[256,256],'margin_mm':MARGIN,'part_gap_mm':GAP,'exclusion':EXCLUSION,'material_order':materials,'slot_instructions':'Load the material_order listed on EACH plate. More than four build colors use spool changes BETWEEN plates; never more than four on one plate.','plates':records}

def make_glb(folder,design,objects):
    scene=trimesh.Scene();conversion=Rotation.from_euler('x',-90,degrees=True).as_matrix()
    for obj in objects:
        p=obj['part']
        for i,r in enumerate(p.get('regions',[p])):
            mesh=trimesh.load_mesh(folder/r['file'],process=True);mesh.vertices=(mesh.vertices@conversion.T)*0.001
            mesh.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(name=r['name'],baseColorFactor=rgb(r['color']),metallicFactor=0.0,roughnessFactor=0.64,doubleSided=False))
            scene.add_geometry(mesh,node_name=f'{p["name"]}/{i}',geom_name=f'{p["name"]}/{i}')
    (folder/'assembly.glb').write_bytes(scene.export(file_type='glb'))

def make_guide(folder,design,layout,checks):
    esc=html.escape
    mounting=design.get('mounting',{})
    if mounting.get('type','hanging')=='hanging':
        mounting_guide='Snap the structural pieces together before hanging. Use outdoor cord through the designed suspension point and a tree-friendly strap around the branch. The cord suspends the completed rigid assembly; it does not retain parts. Confirm every latch is engaged, test the intended seed and camera load over a soft surface, and inspect the printed eye before outdoor use.'
    else:
        mounting_guide='Mounting: '+str(mounting.get('description','Follow the design-specific mounting instructions.'))+' Hardware: '+str(mounting.get('hardware','See assembly notes.'))+' Assemble and verify every snap before loading. Test the mount with the intended seed and camera load over a soft surface; check printed brackets for cracks before installation.'
    camera_guide=''
    if design.get('camera_system'):
        camera_guide='<h2>Camera fit and access</h2><p>'+esc(str(design.get('camera_service',design.get('camera_mount',{}).get('service','Remove the camera before battery or charging service.'))))+'</p><p>The camera is purchased hardware, not a printed part. Published outside dimensions guide this prototype; actual housing contours, grip retention, accessory clearance, sensor triggering and focus are not physically verified. Test a bird-sized target at the intended feeding position. Wyze Battery Cam Pro requires its official close-up lens.</p>'
    colors=''.join(f'<li><i style="background:{m["color"]}"></i><b>Build color {m["extruder"]}</b> {m["color"]}</li>' for m in layout['material_order'])
    instructions=''.join(f'<li>{esc(str(t))}</li>' for t in design.get('assembly',[]))
    notes=''.join(f'<li>{esc(str(t))}</li>' for t in design.get('notes',[]))
    parts=''.join(f'<tr><td>{esc(p["name"])}</td><td>{p["color"]}</td><td>{esc(p.get("support","None; upright"))}</td></tr>' for p in design['parts'])
    dimensions=np.max([p['bounds'][3:] for p in design['parts']],axis=0)-np.min([p['bounds'][:3] for p in design['parts']],axis=0)
    doc=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(design['name'])} — print guide</title><style>body{{font:16px/1.6 system-ui,sans-serif;color:#18382f;background:#f4f1e8;margin:0}}main{{max-width:880px;padding:52px 28px;margin:auto}}h1{{font-size:44px;line-height:1.05}}h2{{margin-top:40px}}.tag{{color:#567968;font-size:13px;letter-spacing:.1em;text-transform:uppercase}}.callout{{border-left:4px solid #c58844;background:white;padding:18px 24px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:10px;text-align:left;border-bottom:1px solid #cdcfc4}}a{{color:#326955}}i{{display:inline-block;width:18px;height:18px;border-radius:50%;vertical-align:middle;margin-right:12px;border:1px solid #aaa}}footer{{border-top:1px solid #bbb;margin-top:50px;padding-top:20px;font-size:13px}}@media print{{main{{padding:0}}}}</style></head><body><main>
<p class="tag">NestForge · {esc(design.get("revision","R5"))} digital prototype · X1 Carbon + AMS</p><h1>{esc(design['name'])}</h1><p>{esc(design['description'])}</p>
<p><b>{len(design['parts'])} printed parts · {len(layout['plates'])} plates · approximately {' × '.join(str(round(x)) for x in dimensions)} mm assembled</b></p>
<div class="callout"><b>Open and slice in Bambu Studio.</b> The included 3MFs contain positioned meshes and color/extruder assignments. They are unsliced, with no G-code. Mesh closure, positive volume, plate limits and spacing were checked digitally. Native Bambu Studio import/export verification: {'passed' if checks.get('native_bambu_studio_roundtrip') else 'not performed'}. Physical fit, feed flow, weathering and hanging strength still require a first prototype.</div>
<h2>1. Prepare the plates</h2><ol><li>Open each <b>plates/plate-XX.3mf</b> as a project. Keep the X1 Carbon 0.4 mm profile and load the plate-specific AMS slots listed in plate-layout.json before slicing; builds with more than four colors use different slot loads between plates.</li><li>Use the same polymer family in every slot. The project starts with Generic {design_material(design)} for the first fit prototype. Choose your actual spool profiles, run the normal filament calibration, then slice. For long outdoor exposure, ASA is the preferred production trial; use an enclosed, well-ventilated printer and the manufacturer's ASA preset.</li><li>Start with 0.20 mm layers, four walls, five top/bottom layers and 15% gyroid infill. Review every layer around the fine mesh, hanging holes and roof. Support requests are listed per part below.</li><li>Keep the front-left 18 × 28 mm exclusion clear. Mixed-color plates reserve a 50 × 50 mm rear corner for the slicer's prime tower. Check tower and brim boundaries in the sliced preview; their actual size depends on the slicer and material.</li><li>Send the sliced plate to your printer only after previewing it. No print duration or filament mass is asserted before slicing.</li></ol><ul>{colors}</ul>
<h2>2. Print and assemble</h2><table><thead><tr><th>Part</th><th>Color</th><th>Support / orientation</th></tr></thead><tbody>{parts}</tbody></table><ol>{instructions}</ol>
<p>Dry-fit the smallest mating pair first. Do not force a tight fit; use the STEP or parametric CAD to adjust the designed clearance to your material's shrinkage. Remove stringing and sharp edges from the printed mesh and openings.</p>
<p>{esc(mounting_guide)}</p>{camera_guide}
<h2>3. Seed, drainage and care</h2><p>These are dry-seed feeders. Match the seed to the designed openings, test flow with a small quantity, and confirm that whole seeds cannot escape the fine mesh. The printed lattice replaces transparent walls; no purchased clear sheet is required. Use a recycled bottle only where the design explicitly calls for one.</p><p>Before filling, pour a little water into the empty tray and confirm the drainage holes run free. Empty wet or spoiled seed promptly, brush blocked holes and allow the feeder to dry fully. Clean approximately every two weeks, more often in wet weather or heavy use, following <a href="{SOURCES['cleaning']}">Cornell's feeder-cleaning guidance</a>. Do not heat-sanitize a print beyond the material's rated temperature. Keep all removable parts accessible for cleaning.</p>
<h2>Design-specific notes</h2><ul>{notes}</ul>
<h2>Files included</h2><p>STL parts in assembly coordinates; STEP solids and assembly; color-assigned 3MF plates; <b>plate-layout.json</b> with exact placements and the AMS map; <b>checks.json</b> with digital validation; <b>assembly.glb</b> for viewing. Parametric CAD source is included when supplied alongside the model. CAD and print dimensions are millimetres. The GLB follows standard glTF units: metres, Y up.</p>
<footer>References: <a href="{SOURCES['x1c_profile']}">official X1C profile</a> · <a href="{SOURCES['3mf_core']}">3MF core format</a> · <a href="{SOURCES['asa']}">Bambu ASA guidance</a>. Packing margin 15 mm, bounding-box gap 8 mm, maximum used XY 240 mm, maximum part height 245 mm. Generated from this model's actual meshes, not reference-image geometry.</footer></main></body></html>'''
    palette_rows=''.join('<h3>Plate '+str(pl['number'])+'</h3><ul>'+''.join(f'<li>AMS slot {m["extruder"]}: {m["color"]}</li>' for m in pl['material_order'])+'</ul>' for pl in layout['plates'])
    doc=doc.replace('<h2>2. Print and assemble</h2>','<h2>Plate-specific AMS loads</h2>'+palette_rows+'<h2>2. Print and assemble</h2>')
    (folder/'PRINT-GUIDE.html').write_text(doc)

def package_design(path):
    folder=path.parent;design=json.loads(path.read_text());slug=design['id']
    objects=[inspect_part(folder,p,i) for i,p in enumerate(design['parts'])]
    materials=[]
    for p in design['parts']:
        for c in sorted(part_colors(p)):
            if c not in [m['color'] for m in materials]:materials.append({'extruder':len(materials)+1,'color':c,'name':f'{design_material(design)} / build color {len(materials)+1}'})
    checks={'design_id':slug,'status':'Digital checks only; physical prototype required','native_bambu_studio_roundtrip':False,'physical_test_print':False,'sources':SOURCES,'parts':[o['checks'] for o in objects],'build_color_limit':len(materials)<=7,'ams_four_color_per_part':all(len(part_colors(p))<=4 for p in design['parts'])}
    input_files={'design.json'}|{p['file'] for p in design['parts']}|{p['step'] for p in design['parts']}|{r['file'] for p in design['parts'] for r in p.get('regions',[p])}
    checks['input_sha256']={f:hashlib.sha256((folder/f).read_bytes()).hexdigest() for f in sorted(input_files)}
    audit_path=folder/'assembly-checks.json'
    audit_ok=True
    if audit_path.exists():
        assembly_audit=json.loads(audit_path.read_text())
        fresh=all((folder/f).exists() and hashlib.sha256((folder/f).read_bytes()).hexdigest()==sha for f,sha in assembly_audit.get('step_sha256',{}).items())
        audit_ok=fresh and assembly_audit.get('passed',False)
        checks['assembly_interference']={'performed':True,'fresh':fresh,'passed':audit_ok,'file':'assembly-checks.json'}
    else:
        checks['assembly_interference']={'performed':False,'passed':None};audit_ok=False
    failed=[p['name'] for p in checks['parts'] if not p['passed']]
    checks['passed']=not failed and checks['build_color_limit'] and checks['ams_four_color_per_part'] and audit_ok
    if not checks['passed']:
        checks['failure_reason']=f'Part validation failed: {failed}; colors={len(materials)}; assembly_audit_ok={audit_ok}'
        (folder/'checks.json').write_text(json.dumps(checks,indent=2));print('FAILED',slug,checks['failure_reason'],flush=True)
        for f in (folder/f'{slug}-X1C.zip',):
            if f.exists():f.unlink()
        return checks
    try:plates=pack(objects)
    except ValueError as e:
        checks['passed']=False;checks['failure_reason']=str(e);
        (folder/f'{slug}-X1C.zip').unlink(missing_ok=True);
        (folder/'checks.json').write_text(json.dumps(checks,indent=2));print('FAILED',slug,str(e),flush=True);return checks
    layout=make_layout(plates,materials)
    plate_dir=folder/'plates';plate_dir.mkdir(exist_ok=True)
    # Remove obsolete numbered output plates when regenerating a design.
    for f in plate_dir.glob('plate-*.3mf'):f.unlink()
    checks['plates']=[]
    for number,plate in enumerate(plates,1):
        for i,obj in enumerate(plate):
            assert obj['print_vertices'][:,2].min()>=-1e-5
            for other in plate[:i]:assert not overlap(obj['rect'],other['rect'])
            assert not overlap(obj['rect'],EXCLUSION)
            if len(plate_colors(plate))>1:assert tower_clear(obj['print_vertices'])
        local_materials=plate_materials(plate,materials)
        c=make_3mf(plate_dir/f'plate-{number:02}.3mf',design,plate,local_materials,number)
        if native_bambu.available():c.update(native_bambu.convert(plate_dir/f'plate-{number:02}.3mf'))
        checks['plates'].append(dict(number=number,bounding_boxes_nonoverlap=True,bed_and_exclusion_clear=True,**c))
    if any(hashlib.sha256((folder/f).read_bytes()).hexdigest()!=h for f,h in checks['input_sha256'].items()):raise RuntimeError('CAD changed while packaging; rerun after writer finishes')
    checks['plate_count']=len(plates)
    checks['native_bambu_studio_roundtrip']=all(p.get('native_bambu_studio_roundtrip',False) for p in checks['plates'])
    (folder/'checks.json').write_text(json.dumps(checks,indent=2))
    (folder/'plate-layout.json').write_text(json.dumps(layout,indent=2))
    make_glb(folder,design,objects);make_guide(folder,design,layout,checks)
    zpath=refresh_archive(folder)
    print('PACKAGED',slug,len(objects),'parts',len(plates),'plates',zpath.stat().st_size,'bytes',flush=True)
    return checks

def refresh_archive(folder):
    source_dir=folder/'sources';source_dir.mkdir(exist_ok=True)
    for name in ['common.py','originals.py','world.py','castles.py','sports.py','whimsy.py','future.py','vegas.py','vegas_arch_a.py','vegas_arch_b.py','vegas_cameras.py','backyard_camera.py','render_hardware.py','audit_backyard_camera.py','backyard_traditional.py','backyard_organic.py','backyard_gravity.py','backyard_structural.py','R7-GUIDE.md','SOURCE-GUIDE.html','package_collection.py','native_bambu.py','read_3mf.py','sanitize_stl.py','audit_assembly.py','finalize_step_exports.py','render_catalog.py']:
        source=Path(__file__).resolve().parent/name
        if source.exists():shutil.copy2(source,source_dir/name)
    slug=folder.name
    zpath=folder/f'{slug}-X1C.zip'
    fd,tmp_name=tempfile.mkstemp(prefix=f'.{slug}-',suffix='.zip',dir=folder)
    os.close(fd);tmp_path=Path(tmp_name)
    try:
        with zipfile.ZipFile(tmp_path,'w',zipfile.ZIP_DEFLATED) as z:
            d=json.loads((folder/'design.json').read_text())
            names={'design.json','preview.png','plate-layout.json','checks.json','assembly-checks.json','assembly-validation.json','castle-validation.json','future-validation.json','joint-validation.json','PRINT-GUIDE.html','assembly.glb',slug+'.step'}|{p['file'] for p in d['parts']}|{p['step'] for p in d['parts']}|{r['file'] for p in d['parts'] for r in p.get('regions',[p])}
            selected=[folder/n for n in sorted(names) if (folder/n).exists()]+sorted((folder/'plates').glob('*.3mf'))+[f for f in sorted(source_dir.glob('*')) if f.is_file()]
            for f in selected:z.write(f,str(Path(slug)/f.relative_to(folder)))
        with zipfile.ZipFile(tmp_path) as z:assert z.testzip() is None
        with tmp_path.open('rb') as handle:os.fsync(handle.fileno())
        tmp_path.replace(zpath)
    finally:tmp_path.unlink(missing_ok=True)
    return zpath

def write_summary():
    hold_file=Path(tempfile.gettempdir())/'nestforge-r2-packaging-holds.json'
    holds=json.loads(hold_file.read_text()) if hold_file.exists() else []
    results=[]
    for p in sorted(EXPORT.glob('*/design.json')):
        if json.loads(p.read_text()).get('revision') not in ('R2','R5','R6','R7'):continue
        cp=p.parent/'checks.json';r=json.loads(cp.read_text()) if cp.exists() else {'design_id':p.parent.name,'passed':False}
        r=dict(r);r['held']=p.parent.name in holds;r['archive_available']=(p.parent/f'{p.parent.name}-X1C.zip').exists()
        r['archive_crc_ok']=False
        if r['archive_available']:
            try:
                with zipfile.ZipFile(p.parent/f'{p.parent.name}-X1C.zip') as z:r['archive_crc_ok']=z.testzip() is None
            except (OSError,zipfile.BadZipFile):pass
        r['deliverable_passed']=r.get('passed',False) and r['archive_crc_ok'] and not r['held']
        results.append(r)
    summary={'designs':len(results),'passed':sum(r['deliverable_passed'] for r in results),'held':[r['design_id'] for r in results if r['held']],'failed':[r['design_id'] for r in results if not r.get('passed',False) and not r['held']],'parts':sum(len(r.get('parts',[])) for r in results if r['deliverable_passed']),'plates':sum(r.get('plate_count',0) for r in results if r['deliverable_passed']),'native_bambu_designs':sum(bool(r.get('native_bambu_studio_roundtrip')) for r in results if r['deliverable_passed']),'results':[{k:v for k,v in r.items() if k in ['design_id','passed','deliverable_passed','held','archive_available','archive_crc_ok','plate_count','native_bambu_studio_roundtrip','failure_reason']} for r in results]}
    (EXPORT/'packaging-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--only',nargs='+');parser.add_argument('--archives-only',action='store_true');parser.add_argument('--changed-only',action='store_true');args=parser.parse_args()
    paths=[p for p in sorted(EXPORT.glob('*/design.json')) if json.loads(p.read_text()).get('revision') in ('R2','R5','R6','R7')]
    if args.only:paths=[p for p in paths if p.parent.name in args.only]
    hold_file=Path(tempfile.gettempdir())/'nestforge-r2-packaging-holds.json'
    holds=json.loads(hold_file.read_text()) if hold_file.exists() else []
    for p in paths:
        if p.parent.name in holds:print('HELD',p.parent.name,flush=True)
    paths=[p for p in paths if p.parent.name not in holds]
    if args.archives_only:
        for p in paths:
            cp=p.parent/'checks.json'
            if cp.exists() and json.loads(cp.read_text()).get('passed'):
                archive=refresh_archive(p.parent);print('REFRESHED',archive.name,flush=True)
        write_summary()
        return
    results=[]
    for p in paths:
        cp=p.parent/'checks.json'
        if args.changed_only and cp.exists():
            prev=json.loads(cp.read_text());hashes=prev.get('input_sha256',{})
            if hashes and prev.get('passed') and prev.get('native_bambu_studio_roundtrip') and all((p.parent/f).exists() and hashlib.sha256((p.parent/f).read_bytes()).hexdigest()==h for f,h in hashes.items()):
                print('UNCHANGED',p.parent.name,flush=True);continue
        try:results.append(package_design(p))
        except Exception as e:
            print('ERROR',p.parent.name,type(e).__name__,str(e),flush=True)
            r={'design_id':p.parent.name,'passed':False,'failure_reason':f'{type(e).__name__}: {e}'}
            (p.parent/'checks.json').write_text(json.dumps(r,indent=2));(p.parent/f'{p.parent.name}-X1C.zip').unlink(missing_ok=True);results.append(r)
    write_summary()


if __name__=='__main__':main()
