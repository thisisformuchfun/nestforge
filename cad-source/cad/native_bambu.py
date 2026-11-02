"""Native Bambu Studio conversion of a positioned unsliced 3MF.

Set BAMBUSTUDIO_BIN to the real Bambu Studio executable, or put it on PATH.
BAMBUSTUDIO_PROFILES must point at its resources/profiles/BBL directory.
BAMBUSTUDIO_LIB is optional, command-scoped shared-library search directories.
This tool never slices or transmits a print. It imports with official flattened
profiles, exports natively, then checks positions, colors, assignments and volume.
"""
from pathlib import Path
import json,os,shutil,subprocess,tempfile,zipfile
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
from scipy.optimize import linear_sum_assignment
from read_3mf import read as read_3mf
_bin=os.environ.get('BAMBUSTUDIO_BIN') or shutil.which('bambu-studio') or shutil.which('BambuStudio')
_profiles=os.environ.get('BAMBUSTUDIO_PROFILES')
BIN=Path(_bin).expanduser().resolve() if _bin else None
PROFILES=Path(_profiles).expanduser().resolve() if _profiles else None
LIB=os.environ.get('BAMBUSTUDIO_LIB')
_CACHE={}

def available():return BIN is not None and PROFILES is not None and BIN.is_file() and PROFILES.is_dir()

def official_profile(name):
    if name in _CACHE:return dict(_CACHE[name])
    index={p.stem:p for p in PROFILES.rglob('*.json')}
    def flatten(n):
        d=json.loads(index[n].read_text());out={}
        if d.get('inherits'):out.update(flatten(d['inherits']))
        for item in d.get('include',[]):out.update(flatten(item))
        out.update(d);out.pop('include',None);out.pop('inherits',None);return out
    _CACHE[name]=flatten(name);return dict(_CACHE[name])

def mapping(xml):
    result={}
    for obj in ET.fromstring(xml).findall('object'):
        kv={e.get('key'):e.get('value') for e in obj.findall('metadata') if e.get('key')}
        parts={}
        for p in obj.findall('part'):
            pk={e.get('key'):e.get('value') for e in p.findall('metadata') if e.get('key')}
            parts[pk.get('name')]=int(pk.get('extruder',kv.get('extruder','1')))
        result[kv.get('name')]=parts
    return result

def convert(path):
    path=Path(path).resolve()
    with zipfile.ZipFile(path) as z:
        settings=json.loads(z.read('Metadata/project_settings.config'))
        assignments=mapping(z.read('Metadata/model_settings.config'))
    before=read_3mf(path);before_volume=before.to_geometry().volume
    types=set(settings.get('filament_type',['PETG']))
    if len(types)!=1 or not types.issubset({'PETG','ASA'}):raise ValueError(f'Unsupported filament types: {types}')
    filament_name='Generic '+next(iter(types))
    machine=official_profile('Bambu Lab X1 Carbon 0.4 nozzle');process=official_profile('0.20mm Standard @BBL X1C');filament=official_profile(filament_name)
    for k in ['wall_loops','top_shell_layers','bottom_shell_layers','sparse_infill_density','sparse_infill_pattern','brim_type','brim_width','enable_support','enable_prime_tower','prime_tower_width','prime_tower_brim_width','wipe_tower_x','wipe_tower_y']:
        process[k]=settings[k]
    machine['filament_colour']=settings['filament_colour'];machine['curr_bed_type']='Textured PEI Plate'
    env=os.environ.copy();env['LC_ALL']='C'
    if LIB:env['LD_LIBRARY_PATH']=LIB
    with tempfile.TemporaryDirectory(prefix='nestforge-native-') as tmp:
        tmp=Path(tmp);presets=[];filaments=[]
        for name,obj in [('machine',machine),('process',process)]:
            p=tmp/f'{name}.json';p.write_text(json.dumps(obj));presets.append(str(p))
        for i,color in enumerate(settings['filament_colour']):
            f=dict(filament);f['filament_colour']=[color];p=tmp/f'filament-{i+1}.json';p.write_text(json.dumps(f));filaments.append(str(p))
        out=tmp/'native.3mf'
        cmd=[str(BIN),'--datadir',str(tmp/'config'),'--debug','1','--arrange','0','--orient','0','--load-settings',';'.join(presets),'--load-filaments',';'.join(filaments),'--export-3mf',str(out),str(path)]
        r=subprocess.run(cmd,env=env,cwd=tmp,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=90)
        if r.returncode or not out.exists():raise RuntimeError('Bambu Studio native export failed: '+r.stdout[-1800:])
        with zipfile.ZipFile(out) as z:
            output_settings=json.loads(z.read('Metadata/project_settings.config'))
            app=ET.fromstring(z.read('3D/3dmodel.model')).find("{*}metadata[@name='Application']").text
            assert app.startswith('BambuStudio-'),f'Unexpected native exporter: {app}'
            version='.'.join(str(int(v)) for v in app.removeprefix('BambuStudio-').split('.'))
            assert output_settings['filament_colour']==settings['filament_colour']
            assert output_settings['filament_type']==settings['filament_type']
            assert output_settings['printer_model']=='Bambu Lab X1 Carbon'
            assert output_settings['printable_area']==['0x0','256x0','256x256','0x256']
            assert mapping(z.read('Metadata/model_settings.config'))==assignments, f"Material assignments changed {assignments} -> {mapping(z.read('Metadata/model_settings.config'))}"
            assert not any(n.endswith('.gcode') for n in z.namelist())
        after=read_3mf(out);after_volume=after.to_geometry().volume
        if os.environ.get('NESTFORGE_NATIVE_DEBUG'):(Path(tempfile.gettempdir())/'nestforge-r2-native-debug.3mf').write_bytes(out.read_bytes())
        assert len(after.geometry)==len(before.geometry)
        assert np.allclose(after.bounds,before.bounds,atol=2e-4), f'Native bounds changed {before.bounds.tolist()} -> {after.bounds.tolist()}'
        assert np.isclose(after_volume,before_volume,rtol=2e-5)
        # Verify each separate part stayed in position, not just aggregate bounds.
        def instance_bounds(scene):
            bounds=[]
            for node in scene.graph.nodes_geometry:
                transform,name=scene.graph[node];mesh=scene.geometry[name].copy();mesh.apply_transform(transform);bounds.append(mesh.bounds)
            return np.asarray(bounds)
        # Serialization rounds coordinates; sorting on near-equal X minima can
        # reorder two untouched regions. Match every box one-to-one instead.
        before_boxes=instance_bounds(before);after_boxes=instance_bounds(after)
        errors=np.max(np.abs(before_boxes[:,None]-after_boxes[None,:]),axis=(2,3))
        rows,cols=linear_sum_assignment(errors)
        assert np.all(errors[rows,cols]<=2e-4),f'Native instance bounds changed: {errors[rows,cols].tolist()}'
        native_data=out.read_bytes()
        # Native re-open is a second independent target-application import.
        rr=subprocess.run([str(BIN),'--datadir',str(tmp/'config'),'--debug','1','--arrange','0','--orient','0','--info',str(out)],env=env,cwd=tmp,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=90)
        if rr.returncode:raise RuntimeError('Bambu Studio could not reopen its native export: '+rr.stdout[-1800:])
        path.write_bytes(native_data)
    return {'native_bambu_studio_roundtrip':True,'bambu_version':version,'official_presets':['Bambu Lab X1 Carbon 0.4 nozzle','0.20mm Standard @BBL X1C',filament_name],'native_extruders_verified':True,'native_palette_verified':True,'native_positions_verified':True,'contains_gcode':False,'native_volume_relative_error':abs(after_volume-before_volume)/before_volume}
