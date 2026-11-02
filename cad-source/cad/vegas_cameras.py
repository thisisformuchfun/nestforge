"""R6 device-specific slide-out camera cradles, millimetres in assembly frame.

Manufacturer envelopes are unmeasured fit starting points. Flexible pressure pads
retain the lower sides, never an invented top height. Camera proxies are for CAD
checks only, not exported printed parts. Lens/PIR face points towards negative Y.
"""
import cadquery as cq

CAMERA_PROFILES = {
    'birdfy-cam-2k': dict(name='Birdfy Cam 2K', width=56., depth=56., height=None,
        height_with_antenna=230., front_y=118., floor_z=41.5,
        source='https://support.birdfy.com/product/birdfy-cam/specifications/',
        status='External rear saddle; no overhead limit. Housing contour and optical test required.',
        service='Lift rear release paddle and withdraw the entire extended cradle towards +Y; reserve 160 mm rearward service travel. Lift camera to charge USB-C; full 230 mm antenna envelope stays in free air behind roof.'),
    'wyze-battery-cam-pro': dict(name='Wyze Battery Cam Pro', width=63.5, depth=45.7, height=88.9,
        front_y=29., floor_z=41.5,
        source='https://support.wyze.com/hc/en-us/articles/17496828536987-Wyze-Battery-Cam-Pro-Tech-Specs',
        status='Requires official close-up lens; lens envelope and focus still need physical verification.',
        service='Withdraw sled, release camera, then open bottom battery compartment with at least 80 mm service allowance.'),
    'blink-outdoor-4': dict(name='Blink Outdoor 4', width=70., depth=41., height=70.,
        front_y=29., floor_z=41.5,
        source='https://support.blinkforhome.com/en_US/tech-specs-outdoor4/outdoor4-camera-tech-specs',
        status='Mechanical prototype only; close-focus optics unverified. Sync Module required.',
        service='Withdraw sled and release camera for rear-cover AA replacement; batteries are not rechargeable.'),
}
for _p in CAMERA_PROFILES.values():
    _p.update(clearance_total_mm=.7, retention='Two integral lateral pressure flexures with finger pads; low front/rear corner stops. No top capture or assumed screw datum.',
        beam_mm=dict(length=22.,thickness=1.6,width=8.),
        latch=dict(release='Lift rear thumb paddle at least 1.5 mm, then pull towards +Y.',
                   hook_bounds_mm=[-5.,96.,35.8,5.,98.,38.2], service_cycle_test_required=True),
        fit_validated=False, physical_print_test=False,
        print_rotation=[0,0,0],
        support='Underhook is 2.2 mm below flat plate bottom: upright printing requires support under elevated plate; inspect slicer preview. Not a support-free part.',
        front_keepout_mm=[-36.,15.,44.5,36.,29.,150.],
        checked_date='2026-10-20')

CAMERA_PROFILES['birdfy-cam-2k'].update(
    front_keepout_mm=[-36.,98.,44.5,36.,118.,271.5],
    rear_service_travel_mm=160.,
    mounting='External rear cantilever, camera entirely aft of roof Y98. Camera front Y118, rear Y174; integral side ribs start Y100.',
    optical_validation='Direct forward-facing lens/PIR path through central bay; field of view, sensor occlusion, focus and camera contour remain physically unverified.',
    structural_validation='Cantilever, suspension balance and repeated latch cycling require physical loaded tests.')

def block(x0,x1,y0,y1,z0,z1):
    return cq.Workplane('XY').box(x1-x0,y1-y0,z1-z0).translate(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))

def camera_sled(camera_id='birdfy-cam-2k'):
    p=CAMERA_PROFILES[camera_id];w=p['width'];depth=p['depth'];half=w/2+.35
    external=camera_id=='birdfy-cam-2k';offset=p['front_y']-29.
    shape=block(-41,41,22,181 if external else 100,38,41)
    if external:
        # Flat bridge clears the slide rails; raised ribs only begin beyond Y100.
        for x0,x1 in [(-40,-36),(36,40)]:
            shape=shape.union(block(x0,x1,100,181,40.8,50))
        # Pocket around the paddle prevents extension welding it to the plate.
        shape=shape.cut(block(-9,9,100,113,37,42))
    # Open U slot isolates the root-supported rear lift beam from the plate.
    for a,b in [(-6,-5),(5,6)]:shape=shape.cut(block(a,b,68,113 if external else 101,37,42))
    shape=shape.cut(block(-5,5,68,113 if external else 101,39.6,42))
    shape=shape.union(block(-5,5,65,108,38,39.6))
    shape=shape.union(block(-8,8,104,112,38,40))
    # Ramp on insertion side, square rear retaining face, 0.2 mm overlap to beam.
    hook=cq.Workplane('YZ').polyline([(96,38.2),(98,38.2),(98,35.8),(96,37.8)]).close().extrude(10).translate((-5,0,0))
    shape=shape.union(hook)
    # Two side runners establish the published camera floor without bridging latch.
    for sign in (-1,1):
        x0,x1=(half-6,half-1) if sign==1 else (-half+1,-half+6)
        shape=shape.union(block(x0,x1,p['front_y'],p['front_y']+depth,40.8,41.5))
        # Rear-supported horizontal cantilever: 22 long, 1.6 thick, 8 high.
        x0,x1=(half,half+1.6) if sign==1 else (-half-1.6,-half)
        shape=shape.union(block(x0,x1,55+offset,58+offset,40.8,50))
        shape=shape.union(block(x0,x1,33+offset,55.2+offset,42,50))
        # A 0.6 mm inward pressure nose flexes 0.25 mm on nominal camera body.
        nose=(half-.6,half+.2) if sign==1 else (-half-.2,-half+.6)
        shape=shape.union(block(*nose,33+offset,36+offset,43,49))
        # Finger pad extends rearwards instead of into the rail keeper envelope.
        shape=shape.union(block(x0,x1,30+offset,34+offset,45,50))
        # Small lower corner stops leave central front sensors/lens exposed.
        stop=(half-2.8,half+.2) if sign==1 else (-half-.2,-half+2.8)
        shape=shape.union(block(*stop,27.5+offset,28.65+offset,40.8,44.5))
        shape=shape.union(block(*stop,p['front_y']+depth+.35,p['front_y']+depth+1.95,40.8,46))
    shape=shape.clean()
    solids=shape.solids().vals()
    if len(solids)!=1 or not solids[0].isValid():raise ValueError(f'{camera_id}: cradle must be one valid connected solid')
    return shape

def camera_envelope(profile):
    """Nominal camera-only rectangular proxy; Birdfy uses full 230 mm envelope.

    The Birdfy proxy is intentionally conservative, not a claimed body height.
    Unknown Wyze accessory lens is excluded; reserve front_keepout_mm separately.
    """
    p=CAMERA_PROFILES[profile] if isinstance(profile,str) else profile
    h=p['height'] if p['height'] is not None else p['height_with_antenna']
    return block(-p['width']/2,p['width']/2,p['front_y'],p['front_y']+p['depth'],p['floor_z'],p['floor_z']+h)
