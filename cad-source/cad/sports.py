"""NestForge R2 sport feeders — editable millimetre CAD, digital fit prototypes."""
import cadquery as cq
import math,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
G='#244C37'; W='#EEE9DC'; N='#172F57'; O='#EF6225'; Y='#F7BF30'; K='#202521'; BROWN='#875038'; RED='#963E37'
def B(x,y,h,px=0,py=0,z=0):return cq.Workplane('XY').box(x,y,h,centered=(True,True,False)).translate((px,py,z))
def C(r,h,z=0,x=0,y=0):return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))
def R(r,ri,h,z=0):return C(r,h,z).cut(C(ri,h+2,z-1))
def E(x,y,h,z=0):return cq.Workplane('XY').ellipse(x,y).extrude(h).translate((0,0,z))
def ER(x,y,t,h,z=0):return E(x,y,h,z).cut(E(x-t,y-t,h+2,z-1))
def fuse(a):
 s=a[0]
 for p in a[1:]:s=s.union(p,clean=False)
 return s.clean()
def rod(a,b,r):
 a,b=cq.Vector(*a),cq.Vector(*b);v=b-a
 return cq.Workplane('XY').add(cq.Solid.makeCylinder(r,v.Length,a,v.normalized()))
def tube(points,r):
 edge=cq.Edge.makeSpline([cq.Vector(*p) for p in points])
 path=cq.Wire.assembleEdges([edge]);v=edge.tangentAt(0)
 return cq.Workplane(cq.Plane(origin=cq.Vector(*points[0]),normal=v)).circle(r).sweep(path)
def drain(s,pts,z=0):
 for x,y in pts:s=s.cut(C(1.3,8,z-1,x,y))
 return s
def eye(z):return cq.Workplane('XZ').center(0,z+7).circle(9).circle(4.3).extrude(4,both=True).union(B(13,8,5,z=z-2))
def snap(lower,upper,pts,z):
 # Exterior release window: press tongue inward through window then pull vertically.
 for x,y in pts:
  tongue=B(8,1.6,17,x,y,z).union(B(8,2.4,1.3,x,y+.4,z+13))
  ramp=cq.Workplane('YZ').polyline([(y+.8,z+14.3),(y+1.6,z+14.3),(y+.8,z+17)]).close().extrude(4,both=True).translate((x,0,0))
  tongue=tongue.union(ramp)
  cage=B(12,7,18,x,y+.2,z).cut(B(8.6,2.2,19,x,y,z-.1)).cut(B(8.8,5,3,x,y+2.4,z+12.7))
  lower=lower.cut(B(9,5,17,x,y+.4,z+.5)).union(tongue)
  upper=upper.union(cage).cut(B(8.6,2.2,19,x,y,z-.1)).cut(B(8.8,5,3,x,y+2.4,z+12.7))
 return lower,upper

def part(n,s,c,e=(0,0,0),regions=None):
 p=dict(name=n,shape=s,color=c,explode=list(e),support='Orient broad planar mating face on bed; support curved overhangs. Keep snap beams free of support.')
 if regions:p['regions']=regions
 return p
NOTES=['R2 digital engineering prototype; snap retention, fatigue, weathering and bird use have not been physically tested.','Outdoor ASA or PETG, 0.4 mm nozzle, 0.20 mm layers, 4 walls. Print snap beams lengthwise in XY where practical; trial-print joint coupon first.','All connections use positive 0.8 mm hooked cantilevers and open release windows; 0.30 mm clearance per side. One metal hanger attaches only to the assembled integral eye.','Drainage holes are integral. Release snap windows to remove the seed floor and roof for washing; dry fully before refill.']
def export(slug,name,desc,parts):
 from common import export_design
 for i,p in enumerate(parts):
  for prev in parts[:i]:p["shape"]=p["shape"].cut(prev["shape"])
 for p in parts:
  solids=p["shape"].val().Solids()
  if len(solids)>1:
   solids=sorted(solids,key=lambda x:x.Volume(),reverse=True)
   if sum(x.Volume() for x in solids[1:])<solids[0].Volume()*.002:p["shape"]=cq.Workplane("XY").add(solids[0])
 # Normalize the heavily trimmed spline ribbon through STEP once before final
 # export; this stabilizes OCC's surface representation for repeated roundtrips.
 if slug=='spiral-football':
  with tempfile.TemporaryDirectory() as td:
   q=Path(td)/'ribbon.step';cq.exporters.export(parts[2]['shape'],str(q));parts[2]['shape']=cq.importers.importStep(str(q))
 cache=Path(tempfile.gettempdir())/'sports-r2-cache'/slug;cache.mkdir(parents=True,exist_ok=True)
 for n,p in enumerate(parts):p["shape"].val().exportBrep(str(cache/(str(n)+".brep")))
 for p in parts:
  ss=p["shape"].val();print(slug,p["name"],ss.isValid(),[(round(q.Volume(),1),tuple(round(v,1) for v in (q.BoundingBox().xmin,q.BoundingBox().ymin,q.BoundingBox().zmin,q.BoundingBox().xmax,q.BoundingBox().ymax,q.BoundingBox().zmax))) for q in ss.Solids()],flush=True)
 return export_design(slug,name,'Game day',desc,parts,NOTES,['Press mating parts together until both hooks click into their receiver windows.','Check every visible hook is fully engaged. Pull-test over a soft surface before hanging.','For cleaning, unload and press accessible snap beams inward through receiver windows; separate mating components.'],reference='image(20261008-183904).png',hanger=[0,0,max(p['shape'].val().BoundingBox().zmax for p in parts)-9],snap_joints=[dict(name='Accessible hooked snap interfaces',parts=[p['name'] for p in parts],description='17 mm integral cantilever with 0.8 mm retaining hook and 3 mm exterior release window',beam_length_mm=17,beam_thickness_mm=1.6,deflection_mm=.8,clearance_mm=.3,release='Press beam inward through the exposed 3 mm window; lift mating part')],refill=('Fill the exposed spiral channel directly; do not fill the hollow football shell. Remove the snap tip and ribbon for cleaning.' if slug=='spiral-football' else 'Release the top cap or shell at its visible latch windows. Remove the drained bottom for complete cleaning.'),detail_features=[desc])

def stadium():
 # Structural four-post stadium crown provides a rigid load path to one hanger.
 tray=E(98,74,3).union(ER(98,74,4,14));tray=drain(tray,[(-50,-25),(0,-30),(50,-25),(-50,25),(50,25)])
 field=fuse([B(1.2,73,.8,x,0,3) for x in range(-50,51,10)]+[B(112,1.2,.8,0,y,3) for y in [-36,36]])
 tray=tray.union(field)
 seats=fuse([ER(97-i*8,73-i*7,9,14-i*5,15) for i in range(3)])
 # Individual seat-back notches and aisle cuts, physically modelled.
 for a in range(0,360,9):
  t=math.radians(a)
  for i in range(3):
   seats=seats.cut(B(1.1,8,1.2,(93-i*8)*math.cos(t),(69-i*7)*math.sin(t),28-i*5).rotate(((93-i*8)*math.cos(t),(69-i*7)*math.sin(t),0),((93-i*8)*math.cos(t),(69-i*7)*math.sin(t),1),a-90))
 # Broad radial aisle breaks and raised stadium entry stairs.
 for a in [45,135,225,315]:
  seats=seats.cut(B(110,5,18,55,0,15).rotate((0,0,0),(0,0,1),a))
 # Thin continuous lower seating ring holds all aisle-separated sections together.
 seats=seats.union(ER(97,73,26,2,15))
 rail=ER(101,77,3,3,33)
 bars=[]
 for a in range(0,360,15):
  t=math.radians(a);bars.append(C(1.5,12,34,99*math.cos(t),75*math.sin(t)))
 rail=fuse([rail,ER(101,77,3,2,45),B(12,16,3,0,-70,33),B(12,16,3,0,70,33)]+bars)
 # Four box trusses arch inward to center; genuine integral hanger structure.
 crown=[]
 for x,y in [(-82,-42),(82,-42),(-82,42),(82,42)]:
  crown += [rod((x,y,32),(x*.5,y*.5,87),2.3),rod((x*.5,y*.5,87),(0,0,109),2.3)]
 crown=fuse(crown+[eye(109),B(24,8,14,0,0,97)])
 # Receiver bosses tied into consecutive stadium tiers.
 tray,seats=snap(tray,seats,[(-88,0),(88,0)],3)
 seats,rail=snap(seats,rail,[(0,-65),(0,65)],19)
 rail,crown=snap(rail,crown,[(-82,-42),(82,42)],33)
 crown=crown.union(rod((-82,-42,49),(-41,-21,87),3)).union(rod((82,42,49),(41,21,87),3))
 export('stadium-bowl','Stadium Bowl','Four-part stadium with sculpted bleachers, individually notched seats, field markings, railing and a rigid overhead hanger truss.',[part('Drained field bowl',tray,G,(0,0,-30),[dict(name='Field markings',shape=field,color=W)]),part('Stepped seating bowl',seats,RED,(0,0,20)),part('Stadium balustrade',rail,W,(0,0,45)),part('Rigid hanger truss',crown,W,(0,0,80))])

def helmet():
 tray=E(65,61,3).union(ER(65,61,3,15));tray=drain(tray,[(-35,-20),(35,-20),(-30,25),(30,25)])
 # True spherical helmet with open face, cheek sides, forehead brow and vents.
 outer=cq.Workplane('XY').sphere(73).translate((0,0,77));inner=cq.Workplane('XY').sphere(69.5).translate((0,0,77))
 shell=outer.cut(inner).intersect(B(155,155,128,z=20)).cut(B(110,100,84,0,-56,25))
 shell=shell.union(ER(67,63,4,7,17)).union(eye(149))
 for x in [-26,26]:shell=shell.cut(B(8,45,7,x,-5,141))
 # Raised center stripe, ear rims, engraved shell panel line.
 stripe=outer.cut(cq.Workplane('XY').sphere(72.2).translate((0,0,77))).intersect(B(15,150,120,z=35))
 for x in [-69,69]:
  ear=cq.Workplane('YZ').center(5,66).circle(12).circle(8).extrude(3).translate((x,0,0))
  shell=shell.union(ear)
 # Curved sweeping face cage; multiple true solid rails.
 mask=[]
 for z in [43,66,88]:
  mask.append(tube([(-53,-39,z),(-48,-60,z),(-25,-73,z),(0,-76,z),(25,-73,z),(48,-60,z),(53,-39,z)],2.8))
 for x,y in [(-47,-61),(0,-76),(47,-61)]:mask.append(rod((x,y,43),(x,y,88),2.6))
 # Rounded molded brow lip and inset ear ventilation, recessed fastener heads.
 brow=tube([(-51,-40,109),(-28,-61,114),(0,-66,116),(28,-61,114),(51,-40,109)],3)
 shell=shell.union(brow)
 for x in [-70,70]:
  for yy,zz in [(1,65),(9,65),(5,73)]:
   shell=shell.cut(cq.Workplane('YZ').center(yy,zz).circle(2.2).extrude(12,both=True).translate((x,0,0)))
 mask=fuse(mask)
 # Lower service frame doubles as chin protector.
 chin=ER(68,65,3,4,14).union(B(103,7,5,0,-67,14))
 tray,chin=snap(tray,chin,[(-56,20),(56,20)],2)
 chin,shell=snap(chin,shell,[(-54,36),(54,36)],15)
 # Facemask latches on cheek posts, with bridges from receiver to side shell.
 for x in [-53,53]:shell=shell.union(B(12,15,33,x,-37,36))
 mask,shell=snap(mask,shell,[(-53,-39),(53,-39)],42)
 export('helmet','Helmet','Detailed football helmet with hollow spherical crown, ear rims, vents, raised stripe and removable multi-rail faceguard.',[part('Seed floor',tray,W,(0,0,-45)),part('Chin and service frame',chin,N,(0,0,-20)),part('Curved face mask',mask,W,(0,-60,0)),part('Helmet crown',shell,N,(0,0,35),[dict(name='Crown stripe',shape=B(15,160,120,z=122),color=W)])])

def football():
 # Smooth circular loft stations give a pointed football profile.
 profile=[(0,18),(10,23),(22,37),(34,59),(41,86),(43,111),(41,137),(34,163),(22,185),(10,200),(0,206)]
 def ball(points):
  w=cq.Workplane('XY')
  for r,z in points:w=w.add(cq.Workplane('XY').workplane(offset=z).circle(max(.5,r)).val())
  return w.toPending().loft(ruled=False)
 outer=ball(profile)
 inner=ball([(0,23),(8,27),(19,40),(31,61),(38,86),(40,111),(38,136),(31,161),(19,182),(8,196),(0,201)])
 body=outer.cut(inner).cut(B(160,160,35,z=179))
 # Four 0.8 mm raised longitudinal seams share the full shell wall beneath them.
 seam_outer=ball([(r+.8,z) for r,z in profile])
 seam_wall=seam_outer.cut(inner).intersect(B(160,160,155,z=24))
 seams=[seam_wall.intersect(B(1.6,120,155,z=24)),seam_wall.intersect(B(120,1.6,155,z=24))]
 body=fuse([body]+seams)
 # Lacing follows the inflated surface instead of floating in front of it.
 laces=[tube([(0,-40,83),(0,-43,111),(0,-40,139)],2)]
 for z in range(88,140,9):
  rr=43-0.004*(z-111)**2
  laces.append(tube([(-8,-rr+1,z),(-4,-rr-1,z+1),(0,-rr-2,z+1),(4,-rr-1,z+1),(8,-rr+1,z)],1.6))
 # Two shallow molded end-panel rings, integral to the shell.
 for z in [52,166]:
  band=seam_outer.cut(inner).intersect(B(140,140,2,z=z));body=body.union(band)
 body=body.union(fuse(laces))
 # Two turns of a true lofted helical feeding channel, 27 mm wide, raised outer lip.
 def helix_band(r0,r1,z0,z1,turns=2,height=2.5):
  w=cq.Workplane('XY');n=48
  for i in range(n+1):
   t=i/n;a=2*math.pi*turns*t;z=z0+(z1-z0)*t
   # Vertical cross section at each angle, loft uses wires in world space.
   pts=[(r0*math.cos(a),r0*math.sin(a),z),(r1*math.cos(a),r1*math.sin(a),z),(r1*math.cos(a),r1*math.sin(a),z+height),(r0*math.cos(a),r0*math.sin(a),z+height)]
   wire=cq.Wire.makePolygon([cq.Vector(*p) for p in pts]+[cq.Vector(*pts[0])]);w=w.add(wire)
  return w.toPending().loft(ruled=True)
 spiral=helix_band(37,64,37,181)
 lip=helix_band(61.5,64,37,181,height=8)
 spiral=spiral.union(lip).union(helix_band(37,39.5,37,181,height=8))
 for i in range(1,16):
  t=i/16;a=4*math.pi*t;spiral=spiral.cut(C(1.3,8,35+144*t,54*math.cos(a),54*math.sin(a)))
 # An annular hub ties the helical shelf to its snap receiver towers.
 spiral=spiral.union(R(48,43,4,108))
 cap=outer.cut(inner).intersect(B(160,160,36,z=179)).union(eye(206))
 base=C(29,4,15).union(C(13,12,3)).union(C(25,3))
 base,body=snap(base,body,[(-16,0),(16,0)],16)
 body=body.union(B(60,8,3,z=176))
 body,cap=snap(body,cap,[(-14,0),(14,0)],178)
 # Attach spiral as one printed part using two visible midbody latch bridges.
 body,spiral=snap(body,spiral,[(-40,0),(40,0)],96)
 # Radial hub relief avoids tangent sliver faces; rim retains seed across clearance.
 spiral=spiral.cut(C(45,4.6,107.7)).union(R(46.5,45,8,108))
 # Restore the full latch ledges across radial relief, retaining the original slot clearances.
 for x in [-40,40]:
  cage=B(12,7,18,x,.2,96).cut(B(8.6,2.2,19,x,0,95.9)).cut(B(8.8,5,3,x,2.4,108.7))
  spiral=spiral.union(cage)
 for x in [-40,40]:spiral=spiral.cut(B(8.8,5,3,x,2.4,108.7))
 # Discard the inaccessible ribbon offcut inside the hollow football after cavity relief.
 spiral=spiral.cut(base).cut(body)
 spiral=cq.Workplane('XY').add(max(spiral.val().Solids(),key=lambda s:s.Volume()))
 export('spiral-football','Spiral Football','Pointed football shell with four raised seams, contoured round cross-laces and end-panel bands, wrapped by a continuous two-turn seed channel and removable snap cap.',[part('Football pedestal',base,G,(0,0,-30)),part('Laced football shell',body,BROWN,(0,0,0)),part('Helical seed ribbon',spiral,G,(45,0,0)),part('Football refill tip',cap,BROWN,(0,0,45))])

def pylon():
 tray=B(84,80,3).union(B(84,80,15).cut(B(77,73,17,z=3)));tray=drain(tray,[(-23,-23),(23,-23),(-23,23),(23,23)])
 cage=B(55,51,4,z=20).cut(B(45,41,6,z=19)).union(B(55,51,4,z=169).cut(B(45,41,6,z=168)))
 for x in [-25,25]:
  for y in [-23,23]:cage=cage.union(B(5,5,152,x,y,21))
 # Actual printable diagonally crossed mesh on all four faces.
 mesh=[]
 for a in [0,90,180,270]:
  for z in range(31,151,12):
   for sign in [-1,1]:mesh.append(rod((-23,-23,z if sign>0 else z+32),(23,-23,z+32 if sign>0 else z),.8).rotate((0,0,0),(0,0,1),a))
 cage=fuse([cage]+mesh)
 # Wide rounded corner pads suggest a padded sideline marker.
 for x in [-25,25]:
  for y in [-23,23]:cage=cage.union(C(3.2,151,21,x,y))
 canopy=cq.Workplane('XY').workplane(offset=173).rect(64,60).workplane(offset=38).rect(48,44).loft().cut(cq.Workplane('XY').workplane(offset=172).rect(57,53).workplane(offset=35).rect(42,38).loft()).union(B(49,45,3,z=210)).union(eye(213))
 for z in range(179,208,4):
  k=(z-173)/38;w=64-16*k;d=60-16*k
  canopy=canopy.union(B(w+.8,d+.8,.8,z=z).cut(B(w-4,d-4,2,z=z-.5)))
 # Raised plinth relief and perching lip.
 plinth=B(91,87,4,z=14).cut(B(75,71,6,z=13))
 for z in [15,17]:plinth=plinth.union(B(94,90,.8,z=z).cut(B(75,71,2,z=z-.5)))
 for x,y in [(-25,23),(25,-23)]:plinth=plinth.union(B(12,22,3,x,30 if y>0 else -30,16))
 tray,plinth=snap(tray,plinth,[(-36,0),(36,0)],1)
 plinth,cage=snap(plinth,cage,[(-25,23),(25,-23)],16)
 cage,canopy=snap(cage,canopy,[(-25,-23),(25,23)],158)
 export('touchdown-pylon','Touchdown Pylon','Ribbed orange touchdown marker with a real crossed printed-mesh reservoir, white corner rails, drained tray and snap refill cap.',[part('Drain tray',tray,O,(0,0,-35)),part('Ribbed perimeter plinth',plinth,O,(0,0,-15)),part('Printed mesh tower',cage,W,(0,0,30)),part('Pylon snap cap',canopy,O,(0,0,65))])

def scoreboard():
 tray=B(136,112,3).union(B(136,112,15).cut(B(129,105,17,z=3)));tray=drain(tray,[(-42,-30),(42,-30),(-42,30),(42,30)])
 frame=B(108,82,4,z=24).cut(B(94,68,6,z=23))
 for x in [-50,50]:
  for y in [-37,37]:frame=frame.union(B(8,8,132,x,y,25))
 frame=frame.union(B(108,82,4,z=153).cut(B(94,68,6,z=152)))
 for x in [-50,50]:frame=frame.union(B(8,76,3,x,0,74))
 panel=B(94,5,76,0,-37,79)
 # High relief seven-segment numerals remain connected to one scoreboard face.
 def digit(v,x,z):
  seg={'0':'abcdef','1':'bc','2':'abged','3':'abgcd','4':'fgbc','7':'abc'}[v]
  boxes={'a':(12,2.2,x,z+23),'g':(12,2.2,x,z+12),'d':(12,2.2,x,z),'f':(2.2,11,x-6,z+13),'b':(2.2,11,x+6,z+13),'e':(2.2,11,x-6,z+1),'c':(2.2,11,x+6,z+1)}
  return fuse([B(w,.8,h,xx,-39.6,zz) for w,h,xx,zz in [boxes[s] for s in seg]])
 # Inset scoreboard bezel with chamfered corners and visible mounting bosses.
 bezel=B(96,2,78,0,-40,78).edges('|Y').fillet(3).cut(B(88,4,70,0,-40,82))
 panel=panel.union(bezel)
 for x in [-43,43]:
  for z in [84,150]:
   bolt=cq.Workplane('XZ').center(x,z).circle(2.2).extrude(1.4).translate((0,-40,0))
   panel=panel.union(bolt).cut(B(2.4,1,.8,x,-41.2,z-.4))
 accents=[]
 for val,x in [('1',-30),('4',-12),('0',12),('7',30)]:
  d=digit(val,x,105);accents.append(d);panel=panel.union(d)
 for txt,size,z in [('HOME  GUEST',8,143),('QTR  3',8,91)]:
  d=cq.Workplane('XZ').text(txt,size,.8).translate((0,-39.5,z));accents.append(d);panel=panel.union(d)
 roof=cq.Workplane('XY').workplane(offset=157).rect(142,118).workplane(offset=24).rect(62,44).loft().cut(cq.Workplane('XY').workplane(offset=156).rect(134,110).workplane(offset=22).rect(60,42).loft()).union(B(64,46,3,z=179)).union(eye(182))
 for z,w,d in [(160,132,108),(166,112,90),(172,92,72)]:roof=roof.union(B(w,d,.8,z=z).cut(B(w-5,d-5,2,z=z-.5)))
 for x,y in [(-50,-37),(50,37)]:tray=tray.union(B(12,10,10,x,y,0))
 for x,y in [(-50,37),(50,-37)]:roof=roof.union(B(12,8,17,x,y,158))
 tray,frame=snap(tray,frame,[(-50,-37),(50,37)],9)
 frame,roof=snap(frame,roof,[(-50,37),(50,-37)],141)
 panel,frame=snap(panel,frame,[(-42,-37),(42,-37)],132)
 export('scoreboard-lantern','Scoreboard Lantern','Stadium lantern with solid relief HOME/GUEST 14–07 scoreboard, lower feeding portals, corner framework and tiered snap roof.',[part('Stadium seed deck',tray,K,(0,0,-35)),part('Lantern structural frame',frame,G,(0,0,15)),part('Relief scoreboard panel',panel,K,(0,-50,0),[dict(name='Raised scoreboard digits',shape=fuse(accents),color=Y)]),part('Tiered lantern roof',roof,G,(0,0,55))])

def goalpost():
 tray=B(130,49,3).union(B(130,49,23).cut(B(123,42,25,z=3)));tray=drain(tray,[(-40,0),(0,0),(40,0)])
 for x in range(-50,51,10):tray=tray.union(B(1.2,39,.8,x,0,3))
 # Massive U goal structure and rear circular target form one rigid hanger body.
 frame=rod((-70,0,16),(70,0,16),6)
 for x in [-70,70]:frame=frame.union(rod((x,0,16),(x,0,174),6))
 target=cq.Workplane('XZ').center(0,111).circle(58).circle(52).extrude(4,both=True)
 target=target.union(eye(169))
 # Raised aiming ticks and rounded upright safety caps.
 for a in range(0,360,30):
  tick=B(2,9,4,0,0,163).rotate((0,0,111),(0,1,111),a)
  target=target.union(tick)
 for x in [-70,70]:frame=frame.union(cq.Workplane('XY').sphere(6).translate((x,0,174)))
 # Shoulder web visibly blends ring to uprights; ring does not rely on cords.
 for x in [-58,58]:target=target.union(rod((56 if x>0 else -56,0,111),(60 if x>0 else -60,0,111),4))
 foot=C(26,4,z=-34).union(C(12,35,z=-30))
 # Small reinforcing collars and physical grip grooves.
 for x in [-70,70]:
  for z in range(30,171,7):frame=frame.union(C(6.7,.8,z,x,0))
 foot,frame=snap(foot,frame,[(-5,0),(5,0)],-4)
 tray,frame=snap(tray,frame,[(-60,0),(60,0)],3)
 for x in [-60,60]:frame=frame.union(B(19,8,3,65 if x>0 else -65,0,95))
 frame,target=snap(frame,target,[(-60,0),(60,0)],96)
 export('goalpost-ring','Goalpost Ring','Yellow U-shaped goal uprights with a circular target and central hanger, green marked seed field, removable plinth and snap service joints.',[part('Goal pedestal',foot,Y,(0,0,-45)),part('U goal frame',frame,Y,(0,0,0)),part('Marked feeding field',tray,G,(0,-50,0)),part('Target ring and hanger',target,Y,(0,0,45))])

if __name__=='__main__':
 for fn in [stadium,helmet,football,pylon,scoreboard,goalpost]:
  if len(sys.argv)==1 or fn.__name__ in sys.argv[1:]:
   try:fn()
   except Exception as e:
    import traceback;traceback.print_exc();print('FAILED',fn.__name__,repr(e),flush=True)
