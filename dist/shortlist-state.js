export function validShortlist(raw, allowed) {
 try { const parsed=typeof raw==='string'?JSON.parse(raw):raw;return Array.isArray(parsed)?[...new Set(parsed.filter(id=>typeof id==='string'&&allowed.includes(id)))]:[]; } catch { return []; }
}
export function toggleShortlist(items,id,allowed) {
 const clean=validShortlist(items,allowed);return allowed.includes(id)?clean.includes(id)?clean.filter(x=>x!==id):[...clean,id]:clean;
}
