import * as THREE from 'three';
const smooth=t=>{t=THREE.MathUtils.clamp(t,0,1);return t*t*(3-2*t);};

// A feathered songbird, modeled here in millimetres to share the CAD's scale.
// Its body points along +Z; wings articulate about their shoulder pivots.
export function createSongbird(){
 const bird=new THREE.Group(),body=new THREE.Group();bird.add(body);
 const materials={back:new THREE.MeshStandardMaterial({color:0x657574,roughness:.87}),buff:new THREE.MeshStandardMaterial({color:0xb5aa89,roughness:.94}),cream:new THREE.MeshStandardMaterial({color:0xd9d4be,roughness:.92}),dark:new THREE.MeshStandardMaterial({color:0x20292b,roughness:.78}),wing:new THREE.MeshStandardMaterial({color:0x4b585b,roughness:.86}),edge:new THREE.MeshStandardMaterial({color:0x929d98,roughness:.9}),beak:new THREE.MeshStandardMaterial({color:0x3c4140,roughness:.64}),eye:new THREE.MeshPhysicalMaterial({color:0x080b0a,roughness:.15,clearcoat:.5})};
 const sphere=new THREE.SphereGeometry(1,20,14);
 function oval(parent,mat,pos,scale){const m=new THREE.Mesh(sphere,materials[mat]);m.position.set(...pos);m.scale.set(...scale);m.castShadow=true;m.receiveShadow=true;parent.add(m);return m;}
 oval(body,'back',[0,0,0],[8.7,10.5,19]);oval(body,'buff',[0,-3,2],[8,8,16]);oval(body,'cream',[0,-3,13],[6.8,7.2,9]);
 const head=new THREE.Group();head.position.set(0,8,17);body.add(head);
 oval(head,'dark',[0,1,0],[7.6,7.5,8.2]);
 for(const side of [-1,1]){oval(head,'cream',[side*6.1,-1.1,1.4],[1.9,4,5.3]);oval(head,'eye',[side*6.7,1.7,4],[1.3,1.3,1.1]);oval(head,'cream',[side*7.45,2.05,4.35],[.24,.25,.25]);}
 oval(head,'dark',[0,-4.1,4.1],[4.4,3,4.5]);
 const beak=new THREE.Mesh(new THREE.ConeGeometry(2.1,7,12),materials.beak);beak.rotation.x=Math.PI/2;beak.position.set(0,.1,10);head.add(beak);
 const wings=[];
 for(const side of [-1,1]){
  const wing=new THREE.Group();wing.position.set(side*6,3,2);body.add(wing);wings.push(wing);
  const shoulder=oval(wing,'back',[side*8,0,-1],[11,2.7,9]);shoulder.rotation.y=side*.35;
  for(let i=0;i<9;i++){
   const feather=oval(wing,i%3===0?'edge':'wing',[side*(15+i*2.6),-.6,-2-i*1.8],[2.3,.65,13-i*.42]);
   feather.rotation.y=side*(.65+i*.09);
  }
  for(let i=0;i<5;i++){const covert=oval(wing,'back',[side*(10+i*3),1.15,-i],[2.5,.65,7]);covert.rotation.y=side*.55;}
 }
 for(let i=-2;i<=2;i++){const tail=oval(body,i%2?'edge':'wing',[i*2.2,0,-23],[1.65,.7,13]);tail.rotation.y=-i*.09;tail.rotation.x=-.1;}
 for(const side of [-1,1]){
  oval(body,'beak',[side*3.5,-10,2],[.65,3,.65]);
  for(let i=-1;i<=1;i++){const toe=oval(body,'beak',[side*3.5+i*.7,-12.5,4],[.4,.45,2.4]);toe.rotation.y=i*.2;}
 }
 bird.visible=false;bird.userData={body,head,wings};return bird;
}

// Pure timeline sampling makes cancellation and animation tests deterministic.
export const VISIT_CYCLE_SECONDS=25;
export function sampleVisit(seconds,radius,height,feedingTarget=null){
 seconds=((seconds%VISIT_CYCLE_SECONDS)+VISIT_CYCLE_SECONDS)%VISIT_CYCLE_SECONDS;
 const centerY=Math.min(height*.12,24),r=radius+48;
 const landing=feedingTarget?feedingTarget.clone().add(new THREE.Vector3(0,13.5,0)):new THREE.Vector3(r*.55,centerY-7,r*.82);
 let point,phase;
 if(seconds<1.8){const t=smooth(seconds/1.8);const angle=2.65*(1-t),approachRadius=r*(1+2.4*(1-t));point=new THREE.Vector3(Math.cos(angle)*approachRadius,centerY+height*.7*(1-t),Math.sin(angle)*approachRadius+r*.15);phase='A visitor is arriving';}
 else if(seconds<6.8){const t=(seconds-1.8)/5,angle=t*Math.PI*2.25;point=new THREE.Vector3(Math.cos(angle)*r,centerY+Math.sin(t*Math.PI*2)*17,Math.sin(angle)*r+r*.15);phase='A curious look around';}
 else if(seconds<8.3){const t=smooth((seconds-6.8)/.8);point=new THREE.Vector3().lerpVectors(new THREE.Vector3(Math.cos(Math.PI*2.25)*r,centerY,Math.sin(Math.PI*2.25)*r+r*.15),landing,t);if(!feedingTarget)point.y+=Math.sin(seconds*5)*1.5;phase=feedingTarget&&seconds>=7.6?'A moment at the feeder':'One last look';}
 else {const t=smooth((seconds-8.3)/1.7);point=new THREE.Vector3().lerpVectors(landing,new THREE.Vector3(r*3.8,height*1.5,-r*2),t);phase=seconds<10?'Back to the trees':'Exploring the assembly';}
 let explode=0;
 if(seconds>=10&&seconds<12.4){explode=100*smooth((seconds-10)/2.4);phase='Every detail unfolds';}
 else if(seconds>=12.4&&seconds<19.4){explode=100;phase='Explore the printed parts';}
 else if(seconds>=19.4&&seconds<22.6){explode=100*(1-smooth((seconds-19.4)/3.2));phase='Coming back together';}
 else if(seconds>=22.6){phase='Ready for another visitor';}
 return {point,phase,visible:seconds<10,explode};
}
export class BirdVisit {
 constructor(scene){this.bird=createSongbird();scene.add(this.bird);this.active=false;this.time=0;this.radius=100;this.height=200;}
 start(bounds,feedingTarget=null,model=null){this.feedingTarget=feedingTarget;this.model=model;this.time=0;this.radius=Math.hypot(bounds.size[0],bounds.size[1])/2;this.height=bounds.size[2];this.active=true;this.bird.visible=true;}
 cancel(){this.active=false;this.bird.visible=false;}
 update(dt){
  if(!this.active)return null;this.time=(this.time+dt)%VISIT_CYCLE_SECONDS;let target=null;if(this.feedingTarget&&this.model){this.model.updateMatrixWorld(true);target=new THREE.Vector3(...this.feedingTarget).applyMatrix4(this.model.userData.native.matrixWorld);}const sample=sampleVisit(this.time,this.radius,this.height,target);this.bird.visible=sample.visible;
  if(sample.visible){
   this.bird.position.copy(sample.point);const next=sampleVisit(this.time+.025,this.radius,this.height,target).point;
   if(this.time>6.8&&this.time<8.3){this.bird.lookAt(0,sample.point.y,0);}else this.bird.lookAt(next);
   const bank=this.time>1.8&&this.time<6.8?.24:0;this.bird.rotateZ(-bank);
   const flap=Math.sin(this.time*Math.PI*2*(this.time>6.8&&this.time<8.3?10:7.5));
   const perched=target&&this.time>=7.6&&this.time<8.3;
   this.bird.userData.wings.forEach((w,i)=>{const side=i===0?-1:1;w.rotation.z=side*(perched?.08:.15+flap*.78);w.rotation.y=perched?side*1.3:0;});
   this.bird.userData.head.rotation.y=Math.sin(this.time*2.7)*.16;
   this.bird.userData.head.rotation.x=Math.sin(this.time*4)*.06;
  }
  return sample;
 }
}
