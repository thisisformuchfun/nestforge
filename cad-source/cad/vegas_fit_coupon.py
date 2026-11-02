"""R6 exact right-front roof-latch fit coupon, cropped from production geometry.

Only a low print foot is added. Latch, spring beam, roof slot and assembly
clearances are unchanged. This exercises local fit, not full-feeder strength.
"""
from pathlib import Path
import json
from common import export_design,ROOT
from vegas import body,roof
from vegas_cameras import block

def coupon_parts():
    roi=block(85,112,-8,16,100,140)
    exact_body=body().intersect(roi)
    coupon_body=exact_body.union(block(85,112,-8,16,97,100.2)).clean()
    coupon_roof=roof().intersect(roi).clean()
    for shape in (coupon_body,coupon_roof):
        assert shape.val().isValid() and len(shape.solids().vals())==1
    assert coupon_body.intersect(coupon_roof).val().Volume()<1e-7
    # The low foot is outside all functional beam/slot surfaces.
    assert coupon_body.intersect(block(85,112,-8,16,100.2,140)).cut(exact_body).val().Volume()<1e-7
    return coupon_body,coupon_roof

def export_coupon():
    base,cap=coupon_parts()
    return export_design('vegas-fit-coupon','Vegas roof snap fit coupon','R6 fit trials',
        'Two small exact crops reproduce one production roof latch and its mating slot. Print before the full ASA feeder.',
        [dict(name='Coupon body and exact latch',shape=base,color='#DFD3C3',support='Upright on added flat foot; localized support under horizontal latch root only. Keep spring beam and hook contact faces clear.',print_rotation=[0,0,0]),
         dict(name='Coupon roof and exact slot',shape=cap,color='#DFD3C3',support='None; flat underside down',print_rotation=[0,0,0])],
        notes=['Production geometry cropped at X85..112, Y-8..16, Z100..140 mm. Added foot only at Z97..100.2; beam, retaining hook, slot and clearances are unchanged.',
               'Print in the same ASA, orientation, layer height and spool calibration intended for the full 216 × 204 mm body. Let the coupon cool before evaluating fit.',
               'This checks one local roof snap, not all four tabs, whole-roof warp, feeder load capacity, weathering or long-term ASA fatigue.',
               'The selected camera adapter itself is the camera fit trial; print only the matching device-specific adapter. No camera profile or housing dimensions are inferred from this coupon.'],
        assembly=['Hold the small body coupon by its foot and align the roof slot above the spring beam. Lower the roof until the hook passes through and its shoulder retains the roof.',
                  'Check that the roof seats with a visible shoulder above it and releases by moving the beam outward (+X) while lifting the roof. Do not pry the thin beam sideways or force a cold brittle part.',
                  'Repeat several gentle cycles and inspect for whitening, cracks, permanent set or a loose catch. If fit is wrong, correct calibration or source clearances before printing the full feeder.'],
        revision='R6',material='ASA',fit_coupon=True,physical_test=False,
        exact_source_crop_mm=[85,-8,100,112,16,140],added_foot_bounds_mm=[85,-8,97,112,16,100.2])

if __name__=='__main__':export_coupon()
