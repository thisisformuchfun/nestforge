"""R2 World architecture. mm, assembly Z-up; four structural physical parts."""
import cadquery as cq, math, sys, json
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
GREEN='#526043'; CREAM='#E8D5AF'; ORANGE='#CF662C'; BROWN='#79543B'; BLUE='#2865A8'
def B(x,y,h,px=0,py=0,z=0):return cq.Workplane('XY').box(x,y,h,centered=(True,True,False)).translate((px,py,z))
def C(r,h,z=0):return cq.Workplane('XY').circle(r).extrude(h).translate((0,0,z))
def R(a,b,h,z=0):return C(a,h,z).cut(C(b,h+.2,z-.1))
def U(parts):
 s=parts[0]
 for p in parts[1:]:s=s.union(p,clean=False)
 return s.clean()
def poly(n,r,h,z=0):return cq.Workplane('XY').polygon(n,2*r).extrude(h).translate((0,0,z))
def pr(n,a,b,h,z):return poly(n,a,h,z).cut(poly(n,b,h+.2,z-.1))
def sq(a,b,h,z):return B(a,a,h,z=z).cut(B(b,b,h+.2,z=z-.1))
def roundloft(st):
 w=cq.Workplane('XY').workplane(offset=st[0][0]).circle(st[0][1]);last=st[0][0]
 for z,r in st[1:]:w=w.workplane(offset=z-last).circle(r);last=z
 return w.loft(ruled=True)
def squareloft(st):
 w=cq.Workplane('XY').workplane(offset=st[0][0]).rect(st[0][1],st[0][1]);last=st[0][0]
 for z,a in st[1:]:w=w.workplane(offset=z-last).rect(a,a);last=z
 return w.loft(ruled=True)
def eye(z):return cq.Workplane('XZ').center(0,z+8).circle(9).circle(4.6).extrude(4,both=True).union(B(16,8,7,z=z-1))
def rotate(s,a):return s.rotate((0,0,0),(0,0,1),a)
def arch(w,z,spring,top,d=12):
 return cq.Workplane('XZ').moveTo(-w/2,z).lineTo(-w/2,spring).threePointArc((-w*.35,top-3),(0,top)).threePointArc((w*.35,top-3),(w/2,spring)).lineTo(w/2,z).close().extrude(d,both=True)
def hooks(z,down=False):
 # 22 x 8 x 1.6 cantilever, 1.0 mm radial undercut with chamfered lead-in.
 out=[]
 for a in [0,90,180,270]:
  if not down:
   arm=B(8,1.6,22,py=-53,z=z)
   barb=cq.Workplane('YZ').polyline([(-53.8,z+16),(-55,z+16),(-55,z+18),(-53.8,z+21)]).close().extrude(8).translate((-4,0,0))
  else:
   arm=B(8,1.6,22,py=-53,z=z-22)
   barb=cq.Workplane('YZ').polyline([(-53.75,z-18),(-55,z-18),(-55,z-16),(-53.75,z-13)]).close().extrude(8).translate((-4,0,0))
  out.extend([rotate(arm,a),rotate(barb,a)])
 return U(out)
def receiver(s,z,down=False):
 for a in [0,90,180,270]:
  s=s.cut(rotate(B(9,7,23,py=-51.8,z=z-22 if down else z),a))
  # add dedicated socket outside cantilever, release window exposes retaining tip
  wall=B(13,3,23,py=-55.9,z=z-22 if down else z)
  wall=wall.cut(B(9,5,5,py=-55.9,z=z-19 if down else z+15))
  s=s.union(rotate(wall,a),clean=False)
 return s.clean()
def tray(round_=False):
 t=(poly(8,83,4) if round_ else B(156,156,4))
 t=t.union(pr(8,83,78,9,4) if round_ else sq(156,148,9,4))
 t=t.union(R(33,29.4,2.5,4)).union(hooks(4))
 # body rests on tray at 18, sockets hang to 4; structural tabs lift tray
 t=t.union(R(26.2,23,10,4))
 cuts=[]
 for x in [-54,-36,-18,0,18,36,54]:
  for y in [-54,-36,-18,0,18,36,54]:cuts.append(C(1.2,5,-.5).translate((x,y,0)).val())
 t=t.cut(cq.Compound.makeCompound(cuts))
 return t
def mesh():
 # The full central storage chamber is printed, with 2.4mm slits and feed ports.
 s=R(29,26.5,111,4)
 cuts=[]
 for a in range(0,360,12):
  for z in range(23,106,13):cuts.append(rotate(B(2.4,8,10,py=-28,z=z),a).val())
 s=s.cut(cq.Compound.makeCompound(cuts))
 for a in [0,90,180,270]:s=s.cut(rotate(B(13,9,7,py=-28,z=7),a))
 return s

def body(style):
 if style in ['pagoda','cabin']:
  f=sq(112,103,112,18)
  for a in [0,90,180,270]:
   cut=B(74,16,82,py=-55,z=25) if style=='pagoda' else arch(71,24,77,112,14).translate((0,-55,0))
   f=f.cut(rotate(cut,a))
  f=U([f,sq(118,102,5,22),sq(118,102,5,117)])
  if style=='pagoda':
   for a in [0,90,180,270]:
    f=f.union(rotate(B(101,7,5,py=-55,z=106),a))
    for x in range(-42,43,14):f=f.union(rotate(B(5,7,10,x,-55,111),a),clean=False)
  else:
   for z in range(30,120,7):
    for a in [0,90,180,270]:f=f.cut(rotate(B(114,1.2,1,py=-55.7,z=z),a))
 else:
  f=pr(8,68,63,112,18)
  ap=68*math.cos(math.pi/8)
  for a in range(0,360,45):
   cut=arch(34,27,83,111,12).translate((0,-ap,0));f=f.cut(rotate(cut,a+22.5))
   rim=arch(42,26,83,116,1.5).cut(arch(35,25,83,111,2)).translate((0,-ap-1,0))
   f=f.union(rotate(rim,a+22.5),clean=False)
   if style=='haveli':
    # physical jali in upper arch, and pierced balcony lower rail
    for x in [-12,-6,0,6,12]:
     f=f.union(rotate(B(1.5,3,18,x,-ap,90),a+22.5),clean=False)
     f=f.union(rotate(B(2,3,12,x,-ap,27),a+22.5),clean=False)
    for z in [94,101]:f=f.union(rotate(B(31,3,1.5,py=-ap,z=z),a+22.5),clean=False)
   if style=='riad':
    for x in [-22,22]:
     for z in range(35,103,10):
      tile=rotate(B(4.2,1.6,4.2,px=x,py=-ap-.5,z=z),0)
      f=f.union(rotate(tile,a+22.5),clean=False)
  f=f.union(pr(8,72,62,4,119)).union(pr(8,70,62,4,24))
  if style=='haveli':
   for a in range(0,360,15):f=f.union(rotate(B(4,8,7,py=-66,z=113),a),clean=False)
 # R5 facade craft: integral transom lattice, timber grain, carved archivolts.
 detail_cuts=[]
 if style=='pagoda':
  for a in (0,90,180,270):
   lattice=[]
   for x in range(-34,35,10):
    lattice.append(beam((x,-55,94),(x+10,-55,106),.85))
    lattice.append(beam((x,-55,106),(x+10,-55,94),.85))
   panel=U(lattice).intersect(B(74,8,12,py=-55,z=94))
   f=f.union(rotate(panel,a))
 elif style=='cabin':
  for a in (0,90,180,270):
   for x in (-48,-43,43,48):
    for zz in (36,58,80,101):
     # Short overlapping cylinders create softly meandering carved grain.
     path=[(x,-56,zz),(x+.8,-56,zz+4),(x-.6,-56,zz+9),(x+.4,-56,zz+14)]
     grain=U([beam(p,q,.72) for p,q in zip(path,path[1:])])
     detail_cuts.append(rotate(grain,a).val())
 else:
  for a in range(0,360,45):
   # Incised joints articulate the existing arch moulding into curved voussoirs.
   for dx,zz in [(-18,91),(-14,104),(-7,111),(7,111),(14,104),(18,91)]:
    detail_cuts.append(rotate(B(1.1,1.1,5,dx,-ap-2.1,zz),a+22.5).val())
   if style=='riad':
    for x in (-22,22):
     for zz in range(35,103,10):
      diamond=cq.Workplane('XZ').center(x,zz+2.1).polyline([(0,-1.5),(1.5,0),(0,1.5),(-1.5,0)]).close().extrude(.7,both=True).translate((0,-ap-1.15,0))
      detail_cuts.append(rotate(diamond,a+22.5).val())
   if style=='haveli':
    # Petal piercings in the deep upper spandrel form a printed floral frieze.
    for x in (-22,22):
     rosette=cq.Workplane('XZ').center(x,108).circle(1.6).extrude(9,both=True).translate((0,-ap,0))
     detail_cuts.append(rotate(rosette,a+22.5).val())
 if detail_cuts:f=f.cut(cq.Compound.makeCompound(detail_cuts))
 # all sockets connect to lower and upper architectural belts
 f=f.union(sq(112,101,4,18)).union(sq(112,101,4,126))
 f=receiver(f,4)
 for a in [0,90,180,270]:f=f.cut(rotate(B(9.2,8,21,py=-53,z=108),a))
 for a in [0,90,180,270]:f=f.cut(rotate(B(14,9,23,py=-58.6,z=108),a))
 f=f.union(hooks(130,True))
 return f.clean()
def roof(style):
 base=sq(119,101,4,130)
 if style=='pagoda':
  # Concave profile: steep upper field flares into lifted deep eaves, two tiers.
  st=[(130,160),(133,151),(139,114),(150,76),(158,52)]
  lower=squareloft(st).cut(squareloft([(129.8,151),(133,140),(139,104),(150,66),(155,44)]))
  upper=squareloft([(173,111),(176,99),(183,62),(196,14)]).cut(squareloft([(172.8,103),(176,90),(183,53),(193,9)]))
  r=U([base,lower,sq(52,44,32,155),upper,B(15,15,4,z=194)])
  # roof tile seams, physical narrow bands follow individual roof stations
  for z,w in [(134,145),(139,115),(144,97),(149,79),(176,99),(181,73),(187,45)]:r=r.union(sq(w+1.5,w-3,1,z))
  # Radial tile seam cuts are engraved on the broad lower roof field.
  skin=squareloft([(130,160.3),(133,151.3),(139,114.3),(150,76.3),(158,52.3)]).cut(squareloft([(130,158.4),(133,149.4),(139,112.4),(150,74.4),(158,50.4)]))
  for a in (0,90,180,270):
   for x in (-30,-15,0,15,30):r=r.cut(rotate(B(1.1,90,22,x,-45,134),a).intersect(skin))
  r=r.union(eye(197))
 elif style=='cabin':
  # True tall A-frame section, transverse ridge, deeply projecting gable eaves.
  outer=cq.Workplane('XZ').polyline([(-83,130),(0,219),(83,130)]).close().extrude(77,both=True)
  inner=cq.Workplane('XZ').polyline([(-76,129),(0,211),(76,129)]).close().extrude(79,both=True)
  r=U([base,outer.cut(inner)])
  cuts=[]
  for sign in [-1,1]:
   for z in range(132,211,9):
    x=sign*(83-(z-130)*83/89)
    r=r.union(B(3,156,1.2,x,0,z),clean=False)
    for y in range(-70+(int(z/9)%2)*7,73,14):cuts.append(B(3,1,7,x,y,z-5).val())
  r=r.cut(cq.Compound.makeCompound(cuts))
  r=r.union(eye(214))
 else:
  if style=='villa':st=[(130,79),(133,79),(161,8),(166,4)]
  elif style=='riad':st=[(130,77),(134,77),(151,47),(171,25),(181,6)]
  else:st=[(130,78),(134,78),(145,68),(158,52),(168,30),(173,9)]
  inn=[(z-.2 if i==0 else z,max(2,r-3.5)) for i,(z,r) in enumerate(st[:-1])]+[(st[-1][0]-3,2)]
  r=U([base,roundloft(st).cut(roundloft(inn)),C(8,5,st[-1][0]-2)])
  # Narrow meridional tile ribs; no transparent material or decal texture.
  for a in range(0,360,15):
   points=[(rr+.8,z) for z,rr in st[:-1]]+[(max(2,st[-1][1]),st[-1][0])]
   back=[(rr-1,z) for z,rr in reversed(st)]
   rib=cq.Workplane('XZ').polyline(points+back).close().extrude(1.1,both=True)
   r=r.union(rotate(rib,a),clean=False)
  # Overlapping curved tile courses complement meridian ribs on the dome.
  for zz in range(139,st[-1][0]-6,6):
   for (z0,r0),(z1,r1) in zip(st,st[1:]):
    if z0<=zz<z1:
     rr=r0+(r1-r0)*(zz-z0)/(z1-z0)
     rn=r0+(r1-r0)*(zz+1.1-z0)/(z1-z0)
     course=roundloft([(zz,rr+.9),(zz+1.1,rn+.9)]).cut(roundloft([(zz-.1,rr-2),(zz+1.2,rn-2)]))
     r=r.union(course,clean=False)
     break
  r=r.union(eye(st[-1][0]+3))
 r=r.union(R(32,29.4,8,111)).union(C(32,3,118))
 end={'pagoda':(54,16,139),'cabin':(72,16,139),'villa':(64,16,137),'riad':(62,16,140),'haveli':(69,16,141)}[style]
 for a in [0,90,180,270]:
  r=r.union(rotate(beam((26,0,119),(45,12,133),2.8),a)).union(rotate(beam((45,12,133),end,2.8),a))
 r=receiver(r,130,True)
 return r.clean()
def beam(p,q,r=2):
 v=cq.Vector(*q).sub(cq.Vector(*p));return cq.Workplane('XY').add(cq.Solid.makeCylinder(r,v.Length,cq.Vector(*p),v.normalized()))
def strut(p,q,r=3):
 v=cq.Vector(*q).sub(cq.Vector(*p))
 return cq.Workplane(cq.Plane(origin=cq.Vector(*p),normal=v.normalized())).polygon(8,2*r).extrude(v.Length)
def geodesic():
 # Geodesic-inspired triangulated latitude cage; every triangle is a physical strut.
 rings=[]
 for z,rad,off in [(18,48,0),(54,76,15),(101,79,0),(142,59,15),(170,19,0)]:
  rings.append([(rad*math.cos(math.radians(k*30+off)),rad*math.sin(math.radians(k*30+off)),z) for k in range(12)])
 beams=[poly(8,4.3,7.2,point[2]-3.6).translate((point[0],point[1],0)) for row in rings for point in row]
 for row in rings:
  for k in range(12):beams.append(strut(row[k],row[(k+1)%12],3))
 for j in range(4):
  for k in range(12):
   beams.append(strut(rings[j][k],rings[j+1][k],3))
   beams.append(strut(rings[j][k],rings[j+1][(k+(-1 if j%2==0 else 1))%12],3))
 shell=U(beams+[sq(112,101,4,18),sq(112,101,4,126)])
 # Low landing ledge and eight small triangular opaque accent facets.
 for k in range(0,12,2):
  pts=[cq.Vector(*rings[1][k]),cq.Vector(*rings[2][k]),cq.Vector(*rings[2][(k-1)%12])]
  face=cq.Face.makeFromWires(cq.Wire.makePolygon(pts+[pts[0]]))
  panel=cq.Workplane('XY').add(cq.Solid.extrudeLinear(face.outerWire(),[],cq.Vector(0,0,2)))
  center=(pts[0]+pts[1]+pts[2]).multiply(1/3)
  # Nested triangular relief ribs are integral to the opaque facets.
  for scale in (.72,.44):
   inset=[center+(point-center).multiply(scale)+cq.Vector(0,0,1.75) for point in pts]
   for j in range(3):panel=panel.union(beam(inset[j].toTuple(),inset[(j+1)%3].toTuple(),.8),clean=False)
  shell=shell.union(panel,clean=False)
 # Split the triangulated shell at its structural waist for full-width refill access.
 lower=shell.intersect(B(220,220,130,z=0)).union(R(68,61,4,126))
 crown=shell.intersect(B(220,220,80,z=130)).union(sq(119,101,4,130)).union(R(68,61,4,130))
 lower=receiver(lower,4)
 for a in [0,90,180,270]:lower=lower.cut(rotate(B(9.2,8,21,py=-53,z=108),a))
 for a in [0,90,180,270]:lower=lower.cut(rotate(B(14,9,23,py=-58.6,z=108),a))
 lower=lower.union(hooks(130,True))
 crown=crown.union(C(23,4,169)).union(eye(173))
 crown=crown.union(R(32,29.4,8,111)).union(C(32,3,118))
 for a in [0,90,180,270]:crown=crown.union(rotate(beam((26,0,119),(45,12,133),2.8),a)).union(rotate(beam((45,12,133),(66,18,141),2.8),a))
 crown=receiver(crown,130,True)
 return lower.clean(),crown.clean()

def run(slug):
 from common import export_design
 styles={'japanese-pagoda':('Japanese Pagoda','pagoda',GREEN),'moroccan-riad':('Moroccan Riad','riad',ORANGE),'scandinavian-cabin':('Scandinavian Cabin','cabin',GREEN),'mediterranean-villa':('Mediterranean Villa','villa',ORANGE),'indian-haveli':('Indian Haveli','haveli',GREEN),'geodesic-fusion':('Geodesic Fusion','geo',BLUE)}
 name,style,col=styles[slug]
 print('BUILD',slug,flush=True)
 bd,rf=geodesic() if style=='geo' else (body(style),roof(style))
 print('STRUCTURE',slug,len(bd.val().Solids()),len(rf.val().Solids()),flush=True)

 # Trim is physically printed relief on body; designate intersecting bottom/top cornice regions.
 mask=B(240,240,8,z=117).union(B(240,240,7,z=22))
 trim=bd.intersect(mask)
 if style=='riad':trim=trim.union(bd.cut(poly(8,68.05,160,0)))
 parts=[dict(name='Drained landing tray',shape=tray(style not in ['pagoda','cabin']),color=BROWN,explode=[0,0,-35]),dict(name='Architectural load frame',shape=bd,color=BROWN if style=='cabin' else CREAM,regions=[dict(name='Architectural cornice accent',shape=trim,color=CREAM if style=='cabin' else col)],explode=[0,0,25],support='Build-plate supports under the lower cornice; keep all snap flexure slots clear'),dict(name='Printed mesh seed chamber',shape=mesh(),color=BROWN,explode=[0,0,65]),dict(name='Snap weather roof and hanger',shape=rf,color=col,explode=[0,0,105],support='Local support under eaves and eye; remove before assembly')]
 return export_design(slug,name,'World architecture','R2 architectural feeder with printed relief, central printed seed mesh and a rigid snap-locked load path.',parts,notes=['Digital prototype: snap flexure, weather resistance and suspended load require physical qualification.','Four physical parts and at most three colors; color relief belongs to the structural part.','Integral 2.4 mm drains. Mesh apertures 2.4 x 10 mm; use seed blend that does not spill through them.','0.6 mm total socket clearance; 22 mm cantilevers are 1.6 mm thick.','Seed chamber is positively captive between tray locating rings and locked roof; remove roof to refill and tray for cleaning.'],assembly=['Seat printed seed chamber between tray locating rings.','Press frame onto four tray snap hooks until all receiver windows engage.','Press roof onto upper frame hooks; inspect each hook through release window.','Suspend completed rigid assembly only from the integral top eye.'],reference='upload/image(20261008-183815).png',hanger=[0,0,205 if style=='pagoda' else 222 if style=='cabin' else 181 if style=='geo' else 192 if style=='riad' else 184 if style=='haveli' else 177],snap_joints=[dict(name='Tray to load frame',parts=['Drained landing tray','Architectural load frame'],description='Four radial cantilevers with positive 1 mm undercuts and external release windows',beam_length_mm=22,beam_thickness_mm=1.6,deflection_mm=1,clearance_mm=.6,release='Depress visible hooks through four external windows while supporting tray.'),dict(name='Roof to load frame',parts=['Architectural load frame','Snap weather roof and hanger'],description='Positive radial snap retention; top eye load passes through frame and tray hooks',beam_length_mm=22,beam_thickness_mm=1.6,deflection_mm=1,clearance_mm=.6,release='Squeeze exposed hooks before lifting roof; never release when hanging.')],refill='Unhang, release roof hooks, lift roof, pour into printed central seed chamber, then re-engage hooks.',detail_features=[{'pagoda':'Two flared pagoda roof tiers and bracket frieze','riad':'Moorish arches, raised tile pilasters and ribbed lantern roof','cabin':'Steep gable, physical board siding and staggered roof shingle seams','villa':'Octagonal stucco arcade and radial terracotta tile ribs','haveli':'Pierced jali, ornamental chajja brackets and ribbed dome','geo':'Triangulated cage with alternating solid facets and removable upper crown'}[style],'Actual 0.8–1.2 mm relief architecture and roof seams','Printed open seed lattice','Single integral top hanger','Accessible positive snap windows'])
if __name__=='__main__':
 for slug in sys.argv[1:] or ['japanese-pagoda','moroccan-riad','scandinavian-cabin','mediterranean-villa','indian-haveli','geodesic-fusion']:run(slug)
