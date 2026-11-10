// Layer test page: every layer and basemap on one full-screen map, with fixed views at zooms 10, 12 and 14.
import '@fontsource/source-sans-3/latin-400.css';
import '@fontsource/source-sans-3/latin-600.css';
import '../styles.css';
import '../map/map.css';
import { BASEMAPS, OVERLAYS, createMap } from '../map/createMap.js';
import { DateChip, LegendCard } from '../ui/legend.js';

export const VIEWS = {
  cbd: { label: 'City centre', center: [36.8235, -1.2865] },
  eastlands: { label: 'Eastlands', center: [36.8870, -1.2830] },
  karura: { label: 'Karura', center: [36.8320, -1.2420] },
};

const el = (tag, attrs = {}, text = '') => Object.assign(document.createElement(tag), attrs, text ? { textContent: text } : {});

async function main() {
  const frame = document.getElementById('map');
  const ctl = await createMap(frame, { basemap: 'light', center: VIEWS.cbd.center, zoom: 12, scale: true, preserveDrawingBuffer: true });
  const legend = new LegendCard(frame, ctl.manifest);
  const chip = new DateChip(frame);
  const rasters = Object.values(ctl.manifest).filter((m) => m.kind === 'raster');
  let current = 'heat-diff';
  let opacity = 0.9;
  const overlays = new Set(['county-line', 'ward-labels']);
  const status = document.getElementById('status');

  const apply = () => {
    const ls = [{ id: current, opacity }];
    for (const o of overlays) ls.push({ id: o, opacity: 1 });
    if (current === 'buildings-only') ls.shift();
    ctl.setLayers(ls, 0);
    const legendKey = overlays.has('buildings') && ctl.map.getZoom() >= 14 ? 'buildings' : current;
    legend.show(legendKey);
    chip.set(ctl.manifest[legendKey]?.chip);
  };

  const bm = document.getElementById('basemaps');
  Object.entries(BASEMAPS).forEach(([k, v]) => {
    const l = el('label');
    const i = el('input', { type: 'radio', name: 'basemap', value: k, checked: k === ctl.basemap });
    i.addEventListener('change', async () => { await ctl.setBasemap(k); opacity = v.imagery ? 0.75 : 0.9; syncOpacity(); apply(); });
    l.append(i, ` ${v.label}`);
    bm.append(l);
  });
  const rs = document.getElementById('rasters');
  rasters.forEach((m) => {
    const l = el('label');
    const i = el('input', { type: 'radio', name: 'raster', value: m.id, checked: m.id === current });
    i.addEventListener('change', () => { current = m.id; apply(); });
    l.append(i, ` ${m.id}`);
    rs.append(l);
  });
  const ov = document.getElementById('overlays');
  Object.keys(OVERLAYS).filter((k) => k !== 'ward-highlight').forEach((k) => {
    const l = el('label');
    const i = el('input', { type: 'checkbox', value: k, checked: overlays.has(k) });
    i.addEventListener('change', () => { if (i.checked) overlays.add(k); else overlays.delete(k); apply(); });
    l.append(i, ` ${k}`);
    ov.append(l);
  });
  const op = document.getElementById('opacity');
  const opOut = document.getElementById('opacity-out');
  const syncOpacity = () => { op.value = opacity; opOut.textContent = opacity.toFixed(2); };
  op.addEventListener('input', () => { opacity = Number(op.value); opOut.textContent = opacity.toFixed(2); apply(); });
  const vs = document.getElementById('views');
  Object.entries(VIEWS).forEach(([k, v]) => {
    const row = el('div', { className: 'layers-page__view' });
    row.append(el('span', {}, v.label));
    [10, 12, 14].forEach((z) => {
      const b = el('button', { type: 'button' }, `z${z}`);
      b.addEventListener('click', () => ctl.map.jumpTo({ center: v.center, zoom: z }));
      row.append(b);
    });
    vs.append(row);
  });
  ctl.map.on('moveend', () => { status.textContent = `Zoom ${ctl.map.getZoom().toFixed(1)}`; apply(); });
  apply();

  // Hooks for the Playwright screenshot script (site/qa/v2_layers.mjs).
  window.__layers = {
    ctl,
    async set({ basemap, raster, overlays: ovs, opacity: o, view, zoom }) {
      if (basemap) await ctl.setBasemap(basemap);
      if (raster) current = raster;
      if (ovs) { overlays.clear(); ovs.forEach((x) => overlays.add(x)); }
      if (o !== undefined) opacity = o;
      if (view) ctl.map.jumpTo({ center: VIEWS[view].center, zoom });
      apply();
      await new Promise((r) => { if (ctl.map.loaded() && ctl.map.areTilesLoaded()) setTimeout(r, 300); else ctl.map.once('idle', () => setTimeout(r, 200)); });
    },
  };
}

main().catch((e) => { console.error(e); });
