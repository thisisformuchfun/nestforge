// Real field recording. Playback begins only after an explicit Sound choice;
// the mute preference survives navigation and no audio runs in a hidden tab.
export function setupNatureAudio(){
 const button=document.querySelector('#sound-toggle'),volume=document.querySelector('#sound-volume'),status=document.querySelector('#sound-status');
 const audio=new Audio(new URL('./assets/nature-loop.mp3',import.meta.url).href);audio.loop=true;audio.preload='none';let enabled=false,muted=true,level=.32;
 try{const stored=localStorage.getItem('nestforge-volume');if(stored!==null&&Number.isFinite(Number(stored))&&Number(stored)>=0&&Number(stored)<=1)level=Number(stored);}catch{}
 volume.value=Math.round(level*100);audio.volume=level;
 const save=()=>{try{localStorage.setItem('nestforge-sound',enabled?'enabled':'muted');localStorage.setItem('nestforge-volume',String(level));}catch{}};
 const show=()=>{button.setAttribute('aria-pressed',String(enabled));button.textContent=enabled?'♫ Sound on':'♪ Sound off';status.textContent=enabled?'Birdsong & breeze':'Tap to hear the garden';};
 async function enable(){try{audio.volume=level;await audio.play();enabled=true;muted=false;show();save();}catch{enabled=false;show();status.textContent='Tap Sound to start audio';}}
 button.onclick=()=>{if(enabled){audio.pause();enabled=false;muted=true;show();save();}else enable();};
 volume.oninput=()=>{level=Number(volume.value)/100;audio.volume=level;if(!enabled&&level>0)enable();else save();};
 document.addEventListener('visibilitychange',()=>{if(document.hidden)audio.pause();else if(enabled)audio.play().catch(()=>{enabled=false;show();});});
 audio.addEventListener('error',()=>{enabled=false;show();status.textContent='Nature audio unavailable';});show();
 return {audio,enable,pause:()=>{audio.pause();enabled=false;show();},get enabled(){return enabled;}};
}
