import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { GardenRenderer } from './garden-renderer.js';
import { BirdVisit } from './bird-visit.js';
import { PartAnnotations } from './part-annotations.js';
import { setupNatureAudio } from './nature-audio.js';
import { renderSourcing, clearSourcing } from './sourcing.js';
import { makeCameraPreview, disposeCameraPreview } from './camera-preview.js';
import { renderPrintPlates, clearPrintPlates, loadPrintSummary, printSummary } from './print-plates.js';
import { filterCatalog, plural, designIdFromHash } from './catalog-tools.js';
import { productPageIds } from './product-pages.js';

const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const viewport=$('#viewport'), experience=$('.experience');
const state={catalog:[],family:'All designs',query:'',includeCameras:false,maxPlates:0,sort:'featured',selected:null,part:null,explode:0,rotation:!matchMedia('(prefers-reduced-motion: reduce)').matches,studio:false,groups:[],generation:0,inspection:false,visitPhase:null,paused:false,dragging:false};
const familyOrder=['Castles','Originals','World architecture','Whimsical','Future habitats','Game day','Backyard camera feeders'];
const geometryCache=new Map(), loader=new STLLoader();
let scene,camera,renderer,controls,ambient,finisher,birdVisit,annotations,animationTime=0,pointerDown=null,renderAvailable=true;
const e=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;};
const colors=d=>[...new Set(d.parts.flatMap(p=>(p.regions||[p]).map(r=>r.color)))];
const showcase=()=>{const items=filtered();if(state.family==='All designs'&&!state.query&&!state.maxPlates&&state.sort==='featured'){const featured=['scandinavian-cabin','fairy-tale-turret','ufo-snackduction'].map(id=>items.find(d=>d.id===id)).filter(Boolean);if(featured.length)return featured;}return items.slice(0,6);};
const url=(d,file)=>`models/${d.id}/${file}`;
const bounds=d=>{const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];for(const p of d.parts){for(let i=0;i<3;i++){lo[i]=Math.min(lo[i],p.bounds[i]);hi[i]=Math.max(hi[i],p.bounds[i+3]);}}return{lo,hi,size:hi.map((v,i)=>v-lo[i]),center:hi.map((v,i)=>(v+lo[i])/2)};};

const natureAudio=setupNatureAudio();
try{
 renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,powerPreference:'high-performance'});
 renderer.setPixelRatio(Math.min(devicePixelRatio,matchMedia('(max-width:760px)').matches?1.4:1.8));renderer.setClearColor(0,0);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.AgXToneMapping;renderer.toneMappingExposure=.94;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;viewport.prepend(renderer.domElement);
 scene=new THREE.Scene();finisher=new GardenRenderer(renderer);birdVisit=new BirdVisit(scene);annotations=new PartAnnotations(viewport,selectPart);camera=new THREE.PerspectiveCamera(36,1,1,5000);
 const pmrem=new THREE.PMREMGenerator(renderer);scene.environment=pmrem.fromScene(new RoomEnvironment(),.04).texture;pmrem.dispose();scene.environmentIntensity=.28;
 ambient=new THREE.HemisphereLight(0xc2d1da,0x374738,.6);scene.add(ambient);
 const sun=new THREE.DirectionalLight(0xffe7c2,1.85);sun.position.set(-350,450,250);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-700;sun.shadow.camera.right=700;sun.shadow.camera.top=450;sun.shadow.camera.bottom=-350;sun.shadow.camera.far=1600;sun.shadow.normalBias=.12;sun.shadow.bias=-.00003;scene.add(sun);
 const fill=new THREE.DirectionalLight(0xb0cbd9,.38);fill.position.set(350,150,-150);scene.add(fill);
 controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.08;controls.enablePan=false;controls.minDistance=220;controls.maxDistance=1700;controls.maxPolarAngle=Math.PI*.77;controls.minPolarAngle=Math.PI*.18;controls.enabled=false;
 controls.addEventListener('start',()=>{state.dragging=true;});controls.addEventListener('end',()=>{state.dragging=false;});
 const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
 renderer.domElement.addEventListener('pointerdown',ev=>{pointerDown=[ev.clientX,ev.clientY]});
 renderer.domElement.addEventListener('pointerup',ev=>{
  if(!pointerDown||Math.hypot(pointerDown[0]-ev.clientX,pointerDown[1]-ev.clientY)>6)return;
  const rect=renderer.domElement.getBoundingClientRect();pointer.set((ev.clientX-rect.left)/rect.width*2-1,-((ev.clientY-rect.top)/rect.height)*2+1);raycaster.setFromCamera(pointer,camera);
  const hit=raycaster.intersectObjects(state.groups.flatMap(g=>g.userData.parts),true)[0];
  if(hit){const d=hit.object.userData.design;if(state.selected?.id===d.id)selectPart(hit.object.userData.partIndex);else selectDesign(d.id);}
 });
 renderer.domElement.addEventListener('pointermove',ev=>{if(state.selected)return;const r=renderer.domElement.getBoundingClientRect();pointer.set((ev.clientX-r.left)/r.width*2-1,-((ev.clientY-r.top)/r.height)*2+1);raycaster.setFromCamera(pointer,camera);renderer.domElement.style.cursor=raycaster.intersectObjects(state.groups.flatMap(g=>g.userData.parts),true).length?'pointer':'default';});
 const resize=()=>{const rect=viewport.getBoundingClientRect();renderer.setSize(rect.width,rect.height);finisher.setSize(rect.width,rect.height);camera.aspect=rect.width/rect.height;camera.updateProjectionMatrix();fitCamera();};new ResizeObserver(resize).observe(viewport);
 const clock=new THREE.Clock();renderer.setAnimationLoop(()=>{
  const dt=Math.min(clock.getDelta(),.05);animationTime+=dt;
  updateVisit(dt);
  for(const g of state.groups){if(state.rotation&&!state.paused&&!state.dragging&&!document.hidden)g.rotation.y+=dt*(state.selected?.id===g.userData.design.id ? .18 : .075);for(let i=0;i<g.userData.parts.length;i++){const p=g.userData.parts[i],v=g.userData.design.parts[i].explode||[0,0,50*(i+1)],t=state.selected?state.explode/100:0;p.position.lerp(new THREE.Vector3(v[0]*t,v[1]*t,v[2]*t),matchMedia('(prefers-reduced-motion: reduce)').matches?1:Math.min(1,dt*9));}g.userData.cords.visible=!state.studio&&(!state.selected||state.explode<2);}
  controls.update();finisher.render(scene,camera);updateLabels();annotations.update(state.selected?state.groups[0]:null,camera,state.explode,state.part);
 });
}catch(error){renderAvailable=false;experience.classList.add('no-webgl');$('#fallback').hidden=false;$('#loading').hidden=true;console.error(error);}


function setExplosion(value){state.explode=value;}
function cancelVisit(){birdVisit?.cancel();state.inspection=false;state.visitPhase=null;state.paused=false;$('#visit-ui').hidden=true;}
function startVisit(d){
 cancelVisit();if(!renderAvailable||state.groups[0]?.userData.design.id!==d.id)return;
 state.part=null;applyPartSelection();setExplosion(0);
 $('#visit-ui').hidden=false;
 if(matchMedia('(prefers-reduced-motion: reduce)').matches){setExplosion(100);$('#visit-status').textContent='Parts view · reduced motion';$('#pause-cycle').hidden=true;fitCamera(true);return;}
 state.inspection=true;birdVisit.start(bounds(d),d.feeding_target,state.groups[0]);$('#pause-cycle').hidden=false;$('#pause-cycle').textContent='Pause';$('#pause-cycle').setAttribute('aria-pressed','false');$('#visit-status').textContent='A visitor is arriving';$('#scene-hint').textContent='Bird visit · unfold · reassemble · repeat';fitCamera(true);
}
function setCyclePaused(paused){state.paused=paused;$('#pause-cycle').textContent=paused?'Resume':'Pause';$('#pause-cycle').setAttribute('aria-pressed',String(paused));if(!paused){state.part=null;applyPartSelection();}$('#visit-status').textContent=paused?'Paused for a closer look':state.visitPhase||'A visitor is arriving';}
function updateVisit(dt){
 if(!state.inspection||state.paused||state.dragging||document.hidden)return;const frame=birdVisit.update(dt);if(!frame)return;
 if(frame.phase!==state.visitPhase){state.visitPhase=frame.phase;$('#visit-status').textContent=frame.phase;}
 if(Math.abs(frame.explode-state.explode)>.001){setExplosion(frame.explode);fitCamera(true);}
}
$('#pause-cycle').onclick=()=>setCyclePaused(!state.paused);

function material(color){
 const albedo=new THREE.Color(color);const peak=Math.max(albedo.r,albedo.g,albedo.b);if(peak>.7)albedo.multiplyScalar(.7/peak);
 const m=new THREE.MeshPhysicalMaterial({color:albedo,roughness:.82,metalness:0,clearcoat:.018,clearcoatRoughness:.85,envMapIntensity:.5});
 // Fine print texture is visual only; the exported meshes contain the larger relief details.
 m.onBeforeCompile=shader=>{shader.vertexShader='varying vec3 vPrintPosition;\n'+shader.vertexShader;shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvPrintPosition=position;');shader.fragmentShader='varying vec3 vPrintPosition;\n'+shader.fragmentShader;shader.fragmentShader=shader.fragmentShader.replace('#include <roughnessmap_fragment>','#include <roughnessmap_fragment>\nfloat layerWave=sin(vPrintPosition.z*31.4159);\nfloat aa=clamp(1.0-fwidth(vPrintPosition.z)*2.5,0.0,1.0);\nroughnessFactor=clamp(roughnessFactor+layerWave*.035*aa,0.4,1.0);\ndiffuseColor.rgb*=1.0-layerWave*.012*aa;');};
 return m;
}
// Weld equal STL vertices for continuous shading on the scanned sculpture only.
// This changes normals, not printed geometry; architectural hard edges stay crisp.
function smoothSculpt(geometry){
 const source=geometry.getAttribute('position'),vertices=[],indices=new Uint32Array(source.count),lookup=new Map();
 for(let i=0;i<source.count;i++){const x=source.getX(i),y=source.getY(i),z=source.getZ(i),key=`${x},${y},${z}`;let index=lookup.get(key);if(index===undefined){index=vertices.length/3;lookup.set(key,index);vertices.push(x,y,z);}indices[i]=index;}
 const result=new THREE.BufferGeometry();result.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));result.setIndex(new THREE.BufferAttribute(indices,1));result.computeVertexNormals();geometry.dispose();return result;
}
async function getGeometry(path){
 if(!geometryCache.has(path))geometryCache.set(path,(async()=>{
  if(!path.endsWith('.gz'))return loader.loadAsync(path);
  const response=await fetch(path);if(!response.ok)throw Error('Mesh download failed: '+path);
  let bytes=await response.arrayBuffer();const magic=new Uint8Array(bytes,0,Math.min(2,bytes.byteLength));
  if(magic[0]===31&&magic[1]===139)bytes=await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  const geometry=loader.parse(bytes);
  return path.includes("dragon-guard-citadel/03-snap-weather-crown-region-02")?smoothSculpt(geometry):geometry;
 })().catch(error=>{geometryCache.delete(path);throw error;}));return geometryCache.get(path);
}
function renderCredits(d){
 const host=$('#design-credit');host.replaceChildren();host.hidden=!d.attributions?.length&&!d.cad_format_note;
 for(const credit of d.attributions||[]){const line=e('p');line.append(document.createTextNode(`${credit.title} by ${credit.creator}. `));const source=e('a','','Original model ↗');source.href=credit.source_url;source.target='_blank';source.rel='noopener noreferrer';const license=e('a','',credit.license);license.href=credit.license_url;license.target='_blank';license.rel='noopener noreferrer';line.append(source,document.createTextNode(' · '),license);host.append(line);if(credit.applies_to)host.append(e('p','',credit.applies_to));const changes=e('details');changes.append(e('summary','','Adaptation details'),e('p','',credit.modifications));host.append(changes);}
 if(d.cad_format_note)host.append(e('p','',d.cad_format_note));
}

function rope(a,b,r=.75){const v=new THREE.Vector3().subVectors(b,a);const mesh=new THREE.Mesh(new THREE.CylinderGeometry(r,r,v.length(),7),new THREE.MeshStandardMaterial({color:0x8e7145,roughness:1}));mesh.position.copy(a).add(b).multiplyScalar(.5);mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),v.normalize());mesh.castShadow=true;return mesh;}
async function createGroup(d){
 const g=new THREE.Group(),native=new THREE.Group(),b=bounds(d);native.rotation.x=-Math.PI/2;native.position.set(-b.center[0],-b.center[2],b.center[1]);g.add(native);
 const partResults=await Promise.allSettled(d.parts.map(async(p,i)=>{
  const part=new THREE.Group();part.userData={design:d,partIndex:i};native.add(part);
  const results=await Promise.allSettled((p.regions||[p]).map(async r=>{const geometry=await getGeometry(url(d,r.file));const mesh=new THREE.Mesh(geometry,material(r.color));mesh.castShadow=true;mesh.receiveShadow=true;mesh.userData={design:d,partIndex:i};part.add(mesh);}));
  const failed=results.find(r=>r.status==='rejected');if(failed)throw failed.reason;return part;
 }));
 const failed=partResults.find(r=>r.status==='rejected');if(failed){native.traverse(o=>{if(o.isMesh)o.material.dispose();});throw failed.reason;}
 const parts=partResults.map(r=>r.value);
 let hardware=null;
 if(d.camera_system){
  const index=d.camera_part_index;
  if(!Number.isInteger(index)||!parts[index])throw Error(`Missing camera carrier index: ${d.id}`);
  hardware=makeCameraPreview({...d.camera_mount,id:d.camera_default},d.camera_pose);
  hardware.traverse(o=>{if(o.isMesh)Object.assign(o.userData,{design:d,partIndex:index});});parts[index].add(hardware);
 }
 const cords=new THREE.Group();cords.name='Illustrative installation hardware · not printed';g.add(cords);
 const mounting=d.mounting?.type||(d.hanger?'hanging':null);
 if(mounting==='hanging'&&d.hanger){
  const a=d.hanger,start=new THREE.Vector3(a[0]-b.center[0],a[2]-b.center[2],-a[1]+b.center[1]);
  cords.add(rope(start,new THREE.Vector3(start.x,Math.max(390,start.y+90),start.z),1.5));
 }else if(mounting==='wall'||mounting==='post'){
  // A mounting position is the rear contact face, not the foot of the post.
  const a=d.mounting.position||[b.center[0],b.hi[1],b.center[2]];
  const width=mounting==='wall'?Math.max(90,b.size[0]*.55):70,depth=mounting==='wall'?24:70;
  const height=mounting==='wall'?b.size[2]+55:Math.max(310,b.size[2]+180);
  const support=new THREE.Mesh(timberGeometry(width,height,depth),weatheredWood());
  support.position.set(a[0]-b.center[0],a[2]-b.center[2]-(mounting==='post'?height*.24:0),-a[1]+b.center[1]-depth/2);
  support.castShadow=true;support.receiveShadow=true;
  support.name=`Illustrative ${mounting==='wall'?'wooden backboard':'timber post'} · mounting hardware not printed`;support.userData={illustrative:true,printed:false,contactPositionCad:a.slice()};cords.add(support);
 }
 const extraHardware=[];
 for(const item of d.extra_hardware||[]){
  if(item.type!=='recycled-bottle'||!Array.isArray(item.position||item.pose?.translation))continue;
  const bottle=makeBottlePreview(item);const index=Number.isInteger(item.part_index)?item.part_index:0;
  bottle.traverse(o=>{if(o.isMesh)Object.assign(o.userData,{design:d,partIndex:index,illustrative:true,printed:false});});(parts[index]||native).add(bottle);extraHardware.push(bottle);
 }
 g.userData={design:d,parts,bounds:b,native,cords,hardware,extraHardware,partOverrides:{}};return g;
}
function timberGeometry(width,height,depth){
 // Small eased timber edges catch light without adding invented print parts.
 const bevel=1.2,w=width-2*bevel,h=height-2*bevel,shape=new THREE.Shape();
 shape.moveTo(-w/2,-h/2);shape.lineTo(w/2,-h/2);shape.lineTo(w/2,h/2);shape.lineTo(-w/2,h/2);shape.closePath();
 const geometry=new THREE.ExtrudeGeometry(shape,{depth:depth-2*bevel,bevelEnabled:true,bevelSize:bevel,bevelThickness:bevel,bevelSegments:2,steps:1});
 geometry.translate(0,0,-(depth-2*bevel)/2);geometry.computeVertexNormals();return geometry;
}
function weatheredWood(){
 const wood=new THREE.MeshStandardMaterial({color:0x827561,roughness:.94,metalness:0});
 wood.onBeforeCompile=shader=>{
  shader.vertexShader='varying vec3 vTimberPosition;\n'+shader.vertexShader;
  shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvTimberPosition=position;');
  shader.fragmentShader=`varying vec3 vTimberPosition;
float timberHash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float timberNoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(timberHash(i),timberHash(i+vec2(1.0,0.0)),f.x),mix(timberHash(i+vec2(0.0,1.0)),timberHash(i+vec2(1.0,1.0)),f.x),f.y);}
`+shader.fragmentShader;
  shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
vec3 timberP=vTimberPosition;
float timberAlong=timberP.y;
float timberAcross=timberP.x+timberP.z*.73;
float timberWarp=timberNoise(vec2(timberAcross*.026,timberAlong*.008));
float timberGrain=sin(timberAcross*1.35+timberWarp*8.0+sin(timberAlong*.017)*.55);
float timberFine=sin(timberAcross*5.8+timberWarp*16.0);
float timberAA=1.0-smoothstep(.25,1.4,fwidth(timberAcross));
float timberWeather=timberNoise(vec2(timberAcross*.055,timberAlong*.018));
float timberPores=smoothstep(.69,.9,timberNoise(vec2(timberAcross*2.3,timberAlong*.11)));
diffuseColor.rgb*=.89+.13*timberWeather+.055*timberGrain+.023*timberFine*timberAA-.12*timberPores;
diffuseColor.rgb=mix(diffuseColor.rgb,diffuseColor.rgb*vec3(1.04,1.055,1.065),timberWeather*.5);`);
  shader.fragmentShader=shader.fragmentShader.replace('#include <roughnessmap_fragment>','#include <roughnessmap_fragment>\nroughnessFactor=clamp(roughnessFactor+.025*timberGrain,.8,1.0);');
 };
 wood.customProgramCacheKey=()=> 'nestforge-weathered-timber-v1';return wood;
}
function makeBottlePreview(item){
 const radius=item.radius_mm??(item.nominal_diameter_mm!=null?item.nominal_diameter_mm/2:34);
 const neck=item.neck_radius_mm??(item.neck_diameter_mm!=null?item.neck_diameter_mm/2:14);
 const shoulder=item.neck_and_shoulder_height_mm??45;
 const height=item.overall_height_mm??item.height_mm??(item.body_height_mm!=null?item.body_height_mm+shoulder:205);
 const bodyHeight=item.body_height_mm??height-shoulder;
 if(![radius,neck,shoulder,height,bodyHeight].every(x=>Number.isFinite(x)&&x>0)||shoulder>=height)throw Error('Bottle preview requires positive, consistent dimensions.');
 const neckHeight=Math.min(22,shoulder*.49),bodyStart=height-bodyHeight,shoulderTop=Math.max(neckHeight,Math.min(shoulder,bodyStart));
 const bottle=new THREE.Group();
 const profile=[[neck,0],[neck,neckHeight],[neck*1.03,neckHeight+1],[radius*.77,neckHeight+(shoulderTop-neckHeight)*.67],[radius*.97,shoulderTop-2],[radius,shoulderTop],[radius,height-9],[radius*.96,height-3],[radius*.85,height],[0,height]].map(([r,z])=>new THREE.Vector2(r,z));
 const shell=new THREE.Mesh(new THREE.LatheGeometry(profile,48).rotateX(Math.PI/2),new THREE.MeshPhysicalMaterial({color:0xd9e6da,roughness:.14,metalness:0,transparent:true,opacity:.3,depthWrite:false,side:THREE.DoubleSide,clearcoat:.55,clearcoatRoughness:.12}));
 bottle.add(shell);bottle.position.set(...(item.position||item.pose.translation));if(item.pose?.rotation)bottle.rotation.set(...item.pose.rotation.map(THREE.MathUtils.degToRad),'ZYX');bottle.name='Reused bottle · illustrative, not printed';
 bottle.userData={illustrative:true,printed:false,dimensions:{diameterMm:radius*2,neckDiameterMm:neck*2,heightMm:height,bodyHeightMm:bodyHeight,neckAndShoulderHeightMm:shoulderTop}};return bottle;
}
function disposeGroup(g){
 if(g.userData.hardware)disposeCameraPreview(g.userData.hardware);
 for(const item of g.userData.extraHardware||[])disposeCameraPreview(item);
 for(const p of g.userData.parts)p.traverse(o=>{if(o.isMesh)o.material.dispose();});
 g.userData.cords.traverse(o=>{if(o.isMesh){o.geometry.dispose();o.material.dispose();}});
}
async function showScene(designs){
 if(!renderAvailable)return;cancelVisit();annotations.clear();const generation=++state.generation;$('#loading').hidden=false;
 for(const g of state.groups){scene.remove(g);disposeGroup(g);}state.groups=[];$('#scene-labels').replaceChildren();
 const results=await Promise.allSettled(designs.map(createGroup));if(generation!==state.generation){for(const r of results)if(r.status==='fulfilled')disposeGroup(r.value);return;}
 let failures=0;results.forEach((r,i)=>{if(r.status==='fulfilled'){const g=r.value;scene.add(g);state.groups.push(g);const label=e('div','model-label');label.innerHTML=`<span>${String(i+1).padStart(2,'0')}</span><strong></strong>`;label.querySelector('strong').textContent=designs[i].name;label.dataset.id=designs[i].id;$('#scene-labels').append(label);}else{failures++;console.error('Mesh failed',designs[i].id,r.reason);}});
 $('#loading').hidden=true;$('#fallback').hidden=!failures;if(failures)$('#fallback').textContent='Some 3D models could not load. Their previews and downloads are available below.';layoutGroups();fitCamera();applyPartSelection();
 const active=new Set(designs.flatMap(d=>d.parts.flatMap(p=>(p.regions||[p]).map(r=>url(d,r.file)))));
 if(geometryCache.size>72)for(const [path,promise] of geometryCache){if(active.has(path))continue;geometryCache.delete(path);promise.then(g=>g.dispose()).catch(()=>{});if(geometryCache.size<=48)break;}
}
function layoutGroups(){if(!renderAvailable)return;const mobile=matchMedia('(max-width:760px)').matches,n=state.groups.length;for(let i=0;i<n;i++){const g=state.groups[i];if(state.selected){g.scale.setScalar(1);g.position.set(0,0,0);g.rotation.y=-.16;}else{const cols=mobile?Math.min(n,3):n,rows=mobile?Math.ceil(n/3):1;g.scale.setScalar(mobile?.76:.82);g.position.set((i%cols-(cols-1)/2)*185,(mobile?(Math.floor(i/cols)-(rows-1)/2)*-235:-55),0);g.rotation.y=-.18+(i%2)*.2;}}}
function fitCamera(preserveLayout=false){
 if(!renderAvailable||!camera)return;if(!preserveLayout)layoutGroups();
 const rect=viewport.getBoundingClientRect(),desktop=!matchMedia('(max-width:760px)').matches;
 controls.enabled=!!state.selected;renderer.domElement.style.touchAction=state.selected?'none':'pan-y';camera.clearViewOffset();
 if(state.selected&&state.groups.length){
  const g=state.groups[0];g.updateMatrixWorld(true);const box=new THREE.Box3();const t=state.explode/100;
  g.userData.parts.forEach((mesh,i)=>{const original=g.userData.design.parts[i],p=g.userData.partOverrides?.[i]||original,b=p.bounds,v=original.explode||[0,0,50*(i+1)];for(const x of [b[0],b[3]])for(const y of [b[1],b[4]])for(const z of [b[2],b[5]])box.expandByPoint(new THREE.Vector3(x+v[0]*t,y+v[1]*t,z+v[2]*t).applyMatrix4(g.userData.native.matrixWorld));});
  if(g.userData.hardware)box.expandByObject(g.userData.hardware,true);for(const item of g.userData.extraHardware||[])box.expandByObject(item,true);
  if(state.inspection){const fade=1-state.explode/100,r=birdVisit.radius+90;box.min.x=THREE.MathUtils.lerp(box.min.x,Math.min(box.min.x,-r),fade);box.max.x=THREE.MathUtils.lerp(box.max.x,Math.max(box.max.x,r),fade);box.min.z=THREE.MathUtils.lerp(box.min.z,Math.min(box.min.z,-r),fade);box.max.z=THREE.MathUtils.lerp(box.max.z,Math.max(box.max.z,r),fade);}
  const size=box.getSize(new THREE.Vector3()),center=box.getCenter(new THREE.Vector3());
  const padHeight=desktop?130:105,padWidth=desktop?270:145,tan=Math.tan(THREE.MathUtils.degToRad(camera.fov/2));
  const distance=Math.max(size.y/(2*tan)*rect.height/Math.max(150,rect.height-padHeight),size.x/(2*tan*camera.aspect)*rect.width/Math.max(150,rect.width-padWidth))+size.z*.7;
  const direction=preserveLayout?new THREE.Vector3().subVectors(camera.position,controls.target).normalize():new THREE.Vector3(.28,.16,1).normalize();
  controls.target.copy(center);camera.position.copy(center).addScaledVector(direction,Math.max(280,distance*1.12));camera.setViewOffset(rect.width,rect.height,0,desktop?30:32,rect.width,rect.height);controls.maxDistance=1800;controls.minDistance=180;
 }else{const n=state.groups.length||6,span=desktop?Math.max((n-1)*185+180+100,480):540;const dist=span/(2*Math.tan(THREE.MathUtils.degToRad(camera.fov/2))*camera.aspect);controls.target.set(0,15,0);camera.position.set(0,100,Math.max(dist+(desktop?75:0),desktop?660:920));}
 camera.lookAt(controls.target);camera.updateProjectionMatrix();controls.update();
}
function updateLabels(){if(!camera)return;for(const el of $$('.model-label')){el.hidden=!!state.selected;if(state.selected)continue;const g=state.groups.find(x=>x.userData.design.id===el.dataset.id);if(!g)continue;const vec=new THREE.Vector3(g.position.x,g.position.y-g.userData.bounds.size[2]*g.scale.y/2-24,g.position.z);vec.project(camera);const r=viewport.getBoundingClientRect();el.style.left=`${(vec.x*.5+.5)*r.width}px`;el.style.top=`${(-vec.y*.5+.5)*r.height}px`;}}
function renderFamilies(){
 const container=$('#families');container.replaceChildren();
 for(const family of ['All designs',...familyOrder.filter(f=>state.catalog.some(d=>d.family===f&&(state.includeCameras||!d.camera_system)))]){
  const button=e('button','',family);button.setAttribute('aria-pressed',String(family===state.family));
  button.dataset.family=family;button.onclick=()=>{state.family=family;refreshCatalog();[...container.children].find(b=>b.dataset.family===family)?.focus({preventScroll:true});};container.append(button);
 }
}
function filtered(){return filterCatalog(state.catalog,printSummary,state);}
function renderCards(){
 const list=$('#catalog'),items=filtered();list.replaceChildren();
 $('#catalog-status').textContent=`${plural(items.length,'design')} shown${state.includeCameras?'':' · no purchased camera required'}.`;
 $('#total-count').textContent=items.length;
 for(const d of items){
  const button=e('button','design-card');button.dataset.id=d.id;button.classList.toggle('active',d.id===state.selected?.id);
  button.setAttribute('aria-label',`Explore ${d.name}`);button.setAttribute('aria-controls','details');
  const img=e('img');img.src=url(d,'preview.png');img.alt=`CAD render of ${d.name}; not a photograph`;img.loading='lazy';img.width=640;img.height=600;
  button.append(img,e('span','card-num',String(state.catalog.indexOf(d)+1).padStart(2,'0')),e('span','card-arrow','+'));
  const info=e('div','card-info');info.append(e('h3','',d.name),e('p','',d.camera_system?`${d.camera_mount.name} · ${d.mounting.type==='hanging'?'hanging':d.mounting.type+' mount'}`:d.family));
  const count=printSummary[d.id]?.plate_count;info.append(e('span','part-count',`${count?plural(count,'plate'):'Plate count unavailable'} · ${plural(d.parts.length,'piece')}`));
  const sw=e('div','card-colors');for(const c of colors(d)){const dot=e('span','swatch');dot.style.background=c;sw.append(dot);}info.append(sw);button.append(info);
  button.onclick=()=>{selectDesign(d.id,{focus:true});experience.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});};list.append(button);
 }
 if(!items.length){const empty=e('div','catalog-empty');empty.append(e('h3','','No matching feeders'),e('p','','Try another search, allow more plates, or reset the filters.'));const reset=e('button','outline-link','Reset filters');reset.onclick=resetFilters;empty.append(reset);list.append(empty);}
}
function refreshCatalog(){closeDetails(false);renderFamilies();renderCards();showScene(showcase());}
function resetFilters(){state.family='All designs';state.query='';state.maxPlates=0;state.sort='featured';state.includeCameras=false;$('#catalog-search').value='';$('#plate-filter').value='0';$('#catalog-sort').value='featured';$('#include-cameras').checked=false;refreshCatalog();}
$('#catalog-search').addEventListener('input',ev=>{state.query=ev.target.value;refreshCatalog();});
$('#plate-filter').addEventListener('change',ev=>{state.maxPlates=Number(ev.target.value);refreshCatalog();});
$('#catalog-sort').addEventListener('change',ev=>{state.sort=ev.target.value;refreshCatalog();});
$('#include-cameras').addEventListener('change',ev=>{state.includeCameras=ev.target.checked;if(!state.includeCameras&&state.family==='Backyard camera feeders')state.family='All designs';refreshCatalog();});
$('#reset-filters').onclick=resetFilters;
async function selectDesign(id,{focus=false}={}){const d=state.catalog.find(x=>x.id===id);if(!d)throw Error('Unknown feeder');if(d.camera_system&&!state.includeCameras){state.includeCameras=true;$('#include-cameras').checked=true;renderFamilies();}clearPrintPlates();state.selected=d;state.part=null;state.explode=0;experience.classList.add('focused');$('#details').hidden=false;$('#back').hidden=false;$('#scene-hint').textContent=renderAvailable?'Drag to rotate · Scroll to zoom · Click a part to inspect':'CAD preview and downloads remain available below';$('#detail-family').textContent=d.family;$('#detail-name').textContent=d.name;$('#detail-description').textContent=d.description;renderCredits(d);const b=bounds(d);$('#camera-preview-note').hidden=!d.camera_system;$('#camera-preview-note').textContent='Illustrative purchased camera: dimensions and sensor positions are approximate. This design is intended for its listed camera only; fit and focus need a real-device trial. Camera, mounting hardware and any reused bottle are separate from printed parts.';$('#design-facts').innerHTML=`<span>${printSummary[d.id]?.plate_count?plural(printSummary[d.id].plate_count,'plate'):'Plate count unavailable'}<small>X1C PRINT PLAN ↓</small></span><span>${d.parts.length} pieces<small>PRINTED PARTS</small></span><span>${Math.round(b.size[0])} × ${Math.round(b.size[1])} × ${Math.round(b.size[2])}<small>PRINTED ASSEMBLY · MM</small></span>`;$('#swatches').replaceChildren();for(const c of colors(d)){const dot=e('span','swatch');dot.style.background=c;dot.title=c;$('#swatches').append(dot);}renderParts(d);renderAssembly(d);renderPrintPlates(d);$('#download-pack').href=url(d,`${d.id}-X1C.zip`);$('#download-cad').href=url(d,d.cad_download||`${d.id}.step`);$('#download-cad').textContent=d.cad_format_note?'CAD + sculpt mesh':d.cad_download?.endsWith('.zip')?'Assembly STEP ZIP':'Assembly STEP';setPane('parts');const pageLink=$('#design-page-link');pageLink.hidden=!productPageIds.includes(d.id);if(!pageLink.hidden)pageLink.href=`designs/${d.id}/`;renderCards();history.replaceState({},'',`#${d.id}`);renderSourcing(d);if(focus)$('#detail-name').focus({preventScroll:true});await showScene([d]);if(state.selected?.id===d.id&&renderAvailable){annotations.setDesign(d);startVisit(d);}return {id:d.id,name:d.name,parts:d.parts.length};}
async function downloadSTL(event,link,part){
 event.preventDefault();const label=link.textContent;link.textContent='Preparing…';
 try{const response=await fetch(link.href);if(!response.ok)throw Error('Download unavailable');let bytes=await response.arrayBuffer();const magic=new Uint8Array(bytes,0,Math.min(2,bytes.byteLength));if(magic[0]===31&&magic[1]===139)bytes=await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();const objectURL=URL.createObjectURL(new Blob([bytes],{type:'model/stl'}));const a=document.createElement('a');a.href=objectURL;a.download=part.file.replace(/\.gz$/,'');a.click();setTimeout(()=>URL.revokeObjectURL(objectURL),30000);}
 catch(error){link.textContent='Retry STL ↓';return;}finally{if(link.textContent!=='Retry STL ↓')link.textContent=label;}
}
function renderParts(d){const pane=$('#pane-parts');pane.replaceChildren();d.parts.forEach((p,i)=>{const row=e('div','part-row');row.dataset.part=i;const button=e('button','part-name');button.style.textAlign='left';button.append(e('span','',p.name),e('small','',p.support));button.onclick=()=>selectPart(i);const dot=e('span','swatch');dot.style.background=p.color;const a=e('a','',p.download_scope==='build'?'STLs ZIP ↓':p.download?.endsWith('.zip')?'STL ZIP ↓':'STL ↓');a.href=url(d,p.download||p.file);a.download='';a.title=p.download_scope==='build'?`Download all build STLs, including ${p.name}`:`Download ${p.name} STL`;if(p.download?.endsWith('.gz'))a.onclick=event=>downloadSTL(event,a,p);row.append(e('span','part-number',String(i+1).padStart(2,'0')),dot,button,a);pane.append(row);});}
function applyPartSelection(){
 for(const g of state.groups)g.userData.parts.forEach((p,j)=>p.traverse(o=>{if(!o.isMesh)return;const selected=state.part===null||state.part===j,m=o.material;m.userData.baseAppearance||={transparent:m.transparent,opacity:m.opacity,depthWrite:m.depthWrite};const base=m.userData.baseAppearance;m.transparent=!selected||base.transparent;m.opacity=base.opacity*(selected?1:.15);m.depthWrite=selected&&base.depthWrite;m.emissive?.setHex(state.part===j?0x15210a:0x000000);}));
 $$('.part-row').forEach(x=>x.classList.toggle('active',Number(x.dataset.part)===state.part));
}
function selectPart(i){if(!state.selected)return;if(state.inspection){setExplosion(100);birdVisit.time=13;birdVisit.bird.visible=false;setCyclePaused(true);fitCamera(true);}state.part=state.part===i?null:i;applyPartSelection();setPane('parts');}
function renderAssembly(d){const pane=$('#pane-build');pane.replaceChildren();
 pane.append(e('p','snap-note',d.mounting?.description||'Follow the part-specific assembly and installation notes.'));
 if(d.architecture){for(const [label,key] of [['Structure','form'],['Seed system','seed_system'],['Camera integration','camera_integration']])if(d.architecture[key])pane.append(e('p','',`${label}: ${d.architecture[key]}`));}
 if(d.mounting?.hardware)pane.append(e('p','',`Installation hardware: ${typeof d.mounting.hardware==='string'?d.mounting.hardware:JSON.stringify(d.mounting.hardware)}`));
 if(d.camera_service)pane.append(e('p','',`Camera service: ${d.camera_service}`));
 if(d.refill)pane.append(e('p','',d.refill));
 const ol=e('ol');for(const s of d.assembly||[])ol.append(e('li','',s));pane.append(ol);
 if(d.detail_features?.length){pane.append(e('h3','','Modeled into the print'));const ul=e('ul');for(const f of d.detail_features)ul.append(e('li','',typeof f==='string'?f:JSON.stringify(f)));pane.append(ul);}
 for(const joint of d.snap_joints||[]){const detail=e('details','joint-note');detail.append(e('summary','',joint.name||'Snap connection'),e('p','',joint.description||''));if(joint.release)detail.append(e('p','',typeof joint.release==='string'?joint.release:JSON.stringify(joint.release)));pane.append(detail);}
 for(const note of d.notes||[])pane.append(e('p','',note));
}

function setPane(name){for(const b of $$('.detail-tabs button')){const active=b.dataset.pane===name;b.setAttribute('aria-selected',String(active));b.tabIndex=active?0:-1;}for(const p of ['parts','build','plates'])$('#pane-'+p).hidden=p!==name;}
function closeDetails(reload=true,restoreFocus=false){const previousId=state.selected?.id;cancelVisit();clearPrintPlates();clearSourcing();annotations?.clear();state.selected=null;state.part=null;state.explode=0;experience.classList.remove('focused');$('#details').hidden=true;$('#back').hidden=true;$('#scene-hint').textContent='Click a feeder to explore it';history.replaceState({},'',location.pathname+location.search);renderCards();if(reload)showScene(showcase());if(restoreFocus&&previousId)($('#catalog')?.querySelector(`[data-id="${previousId}"]`)||$('#catalog-search')).focus({preventScroll:true});}
$('#close-details').onclick=()=>closeDetails(true,true);$('#back').onclick=()=>closeDetails(true,true);
$$('.detail-tabs button').forEach(b=>b.onclick=()=>setPane(b.dataset.pane));
$$('.detail-tabs button').forEach((b,i)=>b.addEventListener('keydown',ev=>{const keys=['ArrowRight','ArrowLeft','Home','End'];if(!keys.includes(ev.key))return;ev.preventDefault();const tabs=$$('.detail-tabs button'),index=ev.key==='Home'?0:ev.key==='End'?tabs.length-1:(i+(ev.key==='ArrowRight'?1:tabs.length-1))%tabs.length;tabs[index].focus();setPane(tabs[index].dataset.pane);}));
document.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&state.selected&&!$('#guide-dialog').open)closeDetails(true,true);});
window.addEventListener('hashchange',()=>{const id=designIdFromHash(location.hash);if(state.catalog.some(d=>d.id===id))selectDesign(id,{focus:true});else if(!id&&state.selected)closeDetails();});
const dialog=$('#guide-dialog');$('#guide-open').onclick=$('#guide-open-bottom').onclick=()=>dialog.showModal();$('#guide-close').onclick=()=>dialog.close();dialog.addEventListener('click',ev=>{if(ev.target===dialog&&ev.clientY>dialog.getBoundingClientRect().bottom)dialog.close();});
try{
 const r=await fetch('catalog.json');if(!r.ok)throw Error('Catalog missing');state.catalog=await r.json();await loadPrintSummary();state.catalog.sort((a,b)=>familyOrder.indexOf(a.family)-familyOrder.indexOf(b.family));const cameraCount=state.catalog.filter(d=>d.family==='Backyard camera feeders').length;$('#intro-copy').textContent=`${state.catalog.length-cameraCount} printable feeders. No camera, app or subscription required. Find your own little world, then make it.`;$('#scene-count').textContent=`${state.catalog.length-cameraCount} CAMERA-FREE DESIGNS`;renderFamilies();renderCards();const id=designIdFromHash(location.hash);if(state.catalog.some(x=>x.id===id))await selectDesign(id);else await showScene(showcase());
 if(document.modelContext?.registerTool){document.modelContext.registerTool({name:'explore_feeder',description:'Select a bird feeder in the 3D viewer and optionally explode its printable parts.',inputSchema:{type:'object',properties:{id:{type:'string'},explode:{type:'number',minimum:0,maximum:100}},required:['id'],additionalProperties:false},annotations:{readOnlyHint:false},execute:async input=>{if(!input||typeof input.id!=='string'||!state.catalog.some(d=>d.id===input.id)||input.explode!==undefined&&(typeof input.explode!=='number'||input.explode<0||input.explode>100))throw Error('Provide a valid feeder ID and explosion from 0 to 100.');const result=await selectDesign(input.id);if(input.explode!==undefined){setCyclePaused(true);if(birdVisit){birdVisit.time=13;birdVisit.bird.visible=false;}setExplosion(input.explode);fitCamera(true);}return result;}});document.modelContext.registerTool({name:'list_feeders',description:'List printable feeders, dimensions, physical parts, and print pack paths.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true},execute:async()=>state.catalog.map(d=>({id:d.id,name:d.name,family:d.family,parts:d.parts.length,dimensions_mm:bounds(d).size,download:url(d,d.id+'-X1C.zip')}))});}
}catch(error){console.error(error);$('#loading').hidden=true;$('#fallback').hidden=false;$('#fallback').textContent='The collection could not load. Refresh this page to try again.';}
