import * as THREE from 'three';

// Manufacturer envelopes in CAD millimetres, Z up. Sensor positions and housing
// contours are visual approximations, never mounting datums or printable parts.
const PROFILES = {
  'birdfy-cam-2k': {width:56,depth:56,height:null,height_with_antenna:230,front_y:0,floor_z:0},
  'wyze-battery-cam-pro': {width:63.5,depth:45.7,height:88.9,front_y:0,floor_z:0},
  'blink-outdoor-4': {width:70,depth:41,height:70,front_y:0,floor_z:0}
};
function roundedRect(width,height,radius) {
  const s=new THREE.Shape(), x=-width/2,y=-height/2,r=Math.min(radius,width/2,height/2);
  s.moveTo(x+r,y);s.lineTo(x+width-r,y);s.quadraticCurveTo(x+width,y,x+width,y+r);
  s.lineTo(x+width,y+height-r);s.quadraticCurveTo(x+width,y+height,x+width-r,y+height);
  s.lineTo(x+r,y+height);s.quadraticCurveTo(x,y+height,x,y+height-r);
  s.lineTo(x,y+r);s.quadraticCurveTo(x,y,x+r,y);return s;
}
function housing(w,h,d,r,bevel) {
  const b=Math.min(bevel,d*.24);
  const g=new THREE.ExtrudeGeometry(roundedRect(w-2*b,h-2*b,r-b),{
    depth:d-2*b,bevelEnabled:true,bevelSize:b,bevelThickness:b,
    bevelSegments:5,steps:1,curveSegments:16
  });
  g.translate(0,0,-(d-2*b)/2);g.rotateX(Math.PI/2);g.computeVertexNormals();return g;
}

/** Returns unprinted illustrative camera hardware at its assembly location.
 * Accepts a CAMERA_PROFILES-like object or one of the three camera IDs.
 * Local origin is the camera front-plane/floor intersection. Lens/PIR positions are
 * illustrative; Birdfy's 90 mm visual body height is expressly not measured.
 */
export function makeCameraPreview(profile='wyze-battery-cam-pro',pose=null) {
  const id=typeof profile==='string'?profile:(profile.id||profile.camera_id||
    (profile.name?.toLowerCase().includes('birdfy')?'birdfy-cam-2k':profile.name?.toLowerCase().includes('blink')?'blink-outdoor-4':'wyze-battery-cam-pro'));
  if(!PROFILES[id])throw new Error(`Unknown camera preview: ${id}`);
  const p={...PROFILES[id],...(typeof profile==='object'?profile:{})};
  const w=Number(p.width),d=Number(p.depth),h=p.height==null?90:Number(p.height);
  if(![w,d,h,p.front_y,p.floor_z].every(n=>Number.isFinite(Number(n)))||Math.min(w,d,h)<=0)throw new Error('Camera preview requires a positive millimetre envelope.');
  const birdfy=id==='birdfy-cam-2k',blink=id==='blink-outdoor-4';
  const group=new THREE.Group();group.name=`Illustrative hardware · ${id}`;
  group.position.set(0,Number(p.front_y)+d/2,Number(p.floor_z)+h/2);
  group.userData={cameraId:id,illustrative:true,printed:false,physicalFitValidated:false,
    units:'mm',coordinateSystem:'Z up; front faces negative Y',
    envelopeSource:p.source||null,bodyHeightMm:h,bodyHeightMeasured:false,bodyHeightPublished:!birdfy,
    bodyHeightBasis:birdfy?'90 mm visual placeholder; manufacturer publishes 230 mm including antenna':'Published manufacturer envelope; not a physical measurement',
    opticalPositions:'Illustrative only; not mechanical datums',dispose:()=>disposeCameraPreview(group)};
  const matte=new THREE.MeshStandardMaterial({color:blink?0x242827:0xf1f1e9,roughness:.57,metalness:.02});
  const front=new THREE.MeshStandardMaterial({color:0x101718,roughness:.29,metalness:.08});
  const trim=new THREE.MeshStandardMaterial({color:0x343e40,roughness:.32,metalness:.36});
  const glass=new THREE.MeshPhysicalMaterial({color:0x071b29,roughness:.07,metalness:.25,clearcoat:1,clearcoatRoughness:.035});
  const pir=new THREE.MeshPhysicalMaterial({color:0xc8d6cb,roughness:.56,metalness:0,clearcoat:.15});
  const ir=new THREE.MeshPhysicalMaterial({color:0x28202b,roughness:.17,metalness:.23,clearcoat:.8});
  const seam=new THREE.MeshStandardMaterial({color:blink?0x101716:0xc5cbc5,roughness:.7});
  const add=(g,m,name,x=0,y=0,z=0)=>{const mesh=new THREE.Mesh(g,m);mesh.name=name;mesh.position.set(x,y,z);mesh.castShadow=true;mesh.receiveShadow=true;mesh.userData={illustrative:true,printed:false};group.add(mesh);return mesh;};
  // Front panel and lens stay within the stated overall depth. The main shell
  // starts 1.4 mm aft of the envelope front; a shallow face panel fills that zone.
  const radius=blink?12:birdfy?10:12;
  add(housing(w,h,d-1.4,radius,1.6),matte,'Rounded camera housing',0,.7,0);
  add(housing(w-3,h-3,1.3,radius-1.5,.18),front,'Satin optical face',0,-d/2+.7,0);
  const faceY=-d/2+.24;
  function disc(radius,depth,material,name,x,z,y=faceY){
    // Cylinder axis Y: circular face lies in the XZ plane.
    return add(new THREE.CylinderGeometry(radius,radius,depth,64),material,name,x,y,z);
  }
  const lensZ=h*.205,lensR=Math.min(w*.176,11.2);
  disc(lensR+.85,.28,trim,'Lens retaining ring',0,lensZ);
  disc(lensR,.32,glass,'Blue-black optical glass',0,lensZ,faceY-.02);
  disc(lensR*.63,.12,front,'Internal optical barrel',0,lensZ,faceY-.11);
  disc(lensR*.42,.1,glass,'Inner lens element',0,lensZ,faceY-.13);
  const reflection=new THREE.MeshBasicMaterial({color:0x76989d,transparent:true,opacity:.2,depthWrite:false});
  const glint=add(new THREE.CircleGeometry(lensR*.14,24),reflection,'Subtle glass reflection',-lensR*.32,-d/2+.045,lensZ+lensR*.36);glint.rotation.x=Math.PI/2;glint.castShadow=false;
  const sensorZ=-h*.235,sensorW=blink?22:20,sensorH=blink?13:16;
  add(housing(sensorW+2,sensorH+2,.45,5,.08),trim,'PIR surround',0,-d/2+.36,sensorZ);
  add(housing(sensorW,sensorH,.4,4.5,.07),pir,'Frosted PIR window',0,-d/2+.21,sensorZ);
  for(const x of [-w*.29,w*.29])disc(2.6,.22,ir,'Infrared emitter window',x,h*.015,faceY-.04);
  disc(1.25,.18,glass,'Ambient light sensor',w*.26,h*.32,faceY-.08);
  // A restrained rear battery/port seam makes the shell read as purchased
  // equipment; there are deliberately no invented logos or mounting sockets.
  add(housing(w-7,h-8,.3,radius-2,.04),seam,'Rear service-cover seam',0,d/2-.19,-.2);
  add(housing(w-8.2,h-9.2,.32,radius-2.5,.04),matte,'Rear service cover',0,d/2-.18,-.2);
  if(birdfy){
    const total=Number(p.height_with_antenna)||230,antennaH=Math.max(0,total-h);
    if(antennaH>0){
      const antenna=new THREE.MeshStandardMaterial({color:0xe8ece5,roughness:.62});
      // Antenna rises within the published 230 mm total envelope. Its diameter,
      // offset and hinge contour are visual approximations.
      const z=h/2+antennaH/2-1.8;
      add(new THREE.CylinderGeometry(2.1,2.7,Math.max(1,antennaH-4),24).rotateX(Math.PI/2),antenna,'External antenna',w*.3,d*.28,z);
      add(new THREE.SphereGeometry(2.1,24,16),antenna,'Rounded antenna tip',w*.3,d*.28,total-h/2-2.1);
      add(new THREE.SphereGeometry(4,24,16),matte,'Antenna hinge',w*.3,d*.28,h/2-1);
    }
  }
  // CAD placement applies rotations around the local camera floor/front origin,
  // X then Y then Z, followed by translation. ZYX Euler gives that matrix order.
  const placement=new THREE.Group();placement.name=group.name;placement.userData={...group.userData};placement.add(group);
  if(pose){
    const translation=pose.translation||[0,0,0],rotation=pose.rotation||pose.rotationXYZ||[0,0,0];
    if(translation.length!==3||rotation.length!==3||![...translation,...rotation].every(Number.isFinite))throw new Error('Camera pose requires three finite translation and rotation values.');
    placement.position.set(...translation);placement.rotation.set(...rotation.map(THREE.MathUtils.degToRad),'ZYX');
  }
  placement.userData.dispose=()=>disposeCameraPreview(placement);
  return placement;
}

/** Dispose only this preview's owned geometries/materials, then detach it. */
export function disposeCameraPreview(group){
  if(!group)return;const geometries=new Set(),materials=new Set();
  group.traverse(object=>{if(object.geometry)geometries.add(object.geometry);if(object.material){for(const m of Array.isArray(object.material)?object.material:[object.material])materials.add(m);}});
  geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());group.removeFromParent();group.clear();
}
