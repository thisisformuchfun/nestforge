"""NestForge R6 Vegas camera feeders. Original parametric architecture, mm Z up.

Three printed parts in the default build: drained twin reservoir body, architectural
snap roof, and one replaceable camera sled. Camera envelopes are manufacturer
dimensions, not metrology. Physical fit, focus, latch fatigue and hanging loads
must be verified before outdoor use. No electronics are represented as printable.
"""
from pathlib import Path
import argparse, json, math, os, sys
import cadquery as cq
from common import box as B, cyl as C, export_design, ROOT, solid, _bounds
import vegas_arch_a as a
import vegas_arch_b as b

STYLES=list(a.STYLE_IDS)+list(b.STYLE_IDS)

def union(parts):
 return cq.Workplane('XY').add(parts[0].val().fuse(*[p.val() for p in parts[1:]]).clean())

def body():
 # One washable body: the reservoirs and drains are not separate accessories.
 floor=B(216,204,3.2).edges('|Z').fillet(6)
 rim=B(216,204,10,0,0,3.2).edges('|Z').fillet(6).cut(B(209.6,197.6,11,0,0,3.1).edges('|Z').fillet(3))
 pieces=[floor,rim]
 for x in (-70,70):
  reservoir=B(44,82,128.8,x,40,3.2).cut(B(39.2,77.2,128,x,40,5.6))
  # 12 x 9 mm feed mouth, curved relief is architectural, never a clear panel.
  reservoir=reservoir.cut(B(26,8,10,x,0,5.6))
  # Fine through mesh on outside faces; 1.4 mm openings, 2.4 mm ribs.
  cutters=[]
  for yy in (17,25,33,41,49,57,65):
   for zz in (34,46,58,70,82,94,106):
    cutters.append(B(5,1.4,8,x+(22 if x>0 else -22),yy,zz))
  reservoir=reservoir.cut(cq.Compound.makeCompound([p.val() for p in cutters]))
  # Gravity ramps converge on the mouth, all surfaces accessible from above.
  ramp=cq.Workplane('YZ').polyline([(2.5,5.5),(78,5.5),(78,30),(2.5,7)]).close().extrude(19.5,both=True).translate((x,0,0))
  pieces.extend([reservoir,ramp])
 # Solid front perch lip, shallow grip grooves, unobstructed camera view.
 perch=B(156,8,7,0,-96,10).edges('|Y').fillet(1.4)
 for x in range(-70,71,10):perch=perch.cut(B(1.2,9,.8,x,-96,16.5))
 pieces.append(perch)
 # Side rails capture the flat camera sled without any camera screws.
 for sg in (-1,1):
  pieces.append(B(5.6,82,38.4,sg*44.4,61,3.2))
  pieces.append(B(5.6,82,2.0,sg*44.4,61,41.6))
  pieces.append(B(5.0,82,2.0,sg*40.3,61,35.6))
  pieces.append(B(4,3,8,sg*40,19.9,35.6))
 # Rear latch keeper is below the slide floor, fully open to thumb access.
 pieces.append(B(94.4,3.6,33.8,0,100.2,3.2))
 # Four long upward roof latches; retention shoulder is above the roof plane.
 for sg in (-1,1):
  for yy in (4,76):
   pieces.append(B(15.8,8,3.6,sg*98.5,yy,103.4))
   pieces.append(B(1.8,8,32.5,sg*105.5,yy,106.5))
   pts=[(sg*106.4,136.2),(sg*102.6,136.2),(sg*104.7,139.6),(sg*106.4,139.6)]
   hook=cq.Workplane('XZ').polyline(pts).close().extrude(4,both=True).translate((0,yy,0))
   pieces.append(hook)
 result=union(pieces)
 drains=[C(1.1,5,-.5).translate((x,y,0)) for x in (-80,-40,0,40,80) for y in (-78,-48,-18)]
 result=result.cut(cq.Compound.makeCompound([p.val() for p in drains])).clean()
 assert result.val().isValid() and len(result.val().Solids())==1
 return result

def roof():
 cap=B(224,116,3.2,0,40,132.4).edges('|Z').fillet(4)
 # Agents leave generous round openings around these manually releasable tabs.
 for x in (-105.5,105.5):
  for y in (4,76):cap=cap.cut(B(3.2,10,5,x,y,131.5))
 # Back-edge antenna slot does not trap the camera during rear withdrawal.
 cap=cap.cut(B(18.4,28,5,0,90,131.5))
 return cap

def add_hanger(cap):
 # Two integral sloping load paths keep the eye over the loaded seed/camera
 # centre, independent of fragile architectural ornaments. Neither is a loose part.
 z=258
 for sg in (-1,1):
  pts=[(sg*101,135.2),(sg*91,135.2),(sg*4,251),(sg*13,256)]
  cap=cap.union(cq.Workplane('XZ').polyline(pts).close().extrude(4,both=True).translate((0,35,0)))
 eye=cq.Workplane('XZ').center(0,z).circle(10).extrude(4,both=True).translate((0,35,0))
 hole=cq.Workplane('XZ').center(0,z).circle(4.5).extrude(7,both=True).translate((0,35,0))
 return cap.union(eye).cut(hole).clean(),[0,35,z]

def build(style, camera_id='wyze-battery-cam-pro', decorate=True):
 from vegas_cameras import camera_sled, CAMERA_PROFILES
 base=body();cap=roof()
 if decorate:
  spec=(a if style in a.STYLE_IDS else b).hotel_style(style,cap,base)
 else:
  spec=dict(name='Vegas fit prototype',description='Shared fit and service geometry',body=base,roof=cap,body_color='#DFD3C3',roof_color='#DFD3C3',roof_regions=[],detail_features=[])
 cap,hang=add_hanger(spec['roof'])
 # The user permitted small mirrors. Straight-through optics avoids an extra
 # optical surface and leaves both PIR and night vision looking at the tray.
 profile=CAMERA_PROFILES[camera_id];sled=camera_sled(camera_id)
 slug='vegas-'+style.replace('-inspired','').replace('_','-')
 parts=[dict(name='Twin reservoir and drained feeding terrace',shape=spec['body'],color=spec['body_color'],explode=[0,0,-24],support='Upright; supports only below camera keeper lips and four roof-latch crossbars. Keep mesh, drains and flexure gaps clear.',purpose='One-piece seed storage, landing terrace, drainage and camera dock.'),
        dict(name='Architectural snap roof',shape=cap,color=spec['roof_color'],regions=spec['roof_regions'],explode=[0,0,100],support='Flat underside down. Local organic supports under architectural cornices, palm fronds, crossbars and hanger eye; inspect each feature in the slicer.',purpose='Weather cover, integral hotel architecture and suspension eye.'),
        dict(name='Slide-out camera cradle',shape=sled,color=spec['body_color'],explode=[0,110,22],support=profile['support']+' Keep the flexible tongue and side arms clear.',purpose='Remove the complete camera for charging or battery service; device and electronics are bought separately.')]
 joints=[dict(name='Four roof retention tabs',parts=[parts[0]['name'],parts[1]['name']],description='Four 32.5 mm vertical cantilevers with ramped hooks, exposed finger release and positive retaining shoulders.',beam_length_mm=32.5,beam_thickness_mm=1.8,deflection_mm=1.3,clearance_mm=.4,release='Unload the hanger, press each tab outward, then lift the roof. Never lift a loaded feeder by an unlatched roof.'),dict(name='Camera drawer catch',parts=[parts[0]['name'],parts[2]['name']],description='Captured side rails and an upward-releasing central spring tongue retain the camera cradle.',clearance_mm=.6,release='Lift the rear thumb paddle, pull the complete cradle straight back. Battery and charging ports are then accessible away from seed.')]
 metadata=export_design(slug,spec['name'],'Vegas camera hotels',spec['description'],parts,
  notes=['Three printed pieces with the default Wyze cradle. Choose one alternate camera cradle; do not print all camera options.','ASA body printed in one color to keep the large footprint free of a prime tower; architectural color changes stay on the roof plate.','Camera envelopes come from manufacturer specifications. Camera housing contours, fit, focus, PIR triggering and weather protection require a real-device trial.','Birdfy and Wyze are close-up prototype platforms. Wyze requires its official close-up lens. Birdfy body height and antenna position require measurement. Blink is a conditional mechanical cradle; close-focus optics have not been verified.','No transparent printed glazing. Fine 1.4 mm mesh slots expose the seed level; use seed larger than the openings.','A mirror is not included: direct optics keep PIR and IR paths unobstructed. Do not assume a mirror fixes focus distance.','These are original hotel-inspired designs, not licensed replicas or affiliated hotel products. Mirage is a legacy architectural theme.'],
  assembly=['Push the chosen camera into its matching cradle and confirm retention without covering the lens or sensors. Test image focus on a bird-sized target before loading seed.','Slide the cradle in from the rear until its tongue engages the keeper. Pull gently to check retention.','Pour dry seed into both top-open reservoirs. Snap the architectural roof over all four retaining tabs.','Hang the complete assembly from the one integral roof eye after a supervised load test. Orient the lens and PIR toward the open terrace.','For charging or battery replacement, lift the rear cradle tab and withdraw the whole camera without disturbing the seed. Remove the camera before washing.','For refilling and cleaning, take the feeder down, release the roof tabs and lift off the roof. All seed cavities are accessible from above.'],
  hanger=hang,snap_joints=joints,refill='Unload the hanger, release four accessible roof tabs and lift the roof. Refill the two reservoirs from above. Camera service is independent: the entire cradle slides out from the rear.',
  detail_features=spec['detail_features']+['Two integral gravity-fed seed reservoirs, no separate drain tray','1.4 mm printed seed mesh and 2.2 mm through-drains','Rear-slide camera service independent of the seed refill','Four long roof snap beams and one integral structural hanger'],
  revision='R6',detail_revision='R6',material='ASA',camera_system=True,camera_default=camera_id,camera_profiles=list(CAMERA_PROFILES),camera_mount=profile,price_checked_utc='2026-10-20',
  optical_validation={'status':'Physical focus and PIR test required','nominal_camera_front_y_mm':29,'landing_target_mm':[0,-74,35],'unfolded_view_distance_mm':103,'mirror_included':False},
  prototype_validation={'physical_print':False,'camera_fit':False,'optical_focus':False,'weather_test':False,'load_test':False})
 return metadata

def main():
 p=argparse.ArgumentParser();p.add_argument('--only',nargs='+');p.add_argument('--fit-prototype',action='store_true');args=p.parse_args()
 if args.fit_prototype:build('fit-prototype',decorate=False);return
 for s in args.only or STYLES:build(s)

if __name__=='__main__':main()
