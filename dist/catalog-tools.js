// Pure catalog helpers: no rendering, network requests, or changes to CAD metadata.
export const plural = (n, singular, pluralForm = `${singular}s`) => `${n} ${n === 1 ? singular : pluralForm}`;
export function filterCatalog(catalog, summary, {family = 'All designs', query = '', includeCameras = false, maxPlates = 0, sort = 'featured'} = {}) {
  const terms = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const result = catalog.filter(design => {
    const searchable = [design.name, design.family, design.description, ...(design.detail_features || [])].join(' ').toLocaleLowerCase();
    const plates = summary[design.id]?.plate_count;
    return (includeCameras || !design.camera_system)
      && (family === 'All designs' || design.family === family)
      && (!maxPlates || Number.isFinite(plates) && plates <= Number(maxPlates))
      && terms.every(term => searchable.includes(term));
  });
  if (sort === 'plates') result.sort((a,b) => (summary[a.id]?.plate_count ?? Infinity) - (summary[b.id]?.plate_count ?? Infinity) || a.name.localeCompare(b.name));
  if (sort === 'name') result.sort((a,b) => a.name.localeCompare(b.name));
  return result;
}
export function designIdFromHash(hash) {
  try { return decodeURIComponent(hash.replace(/^#/, '')); } catch { return ''; }
}
