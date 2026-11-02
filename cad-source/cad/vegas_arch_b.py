"""Original architectural interpretations; no external assets. Millimetres, Z up.
Decorations are integral to the supplied roof/body. ASA palette limited to four.
"""
import math
import cadquery as cq
STYLE_IDS=('luxor','flamingo','wynn','mirage','strat','circus_circus')
PALETTE={'cream':'#DFD3C3','tan':'#A79565','yellow':'#EEC000','black':'#191919','white':'#F0EEE9','darkgray':'#54585A','red':'#CE3533','blue':'#265A9B','green':'#49844A','pink':'#D83076'}
Z=135.2

def box(w,d,h,x=0,y=40,z=Z):
 return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).translate((x,y,z))
def cyl(r,h,x=0,y=40,z=Z):
 return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))
def cone(r1,r2,h,x=0,y=40,z=Z):
 return cq.Workplane('XY').add(cq.Solid.makeCone(r1,r2,h)).translate((x,y,z))
def join(parts):
 out=parts[0]
 for p in parts[1:]: out=out.union(p,clean=False)
 return out.clean()
def profile(points,y=40,depth=6):
 return cq.Workplane('XZ').polyline(points).close().extrude(depth/2,both=True).translate((0,y,0))
def curved(points,y=40,depth=6):
 # Sample the organic spline at 0.04 mm deflection for stable exact color booleans.
 edge=cq.Workplane('XZ').spline(points).val()
 samples=edge.sample(0.04)[0]
 return cq.Workplane('XZ').polyline([(v.x,v.z) for v in samples]).close().extrude(depth/2,both=True).translate((0,y,0))
def keepout():
 return join([cyl(8,110,x,y,132) for x in (-105.5,105.5) for y in (4,76)]+[box(18,24,110,0,88,132)])
def palm(x,y,h=42):
 # Swept, closed silhouettes have broad roots and joined curved leaf clusters.
 trunk=curved([(x-4,Z),(x-2,Z+h*.45),(x+3,Z+h),(x+9,Z+h),(x+5,Z+h*.45),(x+4,Z)],y,7)
 leaves=[]
 for s in (-1,1):
  for dy,dz in [(24,0),(20,9),(13,16)]:
   leaves.append(cq.Workplane('XZ').moveTo(x+5,Z+h-3).threePointArc((x+5+s*dy*.5,Z+h+dz+5),(x+5+s*dy,Z+h+dz-6)).threePointArc((x+5+s*dy*.5,Z+h+dz-1),(x+5,Z+h+3)).close().extrude(3.5,both=True).translate((0,y,0)))
 return join([trunk]+leaves)

def faceted_loft(rings):
 # Triangulate noncoplanar contour quads: every surface is truly planar.
 def face(vertices):return cq.Face.makeFromWires(cq.Wire.makePolygon(vertices,close=True))
 faces=[face(list(reversed(rings[0]))),face(rings[-1])]
 n=len(rings[0])
 for lower,upper in zip(rings,rings[1:]):
  for i in range(n):
   j=(i+1)%n
   faces.extend([face([lower[i],lower[j],upper[j]]),face([lower[i],upper[j],upper[i]])])
 return cq.Workplane('XY').add(cq.Solid.makeSolid(cq.Shell.makeShell(faces)))

def hotel_style(style,roof_base,body_base):
 if style not in STYLE_IDS: raise ValueError(style)
 roof_parts=[]; body_parts=[]; features=[]
 def r(name,shape,color): roof_parts.append({'name':name,'shape':shape,'color':PALETTE[color]})
 def b(name,shape,color): body_parts.append({'name':name,'shape':shape,'color':PALETTE[color]})
 if style=='luxor':
  name='Luxor — Desert Prism'; colors=['cream','black','tan','yellow']
  outer=cq.Workplane('XY').workplane(offset=Z).center(0,35).rect(166,86).workplane(offset=76).rect(5,5).loft(ruled=True)
  inner=cq.Workplane('XY').workplane(offset=Z-.1).center(0,35).rect(157,77).workplane(offset=70).rect(3,3).loft(ruled=True)
  r('hollow four-sided pyramid',outer.cut(inner),'black')
  r('gold apex',cq.Workplane('XY').workplane(offset=Z+70).center(0,35).rect(18,12).workplane(offset=6).rect(5,5).loft(ruled=True),'yellow')
  for x in (-70,70):
   b('sandstone portal',box(38,3.6,104,x,-1.4,24),'tan')
   # Repeated original geometric glyphs on solid front relief, not copied writing.
   glyph=[]
   for zz in range(34,119,17):
    glyph += [profile([(x-11,zz),(x-5,zz+9),(x+1,zz),(x-2,zz),(x-5,zz+5),(x-8,zz)],-3.6,3),box(6,3,3,x+9,-3.6,zz+4)]
   b('abstract triangular glyph relief',join(glyph),'yellow')
  features=['76 mm hollow pyramid with 4+ mm nominal wall and solid apex','Original geometric glyph relief on both seed towers','Pyramid slopes print without exterior support; enclosed cavity ceiling converges to a small apex']
 elif style=='flamingo':
  name='Flamingo — Tropical Curves'; colors=['cream','pink','green','black']
  # Continuous closed spline combines a planted pedestal, belly and S neck.
  bird=curved([(-20,Z),(-23,Z+13),(-39,Z+28),(-37,Z+45),(-21,Z+53),(-5,Z+46),(2,Z+55),(-4,Z+67),(-3,Z+79),(9,Z+85),(23,Z+80),(25,Z+71),(18,Z+68),(13,Z+74),(7,Z+74),(7,Z+67),(16,Z+54),(13,Z+40),(-4,Z+31),(-9,Z+14),(-10,Z)],29,10)
  r('continuous sculptural flamingo',bird,'pink')
  r('bold curved bill',curved([(19,Z+79),(29,Z+74),(24,Z+64),(18,Z+68),(22,Z+73)],29,10),'black')
  r('left palm',palm(-65,53,42),'green');r('right palm',palm(52,54,36),'green')
  for x in (-70,70):
   b('tropical vertical panel',box(35,3.2,104,x,-1.1,24),'pink')
   for zz in (40,66,92):
    b('sweeping leaf bas relief',curved([(x-13,zz),(x-3,zz+15),(x+12,zz+17),(x+2,zz+6),(x-13,zz+3)],-3,3),'green')
  features=['One continuous S-neck flamingo with 10 mm depth and broad planted foot','Integral swept palm leaves and curved tower relief','Supports required under bill, belly and downward palm fronds; use build-plate-only supports where accessible']
 elif style=='wynn':
  name='Wynn — Curved Desert Glass'; colors=['cream','tan','black','yellow']
  # Convex front and concave rear form a genuinely curved thin hotel slab.
  def slab(z,h,thick=7):
   return cq.Workplane('XY').moveTo(-81,20).threePointArc((0,3),(81,20)).lineTo(81,20+thick).threePointArc((0,3+thick),(-81,20+thick)).close().extrude(h).translate((0,0,z))
  r('curved bronze facade shell',slab(Z,70),'tan')
  for zz in range(143,203,8): r('horizontal dark glazing band',slab(zz,2.4,8.5),'black')
  r('crown cornice',slab(203,4,10),'yellow')
  for x in (-70,70):
   b('bronze tower panel',box(38,3,106,x,-1,23),'tan')
   b('horizontal mullions',join([box(38,3,2.4,x,-3,zz) for zz in range(30,126,10)]),'black')
  features=['Continuous doubly curved 7 mm wall facade with 2.4 mm horizontal glazing bands','Crown and bands project no more than 3 mm; no roof support normally needed','Bronze effect uses available tan ASA, not metallic material']
 elif style=='mirage':
  name='Mirage — Volcano Garden';colors=['cream','darkgray','red','green']
  # Irregular loft stations provide natural contours rather than a perfect cone.
  def ring(rx,ry,z,phase):
   pts=[(rx*(1+.08*math.sin(i*2.7/4+phase))*math.cos(i*math.pi/32),35+ry*(1+.08*math.sin(i*2.7/4+phase))*math.sin(i*math.pi/32)) for i in range(64)]
   return [cq.Vector(x,y,z) for x,y in pts]
  hill=faceted_loft([ring(63,39,Z,0),ring(49,30,Z+18,.4),ring(30,22,Z+43,.7),ring(18,15,Z+56,1)])
  hill=hill.cut(faceted_loft([ring(58,34,Z-.1,0),ring(44,25,Z+18,.4),ring(25,17,Z+43,.7),ring(13,10,Z+52,1)])).cut(cyl(11,16,0,35,Z+48))
  # Shallow engraved gullies along sloping flanks, remain below nominal 5 mm skin.
  cuts=[]
  for a in range(0,360,45):
   aa=math.radians(a);p1=cq.Vector(56*math.cos(aa),35+34*math.sin(aa),Z+4);p2=cq.Vector(18*math.cos(aa),35+14*math.sin(aa),Z+54);v=p2-p1
   cuts.append(cq.Workplane('XY').add(cq.Solid.makeCylinder(1.3,v.Length,p1,v.normalized())))
  for c in cuts: hill=hill.cut(c)
  r('contoured hollow volcano with gullies',hill,'darkgray')
  r('lava crater rim',cyl(18,3.5,0,35,Z+53).cut(cyl(11,5,0,35,Z+52.5)),'red')
  r('west palm',palm(-77,45,34),'green');r('east palm',palm(66,47,32),'green')
  for x in (-70,70):
   b('volcanic plinth',box(38,3.2,24,x,-1,23),'darkgray')
   b('garden relief',palm(x-6,-2,32).translate((0,0,-82)),'green')
  features=['Legacy Mirage-inspired hollow irregular volcano, open crater and engraved radial gullies','3.5 mm lava rim and integral palm silhouettes','Support needed beneath palm fronds and crater rim; internal hill surface slopes inward']
 elif style=='strat':
  name='Strat — Observation Crown';colors=['cream','white','darkgray','red']
  r('tapered hollow observation shaft',cone(17,11,56).cut(cone(12,7,56.5,z=Z-.1)),'white')
  r('flared observation bowl',cone(11,34,19,z=Z+55).cut(cone(7,29,19.2,z=Z+55.2)),'white')
  r('observation glazing',cyl(34,7,z=Z+73).cut(cyl(29,8,z=Z+72.5)),'darkgray')
  r('observation roof',cone(34,8,8,z=Z+79),'white')
  r('stout antenna finial',cone(5,2.4,8,z=Z+86),'red')
  for a in (0,120,240):
   brace=profile([(11,Z),(28,Z),(13,Z+55),(8,Z+55)],40,7).rotate((0,40,0),(0,40,1),a)
   r('splayed structural buttress',brace,'white')
  for x in (-70,70):
   b('observation facade relief',box(34,3,98,x,-1,28),'white')
   b('dark vertical glazing',join([box(4,3,84,x+dx,-3,35) for dx in (-10,0,10)]),'darkgray')
  features=['Hollow tapered tower, three 7 mm radial buttresses, flared viewing bowl','Seven millimetre observation glazing ring and stout finial below 230 mm','Flared bowl needs supports; hollow shaft is open at its foot before union to roof']
 else:
  name='Circus Circus — Grand Big Top';colors=['cream','red','white','yellow']
  # Cone has 45-degree sloping underside, substantial edge and integral scallops.
  def tent_ring(radius,z):return [cq.Vector(radius*math.cos(i*math.pi/24),40+radius*math.sin(i*math.pi/24),z) for i in range(48)]
  canopy=faceted_loft([tent_ring(50,Z+15),tent_ring(4,Z+61)]).cut(faceted_loft([tent_ring(45,Z+14.9),tent_ring(2,Z+58)]))
  r('striped big top shell',canopy,'white')
  for a in range(0,360,60):
   wedge=cq.Workplane('XY').moveTo(0,40).lineTo(90*math.cos(math.radians(a)),40+90*math.sin(math.radians(a))).lineTo(90*math.cos(math.radians(a+30)),40+90*math.sin(math.radians(a+30))).close().extrude(75).translate((0,0,Z))
   r('alternating tent stripe',canopy.intersect(wedge),'red')
  valance=cq.Workplane('XY').polygon(96,100).polygon(96,92).extrude(9).translate((0,40,Z+10))
  for a in range(15,360,30):
   aa=math.radians(a); v=cq.Vector(math.cos(aa),math.sin(aa),0)
   valance=valance.cut(cq.Workplane('XY').add(cq.Solid.makeCylinder(8,12,cq.Vector(42*v.x,40+42*v.y,Z+7),v)))
  r('continuous scalloped valance ring',valance,'red')
  for a in range(0,360,30):
   aa=math.radians(a+2)
   # Planted piers, arches implied by varying scalloped valance depth.
   r('integral big top pier',cyl(3.4,17,47*math.cos(aa),40+47*math.sin(aa)),'white')
  r('apex pommel',cyl(4.5,5,z=Z+59),'yellow')
  for x in (-70,70):
   b('cream circus panel',box(36,3,101,x,-1,25),'white')
   b('vertical circus stripes',join([box(6,3,101,x+dx,-3,25) for dx in (-12,0,12)]),'red')
   b('marquee cornice',box(40,4,6,x,-2,120),'yellow')
  features=['Hollow alternating-color conical canopy with integral stout piers and rear antenna clearance','Continuous valance and printed marquee tower stripes','Supports needed under valance between piers; tent cone slope is 45 degrees']
 clearance=keepout(); roof=roof_base
 for region in roof_parts:
  region['shape']=region['shape'].cut(clearance)
  if region['name']!='alternating tent stripe' and region['shape'].solids().size(): roof=roof.union(region['shape'],clean=False)
 body=body_base
 for region in body_parts: body=body.union(region['shape'],clean=False)
 roof_color=PALETTE['white'] if style=='circus_circus' else PALETTE[colors[1]]
 if style!='luxor': roof_parts=[r for r in roof_parts if r['color']!=roof_color]
 if style=='circus_circus':
  roof_parts.sort(key=lambda r: 2 if r['name']=='alternating tent stripe' else 0)
  for r in roof_parts:
   if r['name']=='alternating tent stripe':r['shape']=r['shape'].intersect(box(210,120,55,0,40,Z))
 if style in ('flamingo','circus_circus'):
  for r in roof_parts:
   if style=='circus_circus' and r['name']=='alternating tent stripe':continue
   bb=r['shape'].val().BoundingBox()
   r['shape']=box(bb.xlen+0.2,bb.ylen+0.2,bb.zlen+0.2,(bb.xmin+bb.xmax)/2,(bb.ymin+bb.ymax)/2,bb.zmin-.1)
 return {'roof':roof.clean(),'body':body.clean(),'roof_regions':[r for r in roof_parts if r['shape'].solids().size()],'body_regions':[], 'body_color':PALETTE['cream'], 'roof_color':roof_color,'detail_features':features,'name':name,'description':'; '.join(features),'colors':[PALETTE[c] for c in colors]}

if __name__=='__main__':
 import time
 # Simple connected fixture approximates actual deck and towers.
 roof=box(224,116,3.2,0,40,132.4).cut(keepout())
 body=join([box(216,204,16,0,0,0),box(44,82,116,-70,40,16),box(44,82,116,70,40,16)])
 for s in STYLE_IDS:
  t=time.time(); result=hotel_style(s,roof,body)
  for key in ('roof','body'):
   shape=result[key].val()
   assert shape.isValid(),(s,key,'invalid')
   assert len(shape.Solids())==1,(s,key,'disconnected',len(shape.Solids()))
  print(s,'valid connected roof and body',round(time.time()-t,2),flush=True)
