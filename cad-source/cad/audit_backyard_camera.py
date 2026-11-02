"""R7 exact published-camera proxy, staged service and explicitly assumed sight audit.

No camera solid is a manufacturing part. Nose exclusions are ONLY the actual
0.25 x 3 x 5 mm nominal interference strips, only on the nominated carrier.
Service sweeps are exact translated rectangular prisms, not sampled poses.
"""
from pathlib import Path
import argparse, hashlib, json, math, os
import cadquery as cq
from backyard_camera import profile, place, hardware_envelope
from common import box as B
ROOT=Path(os.environ.get('NESTFORGE_EXPORTS',str(Path(__file__).resolve().parents[1]/'exports')))
TOL=.05
# Explicitly documented component removal; no other assembly part is suppressed.
COVERS={'orchard-hopper':1,'woven-arch':1,'pebble-pod':1}
# Source/author-confirmed lift then local -Y withdrawal; no unspecified tipping.
FORWARD={'pebble-pod':4.,'meadow-lantern':3.5,'ridge-aframe':3.5}
REFILL={'orchard-hopper':([-43,30,150],10),'meadow-lantern':([0,0,181],10),
 'willow-screen':([0,10,210],8),'acorn-column':([0,0,180],10)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def vec(v,pose):
 x,y,z=v
 for axis,angle in enumerate(pose.get('rotation',[0,0,0])):
  a=math.radians(angle);c,s=math.cos(a),math.sin(a)
  if axis==0:y,z=c*y-s*z,s*y+c*z
  elif axis==1:x,z=c*x+s*z,-s*x+c*z
  else:x,y=c*x-s*y,s*x+c*y
 return [x,y,z]
def point(v,pose):return [a+b for a,b in zip(vec(v,pose),pose['translation'])]
def common(a,b):
 ba,bb=a.BoundingBox(),b.BoundingBox();lo=[max(getattr(ba,k+'min'),getattr(bb,k+'min')) for k in 'xyz'];hi=[min(getattr(ba,k+'max'),getattr(bb,k+'max')) for k in 'xyz']
 if min(hi[i]-lo[i] for i in range(3))<=1e-7:return None
 roi=cq.Solid.makeBox(*(hi[i]-lo[i]+.002 for i in range(3)),cq.Vector(*(v-.001 for v in lo)))
 # Keep exact geometry local to the common bounding region.
 ca=a.intersect(roi);cb=b.intersect(roi)
 if not ca.Solids() or not cb.Solids():return None
 result=ca.intersect(cb)
 if result.Solids() and not result.isValid():raise ValueError('Invalid exact BREP common')
 return result

def audit(file):
 raw=file.read_bytes();d=json.loads(raw);cam=d['camera_default'];p=profile(cam);pose=d['camera_pose'];w,depth=p['width'],p['depth'];h=p.get('height') or p['height_with_antenna'];carrier=d['camera_part_index'];slug=d['id']
 parts=[(item,cq.importers.importStep(str(file.parent/item['step'])).val()) for item in d['parts']]
 hashes={item['step']:sha(file.parent/item['step']) for item,_ in parts}
 nose=[]
 for sign in [-1,1]:nose.append(place(B(.25,3,5,sign*(w/2-.125),5.5,3),pose).val())
 def collisions(proxy,exclude=()):
  out=[]
  for i,(item,shape) in enumerate(parts):
   if i in exclude:continue
   inter=common(proxy,shape);rawv=inter.Volume() if inter else 0.;remain=inter
   if i==carrier and inter and inter.Solids():
    for n in nose:remain=remain.cut(n)
   vol=remain.Volume() if remain else 0.
   out.append(dict(part_index=i,name=item['name'],raw_intersection_mm3=round(rawv,6),permitted_nose_intersection_mm3=round(max(0,rawv-vol),6),unpermitted_intersection_mm3=round(vol,6),passed=vol<=TOL))
  return out
 env=hardware_envelope(cam,pose).val();envelope=collisions(env)
 excluded=[]
 if slug in COVERS:
  ci=COVERS[slug]
  # Author instruction is recorded verbatim; ensure cover service is actually documented.
  text=d['camera_service'].lower()
  if not ('roof' in text or 'vault' in text or (slug=='pebble-pod' and 'bowl' in text)):raise ValueError('Cover or bowl removal not documented')
  excluded=[ci]
 pre_removal_checks=[]
 if slug=='pebble-pod':
  # Relative motion identity: bowl-Y swept against camera equals the
  # camera box swept+Y against the fixed bowl, exact for translation.
  inverse_sweep=place(B(w,depth+150,h,0,(depth+150)/2,0),pose).val()
  hit=common(inverse_sweep,parts[1][1]);vol=hit.Volume() if hit else 0
  pre_removal_checks.append(dict(action='Remove seed bowl first by 150 mm forward slide through mouth with both tongues held inward',method='Exact inverse-motion camera envelope swept local +Y against stationary bowl STEP, equivalent to bowl moving world -Y; camera upright here',camera_intersection_mm3=round(vol,6),passed=vol<=TOL,scope='Bowl versus camera only; independent bowl-to-shell conservative continuous clearance is recorded by model author in seed-bowl-service.json.'))
 stages=[]
 if slug=='ridge-aframe':
  lift=9.5;travel=10.
  sweeps=[('Lift9.5mm local+Z with clips spread',B(w,depth,h+lift,0,depth/2,0)),('Withdraw10mm local-Y into triangular center',B(w,depth+travel,h,0,(depth-travel)/2,lift)),('Translate150mm local+X (world-Y) out front of triangle',B(w+150,depth,h,75,depth/2-travel,lift))]
 elif slug in FORWARD:
  lift=FORWARD[slug]
  sweeps=[('Lift locally with pressure clips spread',B(w,depth,h+lift,0,depth/2,0)),('Withdraw 200 mm along camera local -Y with pressure clips spread',B(w,depth+200,h,0,(depth-200)/2,lift))]
 else:
  sweeps=[('Lift 300 mm along camera local +Z with pressure clips spread',B(w,depth,h+300,0,depth/2,0))]
 for label,shape in sweeps:stages.append(dict(action=label,method='Exact continuous translational swept published rectangular envelope',collisions=collisions(place(shape,pose).val(),excluded)))
 # Test final position independently; floor is beyond the feeder, or displaced forward.
 final_local=([150,-10,9.5] if slug=='ridge-aframe' else [0,-200,FORWARD[slug]]) if slug in FORWARD else [0,0,300]
 final=place(B(w,depth,h,0,depth/2,0).translate(final_local),pose).val()
 stages.append(dict(action='Final removed-camera position',method='Exact BREP common',collisions=collisions(final,excluded)))
 # A representative 1mm diameter horizontal/forward corridor, NOT a sensor datum.
 target=d['feeding_target'];delta=[target[i]-pose['translation'][i] for i in range(3)];horizontal=math.hypot(delta[0],delta[1]);forward=vec([0,-1,0],pose);fh=math.hypot(*forward[:2]);bearing=math.degrees(math.acos(max(-1,min(1,(forward[0]*delta[0]+forward[1]*delta[1])/(max(horizontal*fh,1e-9))))))
 start=point([0,-.01,30],pose);axis=cq.Vector(*forward);line=cq.Solid.makeCylinder(.5,max(horizontal,1),cq.Vector(*start),axis)
 sight=[]
 for i,(item,shape) in enumerate(parts):
  hit=common(line,shape);volume=hit.Volume() if hit else 0
  sight.append(dict(part_index=i,name=item['name'],intersection_mm3=round(volume,6),unobstructed=volume<=TOL))
 assumed_heights=[round(.4*h,3),round(.7*h,3),round(.8*h,3)] if p.get('height') else [30.,60.,90.]
 views=[]
 for sensor in assumed_heights:
  origin=point([0,0,sensor],pose);up=vec([0,0,1],pose);right=vec([1,0,0],pose)
  for head in [25.,30.,45.]:
   bird=[target[0],target[1],target[2]+head];v=[bird[i]-origin[i] for i in range(3)];norm=math.sqrt(sum(x*x for x in v));off=math.degrees(math.acos(max(-1,min(1,sum(v[i]*forward[i] for i in range(3))/norm))))
   views.append(dict(assumed_sensor_height_local_mm=sensor,assumed_bird_head_above_target_mm=head,required_world_down_pitch_deg=round(math.degrees(math.atan2(-v[2],math.hypot(*v[:2]))),3),axis_off_angle_deg=round(off,3),vertical_axis_error_deg=round(math.degrees(math.atan2(sum(v[i]*up[i] for i in range(3)),sum(v[i]*forward[i] for i in range(3)))),3),horizontal_axis_error_deg=round(math.degrees(math.atan2(sum(v[i]*right[i] for i in range(3)),sum(v[i]*forward[i] for i in range(3)))),3)))
 # Direct representative ray to an assumed bird head gives a more useful
 # occlusion check than a horizontal-axis line when feed is lower than camera.
 ray_start=point([0,-.01,assumed_heights[1]],pose)
 ray_end=[target[0],target[1],target[2]+30.]
 rv=[ray_end[i]-ray_start[i] for i in range(3)];length=math.sqrt(sum(x*x for x in rv))
 target_ray=cq.Solid.makeCylinder(.5,length,cq.Vector(*ray_start),cq.Vector(*(x/length for x in rv)))
 target_sight=[]
 for i,(item,shape) in enumerate(parts):
  hit=common(target_ray,shape);volume=hit.Volume() if hit else 0
  target_sight.append(dict(part_index=i,name=item['name'],intersection_mm3=round(volume,6),unobstructed=volume<=TOL))
 optical_warnings=[]
 if any(not x['unobstructed'] for x in target_sight):optical_warnings.append('Exact1mm-diameter ray from assumed sensor height to assumed birdhead30mm above feeding target intersects printed geometry; review framing/placement.')
 nominal=next(v for v in views if v['assumed_sensor_height_local_mm']==assumed_heights[1] and v['assumed_bird_head_above_target_mm']==30)
 if p.get('height') and abs(nominal['vertical_axis_error_deg'])>28:optical_warnings.append('Illustrative central head target exceeds nominal28degree vertical half-field. Wyze published56degree vertical FOV is a baseline only; close-up accessory may change it and sensor height is assumed.')
 if not p.get('height') and nominal['axis_off_angle_deg']>35:optical_warnings.append('Illustrative central head target lies over35degrees off nominal camera axis; adjust placement or verify actual framing. Birdfy35degree review threshold is an engineering screen, not a published optical field.')
 if bearing>45:optical_warnings.append('Feeding target horizontal bearing is more45degrees off camera front; review yaw.')
 if slug in REFILL:refill_point,radius=REFILL[slug];basis='Source-confirmed open reservoir aperture after removing its cover'
 else:refill_point,radius=target,10;basis='Representative 20mm-diameter vertical pour corridor above feeding target, with camera removed first if instructions require; only camera occlusion tested'
 refill=cq.Solid.makeCylinder(radius,600,cq.Vector(*refill_point));hit=common(refill,env);refillvol=hit.Volume() if hit else 0
 bottle_check=None
 if slug=='bottle-bough':
  bottle_sweep=cq.Solid.makeCylinder(34,505,cq.Vector(0,0,49));hit=common(bottle_sweep,env);vol=hit.Volume() if hit else 0
  bottle_check=dict(method='Conservative68mm-diameter cylinder containing nominal205mm bottle, swept300mm upward from neckopeningZ49',camera_intersection_mm3=round(vol,6),unobstructed=vol<=TOL,status='Nominal hardware only; actual measured bottle shoulder, support bead, straps and handling unvalidated')
 geometry_pass=all(x['passed'] for x in pre_removal_checks) and all(x['passed'] for x in envelope) and all(x['passed'] for st in stages for x in st['collisions'])
 result=dict(id=slug,camera_id=cam,method='Exact STEP BREP intersections against published conservative box and exact continuous staged translation sweeps',interference_tolerance_mm3=TOL,design_json_sha256=hashlib.sha256(raw).hexdigest(),step_sha256=hashes,auditor_sha256=sha(Path(__file__)),camera_helper_sha256=sha(Path(__file__).with_name('backyard_camera.py')),published_proxy=dict(width_mm=w,depth_mm=depth,height_mm=h,source=p['source'],birdfy_body_height_unknown=not bool(p.get('height')),pose=pose,pose_order='X then Y then Z rotation, then translation'),allowed_contact=dict(carrier_part_index=carrier,local_regions=[dict(x=[-w/2,-w/2+.25],y=[4,7],z=[3,8]),dict(x=[w/2-.25,w/2],y=[4,7],z=[3,8])],reason='Actual defined pressure-nose nominal .25mm-per-side interference; only these exact strips subtracted from carrier intersections.'),envelope_clearance=envelope,camera_service=dict(documented_instructions=d['camera_service'],removed_parts=[dict(index=i,name=d['parts'][i]['name']) for i in excluded],excluded_parts_basis='Explicit roof/vault/bowl removal in camera_service; no other printed part excluded',pre_removal_checks=pre_removal_checks,stages=stages,pressure_release='Both low pressure flexures held spread. Digital fixed nose strips omitted; required finger access, actual deflection force and thermal retention untested.',battery_access='Camera must be entirely removed for battery/USB-C service; real cover/port geometry unpublished and not modeled.'),sight=dict(method='Exact BREP 1mm diameter representative local forward ray from arbitrary local front point[0,-0.01,30], length equal to horizontal feeding-target standoff. No actual optical datum, field of view or focus is implied.',feeding_target_is_feet_position=target,horizontal_standoff_mm=round(horizontal,3),horizontal_bearing_error_deg=round(bearing,3),representative_forward_corridor=sight,assumed_bird_head_sight=dict(sensor_height_local_mm=assumed_heights[1],bird_head_above_target_mm=30,start_mm=ray_start,end_mm=ray_end,collisions=target_sight,status='Assumed datum only; exact occlusion of this representative ray does not establish real optical framing'),assumed_framing=views,nominal_fov_reference=dict(vertical_deg=56,horizontal_deg=108,source='https://www.wyze.com/products/wyze-battery-cam-pro',status='Published stock Wyze FOV; unknown with required close-up accessory') if p.get('height') else None,warnings=optical_warnings,physical_focus='UNKNOWN',accessory_clearance='Wyze close-up lens envelope and optical specification unknown; must verify actual device' if p.get('height') else 'Birdfy body/sensor/antenna positions unknown; all230mm reserved'),nominal_bottle_removal_camera_avoidance=bottle_check,seed_refill_camera_avoidance=dict(documented_refill_instructions=d['refill'],corridor_start_mm=refill_point,radius_mm=radius,height_mm=600,basis=basis,camera_intersection_mm3=round(refillvol,6),unobstructed=refillvol<=TOL,scope='Camera avoidance only; hand/pour-tool ergonomics and seed flow are untested'),digital_geometry_passed=geometry_pass,optical_review_required=bool(optical_warnings),passed=geometry_pass and not optical_warnings,passed_scope='Digital published rectangular-envelope and defined service-path clearance plus absence of flags under explicitly stated representative optical assumptions. Not physical camera fit, lens/accessory clearance, framing or focus certification.',physical_fit_validated=False,physical_print_test=False,focus_validated=False)
 # Reject results if files changed while the BREP work was running.
 if file.read_bytes()!=raw or any(sha(file.parent/n)!=v for n,v in hashes.items()):raise RuntimeError('Input changed during audit; rerun')
 (file.parent/'camera-clearance.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(id=slug,digital_geometry_passed=geometry_pass,optical_review_required=bool(optical_warnings),envelope=[(x['name'],x['unpermitted_intersection_mm3']) for x in envelope],service=[(st['action'],[(x['name'],x['unpermitted_intersection_mm3']) for x in st['collisions']]) for st in stages],sight=sight,refill_volume=refillvol)),flush=True)
 return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--only',nargs='+');ap.add_argument('--changed-only',action='store_true');args=ap.parse_args()
 for file in sorted(ROOT.glob('*/design.json')):
  if args.only and file.parent.name not in args.only:continue
  d=json.loads(file.read_text())
  if d.get('revision')!='R7':continue
  oldfile=file.parent/'camera-clearance.json'
  if args.changed_only and oldfile.exists():
   old=json.loads(oldfile.read_text())
   if old.get('auditor_sha256')==sha(Path(__file__)) and old.get('camera_helper_sha256')==sha(Path(__file__).with_name('backyard_camera.py')) and old.get('design_json_sha256')==sha(file) and all(sha(file.parent/n)==v for n,v in old.get('step_sha256',{}).items()):print('UNCHANGED',file.parent.name,flush=True);continue
  try:audit(file)
  except Exception as e:print('AUDIT ERROR',file.parent.name,repr(e),flush=True);raise
if __name__=='__main__':main()
