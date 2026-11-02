"""Render exact region STL geometry in the supplied assembly-to-plate transforms.
Estimates are geometric planning ranges, deliberately not claimed as slicer results.
"""
from pathlib import Path
import json, math, struct, ctypes, subprocess, tempfile, gzip
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
libpath=Path(tempfile.gettempdir())/'nestforge-plate-raster.so'
subprocess.run(['cc','-O3','-shared','-fPIC',str(ROOT/'scripts/plate-raster.c'),'-o',str(libpath),'-lm'],check=True)
lib=ctypes.CDLL(str(libpath));raster=lib.raster
raster.argtypes=[ctypes.c_int]*3+[ctypes.c_void_p]*4
W,H=1000,820
cam=np.array([.55,-.7,1.0]);cam/=np.linalg.norm(cam)
right=np.array([-.0-cam[1],cam[0],0]);right/=np.linalg.norm(right);up=np.cross(cam,right)
light=np.array([-.4,-.6,1]);light/=np.linalg.norm(light)
plate=np.array([[0,0,0],[256,0,0],[256,256,0],[0,256,0]],float)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def stl(p):
 b=gzip.decompress(p.read_bytes()) if p.suffix==".gz" else p.read_bytes();n=struct.unpack_from('<I',b,80)[0]
 assert len(b)==84+50*n,str(p)
 return np.frombuffer(b,offset=84,count=n,dtype=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]))['v'].astype(float)
def build(d):
 directory=DIST/'models'/d['id'];layout=json.loads((directory/'plate-layout.json').read_text());result=[]
 for p in layout['plates']:
  meshes=[];active={};volumes=0;filament=0;height=0
  for obj in p['objects']:
   mat=np.array(obj['assembly_to_plate_matrix'])
   for reg in obj['regions']:
    t=stl(directory/reg['file']);t=t@mat[:3,:3].T+mat[:3,3]
    cross=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);areas=np.linalg.norm(cross,axis=1)/2
    normals=cross/np.maximum(areas[:,None]*2,1e-12)
    vol=abs(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6);volumes+=vol
    # Shell budget: four 0.42-mm walls and five 0.2-mm top/bottom layers.
    shell=(areas*(1.68*np.sqrt(np.maximum(0,1-normals[:,2]**2))+1.0*np.abs(normals[:,2]))).sum()
    filament+=min(vol,shell)+.15*max(0,vol-shell)
    z=t[:,:,2];height=max(height,float(z.max()))
    lo=np.maximum(0,np.ceil(z.min(axis=1)/.2-.5).astype(int));hi=np.maximum(-1,np.floor(z.max(axis=1)/.2-.5).astype(int))
    n=max(1,math.ceil(float(z.max())/.2));a=active.setdefault(reg['color'],np.zeros(1400,dtype=int))
    ok=(hi>=lo)&(lo<len(a)-1);lo=lo[ok];hi=np.minimum(hi[ok],len(a)-2)
    np.add.at(a,lo,1);np.add.at(a,hi+1,-1)
    rgb=np.array([int(reg['color'][i:i+2],16) for i in (1,3,5)],float)
    shade=.42+.58*np.maximum(0,normals@light);colors=np.clip(rgb*shade[:,None],0,255).astype('uint8')
    meshes.append((t,colors))
  occupied=np.stack([np.cumsum(v)>0 for v in active.values()]).sum(axis=0)
  changes=int(np.maximum(occupied-1,0).sum());layers=math.ceil(height/.2)
  # Effective deposited flow 5–10 mm³/s; 30–65s per modeled layer color change.
  # Adds setup and per-layer overhead; supports are excluded (not yet generated).
  low=(filament/10+layers*1.0+changes*30+480)/3600
  high=(filament/5+layers*2.0+changes*65+900)/3600
  low=math.floor(low*2)/2;high=math.ceil(high*2)/2
  allpts=np.concatenate([plate]+[t.reshape(-1,3) for t,c in meshes]);xx=allpts@right;yy=allpts@up
  scale=min((W-120)/(xx.max()-xx.min()),(H-135)/(yy.max()-yy.min()));cx=(xx.max()+xx.min())/2;cy=(yy.max()+yy.min())/2
  def proj(a):return np.stack([(a@right-cx)*scale+W/2,-(a@up-cy)*scale+H/2-15,a@cam],axis=-1)
  base=Image.new('RGB',(W,H),(12,32,29));draw=ImageDraw.Draw(base);pp=proj(plate)[:,:2]
  draw.polygon([tuple(x) for x in pp],fill=(42,58,53),outline=(133,155,133),width=3)
  for k in range(0,257,16):
   for line in [np.array([[k,0,0],[k,256,0]]),np.array([[0,k,0],[256,k,0]])]:draw.line([tuple(x) for x in proj(line)[:,:2]],fill=(62,79,68),width=1)
  exclusion=np.array([[0,0,0],[18,0,0],[18,28,0],[0,28,0]])
  draw.polygon([tuple(x) for x in proj(exclusion)[:,:2]],fill=(98,63,44))
  if p.get('prime_tower_reserved'):
   x0,y0,x1,y1=p['prime_tower_reserved'];coords=proj(np.array([[x0,y0,0],[x1,y0,0],[x1,y1,0],[x0,y1,0]]))[:,:2]
   draw.polygon([tuple(x) for x in coords],fill=(56,61,48),outline=(175,160,113),width=2)
  image=np.array(base);depth=np.full((H,W),-1e10,dtype='float32')
  for tri,col in meshes:
   screen=np.ascontiguousarray(proj(tri),dtype='float32');col=np.ascontiguousarray(col)
   raster(W,H,len(tri),screen.ctypes.data,col.ctypes.data,image.ctypes.data,depth.ctypes.data)
  im=Image.fromarray(image);draw=ImageDraw.Draw(im)
  draw.text((35,H-65),f'X1C  /  PLATE {p["number"]:02d}',font=ImageFont.truetype(FONT,23),fill=(191,210,182))
  draw.text((W-260,H-65),'256 × 256 mm',font=ImageFont.truetype(FONT,23),fill=(150,174,155))
  filename=f'plate-{p["number"]:02d}-preview.webp';im.resize((610,500),Image.Resampling.LANCZOS).save(directory/'plates'/filename,quality=76,method=6)
  result.append({'number':p['number'],'preview':'plates/'+filename,'file':p['file'],'parts':[o['name'] for o in p['objects']],'piece_count':len(p['objects']),'colors':p.get('material_order',layout['material_order']),'time_hours':[max(.5,low),max(1,high)],'estimated_color_changes':changes,'reserved_prime_tower':bool(p.get('prime_tower_reserved'))})
 plan={'design_id':d['id'],'plate_count':len(result),'total_time_hours':[sum(p['time_hours'][i] for p in result) for i in range(2)],'estimate_status':'Unsliced geometric planning range; confirm in Bambu Studio. Supports excluded.','assumptions':{'layer_height_mm':.2,'nozzle_mm':.4,'walls':4,'infill_percent':15,'effective_flow_mm3_s':[5,10],'color_change_seconds':[30,65]},'plates':result}
 (directory/'print-plan.json').write_text(json.dumps(plan,indent=2)+'\n');print(d['id'],len(result),plan['total_time_hours'],flush=True)
 return {k:plan[k] for k in ['plate_count','total_time_hours']}
if __name__=='__main__':
 catalog=json.loads((DIST/'catalog.json').read_text());summary={d['id']:build(d) for d in catalog};(DIST/'print-plan-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
