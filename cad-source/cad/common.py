"""NestForge R5: physical CAD solids and welded, non-overlapping color regions.
All geometry is millimetres, assembly coordinates, Z up. Export is atomic.
"""
from pathlib import Path
import cadquery as cq
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
import json, math, os, re, shutil, tempfile, hashlib, fcntl
ROOT=Path(os.environ.get('NESTFORGE_EXPORTS', str(Path(__file__).resolve().parent.parent/'exports')))
def cyl(r,h,z=0): return cq.Workplane('XY').circle(r).extrude(h).translate((0,0,z))
def ring(ro,ri,h,z=0): return cq.Workplane('XY').circle(ro).circle(ri).extrude(h).translate((0,0,z))
def box(x,y,z,px=0,py=0,pz=0): return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate((px,py,pz))
def cone(r1,r2,h,z=0): return cq.Workplane('XY').add(cq.Solid.makeCone(r1,r2,h)).translate((0,0,z))
def drain(shape,points,r=1.1):
 for x,y in points: shape=shape.cut(cyl(r,12,-2).translate((x,y,0)))
 return shape

def solid(s):
 return s.val() if isinstance(s,cq.Workplane) else s

def _stem(s):return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
def _bounds(s):
 b=Bnd_Box();BRepBndLib.AddOptimal_s(s.wrapped,b,False,False);return list(b.Get())
def _read_complete_step(path):
 # Keep native-writer bytes immutable; managed mounts can yield a transient
 # empty read even after a successful OCC writer and reader have returned.
 for _ in range(3):
  data=Path(path).read_bytes()
  if len(data)>100 and data.lstrip().startswith(b'ISO-10303-21;') and data.rstrip().endswith(b'END-ISO-10303-21;'):
   return data
 raise ValueError(f'Empty or incomplete STEP bytes: {path}')

def _export(s,path):
 if path.suffix=='.stl':
  cq.exporters.export(s,str(path),tolerance=.10,angularTolerance=.12)
  if path.stat().st_size<100:raise ValueError(f'Empty export: {path}')
  return None
 # Isolate native STEP I/O from managed workspace mounts, then commit bytes.
 with tempfile.TemporaryDirectory(prefix='nestforge-step-') as stage:
  native=Path(stage)/path.name
  cq.exporters.export(s,str(native))
  data=_read_complete_step(native)
 atomic_bytes(path,data)
 return data

def atomic_bytes(path,data):
 """Replace a complete byte file; never truncate a published path."""
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmpname=tempfile.mkstemp(prefix='.'+path.name+'-',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as stream:
   stream.write(data);stream.flush();os.fsync(stream.fileno())
  os.replace(tmpname,path)
  dfd=os.open(path.parent,os.O_RDONLY)
  try:os.fsync(dfd)
  finally:os.close(dfd)
 finally:
  if os.path.exists(tmpname):os.unlink(tmpname)

def cache_validated_steps(slug,steps,design_sha256=None):
 cache=ROOT/'.step-cache'/slug;cache.mkdir(parents=True,exist_ok=True)
 manifest_path=cache/'manifest.json'
 manifest={'slug':slug,'files':{}}
 for filename,data in steps.items():
  if len(data)<100:raise ValueError('Refusing empty validated STEP cache entry')
  digest=hashlib.sha256(data).hexdigest()
  # Immutable content-addressed bytes; manifest commits only after their fsync.
  blob=filename+'.'+digest+'.bin'
  if not (cache/blob).exists():atomic_bytes(cache/blob,data)
  if hashlib.sha256((cache/blob).read_bytes()).hexdigest()!=digest:raise ValueError('STEP cache checksum mismatch')
  manifest['files'][filename]={'blob':blob,'sha256':digest,'bytes':len(data),'validated':'BREP readback'}
 if design_sha256 is not None:
  manifest['design_sha256']=design_sha256
  atomic_bytes(manifest_path,json.dumps(manifest,indent=2).encode())

def export_design(slug,*args,**kwargs):
 ROOT.mkdir(parents=True,exist_ok=True)
 lockdir=ROOT/'.export-locks';lockdir.mkdir(exist_ok=True)
 with open(lockdir/(slug+'.lock'),'a+b') as lock:
  fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
  try:return _export_design_locked(slug,*args,**kwargs)
  finally:fcntl.flock(lock.fileno(),fcntl.LOCK_UN)

def _export_design_locked(slug,name,family,description,parts,notes=None,assembly=None,reference=None,*,hanger=None,snap_joints=None,refill=None,detail_features=None,**extra):
 ROOT.mkdir(parents=True,exist_ok=True)
 out=ROOT/slug;tmp=Path(tempfile.mkdtemp(prefix=f'.{slug}-',dir=ROOT))
 records=[];a=cq.Assembly(name=slug);validated_steps={}
 try:
  for i,p in enumerate(parts):
   s=solid(p['shape']).clean()
   if not s.isValid():raise ValueError(f'{slug}/{p["name"]}: invalid BREP')
   if len(s.Solids())!=1:raise ValueError(f'{slug}/{p["name"]}: {len(s.Solids())} disconnected solids; physical part must be fused')
   base=f'{i+1:02d}-{_stem(p["name"])}'
   _export(s,tmp/(base+'.stl'));step_bytes=_export(s,tmp/(base+'.step'))
   # Read back every STEP before committing the export. This catches empty/truncated writers.
   reread=cq.importers.importStep(str(tmp/(base+'.step'))).val()
   if not reread.isValid() or len(reread.Solids())!=1 or max(abs(a-b) for a,b in zip(_bounds(reread),_bounds(s)))>.002 or abs(reread.Volume()-s.Volume())>max(.02,s.Volume()*5e-5):raise ValueError(f'{base}: STEP roundtrip mismatch valid={reread.isValid()} solids={len(reread.Solids())} volume={s.Volume()} -> {reread.Volume()} bounds={_bounds(s)} -> {_bounds(reread)}')
   validated_steps[base+'.step']=step_bytes
   region_records=[];remaining=s
   accents=[]
   for j,r in enumerate(p.get('regions',[])):
    rr=solid(r['shape']).intersect(remaining).clean()
    if not rr.Solids() or rr.Volume()<1e-5:continue
    if not rr.isValid():raise ValueError(f'{base}/{r.get("name",j)}: invalid color region')
    accents.append((r,rr));remaining=remaining.cut(rr).clean()
   regions=[]
   if remaining.Solids() and remaining.Volume()>1e-5:regions.append(({'name':p['name']+' base','color':p['color']},remaining))
   regions+=accents
   if not accents:regions=[({'name':p['name'],'color':p['color']},s)]
   total=sum(rr.Volume() for _,rr in regions)
   if abs(total-s.Volume())>max(.05,s.Volume()*1e-5):raise ValueError(f'{base}: color partition volume mismatch')
   for j,(r,rr) in enumerate(regions):
    rf=f'{base}-region-{j+1:02d}.stl' if accents else base+'.stl'
    if accents:_export(rr,tmp/rf)
    color=r['color'].upper()
    region_records.append(dict(name=r['name'],file=rf,color=color,volume_mm3=rr.Volume()))
    a.add(rr,name=f'{base}-region-{j+1:02d}',color=cq.Color(color))
   rec=dict(name=p['name'],file=base+'.stl',step=base+'.step',color=p['color'].upper(),explode=p.get('explode',[0,0,40*(i+1)]),bounds=_bounds(s),volume_mm3=s.Volume(),step_roundtrip_relative_volume_error=abs(reread.Volume()-s.Volume())/s.Volume(),solids=len(s.Solids()),support=p.get('support','None; upright'),print_rotation=p.get('print_rotation',[0,0,0]),regions=region_records)
   for k in ['purpose','material','print_notes']: 
    if k in p:rec[k]=p[k]
   records.append(rec)
  cache_validated_steps(slug,validated_steps)
  with tempfile.TemporaryDirectory(prefix='nestforge-assembly-') as stage:
   native=Path(stage)/(slug+'.step')
   a.save(str(native))
   assembly_bytes=_read_complete_step(native)
   assembly_readback=cq.importers.importStep(str(native)).val()
  atomic_bytes(tmp/(slug+'.step'),assembly_bytes)
  if not assembly_readback.isValid() or assembly_readback.Volume()<=0:raise ValueError('Invalid assembly STEP readback')
  validated_steps[slug+'.step']=assembly_bytes
  cache_validated_steps(slug,validated_steps)
  # Restore immutable validated bytes into staging before atomic publication.
  for filename,data in validated_steps.items():
   target=tmp/filename
   if target.read_bytes()!=data:print('RESTORED validated STEP bytes',slug,filename,flush=True)
   atomic_bytes(target,data)
  if (tmp/(slug+'.step')).stat().st_size<100:raise ValueError('Empty assembly STEP')
  colors=list(dict.fromkeys(r['color'] for p in records for r in p['regions']))
  if len(colors)>7:raise ValueError(f'{slug}: {len(colors)} colors exceeds 7')
  mounting_type=extra.get('mounting',{}).get('type','hanging')
  method=extra.pop('assembly_method','Positive snap joints; '+('one hanger suspends completed assembly' if mounting_type=='hanging' else mounting_type+' attachment supports the rigid assembly'))
  metadata=dict(id=slug,name=name,family=family,description=description,parts=records,notes=notes or [],assembly=assembly or [],reference=reference,revision=extra.pop('revision','R5'),status='Digital prototype — physical snap, load and feed trials required',hanger=hanger,snap_joints=snap_joints or [],refill=refill,detail_features=detail_features or [],colors=colors,color_count=len(colors),assembly_method=method,**extra)
  metadata_bytes=json.dumps(metadata,indent=2).encode()
  atomic_bytes(tmp/'design.json',metadata_bytes)
  cache_validated_steps(slug,validated_steps,hashlib.sha256(metadata_bytes).hexdigest())
  out.mkdir(parents=True,exist_ok=True)
  # Replace individual files atomically; publish metadata last as commit marker.
  for f in tmp.iterdir():
   if f.name!='design.json':os.replace(f,out/f.name)
  os.replace(tmp/'design.json',out/'design.json')
  directory_fd=os.open(out,os.O_RDONLY)
  try:os.fsync(directory_fd)
  finally:os.close(directory_fd)
  for filename,data in validated_steps.items():
   if (out/filename).read_bytes()!=data:raise ValueError(f'Atomic STEP commit mismatch {slug}/{filename}')
  print('EXPORTED',slug,len(parts),'physical parts',len(colors),'colors',flush=True)
  return metadata
 finally:shutil.rmtree(tmp,ignore_errors=True)
