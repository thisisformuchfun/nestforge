"""R2 Future habitats. Five serviceable, positively latched printed components.
Millimetres, Z-up; all accents are welded material regions of their parent piece.
"""
from pathlib import Path
import sys,math,json
import cadquery as cq
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
WHITE='#E8E5D9'; SILVER='#AEB7BF'; DARK='#303A40'; ORANGE='#F58224'; OLIVE='#53644A'
def C(r,h,z=0,x=0,y=0):return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))
def B(x,y,h,px=0,py=0,z=0):return cq.Workplane('XY').box(x,y,h,centered=(True,True,False)).translate((px,py,z))
def R(ro,ri,h,z=0):return cq.Workplane('XY').circle(ro).circle(ri).extrude(h).translate((0,0,z))
def K(r1,r2,h,z=0):return cq.Workplane('XY').add(cq.Solid.makeCone(r1,r2,h)).translate((0,0,z))
def rot(s,a):return s.rotate((0,0,0),(0,0,1),a)
def J(items):
 s=items[0]
 for p in items[1:]:s=s.union(p,clean=False)
 return s.clean()
def cut(s,items):return s.cut(cq.Compound.makeCompound([p.val() for p in items])) if items else s

def receiver(r,z):
 s=R(r+3.65,r+.35,14,z)
 return cut(s,[rot(B(8,10,3.8,r+1,0,z+3.5),a) for a in (0,90,180,270)])
def hooks(r,z):
 # 18 mm downward cantilever, 2 mm radial beam, 1.05 mm retaining overlap.
 # Flat upper retaining face; tapered insertion face below. Receiver is external.
 items=[]
 for a in (0,90,180,270):
  beam=B(2,7,18,r-1,0,z)
  barb=cq.Workplane('XZ').polyline([(r-.1,z+3.8),(r+1.4,z+5.0),(r+1.4,z+6.6),(r-.1,z+6.6)]).close().extrude(3.5,both=True)
  items.extend([rot(beam,a),rot(barb,a)])
 return items

def tray():
 t=J([C(72,4),R(70,66.8,10,4),receiver(58,4),receiver(28,4)])
 t=cut(t,[C(1.3,6,-1,r*math.cos(a),r*math.sin(a)) for r,n in [(0,1),(15,8),(39,18),(64,28)] for a in [2*math.pi*i/n for i in range(n)]])
 # Recessed finger channels make the four structural catches reachable.
 t=cut(t,[rot(B(12,10,6,61,0,3.5),a) for a in (0,90,180,270)])
 # Keep receiver windows at z7.5-11.3; channel cutting above opens release access.
 return t

def hopper(top):
 h=R(26,23.6,top-18,18)
 holes=[]
 for row in range(int((top-40)/14)):
  for a in range(0,360,10):holes.append(rot(B(7,1.6,12,25,0,29+row*14),a))
 h=cut(h,holes)
 h=cut(h,[rot(B(8,10,7,25,0,18),a+45) for a in (0,90,180,270)])
 # Remove four line-only contacts between beam inner faces and cylinder.
 h=cut(h,[rot(B(1.2,7.4,3.2,26,0,17.9),a) for a in (0,90,180,270)])
 h=J([h,R(28,24,3,21)]+hooks(28,4))
 return h

def roof_sockets(z):
 # Two non-pivoting rectangular receivers, keyed by 8.7 mm square pockets.
 sockets=[]
 for a in [0,180]:
  r=B(12,12,38,30,0,z-16).cut(B(8.7,8.7,23,30,0,z))
  r=r.cut(B(4,10,4.3,35.2,0,z+4))
  sockets.append(rot(r,a))
 return J(sockets)

def yoke(z,arch_height):
 # Uniform 8 mm extrusion prints flat. Guide rails resist pivot independently
 # of outward flex fingers. Centered eye is outside the cap removal corridor.
 pieces=[B(68,8,8,0,0,z+arch_height)]
 for a in [0,180]:
  guide=B(4,8,22,28,0,z+.35)
  flex=B(1.4,8,22,33.3,0,z+.35)
  shoulder=cq.Workplane('XZ').polyline([(33.8,z+3.5),(35.4,z+6),(35.4,z+7.6),(33.8,z+7.6)]).close().extrude(4,both=True)
  upper=B(8,8,arch_height-22+8,30,0,z+22)
  pieces += [rot(v,a) for v in [guide,flex,shoulder,upper]]
 eye=cq.Workplane('XZ').center(0,z+arch_height+15).circle(9).circle(4.5).extrude(4,both=True)
 pieces.append(eye)
 return J(pieces)

def roof(ro,rt,z,h,facets=0):
 if facets:
  def loft(r1,r2,hh,zz):return cq.Workplane('XY').workplane(offset=zz).polygon(facets,r1*2).workplane(offset=hh).polygon(facets,r2*2).loft(ruled=True)
  s=loft(ro,rt,h,z).cut(loft(ro-3.5,rt-3.5,h-.1,z-.1))
 else:s=K(ro,rt,h,z).cut(K(ro-3.5,rt-3.5,h-.1,z-.1))
 # Crown annulus closes the roof but leaves a 28 mm refill throat.
 s=s.union(R(ro,28,3,z)).union(R(rt,14.35,3,z+h-3)).cut(C(14.35,10,z+h-5))
 # Paired sockets support a separate centered, non-pivoting suspension yoke.
 s=s.union(roof_sockets(z+h))
 # Two accessible upper snap receiver slots, separate from four body snaps.
 neck=R(18,14.35,16,z+h)
 neck=cut(neck,[rot(B(8,8,3.8,16,0,z+h+2),a) for a in (0,180)])
 return s.union(neck)

def hatch(z):
 s=C(19.5,3,z+16).union(R(20.5,17.5,2,z+19)).union(B(27,6,5,0,0,z+19))
 for a in [0,180]:
  beam=B(1.4,6,17,13.1,0,z-.5)
  barb=cq.Workplane('XZ').polyline([(13.8,z+2.3),(15.4,z+3.2),(15.4,z+5),(13.8,z+5)]).close().extrude(3,both=True)
  s=s.union(rot(beam,a)).union(rot(barb,a))
 return s

def strut(r1,r2,z1,z2,w=7):
 return cq.Workplane('XZ').polyline([(r1-w/2,z1),(r1+w/2,z1),(r2+w/2,z2),(r2-w/2,z2)]).close().extrude(w/2,both=True)

def thermal_courses(s,ro,rt,z,h,facets=0,levels=(.3,.6)):
 # True 1.25 mm wide, 0.7 mm radial-deep courses: legible with a 0.4 mm nozzle.
 # The grooves follow the actual conical or faceted skin and leave >2.7 mm wall.
 def form(r1,r2,hh,zz):
  if not facets:return K(r1,r2,hh,zz)
  return cq.Workplane('XY').workplane(offset=zz).polygon(facets,2*r1).workplane(offset=hh).polygon(facets,2*r2).loft(ruled=True)
 for fraction in levels:
  zz=z+h*fraction; r=ro+(rt-ro)*fraction; rr=r+(rt-ro)*1.25/h
  groove=form(r+.4,rr+.4,1.25,zz).cut(form(r-.7,rr-.7,1.45,zz-.1))
  s=s.cut(groove)
 return s

def panel_outline(radius,z,w=16,h=20,a=0):
 # Rounded, shallow hatch perimeter projected into a cylindrical fairing.
 outer=cq.Workplane('XZ').sketch().rect(w,h).vertices().fillet(3).finalize().extrude(1.2,both=True)
 inner=cq.Workplane('XZ').sketch().rect(w-2.8,h-2.8).vertices().fillet(1.6).finalize().extrude(2,both=True)
 return rot(outer.cut(inner).translate((0,-radius+.3,z)),a)

def build(kind):
 zroof={'starship':168,'orbit':140,'cyber':137,'drone':143,'sentry':160,'moonbase':168,'capsule':142}[kind]
 shell=J([R(60,54,6,18)]+hooks(58,4))
 accents=[];features=['Four external cantilever catches with through release windows','Printed 1.6 mm seed mesh with 2.4 mm radial walls','Integrated 2.6 mm through-drains','Independent refill hatch with two positive catches']
 if kind=='starship':
  shell=J([shell,R(36,31,6,zroof-6)]+[rot(strut(55,34,22,zroof,6),a) for a in [45,135,225,315]])
  # Three broad, swept aerodynamic fins and a cylindrical stage belt.
  fins=[]
  for a in [30,150,270]:
   f=cq.Workplane('XZ').polyline([(33,32),(70,18),(67,58),(34,105)]).close().extrude(3,both=True)
   fins.append(rot(f,a))
  shell=J([shell]+fins+[R(38,31,5,115),R(37,31,4,152),roof(38,21,zroof,49)])
  for z in [119,155]:accents.append(R(38.8,35,1.4,z))
  for a in [45,135,225,315]:accents.append(rot(B(2,4,36,35,0,126),a))
  # Real longitudinal panel seams cut 0.9 mm into the sloping nose skin.
  seams=[]
  for a in range(0,360,45):
   seam=cq.Workplane('XZ').polyline([(38.2,170),(36.5,170),(20.9,215),(22.2,215)]).close().extrude(.65,both=True)
   seams.append(rot(seam,a))
  shell=cut(shell,seams)
  # Raised triangular stiffener ribs on both broad faces of each swept fin.
  for a in [30,150,270]:
   for sy in [-1,1]:
    rib=cq.Workplane('XZ').polyline([(40,39),(62,30),(59,54),(57.5,54),(60,33),(40,41)]).close().extrude(1.1).translate((0,sy*3,0))
    # Workplane XZ extrudes toward negative Y; mirror the offset for the far face.
    if sy>0:rib=rib.translate((0,1.1,0))
    accents.append(rot(rib,a))
  features+=['Three swept structural rocket fins' ,'Two staged hull bands and four recessed-look vertical ducts'];top=zroof+49
 elif kind=='orbit':
  # Spherical orbital shell with four generous circular feeding windows.
  orb=cq.Workplane('XY').sphere(77).translate((0,0,88)).cut(cq.Workplane('XY').sphere(72.8).translate((0,0,88)))
  orb=orb.intersect(B(170,170,114,z=26))
  orb=cut(orb,[cq.Workplane('XZ').center(0,82).circle(47).extrude(100,both=True),cq.Workplane('YZ').center(0,82).circle(39).extrude(100,both=True)])
  shell=J([shell,orb,R(57,48,5,136),roof(58,28,140,26)]+[rot(strut(55,44,22,35,7),a) for a in [45,135,225,315]])
  # Equatorial ring is connected at four remaining spherical piers.
  accents=[R(78.2,73.5,4,87),R(58.5,53,2,140)]
  features+=['True hollow spherical pod','Four large circular windows and orbital equator'];top=166
 elif kind=='cyber':
  shell=J([shell,R(56,49,5,132)]+[rot(B(7,7,115,53,0,22),a) for a in range(0,360,60)]+[roof(81,28,137,39,8)])
  accents=[R(62,53,3,24),R(62,50,3,130),R(79,69,2,137)]
  for a in range(0,360,45):
   rib=cq.Workplane('XZ').polyline([(28,176),(30,177),(80,139),(79,137)]).close().extrude(1.2,both=True);shell=shell.union(rot(rib,a))
  features+=['Octagonal pagoda weather roof with raised ribs','Six tall cage mullions and stepped lantern decks'];top=176
 elif kind=='drone':
  shell=J([shell,R(50,40,6,139)]+[rot(strut(53,37,23,143,8),a) for a in [45,135,225,315]]+[roof(53,28,143,15,8)])
  # Four diagonal cantilever arms carry real ducted rotor housings, all welded.
  for a in [45,135,225,315]:
   arm=rot(B(52,13,8,65,0,139),a);motor=rot(R(18,11,11,136).translate((87,0,0)),a)
   shell=J([shell,arm,motor])
   # Rotor crossbars are printable protective grilles, not loose propellers.
   shell=shell.union(rot(B(33,3,3,87,0,145),a)).union(rot(B(3,33,3,87,0,145),a))
  accents=[R(54,47,3,145)]
  for a in [45,135,225,315]:accents.append(rot(R(18.8,16,2,146).translate((87,0,0)),a))
  features+=['Four swept load-bearing robotic legs','Four projecting ducted rotor guards and integral grilles'];top=158
 elif kind=='sentry':
  shell=J([shell,R(52,44,5,124)]+[rot(B(8,8,108,50,0,22),a) for a in [45,135,225,315]])
  # Camera head above seed tube: bulky fairing, recessed circular optical face.
  head=R(42,36,34,126).union(R(45,34,5,154))
  lens=cq.Workplane('XZ').center(0,142).circle(16).circle(9).extrude(6,both=True).translate((0,-39,0))
  head=head.union(lens)
  shell=J([shell,head,roof(72,28,160,29,8)])
  accents=[lens, R(54,47,3,26),R(53,45,3,122)]
  # Three true slotted vents each side of camera fairing.
  shell=cut(shell,[rot(B(7,3,13,41,0,135),a) for a in [55,65,75,105,115,125,235,245,255,285,295,305]])
  features+=['Oversized camera head with deep concentric optical recess','Twelve ventilation slots and polygon sun hood'];top=189
 elif kind=='moonbase':
  hull=R(53,48.5,146,22)
  openings=[]
  for a in [0,90,180,270]:
   # Lower capsule doors have square sill and circular upper arch.
   opening=J([B(33,18,49,0,-51,26),cq.Workplane('XZ').center(0,75).circle(16.5).extrude(10,both=True).translate((0,-51,0))])
   openings.append(rot(opening,a))
   openings.append(rot(cq.Workplane('XZ').center(0,124).circle(11).extrude(12,both=True).translate((0,-51,0)),a))
  hull=cut(hull,openings)
  shell=J([shell,hull,R(56,48,4,22),R(56,48,4,98),R(56,48,4,156),roof(59,28,168,24,8)])
  accents=[R(56.8,52,1.6,100),R(56.8,52,1.6,158)]
  for a in [0,90,180,270]:
   rim=cq.Workplane('XZ').center(0,124).circle(13.5).circle(11).extrude(3,both=True).translate((0,-51,0));accents.append(rot(rim,a))
  # Robust antenna mast is connected along rear upper hull and roof.
  shell=J([shell,C(3.5,39,167,0,48),C(6,3,204,0,48),B(23,4,3,0,48,206)])
  features+=['Four arched lower portals and four raised porthole rims','Two lunar deck bands and a rear communications antenna'];top=192
 else:
  shell=J([shell,R(58,48,5,137)]+[rot(strut(55,52,22,142,8),a) for a in [45,135,225,315]]+[roof(85,28,142,57,8)])
  # Eight broad raised roof panels, inclined with the spacecraft facets.
  for a in range(0,360,45):
   rib=cq.Workplane('XZ').polyline([(28,199),(30,199.8),(84,144),(83,142)]).close().extrude(1.5,both=True);shell=shell.union(rot(rib,a))
  shell=J([shell]+[rot(B(15,7,3,61.5,0,27),a) for a in [45,135,225,315]])
  accents=[R(70,64,3,27),R(81,74,2,144)]
  # Nonfunctional camera housing geometrically recognizable on forward face.
  pod=B(26,12,22,0,-56,161).cut(cq.Workplane('XZ').center(0,172).circle(8).extrude(12,both=True).translate((0,-60,0)))
  shell=shell.union(pod);accents.append(pod)
  features+=['Broad eight-facet conical spacecraft roof','Raised thermal panel seams and forward recessed camera pod'];top=199
 # Family-specific physical surface work. All cuts stay clear of functional catches.
 if kind=='starship':
  shell=thermal_courses(shell,38,21,168,49,levels=(.23,.51,.78))
  # Recessed exhaust channels on each integrated fin create nozzle-like fluting.
  for a in [30,150,270]:
   for zz in [42,47,52]:
    shell=shell.cut(rot(B(11,1.0,1.4,56,-2.8,zz),a))
  features+=['Three recessed nose thermal courses and nine fin exhaust flutes; 0.7 mm skin relief']
 elif kind=='orbit':
  # Latitudinal ceramic tile joints follow the true sphere, not added rings.
  for zz in [39,47,122,130]:
   tool=cq.Workplane('XY').sphere(77.4).translate((0,0,88)).cut(cq.Workplane('XY').sphere(76.2).translate((0,0,88)))
   shell=shell.cut(tool.intersect(B(164,164,1.4,z=zz)))
  shell=thermal_courses(shell,58,28,140,26,levels=(.3,.65))
  features+=['Four spherical recessed tile courses and two crown service seams']
 elif kind=='cyber':
  shell=thermal_courses(shell,81,28,137,39,8,levels=(.22,.43,.64,.82))
  # Repeated inset channels turn each thick mullion into a ribbed extrusion.
  shell=cut(shell,[rot(B(1.0,3,78,56.2,0,40),a) for a in range(0,360,60)])
  features+=['Four octagonal recessed roof courses and six deep-set mullion channels']
 elif kind=='drone':
  shell=thermal_courses(shell,53,28,143,15,8,levels=(.4,))
  for a in [45,135,225,315]:
   # Rounded nacelle belt and printable vertical cooling grooves in duct walls.
   ductcuts=[rot(B(1.4,1.4,6,17.7,0,138),b).translate((87,0,0)) for b in range(0,360,30)]
   shell=cut(shell,[rot(v,a) for v in ductcuts])
   shell=shell.cut(rot(B(23,4,1.2,68,0,146),a))
  features+=['Forty-eight recessed nacelle cooling flutes and four recessed arm channels']
 elif kind=='sentry':
  shell=thermal_courses(shell,72,28,160,29,8,levels=(.27,.56,.8))
  shell=shell.cut(panel_outline(42,141,18,21,180))
  # Concentric stepped optical bore, machined into the welded printed bezel.
  optical=cq.Workplane('XZ').center(0,142).circle(13.6).circle(11.6).extrude(.9,both=True).translate((0,-44.4,0))
  shell=shell.cut(optical)
  accents[0]=accents[0].cut(optical)
  features+=['Rounded rear service-hatch outline, concentric lens groove and three hood courses']
 elif kind=='moonbase':
  shell=thermal_courses(shell,59,28,168,24,8,levels=(.35,.7))
  shell=cut(shell,[panel_outline(53,124,17,28,a) for a in [45,135,225,315]])
  shell=cut(shell,[R(53.4,52.2,1.3,z) for z in [107,144,150]])
  # Coarse paired flutes between lower portals read as insulated habitat piers.
  shell=cut(shell,[rot(B(1.2,1.4,48,52.7,0,39),a+d) for a in [45,135,225,315] for d in [-5,0,5]])
  features+=['Four rounded service hatch outlines, twelve pier flutes and circumferential insulation seams']
 else:
  shell=thermal_courses(shell,85,28,142,57,8,levels=(.18,.34,.50,.66,.82))
  # Coarse rectangular recessed tile grid in the outer portion of each facet.
  for a in range(0,360,45):
   seam=cq.Workplane('XZ').polyline([(74.0,149),(72.75,149),(41.7,182),(42.9,182)]).close().extrude(.6,both=True)
   shell=shell.cut(rot(seam,a+11.25))
  features+=['Five recessed thermal tile courses and eight offset radial tile seams']
 # Weld accent detail to parent; clip assigns materials without loose ornaments.
 shell=J([shell]+accents)
 # Re-cut keyed pockets after ornamental roof ribs so no detail fills a socket.
 shell=cut(shell,[rot(B(8.7,8.7,23,30,0,top),a) for a in [0,180]])
 pnames=['Drain deck','Mesh seed cartridge','Structural habitat shell','Snap refill cap','Centered suspension yoke']
 cap=hatch(top)
 if kind=='starship':cap=cap.union(K(19.5,3,26,top+19))
 parts=[dict(name=pnames[0],shape=tray(),color=WHITE,explode=[0,0,-35]),dict(name=pnames[1],shape=hopper(zroof-2),color=DARK,explode=[0,0,40],support='Localized supports under lower collar spans between latch feet; keep mesh slots and flex beams clear.'),dict(name=pnames[2],shape=shell,color=OLIVE if kind=='sentry' else SILVER if kind in ['starship','cyber'] else WHITE,explode=[0,0,90],regions=[dict(name='Welded accent details',shape=J(accents[:2] if kind=='cyber' else accents[1:] if kind=='sentry' else accents),color=ORANGE)] if accents else [],support='Organic supports under roof eaves, snap shoulders and exposed bridging. Remove before use.'),dict(name=pnames[3],shape=cap,color=ORANGE,explode=[0,0,130],support='Small supports beneath cap disk between latch tabs; keep release barbs clear.')]
 if kind=='sentry':parts[2]['regions']=[dict(name='Printed optical face',shape=B(38,5,34,0,-42.5,125.5),color=DARK)]
 arch_height=72 if kind=='starship' else 50
 parts.append(dict(name=pnames[4],shape=yoke(top,arch_height),color=DARK,explode=[0,0,175],print_rotation=[90,0,0],support='Print flat on its 8 mm broad face; no supports required. Keep both flex slots clear.'))
 features.append('Rigid centered suspension yoke with two keyed positive snap sockets; unobstructed cap lift and sideways removal')
 return parts,top,features

DESIGNS={'starship':('starship-sentinel','Starship Sentinel'),'orbit':('orbit-pod','Orbit Pod'),'cyber':('cyber-lantern','Cyber Lantern'),'drone':('drone-nest','Drone Nest'),'sentry':('sentry-cam-feeder','Sentry Cam Feeder'),'moonbase':('moonbase-tower','Moonbase Tower'),'capsule':('sentinel-capsule','Sentinel Capsule')}
def run(kind):
 from common import export_design
 parts,top,features=build(kind)
 for p in parts:
  s=p['shape'].val(); print(kind,p['name'],'valid',s.isValid(),'solids',len(s.Solids()),flush=True)
  if not s.isValid() or len(s.Solids())!=1:raise RuntimeError('Invalid/disconnected '+kind+' '+p['name'])
  import trimesh,tempfile,numpy as np
  with tempfile.NamedTemporaryFile(suffix='.stl') as f:
   cq.exporters.export(s,f.name,tolerance=.1,angularTolerance=.12);m=trimesh.load(f.name,force='mesh')
   if not m.is_watertight or not m.is_winding_consistent or np.any(m.area_faces<1e-10):raise RuntimeError('STL topology failed '+kind+' '+p['name'])
   print('STL CLOSED',p['name'],len(m.faces),'faces',flush=True)
 for p in parts:
  if not p.get('regions'):continue
  remaining=p['shape'].val().clean();material_shapes=[]
  for r in p['regions']:
   material=r['shape'].val().intersect(remaining).clean();material_shapes.append(material);remaining=remaining.cut(material).clean()
  material_shapes.append(remaining)
  for i,material in enumerate(material_shapes):
   with tempfile.NamedTemporaryFile(suffix='.stl') as f:
    cq.exporters.export(material,f.name,tolerance=.1,angularTolerance=.12);m=trimesh.load(f.name,force='mesh')
    if not m.is_watertight or not m.is_winding_consistent or np.any(m.area_faces<1e-10):raise RuntimeError('Material topology failed '+kind+' '+p['name']+' region '+str(i))
  print('MATERIALS CLOSED',p['name'],flush=True)
 for i,p in enumerate(parts):
  for q in parts[i+1:]:
   bp=p['shape'].val().BoundingBox();bq=q['shape'].val().BoundingBox()
   disjoint=any(getattr(bp,a+'max') < getattr(bq,a+'min') or getattr(bq,a+'max') < getattr(bp,a+'min') for a in 'xyz')
   v=0 if disjoint else p['shape'].val().intersect(q['shape'].val()).Volume()
   print('INTERSECTION',p['name'],q['name'],round(v,6),flush=True)
   if v>.02:raise RuntimeError('Part collision '+str(v))
 # Clearance certificate: lift cap 17 mm, then withdraw along Y inside arch.
 cap=parts[3]['shape'].val();bow=parts[4]['shape'].val()
 for dy in [0,10,25,45,70]:
  moved=cap.translate((0,dy,17));v=moved.intersect(bow).Volume()
  if v>.02:raise RuntimeError('Refill path blocked by yoke '+str(v))
 slug,name=DESIGNS[kind]
 joints=[dict(name='Habitat to drain deck',parts=['Structural habitat shell','Drain deck'],description='Four downward 18 mm cantilevers engage through-windows; 1.05 mm retaining overlap.',beam_length_mm=11.4,beam_thickness_mm=2,deflection_mm=1.05,clearance_mm=.35,release='Press four exposed catches radially inward at lower deck windows while lifting shell.'),dict(name='Seed cartridge to drain deck',parts=['Mesh seed cartridge','Drain deck'],description='Four catches positively retain removable mesh cartridge.',beam_length_mm=11.4,beam_thickness_mm=2,deflection_mm=1.05,clearance_mm=.35,release='Remove shell then press cartridge catch windows inward.'),dict(name='Service cap to crown',parts=['Snap refill cap','Structural habitat shell'],description='Two opposing tabs hook crown slots; removable cap is outside the hanging load path.',beam_length_mm=11,beam_thickness_mm=1.4,deflection_mm=1.05,clearance_mm=.35,release='Press two crown windows inward, pull raised cross-grip.' )]
 joints.append(dict(name='Centered yoke to crown',parts=['Centered suspension yoke','Structural habitat shell'],description='Two 8 mm rectangular keys prevent pivot; outward barbs overlap socket walls by 1.05 mm.',beam_length_mm=14.4,beam_thickness_mm=1.4,deflection_mm=1.05,clearance_mm=.35,release='After unloading hanger, press two outer socket windows inward and lift yoke. Cap services without yoke removal.'))
 arch_height=72 if kind=='starship' else 50
 hanger_point=[0,0,top+arch_height+15]
 weighted=[(p['shape'].val().Volume()*.00127,p['shape'].val().Center()) for p in parts]
 dry_mass=sum(m for m,c in weighted)
 dry_com=[sum(m*getattr(c,axis) for m,c in weighted)/dry_mass for axis in ['x','y','z']]
 loaded_com=[dry_com[0]*dry_mass/(dry_mass+100),dry_com[1]*dry_mass/(dry_mass+100),(dry_com[2]*dry_mass+100*80)/(dry_mass+100)]
 tilt=lambda c:math.degrees(math.atan2(math.hypot(c[0],c[1]),hanger_point[2]-c[2]))
 assert tilt(dry_com)<=5 and tilt(loaded_com)<=5
 print('BALANCE',kind,'dry',tilt(dry_com),'100g_seed',tilt(loaded_com),flush=True)
 export_design(slug,name,'Future habitats','Reference-inspired '+name.lower()+' with modeled relief, printed seed mesh and a rigid positive-snap assembly.',parts,notes=['Five physical printed parts. Four or fewer filament colors. All colored relief is welded into parent components.','No camera electronics or solar hardware included; camera forms are printed aesthetic housings.','PETG recommended. Calibrate snap clearances before full printing. Digital geometry is not a physical load or weather test.'],assembly=['Snap mesh cartridge into deck.','Align four habitat legs; press habitat shell into deck until catches seat in exposed receiver windows.','Fill via crown opening; snap cap until both hooks engage.','Press both keyed yoke legs into crown sockets until both barbs engage. Hang one cord or chain from the centered yoke eye. No cord retains any assembly component.','For cleaning, remove from hanger, release four deck catches, then release cartridge catches.'],reference='image(20261008-183956).png' if kind=='capsule' else 'image(20261008-183943).png',hanger=hanger_point,snap_joints=joints,refill='Release two crown cap catches, lift cap 17 mm, then slide sideways through centered yoke opening. 28.7 mm fill throat; yoke stays attached. Remove shell and cartridge for complete wash access.',detail_features=features,balance_check={'assumed_solid_PETG_density_g_cm3':1.27,'dry_mass_g':dry_mass,'dry_center_of_mass_mm':dry_com,'dry_tilt_deg':tilt(dry_com),'loaded_seed_g':100,'seed_center_mm':[0,0,80],'loaded_center_of_mass_mm':loaded_com,'loaded_tilt_deg':tilt(loaded_com),'note':'Geometric balance estimate, not a hanging load rating or physical trial.'},refill_clearance={'cap_lift_mm':17,'sideways_test_positions_mm':[0,10,25,45,70],'yoke_intersection_mm3':0})
if __name__=='__main__':
 failures=[]
 for kind in (sys.argv[1:] or DESIGNS):
  print('BUILD',kind,flush=True)
  try:run(kind)
  except Exception:
   import traceback;traceback.print_exc();failures.append(kind)
 if failures:raise SystemExit('FAILED: '+', '.join(failures))
