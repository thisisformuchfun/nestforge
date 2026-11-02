"""R7 independent orchard hopper, octagonal lantern, and asymmetric A-frame.
Original ASA prototypes; exact solids, direct camera sight paths, serviceable closures.
"""
import cadquery as cq
import math, json, os, argparse
from pathlib import Path
from common import box as B, cyl as C, export_design, ROOT
from backyard_camera import camera_grip, profile, place
CAM='wyze-battery-cam-pro'
CEDAR='#A8774E'; OLIVE='#59634B'; SAND='#CAB58D'; CHARCOAL='#414B46'

def fuse(base,items):
 return cq.Workplane('XY').add(base.val().fuse(*[s.val() for s in items]).clean()) if items else base

def poly_xz(points,depth,y):return cq.Workplane('XZ').polyline(points).close().extrude(depth).translate((0,y,0))
def octagon(r,h,z=0):return cq.Workplane('XY').polygon(8,2*r,circumscribed=False).extrude(h).translate((0,0,z))
def finger_camera_grip():
 g=camera_grip(CAM)
 for sign in [-1,1]:g=g.union(B(5.5,10,3,sign*35.1,4.5,6))
 return g
def ellipse(rx,ry,h,x=0,y=0,z=0):return cq.Workplane('XY').ellipse(rx,ry).extrude(h).translate((x,y,z))
def groove_grain(shape,xs,y,z0,h):
 # Shallow, broken molded grain. Each cutter leaves >=2.4 mm wall.
 for i,x in enumerate(xs):
  for k in range(3):
   zz=z0+k*h/3+((i%3)-1)*1.4
   cut=poly_xz([(x,zz),(x+.65,zz),(x+1.1,zz+h/4),(x+.45,zz+h/4)],.7,y)
   shape=shape.cut(cut)
 return shape

def keyhole(shape,x,z,y,depth=8):
 cutter=cq.Workplane('XZ').center(x,z).circle(4.4).extrude(depth).translate((0,y,0))
 cutter=cutter.union(B(4.4,depth,11,x,y-depth/2,z))
 return shape.cut(cutter)

def roof_latches(body,roof):
 # Roof-rooted 2.4 x12 x20 mm cantilevers in matching side-post receivers.
 for sign in [-1,1]:
  x=sign*96
  body=body.union(B(8,20,24,x,30,121))
  body=body.cut(B(3.2,12.8,23,x,30,125))
  body=body.cut(B(5,14,3.2,sign*99,30,128))
  roof=roof.union(B(2.4,12,24,x,30,128.5))
  roof=roof.union(B(1.5,12,2,sign*97.95,30,128.5))
 return body,roof

def orchard(detail=True):
 # Deliberately asymmetrical single tapered hopper beside a camera porch niche.
 porch=ellipse(106,72,4,0,-4,0)
 lip=ellipse(106,72,8,0,-4,2).cut(ellipse(101.8,67.8,9,0,-4,2))
 body=porch.union(lip)
 outer=cq.Workplane('XY').workplane(offset=12).center(-43,30).rect(68,57).workplane(offset=129).rect(100,85).loft(ruled=True)
 inner=cq.Workplane('XY').workplane(offset=15.5).center(-43,30).rect(60,49).workplane(offset=128).rect(92,77).loft(ruled=True)
 hopper=outer.cut(inner)
 collar=B(100,85,57,-43,30,140.8).cut(B(92,77,59,-43,30,140.5))
 roof_clear=poly_xz([(-110,140),(110,140),(110,144.6),(0,192.6),(-110,144.6)],90,75)
 hopper=hopper.union(collar.intersect(roof_clear))
 # Metering mouth opens down onto the broad porch; rear stays rain sheltered.
 hopper=hopper.cut(B(54,14,10,-43,0,11.5))
 body=body.union(hopper).union(B(64,52,10,-43,28,3))
 # Right niche supports and rear wall are independent of reservoir capacity.
 body=body.union(B(9,67,122,96,32,3)).union(B(86,5,123,55,65,3))
 body=body.union(B(82,59,8.3,55,31,0))
 # Direct finger access to the right release paddle through niche wall.
 body=body.cut(B(12,20,16,96,23,10.5).edges('|X').fillet(2))
 body=body.union(place(finger_camera_grip(),{'translation':[55,16.5,10.5],'rotation':[0,0,0]}))
 # Back spine is directly joined to hopper and camera wall, carries two screws.
 body=body.union(B(142,6,106,0,72,16))
 body=keyhole(body,-48,99,76,9);body=keyhole(body,48,99,76,9)
 for x,y in [(-78,-30),(-45,-45),(-7,-44),(40,-46),(80,-26)]:body=body.cut(C(1.35,8,-1).translate((x,y,0)))
 roof=poly_xz([(-110,145),(0,193),(110,145),(110,150),(0,198),(-110,150)],115,75)
 body,roof=roof_latches(body,roof)
 if detail:
  # Cedar grain follows the taper on the reservoir fascia; shallow ribs slope with it.
  for i in range(12):
   x=-88+i*8
   stripe=poly_xz([(x,29),(x+.75,29),(x-3,134),(x-3.75,134)],2,-10)
   body=body.cut(stripe)
  # Broken 0.6 mm grain follows the tapered front plane rather than a flat decal.
  for i,x in enumerate(range(-75,-10,7)):
   for k,z in enumerate([25,55,85,115]):
    yf=1.5-(z-12)*14/129
    grain=B(.7,1.2,23,x+(k%2)*.55,yf+.1,z).rotate((x,yf,z),(x+1,yf,z),math.degrees(math.atan2(14,129)))
    body=body.cut(grain)
  # Shingle courses are cut into roof surface; 0.7 mm depth leaves roof intact.
  for sign in [-1,1]:
   for xabs in [20,39,58,77,96]:
    x=sign*xabs;z=198-48*xabs/110
    roof=roof.cut(B(1,134,1.1,x,26,z-.6))
   for row,(xlo,xhi) in enumerate([(4,19),(23,38),(42,57),(61,76),(80,95),(99,108)]):
    for y in range(-31+(row%2)*8,90,18):
     pts=[(sign*xlo,198-48*xlo/110-.55),(sign*xhi,198-48*xhi/110-.55),(sign*xhi,199-48*xhi/110),(sign*xlo,199-48*xlo/110)]
     roof=roof.cut(poly_xz(pts,.65,y))
  # Tactile landing grooves and softly scalloped rim cut-outs.
  for x in range(-75,76,15):body=body.cut(B(1.1,27,.65,x,-42,3.4))
  for x in [-82,-61,-40,-19,2,23,44,65,86]:body=body.cut(C(3,4,7).translate((x,-4-72*math.sqrt(max(0,1-(x/106)**2)),0)))
 return [dict(name='Tapered hopper and camera porch',shape=body,color=CEDAR,print_rotation=[0,0,0],support='Local support beneath camera flexure arms and metering outlet bridge.',explode=[0,0,0]),dict(name='Shingled pitched snap roof',shape=roof,color=OLIVE,print_rotation=[180,0,0],support='Print inverted with localized supports under pitched faces and latch roots.',explode=[0,0,55])],dict(camera_pose={'translation':[55,16.5,10.5],'rotation':[0,0,0]},feeding_target=[40,-55,8],camera_part_index=0,mounting={'type':'wall','position':[0,75,110],'description':'Integral rear spine with two upward keyholes, 96 mm spacing; install level on a rigid post or wall.','hardware':'Two substrate-appropriate screws with 8 mm heads and <=4 mm shanks; anchors as substrate requires.'},hanger=None,architecture={'form':'Asymmetric pitched roof and scalloped front porch','seed_system':'One tapered hopper at left; front 10 mm metering mouth','camera_integration':'Offset right niche and low releasable pressure cradle','signature':'Cedar-grain hopper, shingle courses, scalloped porch'},assembly=['Seat the roof over the two side receivers; push down until both visible hooks engage.','Install two mounting screws, engage keyholes, then lower assembly to lock.','Fit the camera after mounting; verify its front accessories and optics remain clear.'],refill='Press both side roof hooks inward through the exposed receiver windows, lift roof vertically, refill the single open hopper. Empty and brush through its large top and metering mouth.',camera_service='Remove roof. Reach the broad right release paddle through the rounded sidewall window and the left paddle through the open niche; spread both outward, then lift camera vertically clear of its seat; remove before battery service. No verified close-up-lens envelope is modeled.',snap_joints=[{'name':'Roof to side posts','beam_mm':[2.4,12,24],'clearance_mm':.4,'hook_overlap_mm':1.1,'release':'Press both visible side hooks inward, then lift roof.'}],detail_features=['Shallow molded cedar-grain grooves on tapered fascia','Interrupted shingle courses on the pitched roof','Scalloped porch lip, tactile landing grooves and five 2.7 mm drains','Rounded side release window and broad camera-release paddles'])

def meadow(detail=True):
 # A tall octagonal common seed chamber; low central camera cavity leaves side chutes.
 body=octagon(88,4)
 rim=octagon(88,8,2).cut(octagon(83.5,9,2));body=body.union(rim)
 outer=octagon(63,169,12);inner=octagon(58.6,168,16)
 body=body.union(outer.cut(inner)).union(octagon(62,12,3))
 # Low recess walls and ceiling keep seed out of camera; hopper feeds at each flank.
 cavity=B(73,145,106,0,0,8)
 body=body.cut(cavity)
 housing=B(80,103,105,0,0,12).cut(B(73,145,107,0,0,8))
 body=body.union(housing.intersect(octagon(62,113,3)))
 # Sloping seed deflectors over cavity move seed to the two side conduits.
 deflector=poly_xz([(-37,114),(0,128),(37,114)],94,47)
 body=body.union(deflector).union(B(73,88,3,0,0,111))
 for sign in [-1,1]:
  body=body.cut(B(18,26,9,sign*49,-25,11.5))
  body=body.cut(B(18,20,9,sign*49,42,11.5))
 # Sealed side finger tunnels cross the seed chutes. Their sloped roofs route
 # seed to the uninterrupted front passages; 24 x19 mm rounded openings let
 # fingers reach and spread the broad low camera paddles without tools.
 for sign in [-1,1]:
  liner=B(32,30,26,sign*48,15,6)
  ramp=cq.Workplane('YZ').polyline([(0,32),(30,32),(30,42)]).close().extrude(32).translate((32,0,0))
  if sign<0:ramp=ramp.mirror('YZ')
  liner=liner.union(ramp).intersect(octagon(63,44))
  body=body.union(liner)
  tunnel=B(44,24,19,sign*48,15,9).edges('|X').fillet(2)
  body=body.cut(tunnel)
 body=body.union(B(73,62,3.2,0,27,5.8)).union(place(finger_camera_grip(),{'translation':[0,10,9],'rotation':[0,0,0]}))
 # Front grip floor bridges back to recess floor, suspended directly from silo ribs.
 body=body.union(B(75,66,3.2,0,26,5.8))
 for ang in [-140,-100,-60,-20,20,60,100,140]:
  a=math.radians(ang);body=body.cut(C(1.25,9,-1).translate((76*math.cos(a),76*math.sin(a),0)))
 # Four flat-side body-rooted flexures. Flat polygon apothem is 58.206 mm.
 a=63*math.cos(math.pi/8);cap=octagon(69,4,181.4)
 cap=cap.union(cq.Workplane('XY').workplane(offset=185.4).polygon(8,138).workplane(offset=19).polygon(8,34).loft(ruled=True))
 skirt=octagon(66.9,14,168).cut(octagon(63.6,15,168));cap=cap.union(skirt)
 for ang in [22.5,112.5,202.5,292.5]:
  # Radial local X outward, beam centered on flat side; cut slots around beam.
  def turn(s):return s.rotate((0,0,0),(0,0,1),ang)
  body=body.cut(turn(B(5.3,17.6,24,a-1.5,0,157.5)))
  beam=turn(B(2.4,14,24,a-1.5,0,157))
  hook=turn(B(1.7,14,2.2,a+.55,0,177.4))
  body=body.union(beam).union(hook)
  cap=cap.cut(turn(B(8,15.2,3.4,a+3,0,176.8)))
 eye=cq.Workplane('XZ').center(0,215).circle(13).circle(5.5).extrude(9).translate((0,4.5,0))
 cap=cap.union(eye).union(B(23,9,5,0,0,202))
 if detail:
  # Fine ventilation/seed-view mesh at upper lantern walls: 1.35 x 4.5 slots.
  cuts=[]
  for ang in [22.5,67.5,112.5,157.5,202.5,247.5,292.5,337.5]:
   for yy in [-14,-10,-6,-2,2,6,10,14]:
    for z in [137,145,153]:cuts.append(B(8,1.35,4.5,a-1,yy,z).rotate((0,0,0),(0,0,1),ang))
  body=body.cut(cq.Compound.makeCompound([s.val() for s in cuts]))
  # Eight substantial pilasters and incised reed motif, no freestanding ornament.
  for ang in range(0,360,45):
   rib=B(4.5,4.5,151.5,61,0,16).rotate((0,0,0),(0,0,1),ang);body=body.union(rib.cut(cavity))
  for ang in range(0,360,45):
   spoke=B(17,1.1,.8,74,0,3.35).rotate((0,0,0),(0,0,1),ang);body=body.cut(spoke)
 return [dict(name='Octagonal seed lantern and camera recess',shape=body,color=SAND,support='Upright; support camera-recess ceiling, finger-tunnel ceilings and pressure clip arms. Remove supports through the open front recess and side finger tunnels.',explode=[0,0,0]),dict(name='Faceted hanging cap',shape=cap,color=OLIVE,print_rotation=[180,0,0],support='Inverted; supports beneath hanging eye and sloping cap. Keep snap receiver windows clear.',explode=[0,0,55])],dict(camera_pose={'translation':[0,10,9],'rotation':[0,0,0]},feeding_target=[0,-68,7],camera_part_index=0,mounting={'type':'hanging','description':'Compact 11 mm integral eye; cap carries body through four broad positive hooks.','hardware':'Outdoor cord or rated small hook through integral eye; cord only suspends fully latched feeder.'},hanger=[0,0,215],architecture={'form':'Tall octagonal lantern above a continuous octagonal landing ring','seed_system':'Single upper chamber divides around sealed camera recess to four short lower discharge ports','camera_integration':'Camera sits low in a rearward central recess looking across the front ring','signature':'Fine upper mesh, eight corner pilasters, faceted cap and compact eye'},assembly=['Snap cap over all four upper body hooks; visually confirm each through its open receiver window.','Insert the camera through front recess after spreading pressure clips.','Suspend only after four hooks are fully seated.'],refill='Support the body on a table, release four exposed hooks inward, lift the cap, and pour into the common octagonal chamber. For cleaning remove camera, empty feeder, and brush chamber and front and rear side passages from open top and all four discharge ports.',camera_service='Unsuspend and rest feeder on table. Reach both broad release paddles through the rounded side finger tunnels and spread them outward; lift the camera 3.5 mm and slide it straight forward through the open recess. Remove before bottom battery service; verify actual close-up lens and forward removal clearance.',snap_joints=[{'name':'Four upper cap retainers','beam_mm':[2.4,14,24],'clearance_mm':.6,'hook_overlap_mm':.7,'release':'With feeder supported, depress four hooks inward through external cap windows.'}],detail_features=['192 functional seed-view slots, 1.35 mm wide with substantial ribs','Eight fused corner pilasters','Eight drainage holes and radial landing grooves','Two 24 x19 mm sealed finger tunnels with sloping seed-deflector roofs and broad release paddles','One compact eye rooted through faceted roof'])

# Ridge coordinates transform local X normal to slope, local Z up slope, Y depth.
ANGLE=math.degrees(math.atan2(94,184));L=math.hypot(94,184)
def slope(s):return s.rotate((0,0,0),(0,1,0),ANGLE).translate((-100,40,12))
def ridge(detail=True):
 # Outer left sloping wall is removable: wide-open cleaning surface with no trapped cavity.
 local=B(29,84,L,16,0,0).cut(B(24,76,L-7,15.5,0,3.5))
 # Opening extends entire outer slope. Inner back, bottom, and two end cheeks remain one shell.
 local=local.cut(B(8,76,L+1,0,0,3.5))
 body=slope(local)
 cover=slope(B(3.2,83.2,L-.6,-.4,0,.3))
 # Two 22 mm cover-rooted cantilevers are on the accessible front/rear long edges.
 for yy in [-40,40]:
  # End-wall receiver cavities, open outward for release.
  rec=B(6.4,7,26,4.8,yy,84)
  local=local.union(rec)
  local=local.cut(B(5,3.2,23,2.2,yy,87))
  local=local.cut(B(8,5,3.4,2.2,yy+(2.2 if yy>0 else -2.2),87.4))
  beam=B(5,2.4,22,1,yy,87.9)
  hook=B(5,1.5,2,1,yy+(1.8 if yy>0 else -1.8),87.9)
  # Local cover tether from outer wall to top beam root.
  bridge=B(6,3,4,0,yy,106)
  cover=cover.union(slope(beam.union(hook).union(bridge)))
 body=slope(local)
 # Metered opening through lower channel and localized seed bowl.
 ramp=cq.Workplane('YZ').polyline([(2,-3),(78,-3),(78,22),(2,12)]).close().extrude(29).translate((-96,0,0))
 body=body.union(ramp.intersect(slope(B(29,84,L,16,0,0))))
 body=body.cut(B(21,12,10,-82,0,12))
 landing=ellipse(51,35,4,-63,6,0)
 landing=landing.union(ellipse(51,35,9,-63,6,2).cut(ellipse(46,30,10,-63,6,2)))
 body=body.union(landing).union(B(30,79,11.3,-86,40,0))
 # Exposed opposite frame carries a hooded, inward-looking camera pocket.
 right=poly_xz([(0,207),(103,6),(110,9),(6,211)],84,82)
 # Central aperture around physical camera envelope; front/rear triangular ribs survive.
 right=right.cut(B(90,73,100,66,0,20))
 body=body.union(right).union(B(212,8,10,3,78,0))
 # Camera pocket is shelf + rear bridge + rain hood, open towards central landing.
 shelf=B(54,77,5,57,0,9)
 hood=B(54,77,4,57,0,121.5)
 outerwall=B(4,77,102.5,82,0,23)
 body=body.union(shelf).union(hood).union(outerwall)
 pose={'translation':[34,0,17.2],'rotation':[0,0,-90]}
 body=body.union(place(camera_grip(CAM),pose))
 body=body.union(B(31,9,29,97,0,0)).union(B(10,84,8,102,40,0))
 # Rear mount spine is a narrow upright triangle cross-tie, not a suspension arch.
 spine=poly_xz([(-70,45),(66,45),(26,124),(-30,124)],6,88)
 body=body.union(spine)
 body=keyhole(body,-32,77,89,9);body=keyhole(body,30,77,89,9)
 for x,y in [(-90,-5),(-68,-17),(-42,-8)]:body=body.cut(C(1.3,9,-1).translate((x,y,0)))
 if detail:
  # Sloped cover has shallow weatherboard scoring, visibly one major roof plane.
  for z in range(10,int(L)-8,18):cover=cover.cut(slope(B(1.0,85,1.0,-1.65,0,z)))
  for yy in range(-32,33,8):
   for k in range(4):cover=cover.cut(slope(B(.7,.65,29,-1.7,yy,8+k*48)))
  # Real ribs under hood run to outer wall; landing grooves follow the feeding lip.
  for yy in [-28,-14,0,14,28]:body=body.union(B(50,1.4,2,58,yy,120))
  for xx in [-92,-80,-68,-56,-44]:body=body.cut(B(.9,21,.7,xx,-7,3.4))
 return [dict(name='Open triangular feeder and camera pocket',shape=body,color=CEDAR,support='Print upright at 37 degrees around Z. Support beneath the camera shelf, hood, crossbars, lower sloped channel and pressure clip arms; add brim for the narrow lowest edge. Remove supports completely.',print_rotation=[0,0,37],explode=[0,0,0]),dict(name='Weatherboard reservoir snap cover',shape=cover,color=OLIVE,print_rotation=[0,-ANGLE,0],support='Print outer slope face down after indicated rotation; local support under snap beam bridges.',explode=[-32,0,20])],dict(camera_pose=pose,feeding_target=[-54,-17,8],camera_part_index=0,mounting={'type':'wall','position':[0,88,88],'description':'Rear triangular cross-tie includes two keyholes at 62 mm centers; screw to a rigid post or wall.','hardware':'Two substrate-appropriate <=4 mm shank screws with 8 mm heads; anchors as needed.'},hanger=None,architecture={'form':'Exposed triangular frame with asymmetric camera pocket and local oval landing','seed_system':'One long sloping seed channel inside the left leg; entire outer wall removes for refill and cleaning','camera_integration':'Low camera pocket in opposite leg faces inward across the landing','signature':'Weatherboard slope, open center, narrow structural back cross-tie'},assembly=['Press long outer cover onto the sloping seed channel until front and rear hooks engage their receiver windows.','Mount by rear keyholes and verify level.','Spread camera clips and fit the inward-facing camera in its hooded seat.'],refill='Remove the camera first. Remove feeder from its two keyholes and lay the right leg down, so the left sloping opening faces up. Release front and rear cover hooks; remove the whole sloped cover, refill or brush the exposed long channel, re-latch, and remount.',camera_service='Remove camera by spreading the low pressure clips, lift it 9.5 mm, slide it 10 mm inward toward the open triangular center, then pull it toward the front of the feeder (world negative Y) to remove before servicing bottom battery cover. Verify actual close-up lens clearance and focus.',snap_joints=[{'name':'Sloped reservoir cover','beam_mm':[5,2.4,22],'clearance_mm':.4,'hook_overlap_mm':1,'release':'Press accessible front and rear hooks toward channel, then lift entire sloping cover outward.'}],detail_features=['Shallow weatherboard course grooves and broken grain on long sloping cover','Open triangular structural center','Five integral ribs under camera hood','Localized oval landing with three drains and traction grooves'])

BUILDERS={'orchard-hopper':orchard,'meadow-lantern':meadow,'ridge-aframe':ridge}
NAMES={'orchard-hopper':'Orchard Hopper','meadow-lantern':'Meadow Lantern','ridge-aframe':'Ridge A-frame'}
def run(slug,blockout=False):
 parts,meta=BUILDERS[slug](not blockout)
 if blockout:
  folder=Path(os.environ.get('NESTFORGE_BLOCKOUTS',str(ROOT.parent/'blockouts')))/slug;folder.mkdir(parents=True,exist_ok=True)
  records=[]
  for i,p in enumerate(parts):
   name=f'{i+1:02d}.stl';cq.exporters.export(p['shape'],str(folder/name))
   records.append({'name':p['name'],'file':name,'color':p['color'],'regions':[{'file':name,'color':p['color']} ]})
  d={'id':slug,'name':NAMES[slug]+' silhouette','parts':records};(folder/'design.json').write_text(json.dumps(d))
 else:
  export_design(slug,NAMES[slug],'Backyard camera feeders',meta['architecture']['form']+'. '+meta['architecture']['seed_system']+'.',parts,revision='R7',detail_revision='R7',material='ASA',camera_system=True,camera_default=CAM,camera_profiles=[CAM],camera_mount=profile(CAM),prototype_validation={'physical_print_test':False,'camera_fit_test':False,'snap_test':False,'load_test':False,'seed_flow_test':False,'weather_test':False},notes=['Original CAD textures; no external licensed asset.','Published camera envelope is a conservative fit proxy. Nominal side-grip preload intentionally intersects the camera proxy at low retention noses.','Official Wyze close-up lens required; dimensions and practical focus unverified.','All printed parts ASA. Inspect snaps and mount before outdoor use.'],**meta)
  folder=ROOT/slug
 from render_catalog import render_design
 render_design(folder/'design.json')
 if not blockout:
  from sanitize_stl import run as sanitize
  sanitize(folder)
  from audit_assembly import audit
  audit(folder/'design.json')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('slug',choices=list(BUILDERS));parser.add_argument('--blockout',action='store_true');args=parser.parse_args();run(args.slug,args.blockout)
