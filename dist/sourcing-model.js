export const money = n => Number.isFinite(n) ? new Intl.NumberFormat('en-US', {style:'currency',currency:'USD'}).format(n) : 'Price not verified';
export const hex = value => /^#[\da-f]{6}$/i.test(value || '') ? value.toUpperCase() : null;
export const validPrice = value => Number.isFinite(value) && value >= 0;
export function safeStoreUrl(value) {
  try { const url = new URL(value); return url.protocol === 'https:' && !url.username && !url.password ? url.href : null; } catch { return null; }
}
export function snapshotDate(offer, evidence) {
  return offer?.checked_date_utc || evidence?.filaments?.checked_at_utc?.slice(0,10) || evidence?.checked_date_utc || 'date not recorded';
}
function lab(h) {
  const [r,g,b] = h.slice(1).match(/../g).map(x => parseInt(x,16)/255).map(x => x > .04045 ? ((x+.055)/1.055)**2.4 : x/12.92);
  const f = x => x > .008856 ? Math.cbrt(x) : 7.787*x+16/116;
  const x=f((r*.4124+g*.3576+b*.1805)/.95047), y=f(r*.2126+g*.7152+b*.0722), z=f((r*.0193+g*.1192+b*.9505)/1.08883);
  return [116*y-16,500*(x-y),200*(y-z)];
}
function distance(a,b) { const x=lab(a),y=lab(b); return Math.hypot(...x.map((v,i)=>v-y[i])); }
function colorFamily(value) {
  const c = value.toLowerCase().replace(/ \(.*\)/,'').replace('asa-','');
  for (const [name,pattern] of [['black',/black/],['white',/white|natural/],['gray',/gray|grey|silver/],['brown',/brown/],['pink',/pink/],['purple',/purple/],['teal',/teal/]]) if(pattern.test(c)) return name;
  return ['red','green','orange','yellow','blue'].find(x=>c.includes(x)) || c;
}
export function colorsFor(design) {
  return [...new Set([...(design.colors || []).map(c => typeof c === 'string' ? c : c.hex || c.color), ...(design.parts || []).flatMap(p => [p.color, ...(p.regions || []).map(r => r.color)])].map(hex).filter(Boolean))];
}
export function matchColors(design, evidence) {
  const brands = evidence.filaments?.brands || [];
  const eligible = offer => offer.available === true && validPrice(offer.price_usd) && safeStoreUrl(offer.url) && offer.filament_weight_kg === 1;
  const pool = brands.flatMap(b => b.variants || []).filter(v => eligible(v) && hex(v.manufacturer_hex) && v.material === 'ASA');
  return colorsFor(design).map(target => {
    const primary = pool.slice().sort((a,b) => distance(target,a.manufacturer_hex)-distance(target,b.manufacturer_hex) || a.price_usd-b.price_usd)[0] || null;
    const alternatives = brands.map(b => {
      const variants = (b.variants || []).filter(v => primary && eligible(v) && ['ASA','ASA+'].includes(v.material) && colorFamily(v.color) === colorFamily(primary.color));
      variants.sort((a,b) => (hex(a.manufacturer_hex) ? distance(target,a.manufacturer_hex) : 999) - (hex(b.manufacturer_hex) ? distance(target,b.manufacturer_hex) : 999) || a.price_usd-b.price_usd);
      return {brand:b.brand,offer:variants[0] || null};
    });
    return {target,primary,alternatives};
  });
}
export function cameraKit(camera) {
  if (!camera) return {base:null,lens:null,total:null};
  const base = camera.prices?.find(p => p.primary === true && validPrice(p.usd)) || camera.prices?.find(p => validPrice(p.usd) && !/extra battery/i.test(p.seller));
  const lens = typeof camera.optics === 'object' && camera.optics.required ? camera.optics : null;
  return {base:base || null,lens,total:base && (!lens || validPrice(lens.usd)) ? base.usd + (lens?.usd || 0) : null};
}
export function buildShoppingSummary(matches, camera, requiresCamera = false) {
  const spools = [...new Map(matches.filter(m=>m.primary).map(m=>[m.primary.url,m.primary])).values()];
  const kit = cameraKit(camera), missingColors = matches.filter(m=>!m.primary).length;
  const complete = missingColors === 0 && (!requiresCamera || kit.total !== null);
  const filamentTotal = spools.reduce((sum,v)=>sum+v.price_usd,0);
  return {spools,kit,missingColors,complete,filamentTotal,total:complete ? filamentTotal + (requiresCamera ? kit.total : 0) : null};
}
