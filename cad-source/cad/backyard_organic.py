"""Three independent R7 organic camera-feeder CAD architectures. Millimetres."""
from pathlib import Path
import argparse,json,math,os
import cadquery as cq
from common import box as B, export_design, ROOT
from backyard_camera import camera_grip,profile,place,hardware_envelope

BIRDFY='birdfy-cam-2k'; WYZE='wyze-battery-cam-pro'
GREEN='#58684B'; CLAY='#B59C73'; STONE='#AAA69B'; BARK='#77654B'

def ellipse(rx,ry,h,z=0,cx=0,cy=0):return cq.Workplane('XY').ellipse(rx,ry).extrude(h).translate((cx,cy,z))
def rod(a,b,r):
 v=cq.Vector(*b)-cq.Vector(*a)
 return cq.Workplane('XY').add(cq.Solid.makeCylinder(r,v.Length,cq.Vector(*a),v.normalized()))
def keyholes(s,x,z,y):
 # Rear-entry screw heads slide down into 4.8 mm shank necks.
 for zz in z:
  hole=cq.Workplane('XZ').center(x,zz).circle(4.6).extrude(20).translate((0,y+10,0))
  neck=B(4.8,20,10,x,y,zz)
  s=s.cut(hole.union(neck))
 return s

def scoop(rx,ry,base,cy,clipx,clipy,detail=True):
 s=ellipse(rx,ry,3.2,base,cy=cy).union(ellipse(rx,ry,21,base+2.9,cy=cy).cut(ellipse(rx-3,ry-3,24,base+3.0,cy=cy)))
 # Two independent free-standing inward-release snap tongues.
 for sign in [-1,1]:
  s=s.union(B(10,8,3.2,sign*(clipx-4),clipy,base))
  s=s.union(B(1.6,6,21,sign*clipx,clipy,base+2.8))
  s=s.union(B(3.8,6,2.0,sign*(clipx+1.1),clipy,base+18.4))
  s=s.union(B(3.2,10,2.0,sign*(clipx-.8),clipy,base+22.0))
 if detail:
  for x,y in [(-35,cy-8),(0,cy-20),(35,cy-8),(-20,cy+17),(20,cy+17)]:
   s=s.cut(cq.Workplane('XY').center(x,y).slot2D(10,1.4).extrude(6).translate((0,0,base-1)))
 return s.clean()

def receivers(s,base,clipx,clipy):
 for sign in [-1,1]:
  receiver=B(3.6,12,26,sign*(clipx+3.8),clipy,base-2)
  receiver=receiver.cut(B(10,8,4.0,sign*(clipx+3.8),clipy,base+18.0))
  s=s.union(receiver)
 return s

def fern(detail=True):
 # Extruded organic pointed silhouette; the depth curve is in the scoop/veins.
 outline=[(0,0),(-38,14),(-66,54),(-74,111),(-59,169),(-30,214),(0,238),(29,211),(58,168),(73,107),(62,49),(35,13)]
 leaf=cq.Workplane('XZ').spline(outline+[outline[0]],periodic=False).close().extrude(6).translate((0,100,0))
 # XZ normal faces -Y: outer back is Y100, front is Y94.
 body=leaf.union(ellipse(83,53,4,5,cy=-35))
 body=body.union(rod((-46,94,60),(-57,-10,7),7)).union(rod((46,94,60),(57,-10,7),7)).union(B(70,90,4,0,55,5))
 pose={'translation':[0,25,55],'rotation':[20,0,0]}
 body=body.union(place(B(64,70,5,0,30,-8.2),pose)).union(place(camera_grip(BIRDFY),pose))
 body=body.union(B(64,16,7,0,94,69))
 body=body.cut(ellipse(71,44,26,9.1,cy=-35))
 body=receivers(body,9.4,74,-35)
 if detail:
  # Molded raised midrib and paired oblique veins, all embedded in leaf skin.
  body=body.union(rod((0,93.8,14),(0,93.8,223),1.9))
  for z,width in [(40,43),(69,58),(103,62),(137,52),(170,36),(195,22)]:
   for sign in [-1,1]:body=body.union(rod((0,93.8,z),(sign*width,93.8,z+20),1.1))
 body=keyholes(body,0,[35,185],98)
 for x,y in [(-35,-43),(0,-55),(35,-43),(-20,-18),(20,-18)]:body=body.cut(cq.Workplane('XY').center(x,y).circle(1.6).extrude(18).translate((0,0,-1)))
 bowl=scoop(70,43,9.4,-35,74,-35,detail)
 return [dict(name='Veined leaf wall cradle',shape=body.clean(),color=GREEN,print_rotation=[0,0,0],support='Print upright (238.01 mm tall) with organic supports beneath the projecting scoop shelf, diagonal brace ends and tilted camera seat.',purpose='Wall load path, camera seat and basket receivers'),dict(name='Releasable fern seed scoop',shape=bowl,color=CLAY,explode=[0,-30,45],support='None on bowl floor; local support beneath latch noses.',purpose='Open seed basket with five 1.4 mm drain slots')],pose,[0,-77,33.3],{'type':'wall','position':[0,101,110],'description':'Two rear keyholes on the leaf midrib attach to a vertical wall or broad timber post. Use spacers if needed to avoid crushing the leaf contour.','hardware':['Two corrosion-resistant 4 mm screws with 8–9 mm heads and suitable wall anchors; choose length for substrate.']}

def pebble(detail=True):
 # True doubly-curved ellipsoidal shell, cropped at its bottom for a steady foot.
 def egg(rx,ry,rz):
  zs=[-1,12,36,60,84,108,132,72+rz-9,72+rz-.2]
  wp=cq.Workplane('XY');prev=0
  for z in sorted(set(zs)):
   f=math.sqrt(max(.0001,1-((z-72)/rz)**2))
   wp=wp.workplane(offset=z-prev).ellipse(rx*f,ry*f);prev=z
  return wp.loft(combine=True)
 outer=egg(107,78,90).cut(B(400,400,100,0,0,-100))
 inner=egg(103,74,86)
 mouth=cq.Workplane('XZ').center(0,79).ellipse(96,71).extrude(116).translate((0,12,0))
 body=outer.cut(inner).cut(mouth)
 body=body.union(ellipse(82,56,5,7.0,cy=-15)).union(ellipse(65,47,8,0,cy=0))
 for sign in [-1,1]:body=body.union(B(12,22,5,sign*75,-34,7))
 body=receivers(body,12.4,74,-40)
 pose={'translation':[0,10,27.5],'rotation':[0,0,0]}
 shelf=B(72,60,5,0,38,19.3).intersect(outer)
 body=body.union(shelf).union(place(camera_grip(WYZE),pose))
 eye=cq.Workplane('XZ').center(0,166).circle(12).extrude(10).translate((0,23,0))
 eyehole=cq.Workplane('XZ').center(0,166).circle(6.5).extrude(50).translate((0,43,0))
 body=body.union(eye).cut(eyehole)
 if detail:
  # Shallow pebble dimples follow the true double curvature; 0.55 mm depth.
  for sign in [-1,1]:
   for y,z,r in [(4,42,4.5),(14,70,5.5),(-1,103,3.5),(30,125,4.3),(43,48,3.2),(47,87,4.5)]:
    xx=sign*(107*math.sqrt(max(.1,1-(y/78)**2-((z-72)/90)**2))+r-.55)
    body=body.cut(cq.Workplane('XY').sphere(r).translate((xx,y,z)))
 for x,y in [(-35,-48),(0,-60),(35,-48),(-20,-23),(20,-23)]:body=body.cut(cq.Workplane('XY').center(x,y).circle(1.6).extrude(18).translate((0,0,-1)))
 body=body.cut(ellipse(71,44,27,12.1,cy=-40))
 for sign in [-1,1]:
  body=body.cut(B(10.8,14.0,27,sign*70,-40,12.1))
  body=body.cut(B(10,8,4,sign*77.8,-40,30.4))
 bowl=scoop(70,43,12.4,-40,74,-40,detail)
 return [dict(name='Ellipsoidal pebble shell and suspension eye',shape=body.clean(),color=STONE,support='Organic supports inside the mouth, under the curved shell and camera shelf; print rear side down with the suspension eye in the bed plane.',print_rotation=[90,0,0],purpose='Rounded shelter, integral load-bearing cord eye, camera recess and snap receivers'),dict(name='Lift-out pebble seed bowl',shape=bowl,color=CLAY,explode=[0,-35,45],support='None on bowl floor; local support under latch noses.',purpose='Removable drained seed bowl')],pose,[0,-82,36.3],{'type':'hanging','position':[0,18,166],'description':'A single integral eye carries the rigid shell and positively snapped seed bowl. Pass outdoor cord through the 13 mm eye; cord never retains the bowl. Balance and proof-load outdoors at low height before use.','hardware':['Outdoor-rated braided cord, approximately 3 mm diameter, with a secure closed suspension knot.']}

def drift(detail=True):
 # Thin elliptical open deck; forked structure carries loads to a narrow rear spine.
 body=ellipse(110,72,5,80)
 body=body.union(ellipse(110,72,5,84.5).cut(ellipse(106.5,68.5,6,84.4)))
 body=body.union(B(28,9,103,0,88,0))
 for a,b,r in [((0,86,7),(0,-25,81),8),((0,86,39),(-68,12,81),7),((0,86,39),(68,12,81),7),((0,86,76),(0,55,82),7)]:body=body.union(rod(a,b,r))
 # Asymmetric wing lies over the left rear only; it leaves the tall camera sky clear.
 body=body.union(rod((-68,40,83),(-71,45,139),5)).union(rod((-71,45,127),(-36,42,143),4))
 wing=ellipse(47,37,4,142,cx=-63,cy=33).rotate((-63,33,142),(-62,33,142),-8)
 body=body.union(wing)
 pose={'translation':[52,17,101],'rotation':[0,0,-50]}
 body=body.union(place(camera_grip(BIRDFY),pose))
 camera_branches=rod((65,48,83),(74,41,98),9).union(rod((42,22,84),(43,33,98),7)).cut(B(400,400,100,0,0,98.3))
 body=body.union(camera_branches)
 # Removable smaller seed dish occupies left-front deck, clear of the camera base.
 cx=-20;cy=-22;base=85.4
 bowl=ellipse(62,36,3.2,base,cx=cx,cy=cy).union(ellipse(62,36,11,base+2.9,cx=cx,cy=cy).cut(ellipse(59,33,13,base+3,cx=cx,cy=cy)))
 # Front-facing vertical tongue releases are accessible from the open landing edge.
 for xx in [-52,12]:
  beam=B(7,1.6,20,xx,-58,base+2.8);hook=B(7,3.8,2,xx,-59.1,base+16.4)
  bowl=bowl.union(B(9,9,3.2,xx,-55,base)).union(beam).union(hook).union(B(10,3,2,xx,-57.2,base+20.0))
  receiver=B(12,3.6,23,xx,-61.8,base-2).cut(B(8,10,4,xx,-61.8,base+16))
  body=body.union(receiver)
 if detail:
  for x,y in [(-50,-25),(-20,-38),(10,-25),(-20,-8)]:bowl=bowl.cut(cq.Workplane('XY').center(x,y).slot2D(12,1.4).extrude(6).translate((0,0,base-1)))
  # Swept wing grain: shallow, slightly splayed reeds in one molded surface.
  for i in range(-3,4):
   groove=cq.Workplane('XY').center(-63+i*9,33).slot2D(47-abs(i)*5,1.0,90+i*2).extrude(1.0).translate((0,0,145.3)).rotate((-63,33,142),(-62,33,142),-8)
   body=body.cut(groove)
  # Bark channels on the exposed branch surfaces are shallow longitudinal cuts.
  for a,b,r in [((1,78,8),(1,-31,78),1.0),((-4,80,43),(-70,6,78),.9),((4,80,43),(70,6,78),.9)]:body=body.cut(rod(a,b,r))
 body=body.cut(ellipse(63,37,25,85.1,cx=-20,cy=-22))
 for xx in [-52,12]:body=body.cut(B(10,10,25,xx,-55,85.1))
 for x,y in [(-50,-25),(-20,-38),(10,-25),(-20,-8)]:body=body.cut(cq.Workplane('XY').center(x,y).circle(1.6).extrude(19).translate((0,0,69)))
 body=keyholes(body,0,[14,78],89)
 return [dict(name='Branch-supported drift deck and wing',shape=body.clean(),color=BARK,print_rotation=[0,0,12],support='Organic supports under elevated elliptical deck, branch junctions, camera seat and swept wing; retain upright assembly orientation.',purpose='Open landing platform, forked wall bracket, lateral camera and small left weather wing'),dict(name='Front-release shallow seed dish',shape=bowl.clean(),color=CLAY,explode=[0,-25,45],support='None under dish floor; local support under snap noses.',purpose='Removable open feed dish with four 1.4 mm drain slots')],pose,[-20,-57,99.3],{'type':'wall','position':[0,93,49],'description':'Two rear-spine keyholes fasten the forked cradle to a broad wooden post or wall; the wall carries deck and camera cantilever loads.','hardware':['Two corrosion-resistant 4 mm screws with 8–9 mm heads, suitable anchors or pilot holes.']}

DESIGNS={
 'fern-wall-pocket':(fern,'Fern Wall Pocket',BIRDFY,'An upright veined leaf cradles a removable seed scoop beneath a sky-clear camera.',{'form':'Pointed upright leaf with a projecting crescent scoop','seed_system':'Open removable oval basket; direct top refill and five drain slots','camera_integration':'Camera sits above the scoop on a mid-leaf seat; the entire tall antenna envelope is open above','signature':'Raised central midrib, six paired veins and pointed leaf contour'}),
 'pebble-pod':(pebble,'Pebble Pod',WYZE,'A rounded side-on oval cave shelters an open seed bowl and recessed camera.',{'form':'Doubly curved ellipsoidal shell with one broad front mouth and a top suspension eye','seed_system':'Removable oval bowl inside shelter; directly accessible through mouth','camera_integration':'Recessed rear shelf faces across the bowl through the open mouth','signature':'Continuous ellipsoidal shell, shallow curvature-following dimples and an integral suspension eye'}),
 'drift-platform':(drift,'Drift Platform',BIRDFY,'A broad open elliptical deck rests on forked branches under a small offset weather wing.',{'form':'Open elliptical platform on a branching wall cradle','seed_system':'Shallow front-release dish with direct top access; no hopper','camera_integration':'Camera is on the right of the deck, aimed diagonally across the landing area; full antenna envelope is uncovered','signature':'Three structural branch paths, an asymmetric small swept wing and molded grain channels'})}

def build(slug,blockout=False):
 fn,name,cam,description,architecture=DESIGNS[slug]
 parts,pose,target,mount=fn(not blockout)
 if blockout:
  out=Path(os.environ.get('NESTFORGE_BLOCKOUTS',str(ROOT.parent/'blockouts')))/slug;out.mkdir(parents=True,exist_ok=True)
  data={'id':slug,'parts':[]}
  for i,p in enumerate(parts):
   file=f'{i+1:02d}.stl';cq.exporters.export(p['shape'],str(out/file),tolerance=.15,angularTolerance=.15);data['parts'].append({'file':file,'color':p['color']})
  (out/'design.json').write_text(json.dumps(data));from render_catalog import render_design;render_design(out/'design.json');return
 notes=['Digital ASA prototype: no physical print, snap-cycle, wind/load, camera-fit or focus testing has been performed.','Remove camera before washing feeder or charging/service. All lens, PIR and IR features face the open feeding area.','Camera pressure noses deliberately intrude 0.25 mm per side into the nominal envelope. Verify actual housing, release travel and focus before outdoor use.','Use small portions of dry seed and empty/clean regularly; drain slots do not make seed weatherproof.']
 if cam==WYZE:notes.append('Wyze official close-up lens is required; accessory dimensions and exact focus are unpublished and must be tested on-device before use.')
 bowl_install='Hold both seed-dish release tabs inward, lower the dish onto its shelf with hooks aligned to the receiver windows, then release both tabs so the hooks engage. Check both hooks before filling.'
 bowl_remove='Squeeze the accessible release pads inward, then lift the empty dish out for cleaning.'
 cam_service=profile(cam)['service']+(' Lift forward and upward along the 20 degree inclined camera axis for the first 12 mm to clear the low stops; then lift away.' if slug=='fern-wall-pocket' else ' The surrounding structure leaves a vertical lift path.')+' Remove the camera before dish washing.'
 if slug=='pebble-pod':
  bowl_install='Hold both dish release pads inward and slide the empty bowl rearward onto its shelf from the front mouth. Release both pads when both hook noses align with the receiver windows; check both hooks before filling.'
  bowl_remove='Hold both dish release pads inward (nominal 1.4 mm movement), slide the empty bowl 150 mm straight forward off the shelf through the mouth, then lift away.'
  cam_service='FIRST remove the seed bowl: '+bowl_remove+' Then spread both camera pressure clips, raise the camera 4 mm to clear the low stops and withdraw it forward through the mouth before lifting fully. The roof prevents direct vertical extraction. Remove the camera for battery service, charging and dish washing.'
 result=export_design(slug,name,'Backyard camera feeders',description,parts,notes=notes,assembly=[('Pass cord through the integral eye and close securely; suspend the rigid main shell at a low height for proof-loading.' if mount['type']=='hanging' else 'Fasten the main body to the wall/post using both keyholes and substrate-appropriate screws; confirm the body cannot lift free.'),bowl_install,bowl_remove,'Spread low camera pressure clips and seat camera against the floor and low stops; confirm actual retention before adding seed.'],hanger=([0,18,166] if mount['type']=='hanging' else None),snap_joints=[{'name':'Two accessible seed-dish snap tongues','beam_thickness_mm':1.6,'free_length_mm':18.2,'hook_engagement_mm':1.0,'window_clearance_mm':.4,'service':bowl_remove,'physical_test':False}],refill='Remove camera if handling water. Refill the open dish from above. For cleaning: '+bowl_remove+' Wash and dry completely.',detail_features=[architecture['signature'],'Functional 1.4 mm drainage slots',('Integral load-bearing top cord eye' if mount['type']=='hanging' else 'Rear keyholes for a rigid wall load path'),'Bottom-supported camera with releasable low pressure clips'],revision='R7',detail_revision='R7',material='ASA',camera_system=True,camera_default=cam,camera_profiles=[cam],camera_part_index=0,camera_mount=profile(cam),camera_pose=pose,mounting=mount,feeding_target=target,camera_service=cam_service,architecture=architecture,prototype_validation={'physical_print_test':False,'snap_fit_test':False,'camera_fit_test':False,'focus_test':False,'outdoor_load_test':False},assembly_method='Two dish snap tongues; '+('one integral suspension eye' if mount['type']=='hanging' else 'a rigid screw-mounted main body')+'; releasable camera pressure seat')
 from audit_assembly import audit
 audit(ROOT/slug/'design.json')
 from sanitize_stl import run
 run(ROOT/slug)
 from render_catalog import render_design
 render_design(ROOT/slug/'design.json')
 # Camera-to-structure intersection includes only intended low retention contacts.
 env=hardware_envelope(cam,pose).val();contact=parts[0]['shape'].val().intersect(env)
 report={'camera':cam,'published_envelope_mm':profile(cam),'intersection_volume_mm3':contact.Volume(),'intersection_bounds':None if contact.Volume()<1e-6 else [getattr(contact.BoundingBox(),k) for k in ['xmin','ymin','zmin','xmax','ymax','zmax']],'interpretation':'Pressure-nose contact is intentional. Any contact outside the low camera-retention region is a design fault. Physical housing and close-focus remain untested.'}
 (ROOT/slug/'camera-design-checks.json').write_text(json.dumps(report,indent=2))
 print(json.dumps(report),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('slug',choices=DESIGNS);p.add_argument('--blockout',action='store_true');a=p.parse_args();build(a.slug,a.blockout)
