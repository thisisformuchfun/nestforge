"""Six Las Vegas inspired architectural caps; original designs, not licensed replicas.
Units mm, Z up. Architectural walls >=2.4 mm. Export the returned fused parts,
not region compounds; regions are paint/material masks for multi-colour slicing.
"""
import cadquery as cq
import math
STYLE_IDS=('bellagio-inspired','venetian-inspired','caesars-inspired','paris-inspired','excalibur-inspired','newyork-newyork-inspired')
CREAM='#DFD3C3'; TAN='#A79565'; YELLOW='#EEC000'; BLACK='#191919'; WHITE='#F0EEE9'; GRAY='#54585A'; RED='#CE3533'; BLUE='#265A9B'

def B(w,d,h,x=0,y=40,z=135.3):
    return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).translate((x,y,z))
def C(r,h,x,y,z):
    return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))
def compound(items):return cq.Workplane('XY').add(cq.Compound.makeCompound([p.val() for p in items]))
def fuse(base,items):
    return cq.Workplane('XY').add(base.val().fuse(*[p.val() for p in items]).clean()) if items else base

def hip(w,d,tw,td,h,x,y,z):
    return cq.Workplane('XY').workplane(offset=z).center(x,y).rect(w,d).workplane(offset=h).rect(tw,td).loft(ruled=True)
def shell(w,d,h,x,y,z):
    return B(w,d,h,x,y,z).cut(B(w-5.6,d-5.6,h-3,x,y,z-.1))
def cone(r,h,x,y,z):return cq.Workplane('XY').add(cq.Solid.makeCone(r,2.4,h)).translate((x,y,z))
def prism_triangle(w,h,d,x,y,z):
    return cq.Workplane('XZ').polyline([(x-w/2,z),(x+w/2,z),(x,z+h)]).close().extrude(d).translate((0,y,0))
def bar_between(x1,z1,x2,z2,width,depth,y):
    dx=x2-x1; dz=z2-z1; length=math.hypot(dx,dz)
    return B(width,depth,length,0,0,0).rotate((0,0,0),(0,1,0),math.degrees(math.atan2(dx,dz))).translate((x1,y,z1))
def keepouts():
    return [C(8.1,120,x,y,132) for x in (-105.5,105.5) for y in (4,76)]+[B(18.4,24,120,0,88,132)]

SPECS={
'bellagio-inspired':('Bellagio Inspired',CREAM,TAN,WHITE,YELLOW,'Italianate paired palazzi, layered cornices, arched window crowns and warm tan hipped roofs.'),
'venetian-inspired':('Venetian Inspired',CREAM,RED,WHITE,YELLOW,'Doge-style tracery, paired loggias and a compact ribbed campanile with a golden pyramidal crown.'),
'caesars-inspired':('Caesars Inspired',CREAM,WHITE,TAN,YELLOW,'A classical temple silhouette with engaged columns, stepped entablatures and sculpted pediments.'),
'paris-inspired':('Paris Inspired',CREAM,GRAY,WHITE,YELLOW,'French mansard pavilions beside an integral stout lattice Eiffel-inspired tower.'),
'excalibur-inspired':('Excalibur Inspired',CREAM,RED,BLUE,YELLOW,'A medieval curtain wall and four masonry turrets with alternating ribbed red and blue conical caps.'),
'newyork-newyork-inspired':('New York New York Inspired',TAN,GRAY,CREAM,YELLOW,'A stepped Art Deco city silhouette with vertical piers, inset window grids and layered crowns.')}

def hotel_style(style,roof_base,body_base):
    aliases={'bellagio':'bellagio-inspired','venetian':'venetian-inspired','caesars':'caesars-inspired','paris':'paris-inspired','excalibur':'excalibur-inspired','new-york-new-york':'newyork-newyork-inspired','newyork-newyork':'newyork-newyork-inspired'}
    style=aliases.get(style,style)
    name,stone,accent,trim,gold,desc=SPECS[style]
    groups={stone:[],accent:[],trim:[],gold:[]}; bodygroups={stone:[],accent:[],trim:[],gold:[]}
    def add(shape,color=stone):groups[color].append(shape)
    # Facade relief is exclusively on reservoir faces, never in the camera bay.
    # The shallow window panels and raised surrounds fuse into the front wall.
    for sx in (-70,70):
        for row,z in enumerate(range(26,123,16)):
            for dx in (-15,-5,5,15):
                x=sx+dx
                bodygroups[accent].append(B(6.5,1.5,10,x,-1.05,z))
                for off in (-3.8,3.8):bodygroups[trim].append(B(1.35,2.5,11.5,x+off,-.65,z-.4))
                for zz in (z-.6,z+10):bodygroups[trim].append(B(9,2.5,1.4,x,-.65,zz))
        for z in (20,41,73,105,129):bodygroups[stone].append(B(44,3.2,2.4,sx,-.25,z))
        for x in (sx-20.5,sx+20.5):bodygroups[trim].append(B(2.4,3,110,x,-.3,20))
    # Both halves stay on the roof plate and preserve the aerial slot at the rear.
    if style=='bellagio-inspired':
        for sx in (-57,57):
            add(shell(89,58,28,sx,39,135.3))
            for zz,ww,dd in ((138,91,60),(159,93,62),(162,95,64)):
                add(B(ww,dd,2.5,sx,39,zz),trim)
            add(hip(94,63,74,43,14,sx,39,164),accent)
            for dx in range(-36,37,12):
                # Flat-backed circular arch crown with stout jambs.
                x=sx+dx
                add(B(7,2.5,13,x,9.3,143),accent)
                ring=cq.Workplane('XZ').center(x,156).circle(4.5).circle(2.7).extrude(2.4).translate((0,10.6,0))
                add(ring.intersect(B(10,6,6,x,10,156)),trim)
                for off in (-4.1,4.1):add(B(1.8,2.6,14,x+off,9.4,142),trim)
            for dx in range(-42,43,6):add(B(2.4,3.2,2.8,sx+dx,7.7,159),gold)
    elif style=='venetian-inspired':
        for sx in (-61,61):
            add(shell(78,56,25,sx,37,135.3))
            add(B(82,60,3,sx,37,159),trim)
            for dx in range(-32,33,8):
                add(B(2.4,3.5,18,sx+dx,8.8,139),trim)
                diamond=B(5,2.6,5,sx+dx,8.5,153).rotate((sx+dx,8.5,155.5),(sx+dx,9.5,155.5),45)
                add(diamond,accent)
            for dx in range(-34,35,7):add(B(3,4,4,sx+dx,7.5,162),gold)
        add(shell(26,28,51,-56,38,161),accent)
        for dx in (-12,12):add(B(2.6,30,51,-56+dx,38,161),trim)
        add(B(32,34,3,-56,38,209),trim)
        add(shell(25,27,8,-56,38,212),stone)
        add(hip(31,33,3,3,10,-56,38,220),gold)
    elif style=='caesars-inspired':
        for sx in (-57,57):
            add(shell(88,54,30,sx,38,135.3))
            for dx in (-36,-24,-12,0,12,24,36):
                add(C(3.2,26,sx+dx,10.6,138),trim)
                for zz in (137,161):add(B(8,7,2.8,sx+dx,11,zz),gold)
            for z,w,d in ((164,94,59),(167,98,62)):add(B(w,d,3,sx,38,z),trim)
            add(prism_triangle(98,20,59,sx,67.5,170),trim)
            add(prism_triangle(76,12,1.8,sx,8.7,172),accent)
            for dx in range(-42,43,6):add(B(2.5,4,2.6,sx+dx,7.4,165),gold)
    elif style=='paris-inspired':
        for sx in (-66,66):
            add(shell(67,55,22,sx,37,135.3))
            add(B(71,59,3,sx,37,156),trim)
            add(hip(70,58,48,37,22,sx,37,159),accent)
            add(B(49,38,2.8,sx,37,180),trim)
            for dx in (-24,-12,0,12,24):
                add(B(7,5,9,sx+dx,12,160),trim)
                add(B(3,2.5,5,sx+dx,9.7,162),gold)
                add(prism_triangle(10,5,5,sx+dx,14.5,169),trim)
        # Two thick lattice faces, cross-braced through depth at the platforms.
        # Broad legs meet the plate; all braces meet the legs or platforms.
        for y in (24,42):
            for sign in (-1,1):add(bar_between(sign*24,135.3,sign*4,217,4,4,y),accent)
            for z,w in ((155,39),(178,28),(198,18),(216,12)):add(B(w,22,3,0,33,z),gold)
            for z0,z1,w0,w1 in ((137,155,22,18.5),(158,178,18,13),(181,198,12.5,8),(201,216,7,4)):
                add(bar_between(-w0,z0,w1,z1,2.8,3.6,y),accent)
                add(bar_between(w0,z0,-w1,z1,2.8,3.6,y),accent)
        add(B(6,20,11,0,33,216),gold)
    elif style=='excalibur-inspired':
        for sx in (-62,62):
            add(shell(73,51,24,sx,39,135.3))
            add(B(77,55,3,sx,39,157),trim)
            for dx in range(-32,33,8):add(B(4.5,5,6,sx+dx,13,160),stone)
            for y in (24,58):
                x=sx+(-20 if y==24 else 20)
                add(C(13,34,x,y,135.3).cut(C(10.2,31,x,y,135.2)))
                for z in (143,154,165):add(C(13.6,2.4,x,y,z),trim)
                capcolor=accent if y==24 else trim
                add(cone(16,30,x,y,169),capcolor)
                for z,rr in ((175,13.3),(182,10.1),(189,6.9)):
                    add(C(rr+.45,1.5,x,y,z),gold)
                for dx in (-5,5):add(B(2.5,2.5,9,x+dx,y-12.5,151),gold)
    else:
        for sx in (-59,59):
            for i,dx in enumerate((-29,0,29)):
                h=(38,72,50)[i] if sx<0 else (53,40,83)[i]
                x=sx+dx; d=43+(i%2)*12
                add(shell(27,d,h,x,37,135.3))
                for dz,w in ((h-12,24),(h-5,20),(h,14)):
                    add(B(w,d-5,5,x,37,135.3+dz),accent)
                add(B(7,d-10,6,x,37,140.3+h),gold)
                for dx2 in (-10,-5,0,5,10):
                    add(B(1.6,2.8,h-6,x+dx2,37-d/2-.3,138),trim)
                for zz in range(141,int(130+h),7):
                    for dx2 in (-7.5,-2.5,2.5,7.5):add(B(2.8,1.8,3.8,x+dx2,37-d/2-.25,zz),accent)
    # Loggia window grids repeat on exposed roof facades (hundreds of physical details).
    # Restrict to the actual low podium for each style, leaving tall silhouettes legible.
    for sx in (-60,60):
        for dx in range(-24,25,8):
            for z in (140,148):
                # Side relief uses the forward surface of the podium only where it exists.
                y={'bellagio-inspired':10,'venetian-inspired':9,'caesars-inspired':11,'paris-inspired':9.5,'excalibur-inspired':13.5,'newyork-newyork-inspired':15.5}[style]
                # Skyline fronts differ by building; already have dedicated full-height grid.
                if style!='newyork-newyork-inspired':add(B(4.2,2,5,sx+dx,y,z),accent)
    cutters=compound(keepouts())
    # Trim color masks too, so no exporter can accidentally refill critical openings.
    roof_regions=[]; roof_items=[]
    for col,items in groups.items():
        if items:
            clipped=fuse(items[0],items[1:]).cut(cutters)
            roof_items.extend(items)
            roof_regions.append({'name':name+' '+col,'shape':clipped,'color':col})
    roof=fuse(roof_base,[r['shape'] for r in roof_regions]).clean()
    # Leave the primary material as the exporter's implicit remainder. This
    # avoids an OCC same-domain cleanup failure on intersecting turret shells.
    if style=='excalibur-inspired':roof_regions=[r for r in roof_regions if r['color']!=stone]
    body_items=[p.intersect(B(224,220,132,0,0,0)) for items in bodygroups.values() for p in items]
    body=fuse(body_base,body_items)
    body_regions=[{'name':'Reservoir facade '+col,'shape':compound(items),'color':col} for col,items in bodygroups.items() if items]
    return {'roof':roof,'body':body,'roof_regions':roof_regions,'body_regions':[],'body_color':stone,'roof_color':stone,
            'detail_features':['Fused reservoir window surrounds and cornice courses','Integral hollow architectural roof masses with >=2.4 mm walls','Protected antenna and four latch clearances','Supports recommended below cornices, pediments, lattice crossbars and turret caps; keep support away from latch sockets'],
            'name':name,'description':desc+' Original inspired architecture; not a licensed replica.','colors':list(dict.fromkeys((stone,accent,trim,gold)))}

def smoke_test():
    import time
    roof=B(224,116,3.2,0,40,132.4).cut(compound(keepouts()))
    body=fuse(B(216,204,16,0,0,0),[B(44,82,116,x,40,16) for x in (-70,70)])
    for style in STYLE_IDS:
        t=time.time(); out=hotel_style(style,roof,body)
        for key in ('roof','body'):
            shape=out[key].val(); bb=shape.BoundingBox()
            assert shape.isValid(),(style,key,'invalid')
            assert len(shape.Solids())==1,(style,key,'disconnected',len(shape.Solids()))
            assert bb.xlen<=224.01,(style,key,'width',bb.xlen)
            assert bb.zmax<=230.01,(style,key,'height',bb.zmax)
        assert out['roof'].intersect(compound(keepouts())).val().Volume()<.001
        print(style,'valid single solids',round(time.time()-t,1),'seconds',flush=True)
if __name__=='__main__':smoke_test()
