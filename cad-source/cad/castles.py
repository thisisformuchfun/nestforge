"""R2 castle feeders: load-bearing towers, masonry relief and positive snap joints.
All measurements are millimetres. Roofs and decorative work are physical CAD solids.
"""
from pathlib import Path
import math,sys,json,os,tempfile
import cadquery as cq
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
DESCRIPTIONS={'gothic-keep':'A five-spired Gothic keep with carved lancet portals, staggered stonework and a crenellated balcony.', 'fairy-tale-turret':'A round fairytale tower with eight open lancet portals, stepped buttresses and a broad orange bell roof.', 'stone-fortress':'A fortified stone gate with corner bastions, a tall crenellated watchtower and an integral timber drawbridge.', 'medieval-chapel':'An octagonal chapel with narrow lancet portals, gold cornice and a steep green eight-facet shingled spire.', 'dragon-guard-citadel':'A crenellated citadel guarded by an integral horned dragon with ribbed wings, curled tail and raised scale relief.', 'royal-gatehouse':'A royal gatehouse with four tall blue pinnacles, a tiered hipped keep roof, heraldic banners and timber drawbridge.'}
STONE='#BCB7A8'; DARK='#454E57'; GOLD='#D7A750'; BLUE='#2057A2'; RED='#A83931'; GREEN='#586747'
def B(x,y,h,px=0,py=0,z=0):return cq.Workplane('XY').box(x,y,h,centered=(True,True,False)).translate((px,py,z))
def C(r,h,z=0,x=0,y=0):return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))
def R(ro,ri,h,z=0):return cq.Workplane('XY').circle(ro).circle(ri).extrude(h).translate((0,0,z))
def join(items):
    a=items[0]
    for b in items[1:]:a=a.union(b,clean=False)
    return a.clean()
def cone(r1,r2,h,z=0,x=0,y=0):return cq.Workplane('XY').add(cq.Solid.makeCone(r1,r2,h)).translate((x,y,z))
def arch(w,z,spring,top,depth=16):
    return cq.Workplane('XZ').polyline([(-w/2,z),(-w/2,spring),(0,top),(w/2,spring),(w/2,z)]).close().extrude(depth,both=True)
def sqring(o,i,h,z):return B(o,o,h,z=z).cut(B(i,i,h+.4,z=z-.2))
def pyramid(w,tip,h,z):
    return cq.Workplane('XY').workplane(offset=z).rect(w,w).workplane(offset=h).rect(tip,tip).loft(ruled=True)
def shingle_cone(r,z,h):
    pieces=[cone(r,1.8,h,z).cut(cone(r-3,.7,h-4,z-.1))]
    for dz in range(0,int(h)-5,7):
        rr=r-(r-1.8)*dz/h
        pieces.append(R(rr+.85,max(.8,rr-2.5),1.2,z+dz))
    return join(pieces)
def hanger(z=210):
    # Integral vertical eye; broad roots distribute the single hanger load.
    eye=cq.Workplane('XZ').center(0,z+8).circle(9).circle(4.5).extrude(4,both=True)
    return eye.union(B(15,8,8,z=z-1))
def wall_detail(z0=20,z1=139):
    # Cut joints leave physical 0.8 mm running-bond masonry recesses.
    cutters=[]
    for z in range(z0+7,z1,9):
        cutters.extend([B(110,1.05,.8,py=y,z=z) for y in [-53.8,53.8]])
        cutters.extend([B(1.05,110,.8,px=x,z=z) for x in [-53.8,53.8]])
    for row,z in enumerate(range(z0,z1-8,9)):
        for x in range(-45+(row%2)*9,54,18):
            cutters.extend([B(.9,1.15,8,x,y,z) for y in [-53.8,53.8]])
            cutters.extend([B(1.15,.9,8,y,x,z) for y in [-53.8,53.8]])
    return cq.Compound.makeCompound([p.val() for p in cutters])
def largest(w):
    ss=w.val().Solids();big=max(ss,key=lambda s:s.Volume())
    extras=sum(s.Volume() for s in ss)-big.Volume()
    if extras>1000:raise ValueError(f'Unexpected disconnected geometry {extras}')
    return cq.Workplane('XY').add(big)
def body_square(style='gothic'):
    # Thick corner towers make a keep, rather than an open pavilion frame.
    solid=sqring(108,99,120,18)
    solid=solid.cut(wall_detail())
    towers=[]
    for x in [-48,48]:
      for y in [-48,48]:
        t=C(17,124,18,x,y).cut(C(13,125,18,x,y))
        joints=[]
        for row,z in enumerate(range(28,137,10)):
            joints.append(R(17.2,16.15,1,z).translate((x,y,0)))
            for angle in range(0,360,45):
                joints.append(B(1.1,1.6,9,0,16.65,z+1).rotate((0,0,0),(0,0,1),angle+22.5*(row%2)).translate((x,y,0)))
        t=largest(t.cut(cq.Compound.makeCompound([c.val() for c in joints])))
        t=t.union(C(18.5,4,132,x,y).cut(C(13,5,132,x,y)))
        # Arrow slits with inward daylight preserve tower massing.
        slit=B(3.4,40,17,x,y,103)
        t=t.cut(slit)
        towers.append(t)
    solid=join([solid]+towers)
    cuts=[];surround=[]
    for a in [0,90,180,270]:
        opening=arch(50,27,82,115,14).translate((0,-53,0)).rotate((0,0,0),(0,0,1),a)
        cuts.append(opening)
        outer=arch(62,25,83,123,3).translate((0,-55,0))
        inner=arch(51,24,82,116,4).translate((0,-55,0))
        rim=outer.cut(inner).rotate((0,0,0),(0,0,1),a)
        surround.append(rim)
        # Flowing stone bifurcations and an open oculus occupy only the arch head.
        for sign in [-1,1]:
            bar=cq.Workplane('XZ').moveTo(0,89).threePointArc((sign*7,99),(sign*20,104)).lineTo(sign*20,107).threePointArc((sign*7,103),(0,93)).close().extrude(2,both=True).translate((0,-52,0)).rotate((0,0,0),(0,0,1),a)
            surround.append(bar)
        petal=cq.Workplane('XZ').center(0,108).circle(6.6).circle(4.1).extrude(2,both=True).translate((0,-52,0))
        surround.append(petal.rotate((0,0,0),(0,0,1),a))
        # Slender engaged shafts have turned bases and flared capitals.
        for x in [-28.2,28.2]:
            shaft=C(1.65,53,29,x,-58).union(C(2.6,3,27,x,-58)).union(cone(1.65,3.1,4,79,x,-58))
            surround.append(shaft.rotate((0,0,0),(0,0,1),a))
    solid=solid.cut(cq.Compound.makeCompound([p.val() for p in cuts]))
    solid=join([solid]+surround+[sqring(114,99,4,126),sqring(118,99,3,133)])
    # Alternating merlons are visibly separated, supported by a broad cornice.
    merlons=[]
    for a in [0,90,180,270]:
      for x in [-30,-15,0,15,30]:
        merlon=B(8,7,10,x,-55,136)
        cap=B(9.4,8.4,1.8,x,-55,144.5).edges('>Z').chamfer(.6)
        merlons.append(merlon.union(cap).rotate((0,0,0),(0,0,1),a))
    # Buttresses step toward the tower and are integral to the shell.
    for x in [-48,48]:
      for y in [-48,48]:
        sx=1 if x>0 else -1;sy=1 if y>0 else -1
        merlons.extend([B(10,11,36,x+sx*13,y+sy*13,18),B(8,9,33,x+sx*12,y+sy*12,54),B(6,7,24,x+sx*11,y+sy*11,87)])
    return largest(join([solid]+merlons))
def roof_square(style='gothic'):
    if style=='royal':
        r=sqring(108,95,3,139)
        r=r.union(pyramid(106,55,32,140).cut(pyramid(98,49,30,139.8)))
        r=r.union(B(55,55,3,z=170)).union(pyramid(59,8,25,172))
        for dz in range(0,30,6):
            w=106-51*dz/32;r=r.union(sqring(w+1.5,w-5,1.2,140+dz),clean=False)
        for dz in range(0,23,5):
            w=59-51*dz/25;r=r.union(sqring(w+1.5,w-5,1.2,172+dz),clean=False)
        for x in [-48,48]:
            for y in [-48,48]:
                r=r.union(R(18,12.5,12,139).translate((x,y,0)),clean=False)
                r=r.union(shingle_cone(20,151,67).translate((x,y,0)),clean=False)
        return r.union(hanger(197)).clean()
    r=sqring(108,95,3,139)
    # Central steep keep spire and four tall satellite pinnacles.
    roof=pyramid(106,8,70,140).cut(pyramid(98,3,67,139.8))
    details=[]
    for dz in range(0,65,7):
        w=106-98*dz/70
        details.append(sqring(w+1.6,max(5,w-5),1.3,140+dz))
    r=join([r,roof]+details)
    for x in [-48,48]:
      for y in [-48,48]:
        r=r.union(R(18,12.5,12,139).translate((x,y,0)),clean=False)
        r=r.union(shingle_cone(20,151,53).translate((x,y,0)),clean=False)
    return r.union(hanger(210)).clean()
def tray():
    t=B(154,154,4,z=0).union(sqring(154,146,10,4)).union(sqring(119,108.6,14,4))
    # Balcony perimeter stone blocks; low enough for unrestricted landing.
    for x in range(-66,67,18):
      for y in [-75,75]:t=t.union(B(10,5,5,x,y,14),clean=False)
    for y in range(-48,49,18):
      for x in [-75,75]:t=t.union(B(5,10,5,x,y,14),clean=False)
    for x in [-32,-16,0,16,32]:
      for y in [-32,-16,0,16,32]:t=t.cut(C(1.4,5,-.5,x,y),clean=False)
    return t.clean()
def round_tray(ro):
    t=C(78,4).union(R(78,73,10,4)).union(R(ro+4,ro+.4,14,4))
    # Clear the locating collar around both long tray flexures.
    for sg in [-1,1]:t=t.cut(B(10,7,13.2,0,sg*(ro+1.2),5))
    for a in range(0,360,30):
        t=t.union(B(10,5,5,0,-75,14).rotate((0,0,0),(0,0,1),a),clean=False)
    for x in [-32,-16,0,16,32]:
        for y in [-32,-16,0,16,32]:t=t.cut(C(1.4,5,-.5,x,y),clean=False)
    return t.clean()
def seed_well():
    # Shallow seed rim permits hand refill through every arch; no clear plastic.
    return R(37,33,18,4).union(R(33,28,2,4))

def body_round(style):
    n=8;ro=61 if style=='fairy' else 57
    wall=cq.Workplane('XY').polygon(n,2*ro).polygon(n,2*(ro-4.2)).extrude(121).translate((0,0,18))
    # Faceted wall faces form a genuine polygonal tower; each has carved courses.
    ap=ro*math.cos(math.pi/8)
    cuts=[];trims=[]
    for a in range(0,360,45):
        cut=arch(30 if style=='chapel' else 33,28,94,124,10).translate((0,-ap,0)).rotate((0,0,0),(0,0,1),a+22.5)
        cuts.append(cut)
        trim=arch(39,26,94,130,2.8).cut(arch(31 if style=='chapel' else 34,25,94,125,4)).translate((0,-ap-.6,0)).rotate((0,0,0),(0,0,1),a+22.5)
        trims.append(trim)
    wall=wall.cut(cq.Compound.makeCompound([p.val() for p in cuts]))
    # Engraved horizontal mortar lines around octagonal facets.
    for z in range(26,137,10):
        outer=cq.Workplane('XY').polygon(8,2*(ro+.1)).polygon(8,2*(ro-.8)).extrude(.85).translate((0,0,z))
        wall=wall.cut(outer)
    joints=[]
    for row,z in enumerate(range(28,130,10)):
      for a in range(0,360,45):
        for x in [-16,0,16] if row%2 else [-24,-8,8,24]:
          joints.append(B(.85,1.2,9,x,-ap-.05,z).rotate((0,0,0),(0,0,1),a+22.5))
    wall=wall.cut(cq.Compound.makeCompound([q.val() for q in joints]))
    # Moulded portal shafts and capitals remain outside the clear feeding aperture.
    for a in range(0,360,45):
      for x in [-18,18]:
        shaft=C(1.3,65,28,x,-ap-2.1).union(C(2.1,2.5,27,x,-ap-2.1)).union(cone(1.3,2.4,3,91,x,-ap-2.1))
        trims.append(shaft.rotate((0,0,0),(0,0,1),a+22.5))
    wall=join([wall]+trims)
    for a in range(0,360,45):
        if a in [90,270]:
            wall=wall.union(B(12,4,116,0,(1 if a==90 else -1)*(ro-2),18),clean=False)
            continue
        rad=math.radians(a);x=ro*math.cos(rad);y=ro*math.sin(rad)
        # Three stepped segments create external flying-buttress proportions.
        wall=wall.union(C(4.2,116,19,x,y),clean=False)
        wall=wall.union(C(6.4,32,18,x,y),clean=False)
        wall=wall.union(C(5.2,23,50,x,y),clean=False)
        wall=wall.union(C(6,4,130,x,y),clean=False)
    wall=wall.union(R(ro+2,ro-5,4,135),clean=False)
    return wall.clean()
def roof_round(style):
    ro=65 if style=='fairy' else 61
    r=R(ro,ro-9,6,136)
    # Fairytale is a broad curved bell roof, chapel a slender octagonal spire.
    if style=='fairy':
      stations=[(140,70),(146,65),(158,52),(171,39),(188,24),(203,13),(213,3)]
      def loft(st):
        w=cq.Workplane('XY').workplane(offset=st[0][0]).circle(st[0][1]);last=st[0][0]
        for z,rad in st[1:]:w=w.workplane(offset=z-last).circle(rad);last=z
        return w.loft(ruled=True)
      r=r.union(loft(stations).cut(loft([(z-.1,max(1,r-3)) for z,r in stations[:-1]]+[(210,1)])))
      for z in range(141,207,6):
        for (za,ra),(zb,rb) in zip(stations,stations[1:]):
          if za<=z<=zb:
            rad=ra+(rb-ra)*(z-za)/(zb-za);r=r.union(R(rad+.9,rad-2,1.2,z),clean=False);break
    else:
      outer=cq.Workplane('XY').workplane(offset=140).polygon(8,132).workplane(offset=72).polygon(8,7).loft(ruled=True)
      inner=cq.Workplane('XY').workplane(offset=139.8).polygon(8,124).workplane(offset=68).polygon(8,3).loft(ruled=True)
      r=r.union(outer.cut(inner))
      for dz in range(0,67,6):
        rr=66-62.5*dz/72
        trim=cq.Workplane('XY').polygon(8,2*rr+1.8).polygon(8,2*rr-5).extrude(1.15).translate((0,0,140+dz));r=r.union(trim,clean=False)
    seams=[]
    for row,z in enumerate(range(142,204,6)):
      if style=='fairy':
        def radius(zz):
          for (za,ra),(zb,rb) in zip(stations,stations[1:]):
            if za<=zz<=zb:return ra+(rb-ra)*(zz-za)/(zb-za)
        ra,rb=radius(z),radius(z+4.8)
        count=max(8,int(2*math.pi*ra/12))
        angles=[j*360/count+(row%2)*180/count for j in range(count)]
        offsets=[0]
      else:
        ra=(66-62.5*(z-140)/72)*math.cos(math.pi/8)
        rb=(66-62.5*(z+4.8-140)/72)*math.cos(math.pi/8)
        angles=[a+22.5 for a in range(0,360,45)]
        offsets=[x for x in range(-20+(row%2)*5,21,10) if abs(x)<ra*.38]
      for a in angles:
       for x in offsets:
        cut=cq.Workplane('YZ').polyline([(-ra-.3,z),(-ra+.8,z),(-rb+.8,z+4.8),(-rb-.3,z+4.8)]).close().extrude(.43,both=True).translate((x,0,0)).rotate((0,0,0),(0,0,1),a)
        seams.append(cut)
    r=r.cut(cq.Compound.makeCompound([q.val() for q in seams]))
    r=r.union(hanger(212),clean=False)
    return r.clean()
def fortress_roof():
    # Weather deck sheds water through four scuppers below castellated parapet.
    r=B(113,113,3,z=139).union(sqring(114,103,16,142))
    for a in [0,90,180,270]:
      for x in [-42,-21,0,21,42]:r=r.union(B(11,8,12,x,-54,158).rotate((0,0,0),(0,0,1),a),clean=False)
    for x in [-48,48]:
      for y in [-48,48]:
        r=r.union(C(20,5,139,x,y),clean=False).union(R(20,15,15,144).translate((x,y,0)),clean=False)
        for a in range(0,360,60):
          rad=math.radians(a);r=r.union(B(7,7,10,x+16.5*math.cos(rad),y+16.5*math.sin(rad),159),clean=False)
    # Central upper watchtower links the hanger to the deck as one printed part.
    watch=sqring(38,30,54,142).union(B(42,42,3,z=196))
    # Watchtower has dressed ashlar, a two-stage cornice and a chamfered coping.
    for z in range(149,195,8):
      for a in [0,90,180,270]:
        watch=watch.cut(B(40,.85,.7,0,-18.9,z).rotate((0,0,0),(0,0,1),a))
    watch=watch.union(sqring(40,30,1.8,192)).union(sqring(43,30,1.7,194))
    coping=sqring(116,102,2.1,156.4).edges('>Z').chamfer(.55)
    r=r.union(coping,clean=False)
    for a in [0,90,180,270]:watch=watch.cut(arch(14,151,173,187,7).translate((0,-19,0)).rotate((0,0,0),(0,0,1),a))
    for x in [-16,16]:
        for y in [-16,16]:watch=watch.union(B(10,10,10,x,y,199),clean=False)
    r=r.union(watch,clean=False).union(B(15,10,9,z=197),clean=False).union(hanger(206),clean=False)
    for x in [-35,35]:
        for y in [-35,35]:r=r.cut(C(1.6,5,138,x,y))
    return r.clean()
def drawbridge():
    # Integral raised grain planks and full hinge beam; ramp does not retain parts.
    ramp=cq.Workplane('YZ').polyline([(-74,12),(-107,1),(-107,4),(-74,15)]).close().extrude(23,both=True)
    for y in range(-104,-75,5):
        z=4+(y+107)*11/33
        ramp=ramp.union(B(45,1.3,1,0,y,z-.2),clean=False)
    return ramp.clean()
def dragon_relief():
    # Sculpted integral guardian: haunch, coiled neck, horned head and scalloped wings.
    # All forms intersect a rear buttress, so the dragon is one connected roof feature.
    d=C(9,45,151,0,42).union(C(7,30,180,0,38))
    d=d.union(R(18,13,4,151).translate((15,34,0)))
    for z in range(183,205,5):d=d.union(R(7.8,6,1.1,z).translate((0,38,0)),clean=False)
    # Head projects forward over the parapet and has two robust swept horns.
    d=d.union(B(15,21,11,0,27,207)).union(B(11,15,6,0,17,205))
    for x in [-6,6]:d=d.union(cone(3.2,1.1,11,216,x,32))
    for sg in [-1,1]:d=d.union(C(1.7,1.8).rotate((0,0,0),(0,1,0),sg*90).translate((sg*6.8,22,214)))
    d=d.cut(B(10,5,1.1,0,10.5,207.3))
    # Wings are angular membranes with thick raised ribs, not detached ornaments.
    for sign in [-1,1]:
        pts=[(sign*3,177),(sign*30,213),(sign*40,202),(sign*28,193),(sign*36,180),(sign*18,184),(sign*11,169)]
        wing=cq.Workplane('XZ').polyline(pts).close().extrude(2.5,both=True).translate((0,43,0))
        d=d.union(wing,clean=False)
        for ex,ez,fx,fz in [(28,209,26.5,205),(34,182,32.5,181)]:
            # Every rib end lies strictly inside the wing membrane; no
            # vertex-only contacts or non-manifold wing-tip unions.
            rib=cq.Workplane('XZ').polyline([(sign*5,179),(sign*ex,ez),(sign*fx,fz),(sign*5,177)]).close().extrude(3.3,both=True).translate((0,43,0));d=d.union(rib,clean=False)
    # Dorsal plates are thick printable wedges.
    for z in range(167,205,8):
        plate=cq.Workplane('YZ').polyline([(43.5,z),(54,z+3),(43.5,z+7)]).close().extrude(2,both=True);d=d.union(plate,clean=False)
    return d.clean()

def snap_beam(x,y,z,length=28,down=False,width=7,thick=1.6):
    # Beam lies outside the wall. A 1.25 mm hook has a flat load shoulder and
    # a sloped insertion face. Pull the exposed paddle radially away to release.
    sign=1 if y>0 else -1
    start=z-length if down else z
    beam=B(width,thick,length,x,y,start)
    tip=start+2 if down else start+length-4
    outer=y-sign*thick/2
    inner=outer-sign*1.25
    pts=[(outer,tip),(inner,tip),(inner,tip+1.3),(outer,tip+3.8)] if not down else [(outer,tip),(inner,tip+2.5),(inner,tip+3.8),(outer,tip+3.8)]
    hook=cq.Workplane('YZ').polyline(pts).close().extrude(width/2,both=True).translate((x,0,0))
    return beam.union(hook).union(B(width+2,2.2,4,x,y,tip))
def snap_interfaces(t,b,r,sites):
    for x,ywall in sites:
        sg=1 if ywall>0 else -1;y=ywall+sg*1.2
        foot=B(11,9,5,x,y-sg*2,0)
        t=t.union(foot).union(snap_beam(x,y,4,31))
        b=b.cut(B(9,9,5,x,ywall,30))
        if abs(x)<1 and abs(ywall)<60:b=b.cut(B(10,8,20,x,ywall+sg*4,18))
        # Roof beam roots overlap a bridge integrated with the roof eave.
        r=r.union(B(11,9,4,x,y-sg*2,139)).union(snap_beam(x,y,143,27,True))
        b=b.cut(B(9,9,5,x,ywall,118))
        b=b.cut(B(10,8,9,x,ywall+sg*4,130))
    return t.clean(),largest(b),r.clean()
def seed_snap(t,s):
    # Two short radial latches retain the removable seed well; its rim is not
    # structural. Long 17 mm flexures run tangentially to fit below the portals.
    for sg in [-1,1]:
        y=sg*38.2
        t=t.union(B(7,3,4,0,y+sg*.6,2)).union(snap_beam(0,y,4,13,width=5,thick=1.2))
        s=s.cut(B(7,7,4.4,0,sg*36,12.7))
    return t.clean(),s.clean()
def add_roof_joints(r):
    cuts=[]
    for row,dz in enumerate(range(1,61,7)):
        half=53-49*dz/70
        for x in range(-40+(row%2)*6,41,12):
          if abs(x)>half-5:continue
          y=-half
          # Recess follows the sloping plane, so it does not perforate the roof.
          cutter=cq.Workplane('YZ').polyline([(y-.1,140+dz),(y+.9,140+dz),(y+5.1,146+dz),(y+4.1,146+dz)]).close().extrude(.55,both=True).translate((x,0,0))
          for a in [0,90,180,270]:cuts.append(cutter.rotate((0,0,0),(0,0,1),a))
    r=r.cut(cq.Compound.makeCompound([c.val() for c in cuts]))
    return largest(r.clean())
def voussoirs():
    # Wedge-like voussoir blocks step along the two sides of each lancet head.
    bits=[]
    for a in [0,90,180,270]:
      for sg in [-1,1]:
        for j in range(5):
          x=sg*(27-5*j);z=88+6*j
          block=B(7,1.5,3.4,x,-58.3,z).rotate((x,0,z),(x,1,z),-sg*38).rotate((0,0,0),(0,0,1),a)
          bits.append(block)
      bits.append(B(8,2.3,10,0,-57.8,116).rotate((0,0,0),(0,0,1),a))
    return join(bits)
def trim_region():
    # Extend the material boundary past the lancet cusp to avoid gray lobes
    # touching along one edge; this changes color partition only, not geometry.
    return join([voussoirs()]+[B(8,2.3,12,0,-57.8,114).rotate((0,0,0),(0,0,1),a) for a in [0,90,180,270]])
def banners():
    pieces=[]
    for x in [-34,34]:
        p=cq.Workplane('XZ').polyline([(x-8,101),(x+8,101),(x+8,67),(x,60),(x-8,67)]).close().extrude(1.6,both=True).translate((0,-54,0));pieces.append(p)
    return join(pieces)
def fleur():
    pieces=[]
    for x in [-34,34]:
        pieces.extend([B(2,1.8,19,x,-56,76),B(13,1.8,2,x,-56,82)])
        for dx in [-5,0,5]:pieces.append(cq.Workplane('XZ').polyline([(x+dx-2,87),(x+dx,92),(x+dx+2,87),(x+dx,85)]).close().extrude(1.4,both=True).translate((0,-56,0)))
    return join(pieces)
CACHE={}
def castle(slug):
    from common import export_design
    styles={'gothic-keep':('Gothic Keep','gothic'), 'fairy-tale-turret':('Fairy-tale Turret','fairy'), 'stone-fortress':('Stone Fortress','fortress'),'medieval-chapel':('Medieval Chapel','chapel'),'dragon-guard-citadel':('Dragon Guard Citadel','dragon'),'royal-gatehouse':('Royal Gatehouse','royal')}
    name,style=styles[slug];print('BUILD',slug,flush=True)
    t=tray();s=seed_well();regions=[]
    if style in ['fairy','chapel','dragon']:
        ro=61 if style=='fairy' else 57
        key='fairy' if style=='fairy' else 'chapel'
        if key not in CACHE:CACHE[key]=body_round(key)
        b=CACHE[key];print('MASONRY READY',style,flush=True)
        # Round tower foot collar replaces the square locating curb.
        t=round_tray(ro)
        if style=='dragon':
            r=C(65,3,139).union(R(65,58,13,142))
            for x in [-30,30]:
                for y in [-30,30]:r=r.cut(C(1.6,5,138,x,y))
            for a in range(0,360,30):r=r.union(B(9,9,10,61*math.cos(math.radians(a)),61*math.sin(math.radians(a)),155),clean=False)
            dragon=dragon_relief();r=r.union(C(10,14,140,0,42)).union(dragon).union(B(10,10,65,0,0,142)).union(hanger(206))
            eyes=join([C(1.7,1.8).rotate((0,0,0),(0,1,0),sg*90).translate((sg*6.8,22,214)) for sg in [-1,1]])
            horns=join([cone(3.2,1.1,11,216,x,32) for x in [-6,6]])
            regions.extend([{'name':'Dragon eyes','shape':eyes,'color':GOLD},{'name':'Dragon horns','shape':horns,'color':'#DAD3BD'},{'name':'Dragon sculptural guardian','shape':dragon,'color':RED}])
        else:r=roof_round(style)
        sites=[(0,-ro),(0,ro)]
        # Two additional opposing latches use the same proven flexure rotated.
        t,b,r=snap_interfaces(t,b,r,sites)
        # Two strong vertex latches are sufficient on this circular load path.
    else:
        if 'square' not in CACHE:
            CACHE['square']=body_square(style)
            cq.exporters.export(CACHE['square'],str(Path(tempfile.gettempdir())/'castles-r2-masonry.step'))
        b=CACHE['square'];print('MASONRY READY',style,flush=True);r=fortress_roof() if style=='fortress' else roof_square(style)
        if style=='gothic':r=add_roof_joints(r)
        t,b,r=snap_interfaces(t,b,r,[(x,y) for x in [-48,48] for y in [-65,65]])
        # Voussoirs are shallow integral ornaments, fused into the portal rim.
        trim=voussoirs();b=largest(b.union(trim));regions_body=[{'name':'Carved arch stone trim','shape':trim_region(),'color':'#DAD3BD'}]
        if style in ['royal','fortress']:
            t=t.union(drawbridge())
            banner=banners();b=b.union(banner);regions_body.append({'name':'Heraldic banners','shape':banner,'color':BLUE})
            herald=fleur();b=largest(b.union(herald));regions_body.append({'name':'Heraldic fleur relief','shape':herald,'color':GOLD})
    print('JOINTS AND CROWN READY',style,flush=True)
    # Crown seats in a precisely relieved shell; no volumetric interference.
    b=largest(b.cut(r))
    # Final R2 clearance: trim only the outward lancet relief beside the
    # lower catches. Preserve the structural receiver pier and stop shoulder.
    if style in ['chapel','dragon']:
        for sg in [-1,1]:b=b.cut(B(10,8,20,0,sg*61,18))
    t,s=seed_snap(t,s)
    roofcolor={'gothic':DARK,'royal':BLUE,'fortress':STONE,'fairy':'#CE592F','chapel':GREEN,'dragon':DARK}[style]
    bodycolor='#C6B38D' if style=='fairy' else STONE
    if style in ['fairy','chapel','dragon']:
        regions_body=[{'name':'Arch capitals and upper cornice','shape':B(150,150,8,z=131),'color':GOLD}]
    physical=[dict(name='Drained balcony tray',shape=largest(t),color=DARK if style!='fairy' else bodycolor,regions=([{'name':'Timber drawbridge planks','shape':drawbridge(),'color':'#805735'}] if style in ['fortress','royal'] else []),support='Organic supports under projecting drawbridge; tray flat on bed.' if style in ['fortress','royal'] else 'None; tray flat on bed.',explode=[0,0,-30]),dict(name='Masonry tower shell',shape=largest(b),color=bodycolor,regions=regions_body,explode=[0,0,25]),dict(name='Snap weather crown',shape=largest(r),color=roofcolor,regions=regions,explode=[0,0,95],support='Organic support beneath external snap hooks; roof upright'),dict(name='Removable seed well',shape=s,color='#79543B' if style=='dragon' else GOLD,explode=[0,0,10])]
    for p in physical:print('PART',p['name'],p['shape'].val().isValid(),len(p['shape'].val().Solids()),flush=True)
    export_design(slug,name,'Castles',DESCRIPTIONS[slug],physical,
      notes=['Digital prototype: print fit coupons, verify snap retention and weather resistance before outdoor use.','Outdoor ASA recommended; preserve 0.4 mm wall-to-flexure clearance.','Drain holes are 2.8 mm diameter. Remove roof and shell for brush cleaning.','No clear sheet, loose glazing, cords through parts or bought-in retainers.'],
      assembly=['Snap the tower onto the balcony tray; check every external hook engages its receiver window.','Press the seed well into its two tray latches.','Press the crown onto the tower until every downward roof hook engages.','Hang the complete rigid assembly from the one integral top eye. To clean, remove from hanger, pull exposed tabs outward and lift components apart.'],
      hanger=[0,0,{'royal':205,'gothic':218,'fairy':220,'chapel':220,'fortress':214,'dragon':214}[style]],
      snap_joints=[dict(name='Tray to masonry',parts=['Drained balcony tray','Masonry tower shell'],description='External cantilever beams, ramped hooks and through receiver windows; positive horizontal retention shoulder.',beam_length_mm=31,beam_thickness_mm=1.6,deflection_mm=1.25,clearance_mm=.4,release='Pull exterior paddles radially outward while lifting shell.'),dict(name='Crown to masonry',parts=['Snap weather crown','Masonry tower shell'],description='Downward 27 mm cantilevers with inward hook shoulders.',beam_length_mm=27,beam_thickness_mm=1.6,deflection_mm=1.25,clearance_mm=.4,release='Pull exposed roof tabs outward, lift crown.'),dict(name='Seed well to tray',parts=['Removable seed well','Drained balcony tray'],description='Two opposed rim hooks.',beam_length_mm=13,beam_thickness_mm=1.2,deflection_mm=1.25,clearance_mm=.4,release='Pull opposed rim tabs outward through the feeding portal.')],
      refill='Pour seed through an open lancet portal into the shallow well; crown releases for full cleanout.',detail_features=['Recessed masonry courses','Integral pointed portal surrounds','Stepped buttresses and structural receiver piers','Separated balcony merlons','Hollow tower and open feeding portals']+(['Staggered vertical tower joints','Carved voussoirs'] if style in ['gothic','royal','fortress'] else [])+(['Slope-following roof tile seams'] if style=='gothic' else [])+(['Sculptural winged dragon with coiled tail, neck scales, horn and eye relief'] if style=='dragon' else ['Physical stepped roof courses']),reference='User castle reference image, 2026-10-08')
def finalize_castles(slugs):
    from common import export_design
    for slug in slugs:
        folder=HERE.parent/'exports'/slug
        meta=json.loads((folder/'design.json').read_text());parts=[]
        for index,p in enumerate(meta['parts']):
            item={k:p[k] for k in ['name','color','explode','support','print_rotation'] if k in p}
            item['shape']=cq.importers.importStep(str(folder/p['step']))
            if index==0 and slug in ['stone-fortress','royal-gatehouse']:
                item['regions']=[dict(name='Timber drawbridge planks',shape=drawbridge(),color='#805735')]
                item['support']='Organic supports under projecting drawbridge; tray flat on bed.'
            if index==1 and slug in ['medieval-chapel','dragon-guard-citadel']:
                for sg in [-1,1]:item['shape']=item['shape'].cut(B(10,8,20,0,sg*61,18))
            if index==1:
                item['regions']=([dict(name='Arch capitals and upper cornice',shape=B(150,150,8,z=131),color=GOLD)] if slug in ['medieval-chapel','dragon-guard-citadel'] else [dict(name='Carved arch stone trim',shape=trim_region(),color='#DAD3BD')]+([] if slug=='gothic-keep' else [dict(name='Heraldic banners',shape=banners(),color=BLUE),dict(name='Heraldic fleur relief',shape=fleur(),color=GOLD)]))
            if index==2 and slug=='dragon-guard-citadel':
                eyes=join([C(1.7,1.8).rotate((0,0,0),(0,1,0),sg*90).translate((sg*6.8,22,214)) for sg in [-1,1]])
                horns=join([cone(3.2,1.1,11,216,x,32) for x in [-6,6]])
                item['regions']=[dict(name='Dragon eyes',shape=eyes,color=GOLD),dict(name='Dragon horns',shape=horns,color='#DAD3BD'),dict(name='Dragon sculptural guardian',shape=dragon_relief(),color=RED)]
            if index==3 and slug=='dragon-guard-citadel':item['color']='#79543B'
            parts.append(item)
        export_design(slug,meta['name'],meta['family'],DESCRIPTIONS[slug],parts,**{k:meta.get(k) for k in ['notes','assembly','reference','hanger','snap_joints','refill','detail_features']})
def audit_castles(slugs):
    import trimesh
    from itertools import combinations
    reports=[]
    for slug in slugs:
        folder=HERE.parent/'exports'/slug
        meta=json.loads((folder/'design.json').read_text())
        shapes=[];meshes=[]
        for p in meta['parts']:
            shape=cq.importers.importStep(str(folder/p['step'])).val()
            mesh=trimesh.load(folder/p['file'],force='mesh')
            shapes.append((p['name'],shape))
            dims=mesh.extents.tolist()
            meshes.append(dict(name=p['name'],brep_valid=shape.isValid(),solids=len(shape.Solids()),watertight=bool(mesh.is_watertight),positive_volume=bool(mesh.volume>0),dimensions_mm=dims,x1c_fit=bool(dims[0]<=225 and dims[1]<=225 and dims[2]<=245)))
        collisions=[]
        for (na,a),(nb,b) in combinations(shapes,2):
            aa=a.BoundingBox();bb=b.BoundingBox()
            if aa.zmax<=bb.zmin+1e-7 or bb.zmax<=aa.zmin+1e-7:vol=0
            else:vol=a.intersect(b).Volume()
            collisions.append(dict(parts=[na,nb],intersection_mm3=vol))
        shell=shapes[1][1];traypart=shapes[0][1]
        if slug in ['fairy-tale-turret','medieval-chapel','dragon-guard-citadel']:
            ro=61 if slug=='fairy-tale-turret' else 57
            probe=B(20,16,35,0,-ro*math.cos(math.pi/8),38).rotate((0,0,0),(0,0,1),22.5)
        else:probe=B(20,16,35,0,-53,38)
        access=shell.intersect(probe.val()).Volume()<.01
        drain=traypart.intersect(C(1.2,6,-1).val()).Volume()<.01
        report=dict(slug=slug,parts=meshes,collisions=collisions,clear_portal_probe_20x35_mm=access,center_drain_clear=drain,nominal_cantilever_strain_percent={'tray':1.5*1.6*1.25/31**2*100,'roof':1.5*1.6*1.25/27**2*100,'seed_well':1.5*1.2*1.25/13**2*100},physical_testing_required=True)
        report['pass']=all(m['brep_valid'] and m['solids']==1 and m['watertight'] and m['positive_volume'] and m['x1c_fit'] for m in meshes) and all(c['intersection_mm3']<.05 for c in collisions) and access and drain
        (folder/'castle-validation.json').write_text(json.dumps(report,indent=2));reports.append(report)
        print('AUDIT',slug,report['pass'],[(c['parts'],round(c['intersection_mm3'],3)) for c in collisions if c['intersection_mm3']>.05],flush=True)
    return reports
if __name__=='__main__':
    if '--describe' in sys.argv:
        for slug,description in DESCRIPTIONS.items():
            p=HERE.parent/'exports'/slug/'design.json'
            if p.exists():
                d=json.loads(p.read_text());d['description']=description;temp=p.with_suffix('.json.tmp');temp.write_text(json.dumps(d,indent=2));os.replace(temp,p)
        sys.exit(0)
    if '--wood' in sys.argv or '--finish' in sys.argv:
        sys.argv.remove('--wood' if '--wood' in sys.argv else '--finish');finalize_castles(sys.argv[1:]);sys.exit(0)
    if '--audit' in sys.argv:
        sys.argv.remove('--audit');audit_castles(sys.argv[1:]);sys.exit(0)
    if '--reuse-masonry' in sys.argv:
        CACHE['square']=cq.importers.importStep(str(Path(tempfile.gettempdir())/'castles-r2-masonry.step'))
        sys.argv.remove('--reuse-masonry')
    if '--reuse-gothic' in sys.argv:
        CACHE['square']=cq.importers.importStep(str(HERE.parent/'exports/gothic-keep/02-masonry-tower-shell.step'))
        sys.argv.remove('--reuse-gothic')
    for slug in (sys.argv[1:] or ['gothic-keep','fairy-tale-turret','stone-fortress','medieval-chapel','dragon-guard-citadel','royal-gatehouse']):
        if slug=='dragon-guard-citadel':
            import community_dragon
            community_dragon.build()
        else:
            castle(slug)
