// "Find your ward": layer buttons, a searchable ward list, a ward panel and a shareable URL hash.
import { Popup } from 'maplibre-gl';
import { fmtC, fmtInt, fmtPct, fmtSignedC, getJSON } from './config.js';
import { renderLegend } from './legend.js';
import { addBuildings, createMap, setWards, showRaster } from './maps.js';

const LAYERS = ['lst_hot_season', 'lst_anomaly', 'tree_fraction', 'population', 'buildings'];

function readHash() {
  const p = new URLSearchParams(window.location.hash.replace(/^#/, ''));
  return { layer: LAYERS.includes(p.get('layer')) ? p.get('layer') : null, ward: p.get('ward') };
}

function writeHash(state) {
  const p = new URLSearchParams();
  p.set('layer', state.layer);
  if (state.ward) p.set('ward', state.ward);
  window.history.replaceState(null, '', `#${p.toString()}`);
}

function bbox(geom) {
  let [x0, y0, x1, y1] = [180, 90, -180, -90];
  const walk = (c) => { if (typeof c[0] === 'number') { x0 = Math.min(x0, c[0]); y0 = Math.min(y0, c[1]); x1 = Math.max(x1, c[0]); y1 = Math.max(y1, c[1]); } else c.forEach(walk); };
  walk(geom.coordinates);
  return [[x0, y0], [x1, y1]];
}

export async function initExplorer(section) {
  const mapEl = section.querySelector('[data-explorer-map]');
  const legendEl = section.querySelector('[data-legend-explorer]');
  const panel = section.querySelector('[data-ward-panel]');
  const buttons = [...section.querySelectorAll('[data-layer-buttons] button')];
  const input = section.querySelector('#ward-input');
  const list = section.querySelector('#ward-list');
  const [wardsGeo, legends] = await Promise.all([getJSON('data/wards.geojson'), getJSON('data/legends.json')]);
  const wards = wardsGeo.features.map((f) => f.properties).sort((a, b) => a.ward_name.localeCompare(b.ward_name));
  const byId = Object.fromEntries(wardsGeo.features.map((f) => [f.properties.ward_id, f]));
  const n = wards.length;
  const countyMedian = legends._meta.county_median_c;

  const map = await createMap(mapEl);
  addBuildings(map);
  setWards(map, 'outline');

  const hash = readHash();
  const state = { layer: hash.layer || 'lst_hot_season', ward: hash.ward && byId[hash.ward] ? hash.ward : null };

  function overview() {
    const top5 = [...wards].sort((a, b) => a.rank_hottest - b.rank_hottest).slice(0, 5);
    panel.innerHTML = `<h3>Nairobi County</h3>
      <dl><dt>Median surface temperature, hot-season mornings</dt><dd>${fmtC(countyMedian)}</dd>
      <dt>Wards</dt><dd>${n}</dd></dl>
      <p class="muted">The five hottest wards by median surface temperature:</p>
      <ol>${top5.map((w) => `<li><button type="button" class="linklike" data-ward="${w.ward_id}">${w.ward_name}</button>, ${fmtC(w.lst_median_c)}</li>`).join('')}</ol>
      <p class="muted">Choose a ward to see its numbers.</p>`;
  }

  function wardPanel(p) {
    panel.innerHTML = `<h3>${p.ward_name}</h3>
      <dl>
        <dt>Median surface temperature</dt><dd>${fmtC(p.lst_median_c)}</dd>
        <dt>Difference from the city median</dt><dd>${fmtSignedC(p.lst_anomaly_c)}</dd>
        <dt>Rank, hottest first</dt><dd>${p.rank_hottest} of ${n}</dd>
        <dt>Surface temperature under its people</dt><dd>${fmtC(p.pop_weighted_lst_c)}</dd>
        <dt>People (WorldPop 2025 estimate)</dt><dd>${fmtInt(Math.round(p.pop_total / 100) * 100)}</dd>
        <dt>Tree cover</dt><dd>${fmtPct(p.tree_pct)}</dd>
        <dt>Built-up land</dt><dd>${fmtPct(p.built_pct)}</dd>
        <dt>Cool-season median</dt><dd>${fmtC(p.cool_lst_median_c)}</dd>
      </dl>
      <p class="muted">Land surface temperature on clear January to March mornings, 2023 to 2026, measured at about 100 m. City median ${fmtC(countyMedian)}.</p>
      <p><button type="button" class="linklike" data-ward="">Back to the county overview</button></p>`;
  }

  function setLayer(layer) {
    state.layer = layer;
    buttons.forEach((b) => b.setAttribute('aria-checked', String(b.dataset.layer === layer)));
    if (layer === 'buildings') {
      showRaster(map, null);
      map.setLayoutProperty('bldg-lst', 'visibility', 'visible');
      if (map.getZoom() < 13.5) map.easeTo({ zoom: 14, duration: 0 });
    } else {
      map.setLayoutProperty('bldg-lst', 'visibility', 'none');
      showRaster(map, layer);
    }
    renderLegend(legendEl, layer);
    writeHash(state);
  }

  function selectWard(id, { fly = true } = {}) {
    state.ward = id || null;
    map.setFilter('ward-selected', ['==', ['get', 'ward_id'], state.ward || '']);
    if (state.ward) {
      const f = byId[state.ward];
      wardPanel(f.properties);
      input.value = f.properties.ward_name;
      if (fly) map.fitBounds(bbox(f.geometry), { padding: 40, maxZoom: 15, duration: 0 });
    } else {
      overview();
      input.value = '';
      if (fly) map.fitBounds(map.countyBounds, { padding: 16, duration: 0 });
    }
    writeHash(state);
  }

  buttons.forEach((b) => b.addEventListener('click', () => setLayer(b.dataset.layer)));
  // Arrow keys move between layer buttons, like a radio group.
  section.querySelector('[data-layer-buttons]').addEventListener('keydown', (e) => {
    const i = buttons.indexOf(document.activeElement);
    if (i < 0) return;
    let j = null;
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') j = (i + 1) % buttons.length;
    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') j = (i - 1 + buttons.length) % buttons.length;
    if (j === null) return;
    e.preventDefault();
    buttons[j].focus();
    setLayer(buttons[j].dataset.layer);
  });
  panel.addEventListener('click', (e) => {
    const b = e.target.closest('[data-ward]');
    if (b) selectWard(b.dataset.ward);
  });

  // Searchable, keyboard-accessible ward list (combobox pattern).
  let matches = [];
  let active = -1;
  const close = () => { list.hidden = true; input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); active = -1; };
  const render = () => {
    const q = input.value.trim().toLowerCase();
    matches = wards.filter((w) => w.ward_name.toLowerCase().includes(q));
    list.innerHTML = matches.map((w, i) => `<li role="option" id="ward-opt-${i}" data-ward="${w.ward_id}" aria-selected="${i === active}">${w.ward_name}</li>`).join('')
      || '<li role="option" aria-disabled="true">No ward matches</li>';
    list.hidden = false;
    input.setAttribute('aria-expanded', 'true');
    if (active >= 0) input.setAttribute('aria-activedescendant', `ward-opt-${active}`);
  };
  input.addEventListener('focus', () => { active = -1; render(); });
  input.addEventListener('input', () => { active = -1; render(); });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') { active = Math.min(active + 1, matches.length - 1); render(); list.children[active]?.scrollIntoView({ block: 'nearest' }); e.preventDefault(); }
    else if (e.key === 'ArrowUp') { active = Math.max(active - 1, 0); render(); list.children[active]?.scrollIntoView({ block: 'nearest' }); e.preventDefault(); }
    else if (e.key === 'Enter') { const w = matches[active >= 0 ? active : 0]; if (w) { selectWard(w.ward_id); close(); } e.preventDefault(); }
    else if (e.key === 'Escape') { close(); }
  });
  list.addEventListener('mousedown', (e) => {
    const li = e.target.closest('li[data-ward]');
    if (li) { e.preventDefault(); selectWard(li.dataset.ward); close(); }
  });
  input.addEventListener('blur', () => setTimeout(close, 120));

  // Click or tap selects the ward under the pointer; hover shows a small convenience tooltip.
  const pop = new Popup({ closeButton: false, closeOnClick: false, offset: 10, className: 'ward-tip' });
  map.on('click', (e) => {
    const f = map.queryRenderedFeatures(e.point, { layers: ['ward-line'] })[0]
      || wardsGeo.features.find((g) => pointInFeature([e.lngLat.lng, e.lngLat.lat], g));
    if (f) selectWard(f.properties.ward_id, { fly: false });
  });
  map.on('mousemove', (e) => {
    const f = wardsGeo.features.find((g) => pointInFeature([e.lngLat.lng, e.lngLat.lat], g));
    if (!f) { pop.remove(); map.getCanvas().style.cursor = ''; return; }
    map.getCanvas().style.cursor = 'pointer';
    pop.setLngLat(e.lngLat).setHTML(`<strong>${f.properties.ward_name}</strong><br>${fmtC(f.properties.lst_median_c)}`).addTo(map);
  });
  map.getCanvas().addEventListener('mouseleave', () => pop.remove());

  setLayer(state.layer);
  selectWard(state.ward, { fly: Boolean(state.ward) });
  return map;
}

// Ray casting point-in-polygon for GeoJSON Polygon and MultiPolygon.
function pointInRing(pt, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < ((xj - xi) * (pt[1] - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}
function pointInFeature(pt, f) {
  const polys = f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates;
  return polys.some((rings) => pointInRing(pt, rings[0]) && !rings.slice(1).some((h) => pointInRing(pt, h)));
}
