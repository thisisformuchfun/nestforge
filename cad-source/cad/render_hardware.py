"""Illustrative purchased hardware for R7 catalog renders, never print exports.

Camera bodies use published overall dimensions; optical positions and contours
are illustrative. Birdfy's body is a 90mm display placeholder within its published
230mm antenna envelope, not a dimensioned camera CAD model.
"""
from pathlib import Path
import tempfile
import cadquery as cq
import numpy as np
from PIL import ImageColor
from backyard_camera import place
from common import box as B

def camera_shapes(metadata):
 p=metadata.get('camera_mount',{});camera_id=metadata['camera_default'];pose=metadata.get('camera_pose',{})
 w=p['width'];d=p['depth'];h=p.get('height') or 90.;front=p.get('front_y',0);floor=p.get('floor_z',0)
 shapes=[]
 def add(s,color):shapes.append((place(s.translate((0,front,floor)),pose),color))
 def roundbox(w,d,h,x,y,z,r):return B(w,d,h,x,y,z).edges().fillet(min(r,w*.4,d*.4,h*.4))
 add(roundbox(w,d,h,0,d/2,0,6),'#D8DDD5')
 add(roundbox(w-3,1.2,h-3,0,.05,1.5,.45),'#192726')
 def disc(radius,x,z,y=-.65,depth=.45):return cq.Workplane('XZ').center(x,z).circle(radius).extrude(depth).translate((0,y,0))
 lensz=h*.705;lensr=min(w*.176,11.2)
 add(disc(lensr+1,0,lensz),'#62706E')
 add(disc(lensr,0,lensz,-1.1),'#102E39')
 add(disc(lensr*.60,0,lensz,-1.6),'#071A22')
 add(disc(lensr*.18,-lensr*.28,lensz+lensr*.3,-2.1),'#75999F')
 add(roundbox(21,1.1,16,0,-.25,h*.265-8,.4),'#B2C6BE')
 for x in [-w*.29,w*.29]:add(disc(2.5,x,h*.515,-.9),'#483A44')
 if 'birdfy' in camera_id:
  total=p.get('height_with_antenna',230);ah=total-h
  add(cq.Workplane('XY').center(w*.3,d*.78).circle(2.5).extrude(ah).translate((0,0,h)),'#CCD3CC')
 for item in metadata.get('extra_hardware',[]):
  if item.get('type')!='recycled-bottle':continue
  r=item.get('nominal_diameter_mm',68)/2;nr=item.get('neck_diameter_mm',28)/2
  height=item.get('overall_height_mm',205);shoulder=item.get('neck_and_shoulder_height_mm',45)
  bottle_pose=item.get('pose',{'translation':item.get('position',[0,0,0])})
  neck=cq.Workplane('XY').circle(nr).extrude(22)
  shoulder_shape=cq.Workplane('XY').add(cq.Solid.makeCone(nr,r,shoulder-22)).translate((0,0,22))
  body=cq.Workplane('XY').circle(r).extrude(height-shoulder).translate((0,0,shoulder))
  bottle=neck.union(shoulder_shape).union(body)
  for z in range(int(shoulder+14),int(height-8),18):
   bottle=bottle.union(cq.Workplane('XY').circle(r+.65).extrude(2).translate((0,0,z)))
  bottle=bottle.union(cq.Workplane('XY').circle(nr+3).extrude(2).translate((0,0,21)))
  shapes.append((place(bottle,bottle_pose),'#8DAA94'))
 return shapes

def hardware_meshes(metadata,reader):
 if not metadata.get('camera_system'):return []
 result=[]
 with tempfile.TemporaryDirectory(prefix='nestforge-display-hardware-') as tmp:
  for i,(s,color) in enumerate(camera_shapes(metadata)):
   f=Path(tmp)/f'{i}.stl';cq.exporters.export(s,str(f),tolerance=.1,angularTolerance=.12)
   points,normals=reader(f);rgb=np.asarray(ImageColor.getrgb(color)[:3])/255.
   result.append((points,normals,np.broadcast_to(rgb,(len(points),3)).copy()))
 return result
