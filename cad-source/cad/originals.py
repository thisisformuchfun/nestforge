"""NestForge Originals R2. Dimensions mm, assembled Z up. PETG prototype.
All physical interfaces use cantilever hooks and external release windows.
Four pieces/design: basin, sculpted housing, hanging roof, mesh seed basket.
No cord passes between components. Release all three catches before separating.
"""
import cadquery as cq
import math,sys
from common import *
CREAM='#EEE5CC'; GREEN='#657337'; PURPLE='#713A85'; BLUE='#1564B2'; RED='#DC352C'; ORANGE='#EE861E'; TEAL='#174C51'
def pts(n,r,offset=0):return [(r*math.cos(math.radians(offset+360*k/n)),r*math.sin(math.radians(offset+360*k/n))) for k in range(n)]
def loft(ps,n=None):
 w=cq.Workplane('XY').workplane(offset=ps[0][0])
 for i,(z,r) in enumerate(ps):
  if i:w=w.workplane(offset=z-ps[i-1][0])
  w=w.circle(r) if n is None else w.polygon(n,2*r)
 return w.loft(ruled=True)
def shell(ps,t=3,n=None):return loft(ps,n).cut(loft([(z,r-t) for z,r in ps],n))
def rod(a,b,r=1):
 v=cq.Vector(*b)-cq.Vector(*a)
 return cq.Workplane('XY').add(cq.Solid.makeCylinder(r,v.Length,cq.Vector(*a),v.normalized()))
def rot(s,a):return s.rotate((0,0,0),(0,0,1),a)
def arch(s,n,w,z,h,depth=100,offset=0):
 cut=cq.Workplane('XZ').polyline([(-w/2,z),(w/2,z),(w/2,z+h-w/2),(0,z+h),(-w/2,z+h-w/2)]).close().extrude(depth)
 for a in range(n):s=s.cut(rot(cut,offset+a*360/n))
 return s

def joint(low,up,r,z,angles=(30,150,270)):
 """1.6 x 22 mm flexible beam; 0.7 mm locking undercut; 0.30 mm clearance.
 External open windows expose hook noses for simultaneous thumb release.
 """
 for a in angles:
  root=box(18,6,3,r-5,0,z-17)
  beam=box(1.6,5.4,22,r+3.2,0,z-17)
  hook=cq.Workplane('XZ').polyline([(r+3.9,z+3.3),(r+5.0,z+3.3),(r+5.0,z+4.2),(r+3.9,z+6.4)]).close().extrude(2.7,both=True)
  low=low.cut(rot(box(7,7,23,r+4.5,0,z-14),a)).union(rot(root.union(beam).union(hook),a))
  rec=box(7.5,11.5,9.7,r+2.5,0,z+.3)
  rec=rec.cut(box(2.2,6,12,r+3.2,0,z-.5))
  rec=rec.cut(box(5,6.2,3.4,r+5.5,0,z+3.1))
  up=up.union(rot(rec,a)).cut(rot(box(2.2,6,12,r+3.2,0,z-.5),a)).cut(rot(box(5,6.2,3.4,r+5.5,0,z+3.1),a))
 return low,up

def eye(z):
 return cq.Workplane('XZ').center(0,z+10).circle(10).circle(5).extrude(3,both=True).union(cyl(8,4,z-1))
def basket():
 # Printed seed containment mesh: 1.6 mm ribs, 2.8 mm clear cells.
 b=cyl(26,2.5,21)
 b=b.union(ring(26,23.8,3,23)).union(ring(26,23.8,3,71))
 for z in range(27,71,5):b=b.union(ring(26,24.4,1.6,z))
 for a in range(0,360,12):b=b.union(rot(box(2.6,1.8,49,24.9,0,23),a))
 # Two service detents lock under basin internal socket lugs.
 for a in (0,180):
  # Relief behind beam allows inward travel; upper beam segment is exposed
  # above the socket for a finger squeeze. Hook projects 0.7 mm past socket.
  b=b.cut(rot(box(5,6.6,13,25.5,0,22),a))
  tab=box(1.6,6,15,27.1,0,22)
  nose=cq.Workplane('XZ').polyline([(26.3,22.4),(27.9,22.4),(29.5,24.0),(29.5,24.5),(26.3,24.5)]).close().extrude(3,both=True)
  tab=tab.union(nose).union(box(3,6,2,26.5,0,35))
  b=b.union(rot(tab,a))
 return b

def base(r,color):
 b=loft([(0,r-17),(7,r-5),(13,r),(21,r)])
 b=b.cut(loft([(3,r-16),(7,r-9),(13,r-3),(24,r-3)]))
 b=b.union(ring(r+6,r-3,3,14))
 for x,y in pts(12,r*.63):b=b.cut(cyl(1.1,8,-1).translate((x,y,0)))
 # Socket detents with 0.3 mm clearance to basket; push inward through basket.
 for a in (0,180):
  lug=box(7,9,22,30.5,0,3).cut(box(3,6.6,24,27.3,0,3))
  lug=lug.cut(box(5,6.8,1.7,27.5,0,23))
  lug=lug.union(box(5.2,9,3.1,31.4,0,24.9)) # 3.3 mm strong detent shoulder
  b=b.union(rot(lug,a))
 return b

def p(name,s,c,e):return dict(name=name,shape=s,color=c,explode=e,support='PETG 0.20 mm layers, 4 walls; organic supports beneath overhangs only. Keep release windows free.')
def publish(slug,name,b,body,roof,colors,description):
 # Basket socket is common; all other receivers generated at exact interfaces.
 parts=[p('Drained sculpted basin',b,colors[0],[0,0,-45]),p('Architectural shelter',body,colors[1],[65,0,0]),p('Hanging service crown',roof,colors[2],[0,0,55]),p('Printed mesh seed basket',basket(),colors[3],[-60,0,15])]
 # AMS regions are volumes of the single physical shell, never extra loose trim.
 if slug=='modern-pod':
  masks=[]
  for a in (0,120,240):
   mask=cq.Workplane('XZ').center(0,82).ellipse(28,51).extrude(100)
   masks.append(rot(mask,a).val())
  parts[1]['regions']=[dict(name='Purple portal bevel region',shape=cq.Compound.makeCompound(masks),color=PURPLE)]
 if slug=='leaf-cocoon':
  inner=loft([(21.3,53.4),(36,62.4),(57,69.4),(79,68.4),(103,59.4),(126,45.4),(148,29.4),(160,21.4)])
  parts[1]['regions']=[dict(name='Warm orange inner leaf surface',shape=inner,color=ORANGE)]
 if slug=='spiral-shell':
  inner=loft([(21.3,57.2),(35,65.2),(55,69.2),(78,68.2),(100,61.2),(124,48.2),(146,31.2),(158,23.2)])
  parts[1]['regions']=[dict(name='Red reverse of blue spiral ribbons',shape=inner,color=RED)]
 if slug=='geometric-orbit':
  edge_mask=cq.Workplane('XZ').polyline([(-29,38),(29,38),(40,77),(25,120),(-25,120),(-40,77)]).close().extrude(110)
  bands=edge_mask
  for a in range(60,360,60):bands=bands.union(rot(edge_mask,a))
  parts[1]['regions']=[dict(name='Orange polygon window borders',shape=bands,color=ORANGE),dict(name='Blue upper orbit facets',shape=box(200,200,100,0,0,109),color=BLUE),dict(name='Orange window sills',shape=box(200,200,6,0,0,30),color=ORANGE)]
 import itertools
 paircheck=[]
 for ia,ib in itertools.combinations(range(len(parts)),2):
  va=parts[ia]['shape'].val().intersect(parts[ib]['shape'].val()).Volume()
  paircheck.append(dict(parts=[parts[ia]['name'],parts[ib]['name']],volume_mm3=round(va,6)))
  if va>.05:raise ValueError(f'{slug}: interpart clash {ia}/{ib}: {va:.3f} mm3')
 retention=[]
 for lo,hi,dz,label in [(0,1,-.5,'Basin hooks'),(1,2,-.5,'Crown hooks'),(3,0,.5,'Mesh cup detents')]:
  locked=parts[lo]['shape'].val().translate((0,0,dz)).intersect(parts[hi]['shape'].val()).Volume()
  if locked<.05:raise ValueError(f'{slug}: no positive axial retention at {label}')
  retention.append(dict(joint=label,attempted_separation_mm=abs(dz),blocked_overlap_mm3=round(locked,6)))
 export_design(slug,name,'Originals',description,parts,[
 'R2 digital PETG prototype. Four physical parts, four or fewer colors. Exterior relief is 0.8–1.0 mm; all decorative lines at least 1.6 mm wide.',
 'Single integral 10 mm-ID top hanger carries assembled rigid feeder through positive snap joints. Use one external suspension line only. No ropes retain components.',
 'Structural joints: three accessible 1.6 mm-thick cantilever beams, 22 mm overall length (19 mm free), 0.7 mm undercut, 0.30 mm nominal clearance. Physically fit-test PETG coupon and proof-load before hanging.',
 'Printed mesh basket is removable; no clear plastic or purchased reservoir. Use whole sunflower seed, shallow fill; very fine seed can escape mesh.',
 'Drain holes 2.2 mm. Open portals permit brushing; detach crown and basin to clean. Do not glue snap joints.',
 ],['Press mesh basket into basin socket until its two detents click.','Align the three lower shelter receivers over basin hooks; press evenly until every catch is visible through its window.','Press hanging crown onto upper shelter hooks; verify three visible catches. Hang the rigid assembly only by the integral top eye.','For refill lower feeder and release crown hooks through external windows. For cleaning release basin hooks and squeeze basket detents inward.'], 'image(6).png', hanger=[0,0,roof.val().BoundingBox().zmax-10], refill='Release three accessible crown catches after lowering feeder; lift crown and refill mesh cup. Large portals permit shallow tray filling.', snap_joints=[{'name':'Basin to shelter','parts':['Drained sculpted basin','Architectural shelter'],'description':'Three external cantilever hooks retained in window receivers','beam_length_mm':19,'overall_beam_length_mm':22,'beam_thickness_mm':1.6,'deflection_mm':0.8,'clearance_mm':0.3,'release':'Press exposed hook noses inward through three windows.'},{'name':'Shelter to hanging crown','parts':['Architectural shelter','Hanging service crown'],'description':'Three positive undercut snap catches','beam_length_mm':19,'overall_beam_length_mm':22,'beam_thickness_mm':1.6,'deflection_mm':0.8,'clearance_mm':0.3,'release':'Depress hooks via exterior windows and lift crown.'},{'name':'Mesh cup service detents','parts':['Drained sculpted basin','Printed mesh seed basket'],'description':'Two elastic outward detents latch inside basin sockets','beam_length_mm':13,'beam_thickness_mm':1.6,'deflection_mm':0.7,'clearance_mm':0.3,'release':'Squeeze exposed cup tabs inward and lift.'}],validation={'interpart_intersections':paircheck,'interference_free':True,'axial_retention_tests':retention}, detail_features=['Raised 1.8 mm-wide decorative relief','Integrated printed mesh, no clear plastic','Sculpted shell and drained basin'])

def portal_moulding(body,ps,outer,inner,angles,n=None):
 skin=shell([(z,r+1.15) for z,r in ps],4.4,n)
 rim=outer.cut(inner)
 for a in angles:body=body.union(skin.intersect(rot(rim,a)))
 return body

def lantern():
 r=61; z=21; top=148
 b=base(r,GREEN)
 body=shell([(21.3,r),(148,r)],3,6)
 body=arch(body,6,34,29,108,offset=30)
 body=body.union(ring(r,r-5,19,129)).union(ring(r,r-5,10,21.3))
 # Engaged arch jambs and diamonds form sculpted facade, no independent trim.
 for a in range(0,360,60):
  col=box(5,8,107,0,-53,28)
  body=body.union(rot(col,a))
  for zz in [37,121]:body=body.union(rot(box(7,10,3,0,-53,zz),a))
 roof=shell([(148.3,61),(158.5,80),(164,73),(183,40),(187,44),(193,28),(199,20),(205,12)],3,6)
 roof=roof.union(cyl(12,3,203)).union(eye(205))
 # Actual layered roof shingles, six tiers + radial seam battens.
 for zz,rr in [(161,77),(166,69),(171,60),(176,51),(181,43)]:
  roof=roof.union(shell([(zz,rr+1),(zz+1.2,rr-1.1)],2.8,6))
 for a in range(0,360,60):
  roof=roof.union(rot(rod((0,-73,163),(0,-40,183),1.1),a+30))
 # Staggered shingle joints are engraved into the sloping hexagonal roof.
 shingle_skin=shell([(148.3,61.4),(158.5,80.4),(164,73.4),(183,40.4)],1.05,6)
 for zz,rr in [(166,69),(171,60),(176,51)]:
  for a in range(0,360,30):
   cutter=rot(box(1.4,18,3.6,0,-rr+3,zz),a+(15 if zz==171 else 0))
   roof=roof.cut(cutter.intersect(shingle_skin))
 b,body=joint(b,body,r,21)
 body,roof=joint(body,roof,r,148)
 publish('lantern-pavilion','Lantern Pavilion',b,body,roof,[GREEN,CREAM,GREEN,ORANGE],'Six sculpted pointed arches, stepped hexagonal pagoda with raised overlapping shingle courses, integrated single hanger and printed seed mesh.')

def radius(ps,z):
 for (a,r),(b,s) in zip(ps,ps[1:]):
  if a<=z<=b:return r+(s-r)*(z-a)/(b-a)
 return ps[-1][1]
def petal_relief(s,ps,angles):
 for a in angles:
  path=[]
  for z in [27]+[z for z,r in ps if 27<z<153]+[153]:
   r=radius(ps,z)+.1;t=math.radians(a+(z-21)*.13)
   path.append((r*math.cos(t),r*math.sin(t),z))
  for x,y in zip(path,path[1:]):s=s.union(rod(x,y,.95))
  for z0 in (40,66,92,118):
   for sign in (-1,1):
    path=[]
    for k in (0,2,4,5):
     z=z0+k*4;r=radius(ps,z)+.05;t=math.radians(a+(z-21)*.13+sign*k*4)
     path.append((r*math.cos(t),r*math.sin(t),z))
    for x,y in zip(path,path[1:]):s=s.union(rod(x,y,.85))
 return s

def pod():
 ps=[(21.3,54),(30,60),(44,66),(62,70),(82,69),(103,64),(124,55),(145,43),(160,31)]
 b=base(54,PURPLE);body=shell(ps,3)
 # Distinct oval portals cut through front/back and side, with printed violet lip.
 cuts=[]
 for a in (0,120,240):
  cut=cq.Workplane('XZ').center(0,82).ellipse(25,48).extrude(100)
  body=body.cut(rot(cut,a));cuts.append(rot(cut,a))
 body=portal_moulding(body,ps,cq.Workplane('XZ').center(0,82).ellipse(29,52).extrude(100),cq.Workplane('XZ').center(0,82).ellipse(25,48).extrude(101),(0,120,240))
 body=body.union(ring(54,49,10,21.3)).union(ring(31,26,19,141))
 # Integral meridian relief cut from a concentric loft: no detached seam beads.
 ridge=shell([(z,r+.8) for z,r in ps],3.5)
 for a in (60,180,300):
  body=body.union(ridge.intersect(rot(box(2,100,140,0,-50,21),a)))
 roof=shell([(160.3,31),(170,25),(181,17),(192,8)],3).union(cyl(8,3,190)).union(eye(193))
 b,body=joint(b,body,54,21,angles=(60,180,300));body,roof=joint(body,roof,31,160,angles=(60,180,300))
 publish('modern-pod','Modern Pod',b,body,roof,[PURPLE,CREAM,PURPLE,PURPLE],'Sculpted ovoid pod with three deep oval feeding portals, longitudinal embossed seams and contrasting purple cup and hanging crown.')

def ribbon(ps,start,width,turn=240,segments=12):
 w=cq.Workplane('XY').workplane(offset=ps[0][0])
 for i,(z,r) in enumerate(ps):
  if i:w=w.workplane(offset=z-ps[i-1][0])
  a=start+turn*(z-ps[0][0])/(ps[-1][0]-ps[0][0])
  q=[]
  for j in range(segments+1):
   t=math.radians(a+width*j/segments);q.append((r*math.cos(t),r*math.sin(t)))
  for j in reversed(range(segments+1)):
   t=math.radians(a+width*j/segments);q.append(((r-3.5)*math.cos(t),(r-3.5)*math.sin(t)))
  w=w.polyline(q).close()
 return w.loft(ruled=True)
def spiral():
 ps=[(21.3,59),(35,67),(55,71),(78,70),(100,63),(124,50),(146,33),(158,25)]
 b=base(59,CREAM)
 body=ring(59,54,10,21.3).union(ring(25,20,19,139))
 for start in (0,180):body=body.union(ribbon(ps,start,124,245))
 # Raised 4-degree-wide flutes follow the same ruled loft sections exactly.
 for start in (0,180):
  for delta in (13,34,55,76,97):
   body=body.union(ribbon([(z,r+.8) for z,r in ps],start+delta,4,245,segments=1))
 # Short local lofts follow the actual ruled-section radius and phase.
 # This avoids whole-height ribbon/slab booleans and keeps each ridge fused.
 def phase(z):
  for (za,ra),(zb,rb) in zip(ps,ps[1:]):
   if za<=z<=zb:
    t=(z-za)/(zb-za);span=ps[-1][0]-ps[0][0]
    aa=math.radians(245*(za-ps[0][0])/span);ab=math.radians(245*(zb-ps[0][0])/span)
    x=(1-t)*ra*math.cos(aa)+t*rb*math.cos(ab)
    y=(1-t)*ra*math.sin(aa)+t*rb*math.sin(ab)
    return math.hypot(x,y),math.degrees(math.atan2(y,x))
 for start in (0,180):
  for zz in (43,65,90,116):
   dz=1.35;ra,aa=phase(zz);rb,ab=phase(zz+dz)
   turn=(ab-aa)%360
   body=body.union(ribbon([(zz,ra+.9),(zz+dz,rb+.9)],start+aa,124,turn))
 roof=shell([(158.3,25),(169,20),(181,13),(190,7)],3).union(cyl(7,3,188)).union(eye(191))
 b,body=joint(b,body,59,21,angles=(60,180,300));body,roof=joint(body,roof,25,158,angles=(60,180,300))
 publish('spiral-shell','Spiral Shell',b,body,roof,[CREAM,BLUE,RED,RED],'Two broad intertwined helical shelter ribbons with five raised helical flutes per ribbon, red hanging tip and cream basin.')

def deco():
 r=47;b=base(r,ORANGE)
 body=shell([(21.3,r),(160,r)],3,8)
 body=arch(body,8,18,29,116,offset=22.5)
 body=body.union(ring(r,r-5,10,21.3)).union(ring(r,r-5,19,141))
 for a in range(0,360,45):
  body=body.union(rot(box(4,8,137,0,-43.5,22),a))
  for d in (-4,4):body=body.union(rot(box(1.6,3,105,d,-44,26),a))
 roof=shell([(160.3,47),(171,47),(179,38),(188,38),(194,29),(204,29),(211,18),(220,10)],3,8)
 roof=roof.union(cyl(10,3,218)).union(eye(222))
 for a in range(0,360,45):
  for zz,rr,hh in [(169,44,12),(185,35,12),(201,25,12)]:roof=roof.union(rot(box(2.2,4,hh,0,-rr,zz),a))
 # Sunburst engraving across each crown tier, shallow enough to preserve shell.
 for a in range(0,360,45):
  for zz,rr in [(172,45),(189,36),(205,27)]:
   for dx in (-5,0,5):
    roof=roof.cut(rot(rod((dx,-rr,zz),(dx*.4,-rr+5,zz+5),.65),a))
 b,body=joint(b,body,r,21,angles=(0,135,270));body,roof=joint(body,roof,r,160,angles=(0,135,270))
 publish('art-deco-tower','Art-Deco Tower',b,body,roof,[ORANGE,CREAM,ORANGE,TEAL],'Eight pointed bays with triple fluted pilasters and a stepped, ribbed skyscraper crown; no clear panels required.')

def leaf():
 ps=[(21.3,55),(36,64),(57,71),(79,70),(103,61),(126,47),(148,31),(160,23)]
 b=base(55,GREEN);body=shell(ps,3.2)
 body=arch(body,1,67,27,116)
 body=body.union(ring(55,50,10,21.3)).union(ring(23,18,19,141))
 # Fine secondary leaf venation is shallow physical carving, bounded to skin.
 skin=shell([(z,r+.2) for z,r in ps],.9)
 for zz in (44,53,63,74,86,99,112,125,137):
  body=body.cut(skin.intersect(box(180,180,.85,0,0,zz)))
 # Branching veins across three overlapping leaf-like lobes, rear and shoulders.
 body=petal_relief(body,ps,[20,95,165,225,315])
 body=arch(body,1,67,27,116) # no loose veins crossing feeding aperture
 roof=shell([(160.3,23),(172,18),(193,6)],3).union(cyl(6,3,191)).union(eye(194))
 for a in range(0,360,60):roof=roof.union(rot(rod((0,-22.7,161),(0,-9.8,186),.9),a))
 b,body=joint(b,body,55,21,angles=(20,140,260));body,roof=joint(body,roof,23,160,angles=(20,140,260))
 publish('leaf-cocoon','Leaf Cocoon',b,body,roof,[GREEN,GREEN,GREEN,ORANGE],'Tapered leaf cocoon with actual raised branching veins, deep pointed feeding portal, warm orange printed seed mesh and sculpted cupped basin.')

def orbit():
 ps=[(21.3,58),(45,77),(92,80),(125,64),(151,35)]
 b=base(58,ORANGE);body=shell(ps,4,6)
 portal=cq.Workplane('XZ').polyline([(-24,43),(24,43),(34,77),(21,114),(-21,114),(-34,77)]).close().extrude(110)
 for a in range(0,360,60):body=body.cut(rot(portal,a))
 border=cq.Workplane('XZ').polyline([(-28,39),(28,39),(38,77),(25,118),(-25,118),(-38,77)]).close().extrude(110)
 body=portal_moulding(body,ps,border,portal,range(0,360,60),6)
 body=body.union(ring(58,53,10,21.3)).union(ring(35,30,19,132))
 # Radial edges join vertices and give a geometric segmented exoskeleton.
 for k in range(6):
  aa=math.radians(k*60)
  path=[(r*math.cos(aa),r*math.sin(aa),z) for z,r in ps]
  for x,y in zip(path,path[1:]):body=body.union(rod(x,y,2.5))
 body=body.intersect(box(220,220,151,0,0,0)) # flush rib tips below crown receiver
 roof=shell([(151.3,35),(164,29),(177,18),(185,9)],3,6).union(cyl(9,3,183)).union(eye(187))
 b,body=joint(b,body,58,21,angles=(0,120,240));body,roof=joint(body,roof,35,151,angles=(0,120,240))
 publish('geometric-orbit','Geometric Orbit',b,body,roof,[ORANGE,CREAM,BLUE,TEAL],'Angular orbit lantern with six polygonal windows and raised crystal edges, contrasting blue crown and orange lower facet cup.')

if __name__=='__main__':
 fns={'lantern-pavilion':lantern,'modern-pod':pod,'spiral-shell':spiral,'art-deco-tower':deco,'leaf-cocoon':leaf,'geometric-orbit':orbit}
 for s,f in fns.items():
  if len(sys.argv)==1 or s in sys.argv[1:]:print('BUILD',s,flush=True);f()
