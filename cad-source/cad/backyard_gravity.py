"""R7 two independently constructed gravity feeders; no shared feeder chassis."""
import math, argparse, json
from pathlib import Path
import cadquery as cq
from common import box as B, cyl, ring, cone, export_design, ROOT
from backyard_camera import camera_grip, profile, place, hardware_envelope

ASA_BARK='#71533B'; ASA_SAGE='#71806A'; ASA_ACORN='#996E43'; ASA_DARK='#4F5142'
def rod(a,b,r):
 v=cq.Vector(*b).sub(cq.Vector(*a));return cq.Workplane('XY').add(cq.Solid.makeCylinder(r,v.Length,cq.Vector(*a),v.normalized()))
def branch(points,radii):
 s=None
 for i in range(len(points)-1):
  a=cq.Vector(*points[i]);v=cq.Vector(*points[i+1]).sub(a)
  seg=cq.Workplane('XY').add(cq.Solid.makeCone(radii[i],radii[i+1],v.Length,a,v.normalized()))
  s=seg if s is None else s.union(seg)
  if i:s=s.union(cq.Workplane('XY').sphere(radii[i]).translate(points[i]))
 return s

def drains(s,pts,z=0,h=10):
 for x,y in pts:s=s.cut(cyl(.7,h,z).translate((x,y,0)))
 return s

def camera_meta(camera,pose,index=0):
 return dict(preview_direction=[-1.3,-2,1.2],camera_system=True,camera_default=camera,camera_profiles=[camera],camera_mount=profile(camera),camera_part_index=index,camera_pose=pose,camera_service=profile(camera)['service']+(' Lift first along the cradle axis, tilted 8 degrees forward from vertical, until both stops are cleared; then lift freely away.' if camera=='wyze-battery-cam-pro' else '')+' Keep the release pads accessible. The intended pressure grip contacts the published rectangular envelope; physical fit and photographic framing have not been tested.',material='ASA',detail_revision='R7',prototype_validation=dict(physical_print_test=False,camera_fit_test=False,focus_test=False,snap_test=False,load_test=False,feed_test=False))

def bottle_parts():
 # A shallow seed saucer and long asymmetrical trunk, with a true neck collar.
 base=cyl(43,3).union(ring(43,39,10,3))
 base=base.union(ring(17.5,15.1,42,8))
 base=base.cut(B(20,18,10,0,-15,5))
 # Neck support half-ring is open to the front for loading a measured bottle.
 saddle=ring(22,14.6,5,65).intersect(B(60,40,8,0,20,64))
 base=base.union(rod((0,17,0),(0,27,82),8)).union(saddle)
 # The rear mounting bough supports bottle and mounting straps without a hanger.
 base=base.union(rod((0,27,65),(0,47,96),7)).union(rod((0,47,90),(0,47,194),7))
 for z in [91,177]:
  base=base.union(B(39,9,14,0,51,z))
  for x in [-13,13]:base=base.cut(B(5,18,6,x,51,z+4))
 # Camera sits at the end of a tapered lateral bough, pointed across the dish.
 pose={'translation':[85,-10,15],'rotation':[8,0,-58]}
 base=base.union(branch([(25,12,4),(47,17,7),(78,15,9),(106,4,11)],[9,8,6,5]))
 base=base.union(place(camera_grip('wyze-battery-cam-pro'),pose))
 # Forked, round bird perch rather than a rectangular platform.
 base=base.union(rod((-29,-24,6),(-50,-50,13),4.5)).union(rod((-50,-50,13),(-13,-65,13),4))
 base=base.union(rod((-35,-56,13),(-54,-68,17),3.5))
 # Real snap receiver blocks. Gate beams pass through open underside channels.
 for x in [-23.7,23.7]:
  recv=B(7,16,10,x,8,60)
  recv=recv.cut(B(2.7,24,3.8,x,6,59.7)).cut(B(3,4.4,7,x,7,63.4))
  base=base.union(recv).union(rod((x,6,69),(x*.65,15,69),3))
 # Neck gate includes a full front-half support ledge and positive hooks.
 gate=ring(22,14.6,5,65).intersect(B(60,40,8,0,-20.4,64))
 for sign in [-1,1]:
  x=sign*23.7
  gate=gate.union(B(6,5,5,sign*21,-9,65)).union(B(2.1,19,2.8,x,-1.5,60.1))
  gate=gate.union(B(2.1,5,7,x,-9,60.1))
  # Upper hook catches receiver pocket, with a 45 degree insertion nose.
  hook=cq.Workplane('YZ').polyline([(5.1,62.8),(9,62.8),(9,63.8),(7.2,65.2),(5.1,65.2)]).close().extrude(2.1).translate((x-1.05,0,0))
  gate=gate.union(hook).union(B(4.5,4,2.8,x,-4,60.1))
 # Subtle molded bark grooves, separate from the large structural grooves.
 for z in range(21,75,13):base=base.cut(rod((-4,20,z),(3,26,z+8),.7))
 base=drains(base,[(-27,-5),(27,-5),(-24,-23),(24,-23),(0,-29)],-1,6)
 return [dict(name='Bottle bough and camera seat',shape=base.clean(),color=ASA_BARK,explode=[0,0,0],support='Organic support beneath camera bough, branch perch and saddle. Keep drain and snap channels clear.',print_rotation=[0,0,0]),dict(name='Measured neck snap gate',shape=gate.clean(),color=ASA_SAGE,explode=[0,-45,0],support='Print with rear split face on bed; local support beneath hook nose.',print_rotation=[90,0,0])],pose

def acorn_parts():
 # Tall, modestly tapered single round silo, with an internal sloping seed floor.
 shell=cone(36,46,180)
 cavity=cone(32.5,42.5,180,3)
 above=B(200,500,350,0,0,0).rotate((0,0,0),(1,0,0),24).translate((0,0,24))
 shell=shell.cut(cavity.intersect(above))
 # One small front feeding cup, fed through an actual low silo outlet.
 cup=cyl(28,4,3).translate((0,-52,0)).union(ring(28,24,15,7).translate((0,-52,0)))
 shell=shell.union(cup).cut(B(23,40,18,0,-34,9))
 # Integral lower perch lip. Cup floor is accessible through the open mouth.
 shell=shell.union(rod((-23,-69,16),(23,-69,16),3.5))
 # Fluting is geometric: eighteen shallow vertical exterior channels.
 for n in range(18):
  a=2*math.pi*n/18;x,y=math.cos(a),math.sin(a)
  shell=shell.cut(rod((x*37.2,y*37.2,9),(x*47.1,y*47.1,178),1.55))
 # Strong side root carrying a low external camera, entire antenna zone open.
 pose={'translation':[91,-8,10],'rotation':[0,0,-58]}
 shell=shell.union(branch([(28,12,4),(51,15,4),(81,16,6),(114,8,7)],[9,8,6,5]).intersect(B(300,300,40,0,0,-30.2)))
 shell=shell.union(place(camera_grip('birdfy-cam-2k'),pose))
 # Post/tree mounting lugs on the narrow back, with two through-strap slots.
 for z in [51,133]:
  shell=shell.union(B(42,13,16,0,43,z))
  for x in [-14,14]:shell=shell.cut(B(5,22,7,x,43,z+4.5))
 # Cap latches are external and readily accessible, no hidden seed-side snaps.
 for sign in [-1,1]:
  x=sign*46
  r=B(6,13,12,x,0,152)
  r=r.cut(B(8,10.8,3.1,sign*49,0,156.9))
  shell=shell.union(r)
 # True hollow rounded acorn cap with continuous weather skirt.
 cap=cq.Workplane('XY').sphere(58).translate((0,0,155)).cut(cq.Workplane('XY').sphere(54).translate((0,0,155))).intersect(B(120,120,40,0,0,182))
 cap=cap.union(ring(49,46.5,11,171.5))
 # Restrained crosshatch dimples molded into the cap, not separate ornaments.
 for z,rad,count in [(187,48,24),(195,42,20),(202,33,16)]:
  for n in range(count):
   a=2*math.pi*(n+.25*(z%2))/count
   cap=cap.cut(cq.Workplane('XY').sphere(1.7).translate((rad*math.cos(a),rad*math.sin(a),z)))
 for sign in [-1,1]:
  x=sign*50
  cap=cap.union(B(1.8,9,25,x,0,154)).union(B(4,9,5,sign*48.9,0,174))
  hook=B(3.7,9,2.5,sign*48.2,0,157.2)
  cap=cap.union(hook).union(B(4.5,12,2.5,sign*51.5,0,153))
 shell=drains(shell,[(-12,-55),(12,-55),(0,-68)],2,6)
 return [dict(name='Fluted acorn silo and cup',shape=shell.clean(),color=ASA_ACORN,explode=[0,0,0],support='Support beneath side camera root, mounting lugs and latch receivers; remove through the open top and outlet.',print_rotation=[0,0,0]),dict(name='Textured acorn snap cap',shape=cap.clean(),color=ASA_DARK,explode=[0,0,55],support='Print crown up with supports beneath hollow dome and release beams.',print_rotation=[0,0,0])],pose

def build(slug):
 if slug=='bottle-bough':
  parts,pose=bottle_parts()
  return export_design(slug,'Bottle Bough','Backyard camera feeders','A reused inverted bottle supplies a round dish held by an asymmetric bark-textured bough, with a side-mounted camera.',parts,revision='R7',hanger=None,
   assembly=['Print the two ASA parts and remove every support from drain, beam and receiver openings.','Measure the actual uncapped bottle: this prototype accepts a 28.0 mm maximum threaded neck envelope within a 29.2 mm collar bore, a support bead of 32–35 mm diameter, and 21 mm from mouth to bead underside. Re-model the collar if those measured dimensions differ.','Slide the bottle mouth into the 30.2 mm chute bore, rest its neck support bead on the rear saddle, and push the front gate rearward until both hooks enter the receiver windows.','Fasten the two mounting bough pads to a post with two UV-resistant 12 mm straps. Add a separate reusable strap around the bottle body and upper bough to restrain wind; load-test the installed feeder before use.','Spread the two camera pressure clips, lower the Wyze onto its seat, and release. Fit the official close-up lens and check framing on the real camera.'],
   notes=['This is a measured-neck support-bead interface, not a universal bottle thread. No thread is printed.','Bottle and three straps are purchased/reused hardware, not printed parts. Use only the bottle measured to match this collar.','The open dish and 1.4 mm drain bores need routine brushing. Keep the outlet clear; mixed-seed flow remains untested.'],
   mounting={'type':'post','description':'Two narrow bark-bough strap pads bear against a post or tree; separate bottle restraint strap stabilizes the tall reused vessel.','hardware':['Two UV-resistant 12 mm post straps','One reusable 12 mm bottle restraint strap','One measured recycled bottle without cap'],'position':[0,55.5,132]},
   feeding_target=[0,-26,15],architecture={'form':'Asymmetric round dish on branching bough below an exposed recycled bottle','seed_system':'Unprinted inverted bottle, measured support-bead collar, short enclosed gravity chute','camera_integration':'Low lateral branch seat angled across the round feeding dish','signature':'Visible reused bottle and forked branch perch'},
   snap_joints=[{'name':'Neck gate twin positive hooks','type':'Two 19 mm cantilever beams with raised hook noses engaging open receiver windows','clearance_mm':.3,'engagement_mm':1.8,'release':'Press both visible gate beam pads downward, then slide the gate forward while supporting the empty bottle.'}],
   refill='Remove the camera if it obstructs access. Support the bottle, undo its body restraint strap, depress the two gate beams and pull the gate forward. Lift the bottle from the chute, fill away from the feeder, invert while covering the mouth, and reassemble. Never refill by pulling against the latched collar.',
   detail_features=['Molded shallow bark grooves on the load-bearing bough','Round 1.4 mm floor drains','Forked cylindrical branch perch','Short gravity chute with forward seed outlet','Accessible snap receiver windows'],
   extra_hardware=[{'type':'recycled-bottle','pose':{'translation':[0,0,49],'rotation':[0,0,0]},'local_origin':'downward-facing neck opening; local +Z toward bottle base','nominal_diameter_mm':68,'body_height_mm':160,'neck_diameter_mm':28,'overall_height_mm':205,'neck_and_shoulder_height_mm':45}],**camera_meta('wyze-battery-cam-pro',pose))
 parts,pose=acorn_parts()
 return export_design(slug,'Acorn Column','Backyard camera feeders','One tall fluted round silo ends in a small local feeding cup beneath a rounded acorn cap; a separate side root carries the camera.',parts,revision='R7',hanger=None,
  assembly=['Print both ASA parts and remove supports from the outlet, latch windows and camera grip.','Secure both rear pads to a post or tree using two UV-resistant 12 mm straps; check strap tension and stability under full seed and camera load.','Fill the silo through the open top. Lower the cap until both external hooks engage the silo receiver windows.','Spread the camera pressure clips, seat the Birdfy on its floor and release. The full 230 mm published camera envelope remains open above the seat.'],
  notes=['The internal floor slopes 24 degrees toward the localized front outlet; seed bridging and flow require physical trials.','The camera is external with no nearby roof over the antenna envelope. Actual body height and focus remain unverified.','Three 1.4 mm holes drain the front cup. Open the cap and brush the slope and outlet regularly.'],
  mounting={'type':'post','description':'Two integral rear strap pads register the circular silo against a post or tree.','hardware':['Two UV-resistant 12 mm post straps'],'position':[0,49.5,100]},
  feeding_target=[0,-56,22],architecture={'form':'Single tall tapered fluted round silo with a rounded acorn cap and one small cup','seed_system':'Integral round reservoir with sloping floor and forward gravity outlet','camera_integration':'Low exposed lateral root supports upright Birdfy, aimed across the cup','signature':'Slender fluted column, dimpled acorn cap and localized feeding lip'},
  snap_joints=[{'name':'Acorn cap side hooks','type':'Two external 25 mm vertical cantilevers with inward hooks engaging receiver slots','clearance_mm':.3,'engagement_mm':1.9,'release':'Pull the two lower external release pads outward and lift the cap vertically.'}],
  refill='Pull both cap release pads outward, lift the cap, and refill through the full open silo mouth. Brush the sloping floor and forward outlet during cleaning; rinse and dry completely before filling.',
  detail_features=['Eighteen actual shallow taper-following flute channels','Rounded hollow acorn cap with staggered molded dimples','24 degree internal seed floor','Single round localized feeding cup and integral round perch lip','External accessible cap latches','1.4 mm cup drains'],**camera_meta('birdfy-cam-2k',pose))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('slug',choices=['bottle-bough','acorn-column']);args=p.parse_args();build(args.slug)
