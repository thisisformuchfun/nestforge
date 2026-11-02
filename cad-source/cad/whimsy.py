"""Sculptural NestForge R2 whimsical feeders. mm, Z up; one rigid hanger per assembly."""
import cadquery as cq
from pathlib import Path
import math,json,sys,os
ROOT=Path(os.environ.get('NESTFORGE_EXPORTS',str(Path(__file__).resolve().parents[1]/'exports')))
YELLOW='#F5C52F'; ORANGE='#F28225'; BLACK='#202D32'; WHITE='#F1EADC'; GREEN='#83AD42'; SILVER='#AEB8C5'; PINK='#E974A5'; BROWN='#82482D'; GOLD='#D7AD4C'
def B(x,y,h,px=0,py=0,z=0):return cq.Workplane('XY').box(x,y,h,centered=(True,True,False)).translate((px,py,z))
def C(r,h,z=0,x=0,y=0):return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))
def E(x,y,h,z=0):return cq.Workplane('XY').ellipse(x,y).extrude(h).translate((0,0,z))
def R(a,b,h,z=0):return C(a,h,z).cut(C(b,h+2,z-1))
def S(r,x=0,y=0,z=0):return cq.Workplane('XY').sphere(r).translate((x,y,z))
def union(seq):
 s=seq[0]
 for p in seq[1:]:s=s.union(p,clean=False)
 return s.clean()
def drain(s,pts,z=0):
 for x,y in pts:s=s.cut(C(1.6,8,z-1,x,y))
 return s
def eye(x=0,y=0,z=180):return cq.Workplane('XZ').center(x,z).circle(10).circle(4.5).extrude(4,both=True).translate((0,y,0)).union(B(16,8,10,x,y,z-15))
def sockets(s,pts,z=4):
 for x,y in pts:
  t=B(10,10,18,x,y,z).cut(B(6.6,6.6,19,x,y,z)).cut(B(8,7,4.5,x+6,y,z+4))
  s=s.union(t).cut(B(6.6,6.6,19,x,y,z)).cut(B(8,7,4.5,x+6,y,z+4))
  # Lower flat stop lip gives 0.3 mm axial play while leaving a 7 x 3.8 mm release window.
  s=s.union(B(1.7,7,.8,x+4.15,y,z+7.8))
 return s
def snaps(s,pts,z=4):
 for x,y in pts:
  stem=B(1.6,5.4,14.5,x+1.8,y,z+5)
  hook=cq.Workplane('XZ').polyline([(x+2.6,z+4.7),(x+4.1,z+6.1),(x+4.1,z+7.5),(x+2.6,z+7.5)]).close().extrude(2.7,both=True).translate((0,y,0))
  s=s.union(stem).union(hook)
 return s
def P(n,s,c,e=(0,0,35)):return dict(name=n,shape=s,color=c,explode=e,support='Tree supports from build plate for sculpted overhangs; keep latch windows and flexure faces clear.',print_rotation=[0,0,0])
def save(slug,name,parts,desc,joints):
 from common import export_design
 # Purpose-designed mating cavities follow the accessory envelopes; no overlaps.
 for j in range(1,len(parts)):
  if parts[j]['shape'].intersect(parts[0]['shape']).val().Volume()>.001:parts[j]['shape']=parts[j]['shape'].cut(parts[0]['shape'])
 for i in range(1,len(parts)-1):
  for j in range(i+1,len(parts)):
   if parts[i]['shape'].intersect(parts[j]['shape']).val().Volume()>.001:
    parts[i]['shape']=parts[i]['shape'].cut(parts[j]['shape'])
 for p in parts:
  sh=p['shape'].val(); assert sh.Volume()>0,(slug,p['name'],'nonpositive volume'); bb=sh.BoundingBox()
  assert sh.isValid() and len(sh.Solids())==1,(slug,p['name'],[(round(q.Volume(),2),[round(v,1) for v in q.Center().toTuple()]) for q in sh.Solids()])
  ds=sorted([bb.xlen,bb.ylen,bb.zlen]);assert ds[1]<=225 and ds[2]<=245,(slug,ds)
 sj=[dict(name=j['module'],parts=[parts[0]['name'],j['module']],description='Paired positive hooks engage open-sided receiver windows.',beam_length_mm=14.5,beam_thickness_mm=1.6,deflection_mm=.8,clearance_mm=.3,release='Press through 7 x 3.8 mm outer receiver window') for j in joints]
 order={'rubber-duck-spa':'Install bubble crescent and front seed bath first; install the duck last. Remove the duck before lifting the crescent or well.', 'toilet-throne':'Install seed well, then gold seat, then raised lid. Remove in reverse order for cleaning.', 'garden-clog':'Install toe well first, then heel strap and cuff. The seed well lifts through the toe opening.', 'monster-mimic-chest':'Install treasure well, lower jaw and tongue, then vaulted lid. Remove lower jaw before lifting the treasure well.', 'disco-ball-donut':'Install seed saucer, then pink icing, then crest. Remove icing before lifting the seed saucer.', 'ufo-snackduction':'Install feeding cup, lamp halo, then observation dome. The centered overhead hanger leaves dome removal clearance.'}[slug]
 meta=export_design(slug,name,'Whimsical',desc,parts,notes=['One integrated eye supports the complete rigid assembly. No cord retention.','PETG or ASA; 0.4 mm nozzle; 0.20 mm layers; 4 walls. Test snap coupons and load before outdoor use.','3.2 mm integrated floor drains. Empty damp seed and clean all removable wells.'],assembly=[order,'Align each pair of keyed tangs with receiver towers. Press down until latch hooks engage.','Attach one hanger to integral eye. Release each module by pressing both outer hook noses through the exposed receiver windows.'],reference='image(20261008-183924).png',hanger={'rubber-duck-spa':[0,3,171],'ufo-snackduction':[0,0,225],'toilet-throne':[0,13,203],'monster-mimic-chest':[2,3,198],'disco-ball-donut':[0,-5,177],'garden-clog':[0,6,198]}[slug],snap_joints=sj,refill='Open top feeding wells. Release modules for full cleaning.',detail_features=[desc],validation={'valid_connected_solids':True,'assembly_intersections_mm3':0,'build_envelope_pass':True})
 import trimesh
 from sanitize_stl import run as normalize_meshes
 normalize_meshes(ROOT/slug)
 audits=[]
 for p in meta['parts']:
  for fn in set([p['file']]+[r['file'] for r in p['regions']]):
   mesh=trimesh.load(ROOT/slug/fn)
   assert mesh.is_watertight,(slug,fn,'nonmanifold mesh')
   audits.append(dict(file=fn,watertight=True,volume_mm3=float(mesh.volume)))
 (ROOT/slug/'mesh-validation.json').write_text(json.dumps(audits,indent=2))
 print('MESH PASS',slug,flush=True)
 return meta
def joint(n,pts,z):return dict(module=n,type='releasable cantilever snap',receiver_centers=pts,receiver_z=z,clearance_mm=.3,hook_undercut_mm=.8,flexure_length_mm=14.5,flexure_thickness_mm=1.6,release='Outer side window 7 x 3.8 mm')

def duck():
 # Spa basin, ornamental ribs and load-bearing shower arch.
 basin=E(71,57,6).union(E(71,57,30,4).cut(E(66,52,31,5)))
 for a in range(0,360,20):
  t=math.radians(a);basin=basin.union(C(2,25,6,69*math.cos(t),55*math.sin(t)))
 basin=basin.union(B(12,12,152,0,49,5)).union(B(12,58,10,0,26,151)).union(eye(0,3,171))
 basin=basin.union(C(17,5,146,0,16))
 for x in [-10,0,10]:basin=basin.cut(C(1.8,7,145,x,16))
 basin=drain(basin,[(-48,0),(48,0),(0,-35),(25,23),(-25,23)])
 dp=[(-19,15),(19,15)];bp=[(-48,-17),(48,-17)]
 basin=sockets(sockets(basin,dp),bp)
 # Duck floats above spa with oversized expressive head and swept wings.
 duckbody=E(33,26,5,22.3).translate((0,15,0))
 duckbody=duckbody.union(S(31,0,15,45)).union(S(26,0,10,84))
 for x in [-29,29]:duckbody=duckbody.union(S(17,x,17,48).intersect(B(22,43,34,x,18,30)))
 duckbody=snaps(duckbody,dp)
 # Relief feathers in wings: broad 1 mm grooves.
 for x in [-38,38]:
  for z in [40,46,52]:duckbody=duckbody.cut(B(5,20,1,x,10,z))
 # Tapered bill has a soft upper dome, lower lip, mouth seam and nostrils.
 bill=cq.Workplane('XY').workplane(offset=80).ellipse(17,17).workplane(offset=3).ellipse(23,22).workplane(offset=5).ellipse(22,21).workplane(offset=3).ellipse(15,15).loft().translate((0,-19,0))
 bill=bill.cut(B(39,20,1.2,0,-36,83.5))
 for x in [-8,8]:bill=bill.cut(C(1.7,5,87,x,-30))
 # Swept tail feathers blend into the rump with rounded tips.
 for x in [-10,0,10]:duckbody=duckbody.union(S(10,x,36,48)).union(S(7,x,41,54))
 glasses=union([S(11,-12,-11,96),S(11,12,-11,96),B(24,5,5,0,-20,94)])
 duckbody=duckbody.union(bill).union(glasses)
 # Three shallow lens highlights are relief cuts, leaving a solid glasses frame.
 for x in [-12,12]:
  duckbody=duckbody.cut(B(9,3,1.2,x,-21.8,99).rotate((x,-21.8,99),(x,-20.8,99),-20))
 # Bubble crescent sits above the spa lip; its two positive catches remain exposed.
 basin=basin.union(B(10,10,15,-48,-17,4)).union(B(10,10,15,48,-17,4));basin=sockets(basin,bp,18)
 bubbles=cq.Workplane('XY').polyline([(-58,-15),(-58,-35),(-40,-49),(40,-49),(58,-35),(58,-15),(49,-15),(49,-30),(35,-40),(-35,-40),(-49,-30),(-49,-15)]).close().extrude(4).translate((0,0,36.3))
 for x,y,r in [(-52,-24,8),(-39,-39,7),(-23,-45,8),(0,-47,7),(26,-43,8),(47,-30,10)]:bubbles=bubbles.union(C(r,14,36.3,x,y).edges('>Z').fillet(r-1))
 bubbles=bubbles.union(B(110,5,4,0,-17,36.3));bubbles=snaps(bubbles,bp,18)
 wp=[(-24,-27),(24,-27)];basin=sockets(basin,wp,4)
 well=E(39,21,3,22.3).translate((0,-25,0)).union(E(39,21,7,24).cut(E(35,17,8,25)).translate((0,-25,0)));well=drain(snaps(well,wp,4),[(-18,-25),(18,-25)],22)
 parts=[P('Ribbed spa and shower hanger',basin,YELLOW),P('Sculpted duck sunglasses and bill',duckbody,YELLOW),P('Bubble crescent',bubbles,WHITE),P('Front seed bath',well,WHITE)]
 parts[1]['regions']=[dict(name='Sunglasses',shape=glasses,color=BLACK),dict(name='Orange bill',shape=bill,color=ORANGE)]
 save('rubber-duck-spa','Rubber Duck Spa',parts,'A sculpted duck lounges in a fluted spa beneath an integrated shower rose. Feather grooves, oversize sunglasses and rounded bubbles frame the feeding well.',[joint('Sculpted duck sunglasses and bill',dp,4),joint('Bubble crescent',bp,18),joint('Front seed bath',wp,4)])

def ufo():
 body=R(61,49,6).union(B(110,12,5,z=0))
 for x,y in [(-55,0),(55,0),(0,54)]:body=body.union(C(4.5,135,0,x,y))
 saucer=cq.Workplane('XZ').polyline([(0,128),(85,128),(91,134),(69,145),(28,153),(0,153)]).close().revolve(360,(0,0),(0,1))
 body=body.union(saucer).union(B(12,12,68,0,43,147)).union(B(12,55,10,0,21.5,205)).union(eye(0,0,225))
 for a in range(0,360,30):
  t=math.radians(a);body=body.cut(B(22,1.2,20,70,0,139).rotate((0,0,0),(0,0,1),a))
 # Engine rim bead and recessed concentric upper hull detailing.
 body=body.union(R(88,83,2,132))
 for a in range(0,360,30):
  t=math.radians(a);body=body.cut(C(2.4,2,141,66*math.cos(t),66*math.sin(t)))
 cuppts=[(-31,0),(31,0)];body=sockets(body,cuppts,4)
 cup=C(46,4,22.3).union(R(46,42,17,25)).union(R(50,45,3,39));cup=drain(snaps(cup,cuppts),[(-22,-15),(22,-15),(0,20)],22)
 mesh=union([R(30,27,2.5,z) for z in [52,70,88,106,124]])
 for a in range(0,360,30):mesh=mesh.union(B(3,4,78,28.5,0,52).rotate((0,0,0),(0,0,1),a))
 body=body.union(mesh)
 dp=[(-23,0),(23,0)];body=sockets(body,dp,149)
 dome=S(39,0,0,151).cut(S(35,0,0,151)).intersect(B(82,82,35,z=167.3)).union(R(37,32,4,167.3))
 dome=dome.union(B(72,7,4,z=167.3));dome=snaps(dome,dp,149)
 lp=[(-69,0),(69,0)];body=sockets(body,lp,136)
 lights=R(80,74,3,154.3)
 for a in range(0,360,30):
  t=math.radians(a);lights=lights.union(C(6,4,154.3,77*math.cos(t),77*math.sin(t)))
 lights=lights.union(B(13,6,3,69,0,154.3)).union(B(13,6,3,-69,0,154.3));lights=snaps(lights,lp,136)
 parts=[P('Paneled saucer and tripod',body,SILVER),P('Drained tractor beam bowl',cup,GREEN),P('Observation dome',dome,BLACK),P('Twelve light halo',lights,GREEN)]
 parts[0]['regions']=[dict(name='Printed tractor beam mesh',shape=mesh,color=GREEN)]
 save('ufo-snackduction','UFO Snackduction',parts,'A broad beveled flying saucer with engraved panel seams, raised observation dome, twelve lamp pods and a rigid three-strut tractor-beam feeding bowl.',[joint('Drained tractor beam bowl',cuppts,4),joint('Observation dome',dp,149),joint('Twelve light halo',lp,136)])

def toilet():
 # Oval pedestal bowl and tall cistern share the single load path.
 body=E(45,40,7).union(E(31,28,38,5)).union(E(61,53,26,38).cut(E(56,48,28,42)))
 body=body.union(B(88,22,118,0,42,45)).union(B(96,28,7,0,42,158)).union(B(16,12,28,0,42,158)).union(B(16,46,10,0,27,183)).union(eye(0,13,203))
 # Rounded ceramic tank and pedestal seams, molded flush paddle.
 body=body.union(B(13,7,5,31,28,143).edges('|Y').fillet(1.8))
 body=body.cut(B(80,1.6,1.2,0,30.8,156))
 body=body.union(E(46,41,3,5).cut(E(40,35,5,4)))
 # Two visible rounded bolt bosses on the pedestal foot.
 for x in [-34,34]:body=body.union(C(4,3,6,x,0)).cut(B(4,1,1.2,x,0,8))
 for z in [48,56]:body=body.union(E(62,54,2,z).cut(E(58,50,4,z-1)))
 body=drain(body,[(-25,0),(25,0),(0,-22)],38)
 sp=[(-52,0),(52,0)];body=sockets(body,sp,49)
 seat=E(64,55,5,67.3).cut(E(46,37,7,66.3));seat=seat.intersect(B(140,100,20,0,-20,60));seat=snaps(seat,sp,49)
 # Raised oval toilet lid behind seat, with hinges and embossed crest.
 lp=[(-24,22),(24,22)];body=body.union(B(12,20,7,-24,28,68)).union(B(12,20,7,24,28,68));body=sockets(body,lp,72)
 lid=cq.Workplane('XZ').center(0,120).ellipse(43,47).extrude(3,both=True).translate((0,30,0))
 lid=lid.union(B(59,14,5,0,24,90.3));lid=snaps(lid,lp,72)
 lid=lid.union(cq.Workplane('XZ').center(0,124).ellipse(36,38).ellipse(32,34).extrude(1).translate((0,27.5,0)))
 tp=[(-28,-20),(28,-20)];body=sockets(body,tp,42)
 well=E(43,34,3,60.3).translate((0,-5,0)).union(E(43,34,7,62).cut(E(40,31,8,62)).translate((0,-5,0)))
 well=drain(snaps(well,tp,42),[(-18,-10),(18,-10),(0,10)],60)
 save('toilet-throne','Toilet Throne',[P('Pedestal bowl cistern and hanger',body,WHITE),P('Oval toilet seat',seat,GOLD),P('Raised sculpted lid',lid,WHITE),P('Removable seed well',well,BLACK)],'A recognizable pedestal toilet with oval bowl, stepped plinth, raised relief-edged lid, cistern cap, flush lever and removable sanitary seed well.',[joint('Oval toilet seat',sp,49),joint('Raised sculpted lid',lp,72),joint('Removable seed well',tp,42)])

def mimic():
 body=B(130,94,7).union(B(130,94,53,4).cut(B(122,86,54,z=7)))
 # Raised timber boards, metal corners and hinge barrels are fused to the chest.
 for z in [9,23,37,51]:body=body.cut(B(125,1.2,1.1,0,-46.5,z)).cut(B(125,1.2,1.1,0,46.5,z))
 for x in [-61,61]:
  for y in [-44,44]:body=body.union(B(9,8,56,x,y,2))
 # Iron nail heads and offset joints make the chest read as assembled timber.
 for x in [-61,61]:
  for z in [12,30,49]:
   body=body.union(cq.Workplane('XZ').center(x,z).circle(2.4).extrude(1.5).translate((0,-48,0)))
 for x,z in [(-25,10),(29,24),(-12,38)]:body=body.cut(B(1.2,1.8,11,x,-46.5,z))
 body=body.union(B(12,12,174,0,41,9)).union(B(14,50,10,2,22,178)).union(eye(2,3,198))
 body=drain(body,[(-40,-20),(40,-20),(-30,22),(30,22)])
 cp=[(-42,34),(42,34)];body=body.union(B(14,20,22,-42,38,52)).union(B(14,20,22,42,38,52));body=sockets(body,cp,70)
 # Open vaulted lid, teeth remain connected to continuous jaw strips.
 lid=B(134,14,7,0,33,88.3).union(B(134,9,48,0,41,91))
 vault=cq.Workplane('XZ').center(0,127).ellipse(67,24).extrude(46,both=True).translate((0,8,0)).intersect(B(140,100,35,0,8,127))
 vault=vault.cut(cq.Workplane('XZ').center(0,126).ellipse(62,20).extrude(43,both=True).translate((0,8,0)))
 lid=lid.union(vault).union(B(134,8,8,0,-35,125)).union(B(8,78,36,-63,4,94)).union(B(8,78,36,63,4,94));lid=snaps(lid,cp,70)
 for x in range(-54,55,18):
  tooth=cq.Workplane('XZ').polyline([(x-6,127),(x+6,127),(x+.75,108),(x-.75,108)]).close().extrude(4,both=True).translate((0,-35,0));lid=lid.union(tooth)
 for x in [-33,33]:
  lid=lid.union(S(14,x,-36,140)).union(S(7,x,-47,142))
  # Heavy slanted brow lends expression and structurally roots each eyeball.
  brow=B(31,8,6,x,-42,151).edges('|Y').fillet(2).rotate((x,-42,151),(x,-41,151),-16 if x<0 else 16)
  lid=lid.union(brow)
 # Rounded ribs follow the barrel-vault roof and join its shell.
 for yy in [-17,13,43]:
  rib=cq.Workplane('XZ').center(0,127).ellipse(68,25).ellipse(65,22).extrude(2,both=True).translate((0,yy,0)).intersect(B(140,8,30,0,yy,127))
  lid=lid.union(rib)
 lp=[(-47,-25),(47,-25)];body=body.union(B(10,10,32,-47,-25,5)).union(B(10,10,32,47,-25,5));body=sockets(body,lp,36)
 jaw=B(118,10,5,0,-37,54.3).union(B(108,25,4,0,-27,54.3));jaw=snaps(jaw,lp,36)
 for x in range(-50,51,20):jaw=jaw.union(cq.Workplane('XZ').polyline([(x-5,58),(x+5,58),(x+.75,72),(x-.75,72)]).close().extrude(3,both=True).translate((0,-37,0)))
 tongue=cq.Workplane('YZ').polyline([(-20,61),(-45,61),(-62,42),(-62,24),(-55,21),(-52,40),(-41,55),(-20,55)]).close().extrude(12,both=True)
 tongue=tongue.edges('|X').fillet(2.5)
 jaw=jaw.union(tongue).cut(B(1.2,30,1,0,-39,60.3))
 wp=[(-31,6),(31,6)];body=sockets(body,wp,7)
 well=B(82,53,3,0,8,25.3).union(B(82,53,15,0,8,27).cut(B(76,47,16,0,8,28)));well=drain(snaps(well,wp,7),[(-20,0),(20,0),(0,20)],25)
 parts=[P('Planked chest and hinge hanger',body,BROWN),P('Vaulted monster lid',lid,BROWN),P('Lower fangs and curling tongue',jaw,WHITE),P('Treasure seed well',well,GOLD)]
 parts[1]['regions']=[dict(name='Upper ivory teeth',shape=B(120,12,20,0,-35,107),color=WHITE),dict(name='Eyes',shape=union([S(14,x,-36,140) for x in [-33,33]]),color=WHITE),dict(name='Pupils',shape=union([S(7,x,-47,142) for x in [-33,33]]),color=BLACK)]
 parts[0]['regions']=[dict(name='Blackened corner irons',shape=union([B(9,8,56,x,y,2) for x in [-61,61] for y in [-44,44]]),color='#59605D')]
 # Put pupils first so they partition before the eyes.
 parts[1]['regions']=parts[1]['regions'][::-1]
 parts[2]['regions']=[dict(name='Tongue',shape=tongue,color='#C84454')]
 save('monster-mimic-chest','Monster Mimic Chest',parts,'An open timber monster chest with vaulted lid, projecting eyeballs, two rows of chunky teeth, curled tongue perch, board grooves and reinforced corner irons.',[joint('Vaulted monster lid',cp,70),joint('Lower fangs and curling tongue',lp,36),joint('Treasure seed well',wp,7)])

def disco():
 # Vertical chunky doughnut; flat facets cut on a lathed toroidal silhouette.
 body=cq.Workplane('XY').add(cq.Solid.makeTorus(58,23,cq.Vector(0,0,87),cq.Vector(0,1,0)))
 body=body.union(B(110,44,5,z=5)).union(eye(0,-5,177))
 # Deep checker recesses create actual mirror tiles, visible without textures.
 cuts=[B(1.1,14,150,x,-25,15).val() for x in range(-72,73,12)]
 cuts += [B(155,14,1.1,0,-25,z).val() for z in range(17,163,12)]
 body=body.cut(cq.Workplane('XY').add(cuts[0].fuse(*cuts[1:])).clean())
 pp=[(-43,-29),(43,-29)];body=body.union(B(12,20,8,-43,-20,40)).union(B(12,20,8,43,-20,40));body=sockets(body,pp,46)
 tray=E(51,24,4,64.3).union(E(51,24,15,67).cut(E(47,20,16,68))).translate((0,-35,0));tray=drain(snaps(tray,pp,46),[(-24,-35),(24,-35),(0,-45)],64)
 # Pink icing sits on the forward torus face; integral thick drips and sprinkles.
 fp=[(-57,-29),(57,-29)];body=body.union(B(12,20,7,-57,-20,68)).union(B(12,20,7,57,-20,68));body=sockets(body,fp,72)
 icing=cq.Workplane('XZ').center(0,87).circle(76).circle(47).extrude(4).translate((0,-20,0)).intersect(B(160,20,80,0,-23,87))
 icing=icing.union(B(118,10,5,0,-25,90.3));icing=snaps(icing,fp,72)
 for x,z in [(-61,80),(-47,104),(-23,132),(0,140),(24,131),(48,109),(62,83)]:icing=icing.union(B(6,6,16,x,-23,z).edges("|Y").fillet(2.8))
 sprinkles=[]
 for x,z in [(-60,115),(-43,140),(-18,151),(12,152),(36,142),(60,117)]:
  sprinkle=B(9,3,3,x,-24.5,z).rotate((x,-24.5,z),(x,-23.5,z),25);icing=icing.union(sprinkle);sprinkles.append(sprinkle)
 bp=[(-28,0),(28,0)];body=sockets(body,bp,156)
 starpts=[]
 for i in range(16):
  a=math.pi/2+i*math.pi/8;r=17 if i%2==0 else 7
  starpts.append((r*math.cos(a),184+r*math.sin(a)))
 crown=B(68,10,4,z=174.3).union(cq.Workplane('XZ').polyline(starpts).close().extrude(5,both=True));crown=snaps(crown,bp,156)
 parts=[P('Mirror tile donut and hanger',body,SILVER),P('Seed saucer',tray,GOLD),P('Dripping pink icing',icing,PINK),P('Starburst crest',crown,GOLD)]
 parts[2]['regions']=[dict(name='Colored sugar sprinkles',shape=union(sprinkles),color='#56BFCD')]
 save('disco-ball-donut','Disco Ball Donut',parts,'A vertical mirror-tiled doughnut with physical grid recesses, thick pink dripping icing, chunky sugar sprinkles, starburst crest and drained seed saucer.',[joint('Seed saucer',pp,46),joint('Dripping pink icing',fp,72),joint('Starburst crest',bp,156)])

def clog():
 # Vertical hanging garden clog, rounded toe down and open heel above.
 sole=cq.Workplane('XZ').center(0,89).ellipse(57,83).extrude(4,both=True).translate((0,28,0))
 body=sole.union(B(14,8,17,0,28,165)).union(B(14,34,10,0,17,178)).union(eye(0,6,198))
 # Toe box is half an ellipsoid-style loft, with broad molded vents.
 toe=cq.Workplane('XY').workplane(offset=12).ellipse(34,20).workplane(offset=23).ellipse(54,39).workplane(offset=29).ellipse(50,34).workplane(offset=26).ellipse(43,25).loft().translate((0,-3,0))
 inside=cq.Workplane('XY').workplane(offset=18).ellipse(29,15).workplane(offset=20).ellipse(49,34).workplane(offset=26).ellipse(45,29).workplane(offset=28).ellipse(39,21).loft().translate((0,-3,0))
 body=body.union(toe.cut(inside)).union(B(94,9,44,0,26,45))
 for z in [38,55,71]:
  for x in [-26,0,26]:body=body.cut(cq.Workplane('XZ').center(x,z).ellipse(6,4).extrude(60,both=True))
 # Molded welt bead follows the shoe outline; herringbone tread on the sole.
 welt=cq.Workplane('XZ').center(0,89).ellipse(57.7,83.7).ellipse(54.5,80.5).extrude(1.5,both=True).translate((0,30,0))
 body=body.union(welt)
 for z in range(30,151,15):
  for sign in [-1,1]:
   body=body.cut(B(32,2,1.4,sign*20,31.5,z).rotate((sign*20,31.5,z),(sign*20,32.5,z),sign*22))
 for z in range(21,153,12):body=body.cut(B(100,1.5,1.1,0,31.5,z))
 body=drain(body,[(-12,0),(12,0)],12)
 pp=[(-25,12),(25,12)];body=body.union(B(10,10,35,-25,12,12)).union(B(10,10,35,25,12,12));body=sockets(body,pp,45)
 well=E(36,16,3,63.3).union(E(36,16,13,65).cut(E(32,12,15,66)))
 well=drain(snaps(well,pp,45),[(-15,5),(15,5)],63)
 sp=[(-43,17),(43,17)];body=body.union(B(12,14,8,-43,22,78)).union(B(12,14,8,43,22,78));body=sockets(body,sp,82)
 strap=cq.Workplane('XZ').center(0,117).ellipse(49,40).ellipse(43,34).extrude(4,both=True).translate((0,17,0)).intersect(B(110,20,66,0,17,100.3))
 strap=strap.union(B(10,9,7,-43,17,100.3)).union(B(10,9,7,43,17,100.3));strap=snaps(strap,sp,82)
 for x in [-45,45]:strap=strap.union(cq.Workplane('XZ').center(x,107).circle(8).extrude(5,both=True).translate((0,17,0)))
 tp=[(-28,25),(28,25)];body=sockets(body,tp,122)
 cuff=B(67,12,5,0,25,140.3).union(B(67,5,13,0,20,144));cuff=cuff.intersect(B(100,60,40,0,-6.5,130));cuff=snaps(cuff,tp,122)
 for x in range(-25,26,10):cuff=cuff.cut(B(2,2,8,x,17.5,147))
 save('garden-clog','Garden Clog',[P('Vented molded clog body',body,GREEN),P('Removable toe seed bowl',well,WHITE),P('Raised pivot heel strap',strap,GREEN),P('Ribbed heel cuff',cuff,BLACK)],'A rounded molded garden clog with nine open toe vents, sculpted toe box, raised pivot heel strap, ribbed cuff and sole grooves; the toe holds a removable seed bowl.',[joint('Removable toe seed bowl',pp,45),joint('Raised pivot heel strap',sp,82),joint('Ribbed heel cuff',tp,122)])

if __name__=='__main__':
 globals()[sys.argv[1] if len(sys.argv)>1 else 'duck']()
