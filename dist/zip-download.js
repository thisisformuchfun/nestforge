// Individual native plates are stored once, inside their complete print pack.
// Extract exactly the named ZIP entry; never regenerate or modify the 3MF.
const crcTable=Uint32Array.from({length:256},(_,n)=>{let c=n;for(let i=0;i<8;i++)c=(c&1)?0xedb88320^(c>>>1):c>>>1;return c>>>0;});
export function crc32(bytes){let crc=0xffffffff;for(const byte of bytes)crc=crcTable[(crc^byte)&255]^(crc>>>8);return (crc^0xffffffff)>>>0;}
export async function extractZipEntry(buffer, name) {
 const view=new DataView(buffer), bytes=new Uint8Array(buffer);
 const requireRange=(offset,length)=>{if(!Number.isSafeInteger(offset)||!Number.isSafeInteger(length)||offset<0||length<0||offset+length>bytes.length)throw Error('Truncated ZIP');};
 if(bytes.length<22)throw Error('ZIP directory missing');
 let end=-1;
 for(let i=buffer.byteLength-22;i>=Math.max(0,buffer.byteLength-65557);i--){if(view.getUint32(i,true)===0x06054b50&&i+22+view.getUint16(i+20,true)===bytes.length){end=i;break;}}
 if(end<0)throw Error('ZIP directory missing');
 if(view.getUint16(end+4,true)||view.getUint16(end+6,true))throw Error('Split ZIP files are unsupported');
 const count=view.getUint16(end+10,true);let pos=view.getUint32(end+16,true);
 const directorySize=view.getUint32(end+12,true);
 if(count===65535||pos===0xffffffff||directorySize===0xffffffff)throw Error('ZIP64 files are unsupported');
 requireRange(pos,directorySize);if(pos+directorySize>end)throw Error('Invalid ZIP directory bounds');
 for(let i=0;i<count;i++){
  requireRange(pos,46);
  if(view.getUint32(pos,true)!==0x02014b50)throw Error('Invalid ZIP directory');
  const flags=view.getUint16(pos+8,true),method=view.getUint16(pos+10,true),checksum=view.getUint32(pos+16,true),length=view.getUint32(pos+20,true),size=view.getUint32(pos+24,true);
  const n=view.getUint16(pos+28,true),extra=view.getUint16(pos+30,true),comment=view.getUint16(pos+32,true);
  requireRange(pos+46,n+extra+comment);
  const entry=new TextDecoder().decode(bytes.subarray(pos+46,pos+46+n));
  if(entry===name){
   if(flags&1)throw Error('Encrypted ZIP files are unsupported');
   const offset=view.getUint32(pos+42,true);
   requireRange(offset,30);
   if(view.getUint32(offset,true)!==0x04034b50)throw Error('Invalid ZIP entry');
   if(view.getUint16(offset+8,true)!==method)throw Error('ZIP method mismatch');
   const start=offset+30+view.getUint16(offset+26,true)+view.getUint16(offset+28,true);
   requireRange(start,length);if(start+length>view.getUint32(end+16,true))throw Error('Invalid ZIP entry bounds');
   const packed=bytes.slice(start,start+length);let result;
   if(method===0)result=packed;
   else if(method===8)result=new Uint8Array(await new Response(new Blob([packed]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).arrayBuffer());
   else throw Error('Unsupported ZIP compression');
   if(result.byteLength!==size)throw Error('Incomplete plate download');
   if(crc32(result)!==checksum)throw Error('Plate checksum mismatch');
   return result;
  }
  pos+=46+n+extra+comment;
 }
 throw Error('Plate not found in print pack');
}
export async function downloadPlate(event,link,archive,entry){
 event.preventDefault();const label=link.textContent;link.textContent='Preparing this plate…';
 try{
  const response=await fetch(archive);if(!response.ok)throw Error('Print pack unavailable');
  const bytes=await extractZipEntry(await response.arrayBuffer(),entry);
  const object=URL.createObjectURL(new Blob([bytes],{type:'model/3mf'}));const a=document.createElement('a');a.href=object;a.download=entry.split('/').pop();a.click();setTimeout(()=>URL.revokeObjectURL(object),30000);link.textContent=label;
 }catch(error){link.textContent='Download complete print pack ↓';link.onclick=null;link.href=archive;link.title='This browser could not extract one plate. The complete ZIP contains it unchanged.';}
}
