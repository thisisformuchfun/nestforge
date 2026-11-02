import { downloadPlate } from './zip-download.js';
const $=s=>document.querySelector(s);
let request=0;
export let printSummary={};
export async function loadPrintSummary(){try{const r=await fetch('print-plan-summary.json');if(r.ok)printSummary=await r.json();}catch{}return printSummary;}
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;};
export function formatHours(range){const f=n=>Number.isInteger(n)?String(n):n.toFixed(1);return `${f(range[0])}–${f(range[1])} h`;}
export function clearPrintPlates(){request++;$('#print-planning').hidden=true;$('#print-plate-grid').replaceChildren();$('#print-totals').replaceChildren();}
export async function renderPrintPlates(d){
 const ticket=++request,section=$('#print-planning'),grid=$('#print-plate-grid'),pane=$('#pane-plates');
 section.hidden=false;if($('#plan-material'))$('#plan-material').textContent=d.material||'PETG';$('#print-design-name').textContent=d.name;$('#print-title').textContent='What it takes to print';grid.textContent='Loading the plate layouts…';pane.textContent='Loading print plan…';
 try{
  const response=await fetch(`models/${d.id}/print-plan.json`);if(!response.ok)throw Error('Print plan missing');const plan=await response.json();if(ticket!==request)return;
  grid.replaceChildren();$('#print-totals').replaceChildren();
  for(const [value,label] of [[`${plan.plate_count}`,plan.plate_count===1?'X1C plate':'X1C plates'],[formatHours(plan.total_time_hours),'Estimated total · one printer']]){const item=el('div');item.append(el('strong','',value),el('span','',label));$('#print-totals').append(item);}
  pane.replaceChildren(el('p','plate-summary',`${plan.plate_count} ${plan.plate_count===1?'plate':'plates'} · estimated ${formatHours(plan.total_time_hours)} total`));
  const jump=el('a','plate-jump','See every plate below ↓');jump.href='#print-planning';jump.onclick=ev=>{ev.preventDefault();section.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});};pane.append(jump,el('p','plate-estimate-note','Actual part geometry in its packed print orientation. Time ranges are planning estimates; slice the 3MF for your exact profile.'));
  for(const plate of plan.plates){
   const card=el('article','print-plate');const image=el('img');image.src=`models/${d.id}/${plate.preview}`;image.alt=`Plate ${plate.number} for ${d.name}: ${plate.parts.join(', ')}, shown in their supplied print positions.`;image.width=610;image.height=500;image.loading='lazy';
   const info=el('div','print-plate-info'),heading=el('div','print-plate-heading');heading.append(el('h3','',`Plate ${String(plate.number).padStart(2,'0')}`),el('span','plate-time',`~ ${formatHours(plate.time_hours)}`));info.append(heading,el('p','plate-meta',`${plate.piece_count} printed ${plate.piece_count===1?'piece':'pieces'} · ${plate.colors.length} ${plate.colors.length===1?'color':'colors'} · unsliced estimate`));
   const parts=el('ul','plate-parts');for(const name of plate.parts)parts.append(el('li','',name));info.append(parts);
   const slots=el('div','plate-color-list');for(const color of plate.colors){const swatch=el('span','plate-color');const dot=el('i');dot.style.background=color.color;swatch.append(dot,document.createTextNode(`Slot ${color.extruder}`));swatch.title=color.color;slots.append(swatch);}info.append(slots);
   if(plate.reserved_prime_tower)info.append(el('p','prime-note','Outlined area reserves room for a prime tower.'));
   const link=el('a','plate-download','Download this plate · 3MF ↓');const archive=`models/${d.id}/${d.id}-X1C.zip`;link.href=archive;link.download='';link.onclick=event=>downloadPlate(event,link,archive,`${d.id}/${plate.file}`);info.append(link);card.append(image,info);grid.append(card);
  }
 }catch(error){if(ticket!==request)return;grid.textContent='Plate previews are unavailable. The print pack contains the populated 3MF plates.';pane.textContent=grid.textContent;console.error(error);}
}
