"""R7 independently structured barrel-vault and lattice-wall camera feeders."""
import argparse, math, os, json
from pathlib import Path
import cadquery as cq
from common import box as B, cyl, export_design
from backyard_camera import camera_grip, profile, place

WYZE='wyze-battery-cam-pro'; BIRDFY='birdfy-cam-2k'

def ellipse(rx,ry,h,x=0,y=0,z=0):
 return cq.Workplane('XY').ellipse(rx,ry).extrude(h).translate((x,y,z))

def ycyl(r,length,y,z):
 return cq.Workplane('XZ').circle(r).extrude(length).translate((0,y,z))

def holes_y(shape,points,r=2.4):
 for x,z in points:
  cutter=cq.Workplane('XZ').center(x,z).circle(r).extrude(70).translate((0,50,0))
  shape=shape.cut(cutter)
 return shape

def bar_between(a,b,r):
 v=cq.Vector(*b)-cq.Vector(*a)
 return cq.Workplane().add(cq.Solid.makeCylinder(r,v.Length,cq.Vector(*a),v.normalized()))

def metadata(camera,pose,target,mount,form,seed,integration,signature):
 return dict(revision='R7',detail_revision='R7',material='ASA',camera_system=True,
  camera_default=camera,camera_profiles=[camera],camera_part_index=0,
  camera_mount=profile(camera),camera_pose=pose,feeding_target=target,mounting=mount,
  architecture=dict(form=form,seed_system=seed,camera_integration=integration,signature=signature),
  prototype_validation=dict(physical_print_test=False,snap_test=False,load_test=False,camera_fit_test=False,focus_test=False),
  assembly_method='Accessible positive snap lid; rigid integral feeder body and camera seat')

def woven_arch(blockout=False):
 pose=dict(translation=[0,35,9],rotation=[0,0,0])
 # The trough is a long oval basin, distinct from the supporting rear tunnel floor.
 body=ellipse(89,38,23,y=-48)
 body=body.cut(ellipse(84.8,33.8,25,y=-48,z=4)).edges('>Z').fillet(.8)
 # Rear floor and low side sills distribute the camera and trough loads to the vault hooks.
 body=body.union(B(179,91,4,0,34,0))
 for sign in [-1,1]:
  body=body.union(B(5.8,162,20,sign*89.5,0,0))
 body=body.union(B(179,5,31,0,77,0))
 body=body.cut(B(65,12,32,0,77,8.5))
 # The completed feeder hangs through the roof eye and four positive side hooks.
 body=body.union(place(camera_grip(WYZE),pose)).union(B(66,50,2.1,0,58,3.8))
 # Four integral free-ended exterior latches, with finger pads accessible outside.
 for xsign in [-1,1]:
  for y in [-54,48]:
   body=body.union(B(7.6,12,6,xsign*94, y,0))
   body=body.union(B(1.6,10,26,xsign*97,y,5))
   body=body.union(B(6.6,10,2,xsign*94.5,y,29))
   body=body.union(B(3,12,3,xsign*98,y,27))
 for x in [-65,-35,0,35,65]:
  body=body.cut(cyl(1.3,7,-1).translate((x,-48,0)))
 # True half-cylinder roof: open front and rear, not an A-frame or a seed box.
 shell=ycyl(94,170,85,31).cut(ycyl(90.4,172,86,31)).intersect(B(210,180,110,0,0,31))
 for sign in [-1,1]:
  shell=shell.union(B(3.6,170,10.65,sign*92.2,0,20.35))
  for y in [-54,48]:
   shell=shell.cut(B(12,10.7,3,sign*93,y,28.5))
 eye=ycyl(9,8,4,132).cut(ycyl(4.5,10,5,132))
 shell=shell.union(eye)
 # Circumferential ribs and axial reed bands are structural thickness, not loose ornaments.
 if not blockout:
  for y in [-83,-63,-42,-21,0,21,42,63,83]:
   rib=ycyl(96,2.8,y+1.4,31).cut(ycyl(93.2,4,y+2,31)).intersect(B(210,180,110,0,0,31))
   shell=shell.union(rib)
  for deg in range(12,180,12):
   a=math.radians(deg);x=94*math.cos(a);z=31+94*math.sin(a)
   reed=bar_between((x,-84,z),(x,84,z),1.15)
   shell=shell.union(reed)
  # Shallow longitudinal bark grooves on basin fascia.
  for z in [8,13,18]:
   groove=ellipse(89.4,38.4,.7,y=-48,z=z).cut(ellipse(88.4,37.4,1,y=-48,z=z-.1))
   body=body.cut(groove)
 parts=[dict(name='Oval trough and rear camera tunnel floor',shape=body.clean(),color='#76634A',
  support='Local removable support beneath camera pressure clips and exterior snap hooks.',purpose='Open seed basin, camera retention and four load-carrying vault latch beams',print_notes='Base down. Keep drain holes and four flexure gaps clear.'),
  dict(name='Woven barrel vault',shape=shell.clean(),color='#B69D70',explode=[0,0,70],print_rotation=[90,0,0],
  support='Print on one open arch end; no roof interior support expected. Support only receiver bridge if slicer requires.',purpose='Full tunnel rain shelter with thickened transverse ribs and axial reeds')]
 return parts,dict(name='Woven Arch',hanger=[0,0,132],description='A low, broad woven barrel vault shelters one elongated open seed trough. A rear tunnel seat holds the Wyze camera above the floor.',
  notes=['Use coarse dry seed; clean and dry the open trough frequently. Drain openings are 2.6 mm.', 'Camera fit, snap flex, ASA weathering, mounting strength and image focus are untested.', 'Wyze official close-up lens required; its dimensions and optical working distance must be checked before printing.'],
  assembly=['Pass outdoor suspension cord through the compact integral ridge eye and secure it to a sound overhead support. The completed base is retained by four positive roof hooks.','Set the vault onto both side sills; push down until all four hooks enter their side windows.','Spread the two low camera clips, seat the Wyze at the rear and release the clips.'],
  refill='Pour seed directly into the long front basin. For full cleaning, take the feeder down and rest the basin on a table; pull all four exterior latch pads outward in pairs and lift the vault.',
  camera_service='Take the feeder down and rest the basin on a table, then release and lift off the vault. Spread both camera side pressure clips, then lift the camera vertically; remove it before battery service. Front optics remain uncovered.',
  snap_joints=[dict(name='Four accessible vault edge hooks',type='cantilever hook into through window',beam_mm=[1.6,10,26],hook_undercut_mm=2.2,clearance_mm=.35,release='Pull the four exterior pads outward in opposing pairs, then lift the vault.')],
  detail_features=['Real half-cylindrical open-ended rain vault','Nine structural transverse arch ribs','Fourteen continuous axial reed ridges','Elongated oval open trough with integral drains','Four exterior releasable roof snaps','Compact integral suspension eye with a 9 mm bore'],
  **metadata(WYZE,pose,[0,-58,23],dict(type='hanging',position=[0,0,132],description='Compact integral roof ridge eye; four positive roof receiver shoulders carry the trough and camera through the side hooks.',hardware=['Outdoor suspension cord or suitable purchased hanger through the 9 mm ridge eye']),
  'Low horizontal barrel vault','Single open elongated oval trough; no hidden seed reservoir','Camera at rear of open tunnel looking down the feeding aisle','Crossing axial reeds and transverse curved roof ribs'))

def willow_screen(blockout=False):
 pose=dict(translation=[102,-21,29],rotation=[0,0,-72])
 # A shallow curved seed wall, open at the top under its removable cap.
 body=ellipse(65,45,24,y=-23)
 body=body.cut(ellipse(60.8,40.8,25,y=-23,z=4)).edges('>Z').fillet(.8)
 body=body.union(B(99,4,194,0,22,16))
 for sign in [-1,1]:
  body=body.union(B(4.6,27,194,sign*47.2,10.5,16))
 body=body.union(B(94,24,5,0,10,16))
 # A low open feed mouth below the grille releases seed to the curved bowl.
 body=body.union(B(94,3.2,7,0,-1.6,26))
 body=body.union(B(94,3.2,6,0,-1.6,204))
 for x in range(-45,46,3):
  body=body.union(B(1.6,3.2,178,x,-1.6,29))
 for z in range(34,204,14):
  body=body.union(B(94,4.2,1.8,0,-1.6,z))
 # Wing is an integral load-bearing branch, with the camera facing across the bowl.
 body=body.union(bar_between((43,0,23),(112,-6,23),5.8))
 body=body.union(bar_between((39,18,19),(120,4,26),4.6).intersect(B(400,400,28.5)))
 body=body.union(place(camera_grip(BIRDFY),pose))
 # Back stand-offs keep screw heads away from the seed cavity.
 for z in [60,174]:
  body=body.union(B(82,8,14,0,27,z-7))
 for x,z in [(-31,60),(31,60),(-31,174),(31,174)]:
  small=cq.Workplane('XZ').center(x,z).circle(2.3).extrude(14).translate((0,34,0))
  head=cq.Workplane('XZ').center(x,z-5).circle(4.4).extrude(14).translate((0,34,0))
  neck=B(4.6,14,5,x,27,z-5)
  body=body.cut(small.union(head).union(neck))
 # Lid lip with two positive outward-accessible snap beams.
 cap=B(103,32,3.2,0,10,210.4)
 cap=cap.union(B(89.2,20,5.8,0,10,204.6))
 # Rim is inset, not a solid plug: cavity remains reachable through the whole top opening.
 cap=cap.cut(B(83,14,6.2,0,10,204.3))
 for sign in [-1,1]:
  # Each cap beam roots at its top and carries a hook into a body side window.
  cap=cap.union(B(1.4,10,22,sign*51.9,10,191.6))
  cap=cap.union(B(4.5,10,2,sign*50.35,10,192))
  cap=cap.union(B(3,12,3,sign*53.1,10,193))
  body=body.cut(B(9,10.7,2.7,sign*47.5,10,191.65))
 for x in [-40,-20,0,20,40]:
  body=body.cut(cyl(1.25,7,-1).translate((x,-34,0)))
 if not blockout:
  # Bent reed rails reinforce the fine mesh without blocking its seed openings.
  for sign in [-1,1]:
   for i in range(3):
    x=sign*(43.5-i*3.0)
    for za,zb in [(32,86),(86,145),(145,205)]:
     xa=x+sign*(1.1 if za==86 else 0);xb=x+sign*(1.1 if zb==86 else 0)
     body=body.union(bar_between((xa,-3.2,za),(xb,-3.2,zb),1.1))
  for z in [8,13,18]:
   gro=ellipse(65.4,45.4,.7,y=-23,z=z).cut(ellipse(64.4,44.4,1,y=-23,z=z-.1))
   body=body.cut(gro)
 parts=[dict(name='Lattice seed wall with curved basin and camera branch',shape=body.clean(),color='#72755A',print_rotation=[0,0,75],
  purpose='Fine slit seed wall, curved feeding bowl, lateral camera support and rear mounting',
  support='Tree supports under lateral branch and camera pressure flexures; keep mesh and feed mouth free.',
  print_notes='Print basin down. Fine grille is 1.6 mm rib / 1.4 mm clear opening. Remove all support from camera flexures.'),
  dict(name='Willow wall refill cap',shape=cap.clean(),color='#B29A71',explode=[0,0,55],print_rotation=[180,0,0],
  support='Print cap top down; short hooks may need local support.',purpose='Shallow rim cap with two exposed releasable side hooks')]
 return parts,dict(name='Willow Screen',preview_direction=[-1.3,-2,1.2],description='A tall, narrow woven seed wall feeds a curved lower basin. The Birdfy camera sits on a lateral branch aimed across the landing area, with its antenna envelope open above.',
  notes=['Fine grille has 1.4 mm gaps and 1.6 mm ribs. Use clean coarse seed; check bridging and flow with the selected seed mix.', 'The complete 230 mm published Birdfy camera-plus-antenna envelope is reserved above the seat.', 'Camera floor-to-target horizontal distance is about 107 mm. The seat is level; Birdfy optical datum is unpublished. Verify real-device framing and focus before use.', 'Camera fit, feed flow, ASA snap durability, screw mounting strength and image focus are untested.'],
  assembly=['Install four suitable round-head screws in a sound wall or vertical timber, 62 mm horizontal and 114 mm vertical centers. Leave heads proud; insert through the large rear keyhole entries and slide the feeder down onto the narrow slots.','Press the refill cap down until both side hooks engage their windows.','Seat the Birdfy on its lateral branch and release both low pressure clips.'],
  refill='Pull the two exposed cap release pads outward and lift the cap; fill through the full-width top opening. Remove cap and camera, then rinse the cavity, mesh and bowl and dry thoroughly.',
  camera_service='Spread the two low side clips and lift the camera vertically from the open wing. The full camera and antenna height is unobstructed; remove the device before USB-C charging.',
  snap_joints=[dict(name='Two refill-cap edge hooks',type='top-rooted cantilever into open side windows',beam_mm=[1.4,10,22],hook_undercut_mm=1.4,clearance_mm=.35,release='Pull exposed lateral pads outward and lift cap vertically.')],
  detail_features=['31 vertical seed grille ribs with 1.4 mm gaps','13 crossing horizontal weave ribs','Six bent reed reinforcement rails','Curved lower feeding basin with five drains','Integral forked lateral camera branch','Two cap latches and four rear-only mounting keyholes'],
  **metadata(BIRDFY,pose,[0,-54,24],dict(type='wall',position=[0,31,116],description='Rear stand-offs fastened to a sound vertical wall or timber.',hardware=['4 outdoor round-head screws appropriate to mounting surface; 4 mm shank and head under 8.8 mm']),
  'Tall narrow lattice seed wall above a curved bowl','Shallow vertical seed chamber behind a 1.4 mm slit grille, feeding through its low mouth','Lateral forked branch with 72-degree inward yaw and open antenna clearance','Full-height functional fine weave and asymmetric camera wing'))

def build(slug,blockout=False):
 parts,kw={'woven-arch':woven_arch,'willow-screen':willow_screen}[slug](blockout)
 return export_design(slug,family='Backyard camera feeders',parts=parts,hanger=kw.pop('hanger',None),**kw)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('slug',choices=['woven-arch','willow-screen']);p.add_argument('--blockout',action='store_true');a=p.parse_args();build(a.slug,a.blockout)
