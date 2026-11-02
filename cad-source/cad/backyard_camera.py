"""R7 compact camera grips and published envelopes, CAD millimetres, Z up.

This is a small contact interface, not a common feeder body. Front looks -Y.
Camera bodies are references only and NEVER exported as printed solids. The .25
mm side preload is a fit starting point; retention/thermal cycling remain untested.
"""
from copy import deepcopy
import cadquery as cq
from common import box as B

PROFILES={
 'wyze-battery-cam-pro':dict(id='wyze-battery-cam-pro',name='Wyze Battery Cam Pro',width=63.5,depth=45.7,height=88.9,front_y=0.,floor_z=0.,source='https://support.wyze.com/hc/en-us/articles/17496828536987-Wyze-Battery-Cam-Pro-Tech-Specs',status='Official Wyze close-up lens required; its envelope and focus must be verified on the device.',service='Spread the two low side pressure clips and lift the camera from its seat. Remove it before opening the bottom battery cover.'),
 'birdfy-cam-2k':dict(id='birdfy-cam-2k',name='Birdfy Cam 2K',width=56.,depth=56.,height=None,height_with_antenna=230.,front_y=0.,floor_z=0.,source='https://support.birdfy.com/product/birdfy-cam/specifications/',status='Body height and antenna position unpublished separately; the full 230 mm envelope must remain clear overhead.',service='Spread both low side pressure clips and lift out the complete camera for USB-C charging. Keep the antenna and ports clear.'),
}
for p in PROFILES.values():
 p.update(clearance_total_mm=.7,fit_validated=False,physical_print_test=False,checked_date='2026-10-20',retention='Bottom seat, low front/rear stops and releasable side pressure clips. Nominal .25 mm preload per side; friction retention must be tested with the actual device.',support='Local support may be needed beneath side pressure flexures; remove support completely so they can flex.')

def profile(camera_id):return deepcopy(PROFILES[camera_id])

def camera_grip(camera_id):
 p=PROFILES[camera_id];w=p['width'];d=p['depth'];half=w/2+.35
 s=B(w+8,d+8,3.2,0,d/2,-3.2)
 # Rear-rooted lateral flexures, independent of the floor along their free span.
 for sign in [-1,1]:
  x=sign*(half+.8)
  s=s.union(B(1.6,3,9.2,x,27.5,-.2))
  s=s.union(B(1.6,22,7,x,15,2))
  s=s.union(B(.8,3,5,sign*(half-.2),5.5,3))
  s=s.union(B(3.4,3,3,x+sign*.8,4.5,6))
  # Lower corner stops do not cover the central lens/PIR/IR face.
  s=s.union(B(2.5,1.3,3,sign*(half-1),-.95,-.2))
  s=s.union(B(2.5,1.3,5,sign*(half-1),d+.95,-.2))
 return s.clean()

def place(shape,pose=None):
 pose=pose or {};s=shape
 for axis,a in zip([(1,0,0),(0,1,0),(0,0,1)],pose.get('rotation',[0,0,0])):
  if a:s=s.rotate((0,0,0),axis,float(a))
 return s.translate(tuple(pose.get('translation',[0,0,0])))

def hardware_envelope(camera_id,pose=None):
 p=PROFILES[camera_id];h=p['height'] or p['height_with_antenna']
 return place(B(p['width'],p['depth'],h,0,p['depth']/2,0),pose)
