import * as THREE from 'three';
const NS='http://www.w3.org/2000/svg';
export class PartAnnotations {
 constructor(viewport,onSelect){
  this.viewport=viewport;this.onSelect=onSelect;this.rows=[];this.layer=document.createElement('div');this.layer.className='part-annotations';this.layer.hidden=true;
  this.svg=document.createElementNS(NS,'svg');this.svg.setAttribute('aria-hidden','true');this.layer.append(this.svg);viewport.append(this.layer);
 }
 clear(){for(const r of this.rows){r.button.remove();r.line.remove();r.dot.remove();}this.rows=[];this.layer.hidden=true;}
 setDesign(d){this.clear();d.parts.forEach((p,i)=>{
  const button=document.createElement('button');button.className='part-callout';button.setAttribute('aria-label',`Inspect part ${i+1}: ${p.name}`);
  const number=document.createElement('span');number.className='callout-number';number.textContent=String(i+1).padStart(2,'0');
  const title=document.createElement('strong');title.textContent=p.name;const sub=document.createElement('small');sub.textContent='Click to isolate';button.append(number,title,sub);button.onclick=()=>this.onSelect(i);
  const line=document.createElementNS(NS,'path');const dot=document.createElementNS(NS,'circle');dot.setAttribute('r','3');this.svg.append(line,dot);this.layer.append(button);
  this.rows.push({button,line,dot,index:i,position:null});
 });}
 update(group,camera,explode,selected){
  this.layer.hidden=!group||explode<8;if(this.layer.hidden)return;
  const w=this.viewport.clientWidth,h=this.viewport.clientHeight,mobile=w<600,width=mobile?108:174,margin=mobile?8:22,top=65,bottom=h-100;
  this.svg.setAttribute('viewBox',`0 0 ${w} ${h}`);group.updateMatrixWorld(true);
  const sides=[[],[]];for(const row of this.rows){
   const p=group.userData.partOverrides?.[row.index]||group.userData.design.parts[row.index],b=p.bounds;const v=new THREE.Vector3((b[0]+b[3])/2,(b[1]+b[4])/2,(b[2]+b[5])/2).applyMatrix4(group.userData.parts[row.index].matrixWorld).project(camera);
   row.anchor={x:(v.x*.5+.5)*w,y:(-.5*v.y+.5)*h};row.button.hidden=v.z>1||v.z< -1;row.line.style.display=row.dot.style.display=row.button.hidden?'none':'';
   row.side=row.index%2;row.y=THREE.MathUtils.clamp(row.anchor.y,top,bottom);sides[row.side].push(row);
  }
  for(const side of sides){side.sort((a,b)=>a.y-b.y);let last=top-72;for(const row of side){row.y=Math.max(row.y,last+72);last=row.y;}const overflow=Math.max(0,last-bottom);for(const row of side)row.y-=overflow;}
  for(const row of this.rows){
   const desired={x:row.side?w-margin-width:margin,y:row.y};if(!row.position)row.position={...desired};else{row.position.x+=(desired.x-row.position.x)*.18;row.position.y+=(desired.y-row.position.y)*.18;}
   const x=row.position.x,y=row.position.y;row.button.style.width=width+'px';row.button.style.transform=`translate(${x}px,${y-24}px)`;row.button.classList.toggle('selected',row.index===selected);
   const edge=row.side?x:x+width,elbow=row.side?edge-14:edge+14;row.line.setAttribute('d',`M${row.anchor.x.toFixed(1)},${row.anchor.y.toFixed(1)} L${elbow.toFixed(1)},${y.toFixed(1)} L${edge.toFixed(1)},${y.toFixed(1)}`);row.dot.setAttribute('cx',row.anchor.x);row.dot.setAttribute('cy',row.anchor.y);
  }
 }
}
