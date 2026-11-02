import { validShortlist, toggleShortlist } from './shortlist-state.js';
const key='nestforge-concept-shortlist-v1';
try {
 const response=await fetch(new URL('./editorial-data.json',import.meta.url));if(!response.ok)throw Error('Unavailable');
 const {concepts}=await response.json(),allowed=concepts.map(c=>c.id);let items=[],durable=true;
 try {items=validShortlist(localStorage.getItem(key),allowed);}catch{durable=false;}
 const buttons=[...document.querySelectorAll('[data-concept-id]')],list=document.getElementById('shortlist-items'),status=document.getElementById('shortlist-status'),exportButton=document.getElementById('export-shortlist');
 function render(){
  for(const button of buttons){const saved=items.includes(button.dataset.conceptId);button.setAttribute('aria-pressed',String(saved));button.textContent=saved?'Remove from shortlist':'Save to my shortlist';}
  if(list){list.replaceChildren();for(const id of items){const c=concepts.find(c=>c.id===id),li=document.createElement('li'),a=document.createElement('a'),remove=document.createElement('button');a.href=new URL(`./concepts/${id}/`,import.meta.url).href;a.textContent=c.name;remove.textContent='Remove';remove.setAttribute('aria-label',`Remove ${c.name} from shortlist`);remove.onclick=()=>toggle(id);li.append(a,remove);list.append(li);}}
  if(exportButton)exportButton.disabled=items.length===0;
  if(status)status.textContent=items.length?`${items.length} ${items.length===1?'idea':'ideas'} saved ${durable?'in this browser':'for this visit only; browser storage is unavailable'}. Nothing has been submitted.`:'No ideas saved. Shortlisting is private to this browser.';
 }
 function toggle(id){items=toggleShortlist(items,id,allowed);try{localStorage.setItem(key,JSON.stringify(items));durable=true;}catch{durable=false;}render();}
 for(const button of buttons)button.onclick=()=>toggle(button.dataset.conceptId);
 if(exportButton)exportButton.onclick=()=>{const selected=items.map(id=>concepts.find(c=>c.id===id));const file={title:'My NestForge concept shortlist',concept_only:true,print_files_available:false,selected:selected.map(({id,name,theme})=>({id,name,theme}))};const url=URL.createObjectURL(new Blob([JSON.stringify(file,null,2)+'\n'],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='nestforge-concept-shortlist.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 render();
}catch{
 for(const button of document.querySelectorAll('[data-concept-id]')){button.disabled=true;button.textContent='Shortlist unavailable';}
 const status=document.getElementById('shortlist-status');if(status)status.textContent='The shortlist could not load. The concept descriptions and existing downloads are still available.';
}
