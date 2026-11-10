// The explorer (chunk 5): a small version of NASA's dashboard exploration view.
// Layer panel with groups, real checkboxes, opacity sliders and "i" buttons; a built-up year selector with a
// play button (paused by default); swipe compare with a layer picker per side; an accessible ward combobox
// and ward panel; building popups from zoom 14; the whole view written into the URL hash.
import mapboxgl from 'mapbox-gl';
import { BASEMAPS, createMap } from '../map/createMap.js';
import { createCompare } from '../map/compare.js';
import { DateChip, LegendCard } from '../ui/legend.js';
import { getJSON, fmtC, fmtInt, fmtPct, fmtSignedC, ordinal } from '../config.js';

const HOME = { center: [36.86, -1.29], zoom: 10.4 };
const EPOCHS = [1975, 1990, 2000, 2010, 2020, 2025];
const GROUPS = [
  { name: 'Heat', exclusive: true, layers: [
    ['heat-diff', 'Difference from the city median'], ['heat-abs', 'Surface temperature'],
    ['heat-hottest-day', 'Hottest clear morning, 29 September 2022'], ['heat-cool-season', 'Cool season, difference from its median']] },
  { name: 'Land', layers: [['s2-true', 'Sentinel-2 true colour'], ['s2-false', 'Sentinel-2 false colour'], ['landcover', 'Land cover'], ['trees', 'Tree cover']] },
  { name: 'People and buildings', layers: [['population', 'Where people live'], ['buildings', 'Buildings by heat (from zoom 14)']] },
  { name: 'Change', layers: [['ghsl', 'Built-up area']] },
];
// Bottom to top.
const STACK = ['s2-true', 's2-false', 'landcover', 'trees', 'population', ...EPOCHS.map((y) => `ghsl-${y}`),
  'heat-cool-season', 'heat-hottest-day', 'heat-abs', 'heat-diff', 'buildings'];   // for the legend: topmost active layer
const ROOF = 'Bare iron sheet roofs give off heat less efficiently, so where they cover much of the ground the satellite can read the surface as cooler than it is. Treat the surface temperature of this ward as a lower bound.';
const MOBILE = window.matchMedia('(max-width: 767px)');

const el = (tag, props = {}, ...kids) => { const e = Object.assign(document.createElement(tag), props); e.append(...kids); return e; };

export async function initExplorer(section) {
  const frame = section.querySelector('#ex-map');
  const state = parseHash() || defaults();
  const ctl = await createMap(frame, { basemap: state.basemap, center: state.center || HOME.center, zoom: state.zoom ?? HOME.zoom, scrollZoom: true, scale: true });
  const { map, manifest } = ctl;
  const legend = new LegendCard(frame, manifest);
  const chip = new DateChip(frame);
  const wardsGeo = await getJSON('data/wards.geojson');
  const wards = wardsGeo.features.map((f) => f.properties).sort((a, b) => a.ward_name.localeCompare(b.ward_name));
  const byId = new Map(wardsGeo.features.map((f) => [f.properties.ward_id, f]));
  const N = wards.length;

  // ---------------------------------------------------------------- layer panel
  const pane = section.querySelector('#ex-layers');
  pane.querySelectorAll('noscript').forEach((n) => n.remove());
  const bmField = el('fieldset', { className: 'ex-group' }, el('legend', {}, 'Basemap'));
  const bmRow = el('div', { className: 'ex-basemaps' });
  ['satellite', 'light'].forEach((k) => {
    const i = el('input', { type: 'radio', name: 'ex-basemap', value: k, checked: state.basemap === k });
    i.addEventListener('change', async () => { state.basemap = k; await ctl.setBasemap(k); apply(); });
    bmRow.append(el('label', {}, i, ` ${BASEMAPS[k].label}`));
  });
  bmField.append(bmRow);
  pane.append(bmField);
  const rows = new Map();
  for (const g of GROUPS) {
    const fs = el('fieldset', { className: 'ex-group' }, el('legend', {}, g.name));
    for (const [id, label] of g.layers) {
      const key = id === 'ghsl' ? `ghsl-${state.year}` : id;
      const cb = el('input', { type: 'checkbox', id: `ex-cb-${id}` });
      const info = el('button', { type: 'button', className: 'info-btn', textContent: 'i' });
      info.setAttribute('aria-label', `About ${label}`);
      info.setAttribute('aria-expanded', 'false');
      const desc = el('p', { className: 'ex-desc', hidden: true });
      const range = el('input', { type: 'range', min: '0', max: '1', step: '0.05', className: 'ex-opacity' });
      range.setAttribute('aria-label', `Opacity of ${label}`);
      const row = el('div', { className: 'ex-layer' },
        el('div', { className: 'ex-layer__top' }, cb, el('label', { htmlFor: cb.id }, label), info), range, desc);
      if (id === 'ghsl') {
        const sel = el('select', { id: 'ex-year' }, ...EPOCHS.map((y) => el('option', { value: y, selected: y === state.year }, y === 2025 ? '2025 (projection)' : String(y))));
        sel.setAttribute('aria-label', 'Year of the built-up layer');
        const play = el('button', { type: 'button', className: 'ex-btn ex-play' }, 'Play');
        play.setAttribute('aria-pressed', 'false');
        let timer = null;
        const stepYear = (y) => {
          const on = state.layers.find((l) => l.id.startsWith('ghsl-'));
          state.layers = state.layers.filter((l) => !l.id.startsWith('ghsl-'));
          state.layers.push({ id: `ghsl-${y}`, opacity: on ? on.opacity : 0.85 });
          state.year = y;
          sel.value = String(y);
          apply();
        };
        sel.addEventListener('change', () => stepYear(Number(sel.value)));
        play.addEventListener('click', () => {
          if (timer) { clearInterval(timer); timer = null; play.textContent = 'Play'; play.setAttribute('aria-pressed', 'false'); return; }
          play.textContent = 'Pause';
          play.setAttribute('aria-pressed', 'true');
          let i = EPOCHS.indexOf(state.year);
          timer = setInterval(() => { i = (i + 1) % EPOCHS.length; stepYear(EPOCHS[i]); }, 1300);
        });
        row.append(el('div', { className: 'ex-year' }, sel, play));
      }
      cb.addEventListener('change', () => {
        const lid = id === 'ghsl' ? `ghsl-${state.year}` : id;
        if (cb.checked) {
          if (g.exclusive) state.layers = state.layers.filter((l) => !l.id.startsWith('heat-'));
          if (id === 'ghsl') state.layers = state.layers.filter((l) => !l.id.startsWith('ghsl-'));
          state.layers.push({ id: lid, opacity: defaultOpacity(lid) });
        } else state.layers = state.layers.filter((l) => (id === 'ghsl' ? !l.id.startsWith('ghsl-') : l.id !== lid));
        apply();
      });
      range.addEventListener('input', () => {
        const l = state.layers.find((x) => (id === 'ghsl' ? x.id.startsWith('ghsl-') : x.id === id));
        if (l) { l.opacity = Number(range.value); ctl.setLayerOpacity(l.id, l.opacity, 0); writeHash(); }
      });
      info.addEventListener('click', () => {
        const open = info.getAttribute('aria-expanded') !== 'true';
        info.setAttribute('aria-expanded', String(open));
        const m = manifest[id === 'ghsl' ? `ghsl-${state.year}` : id];
        desc.textContent = m ? `${m.description} Source: ${m.source}.` : '';
        desc.hidden = !open;
      });
      rows.set(id, { cb, range, key });
      fs.append(row);
    }
    pane.append(fs);
  }
  const tools = el('div', { className: 'ex-tools' });
  const cmpBtn = el('button', { type: 'button', className: 'ex-btn' }, 'Compare');
  cmpBtn.setAttribute('aria-pressed', 'false');
  const copyBtn = el('button', { type: 'button', className: 'ex-btn' }, 'Copy link');
  const resetBtn = el('button', { type: 'button', className: 'ex-btn' }, 'Reset view');
  const toolMsg = el('p', { className: 'ex-msg', role: 'status' });
  tools.append(cmpBtn, copyBtn, resetBtn);
  pane.append(tools, toolMsg);
  const cmpPanel = el('div', { className: 'ex-compare', hidden: true });
  pane.append(cmpPanel);

  function defaultOpacity(id) { return id.startsWith('s2') ? 1 : (state.basemap === 'satellite' ? 0.75 : 0.9); }

  function syncPanel() {
    for (const [id, r] of rows) {
      const l = state.layers.find((x) => (id === 'ghsl' ? x.id.startsWith('ghsl-') : x.id === id));
      r.cb.checked = !!l;
      r.range.disabled = !l;
      r.range.value = l ? l.opacity : 0.8;
    }
    section.querySelectorAll('input[name="ex-basemap"]').forEach((i) => { i.checked = i.value === state.basemap; });
  }

  function topLayer() {
    const on = state.layers.map((l) => l.id);
    if (on.includes('buildings') && map.getZoom() >= 14) return 'buildings';
    return [...STACK].reverse().find((id) => on.includes(id)) || null;
  }

  function apply() {
    ctl.setLayers([...state.layers, { id: 'wards-line', opacity: 1 }, { id: 'ward-labels', opacity: 1 }, { id: 'county-line', opacity: 1 }], 250);
    const top = topLayer();
    legend.show(top);
    chip.set(top ? manifest[top]?.chip : '');
    syncPanel();
    writeHash();
  }

  // ---------------------------------------------------------------- wards: combobox, panel, map clicks
  const input = section.querySelector('#ex-search');
  const list = section.querySelector('#ex-options');
  let matches = [];
  let active = -1;
  const renderOptions = () => {
    list.replaceChildren(...matches.map((w, i) => {
      const li = el('li', { id: `ex-opt-${w.ward_id}`, textContent: w.ward_name });
      li.setAttribute('role', 'option');
      li.setAttribute('aria-selected', String(i === active));
      li.addEventListener('pointerdown', (e) => { e.preventDefault(); choose(w.ward_id); });
      return li;
    }));
    list.hidden = matches.length === 0;
    input.setAttribute('aria-expanded', String(!list.hidden));
    input.setAttribute('aria-activedescendant', active >= 0 ? `ex-opt-${matches[active].ward_id}` : '');
    if (active >= 0) list.children[active]?.scrollIntoView({ block: 'nearest' });
  };
  const filter = () => {
    const q = input.value.trim().toLowerCase();
    matches = q ? wards.filter((w) => w.ward_name.toLowerCase().includes(q)) : wards.slice();
    active = matches.length ? 0 : -1;
    renderOptions();
  };
  const close = () => { list.hidden = true; input.setAttribute('aria-expanded', 'false'); active = -1; };
  input.addEventListener('input', filter);
  input.addEventListener('focus', filter);
  input.addEventListener('blur', () => setTimeout(close, 120));
  input.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') { if (list.hidden) filter(); else active = Math.min(matches.length - 1, active + 1); renderOptions(); e.preventDefault(); }
    else if (e.key === 'ArrowUp') { active = Math.max(0, active - 1); renderOptions(); e.preventDefault(); }
    else if (e.key === 'Enter') { if (active >= 0 && matches[active]) { choose(matches[active].ward_id); e.preventDefault(); } }
    else if (e.key === 'Escape') { close(); }
  });

  // The five hottest wards where people live, as buttons (re-rendered when the county summary returns).
  const renderTop5 = () => {
    const top5 = section.querySelector('#ex-top5');
    if (!top5) return;
    const t = wards.filter((w) => w.rank_pop_weighted).sort((a, b) => a.rank_pop_weighted - b.rank_pop_weighted).slice(0, 5);
    top5.replaceChildren(...t.map((w) => {
      const b = el('button', { type: 'button', className: 'linklike', textContent: w.ward_name });
      b.addEventListener('click', () => choose(w.ward_id));
      return el('li', {}, b, `, ${fmtC(w.pop_weighted_lst_c)}`);
    }));
  };
  renderTop5();
  const countyHTML = section.querySelector('#ex-ward-body').innerHTML;

  function bboxOf(f) {
    let [x0, y0, x1, y1] = [180, 90, -180, -90];
    const walk = (c) => { if (typeof c[0] === 'number') { x0 = Math.min(x0, c[0]); y0 = Math.min(y0, c[1]); x1 = Math.max(x1, c[0]); y1 = Math.max(y1, c[1]); } else c.forEach(walk); };
    walk(f.geometry.coordinates);
    return [[x0, y0], [x1, y1]];
  }

  function wardPanel(p) {
    const body = section.querySelector('#ex-ward-body');
    const back = el('button', { type: 'button', className: 'linklike ward-panel__back' }, 'Back to the county summary');
    back.addEventListener('click', () => choose(null));
    const dl = el('dl', { className: 'ward-panel__facts' });
    const add = (k, v) => dl.append(el('dt', {}, k), el('dd', {}, v));
    add('Median surface temperature, hot-season mornings', fmtC(p.lst_median_c));
    add('Difference from the city median', fmtSignedC(p.lst_anomaly_c));
    add('Surface temperature where people live', p.pop_weighted_lst_c != null ? fmtC(p.pop_weighted_lst_c) : 'no estimate');
    add('Cool-season median', fmtC(p.cool_lst_median_c));
    add('People (WorldPop 2025 estimate)', `about ${fmtInt(Math.round(p.pop_total / 100) * 100)}`);
    add('Tree cover', fmtPct(p.tree_pct));
    add('Built-up land', fmtPct(p.built_pct));
    add('Area', `${Number(p.area_km2).toFixed(1)} km²`);
    const ranks = el('ul', { className: 'ward-panel__ranks' },
      el('li', {}, `${ordinal(p.rank_hottest)} hottest of ${N} by median surface temperature`),
      el('li', {}, p.rank_pop_weighted ? `${ordinal(p.rank_pop_weighted)} hottest of ${N} where people live, weighted by population` : 'No population-weighted rank'));
    const notes = el('div', { className: 'ward-panel__notes' },
      el('p', {}, 'Land surface temperature on clear January to March mornings, 2023 to 2026: the heat of the ground, roofs and roads, not of the air. Population is a modelled estimate and may undercount the densest settlements.'));
    if (p.roof_caveat === true || p.roof_caveat === 'true') notes.append(el('p', { className: 'ward-panel__roof' }, el('strong', {}, 'Iron sheet roofs. '), ROOF));
    body.replaceChildren(el('h3', {}, p.ward_name), el('p', { className: 'ward-panel__sub' }, `${p.subcounty} sub-county`), ranks, dl, notes, back);
  }

  function choose(id, { fly = true } = {}) {
    close();
    state.ward = id;
    if (!id) {
      ctl.highlightWards([]);
      section.querySelector('#ex-ward-body').innerHTML = countyHTML;
      renderTop5();
      writeHash();
      return;
    }
    const f = byId.get(id);
    if (!f) return;
    input.value = f.properties.ward_name;
    ctl.highlightWards([f.properties.ward_name]);
    ctl.setLayerOpacity('ward-highlight', 1, 0);
    wardPanel(f.properties);
    selectTab('ward');
    if (fly) map.fitBounds(bboxOf(f), { padding: MOBILE.matches ? { top: 40, bottom: 260, left: 30, right: 30 } : 60, maxZoom: 14.5, duration: ctl.reduced ? 0 : 1200 });
    writeHash();
  }
  // Map clicks: a building popup from zoom 14, otherwise the ward under the pointer.
  const popup = new mapboxgl.Popup({ closeButton: true, maxWidth: '260px', className: 'ex-popup' });
  map.on('click', (e) => {
    if (map.getZoom() >= 14 && map.getLayer('buildings') && state.layers.some((l) => l.id === 'buildings')) {
      const b = map.queryRenderedFeatures(e.point, { layers: ['buildings'] })[0];
      if (b) {
        const d = Number(b.properties.diff_c);
        popup.setLngLat(e.lngLat).setHTML(`<strong>${fmtSignedC(d)}</strong> compared with the city median on hot mornings (${fmtC(b.properties.lst_c)}).<br><span>Describes the area of about 100 m around this building, not the roof itself.</span>`).addTo(map);
        return;
      }
    }
    // Ward outlines are lines, so find the ward polygon under the point in the ward GeoJSON.
    const hit = wardsGeo.features.find((f) => inside([e.lngLat.lng, e.lngLat.lat], f.geometry));
    if (hit) choose(hit.properties.ward_id, { fly: false });
  });
  map.on('moveend', () => { legend.show(topLayer()); chip.set(topLayer() ? manifest[topLayer()]?.chip : ''); writeHash(); });

  // ---------------------------------------------------------------- tabs and the phone bottom sheet
  const tabs = [...section.querySelectorAll('[role="tab"]')];
  function selectTab(which) {
    tabs.forEach((t) => {
      const on = t.id === `ex-tab-${which}`;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      section.querySelector(`#${t.getAttribute('aria-controls')}`).hidden = !on;
    });
  }
  tabs.forEach((t, i) => {
    t.addEventListener('click', () => selectTab(t.id.replace('ex-tab-', '')));
    t.addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      const n = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
      n.focus();
      selectTab(n.id.replace('ex-tab-', ''));
    });
  });
  const sheetBtn = section.querySelector('.explorer__sheet-toggle');
  sheetBtn.addEventListener('click', () => {
    const open = section.classList.toggle('is-sheet-open');
    sheetBtn.setAttribute('aria-expanded', String(open));
    sheetBtn.textContent = open ? 'Collapse' : 'Expand';
  });

  // ---------------------------------------------------------------- compare
  let cmp = null;
  const pickable = Object.values(manifest).filter((m) => m.kind === 'raster');
  const picker = (side, value) => {
    const s = el('select', { className: 'ex-cmp-select' }, ...pickable.map((m) => el('option', { value: m.id, selected: m.id === value }, m.title)));
    s.setAttribute('aria-label', `Layer on the ${side} side`);
    return s;
  };
  async function openCompare(left = state.compare?.left || 'heat-abs', right = state.compare?.right || 'heat-cool-abs', pos = state.compare?.pos ?? 50) {
    state.compare = { left, right, pos };
    cmpBtn.setAttribute('aria-pressed', 'true');
    cmpBtn.textContent = 'Close compare';
    const holder = el('div', { className: 'ex-compare-maps' });
    frame.append(holder);
    const view = { center: map.getCenter().toArray(), zoom: map.getZoom() };
    const lp = picker('left', left);
    const rp = picker('right', right);
    cmpPanel.replaceChildren(el('p', { className: 'ex-cmp-help' }, 'Drag the handle, or focus it and use the arrow keys.'),
      el('label', {}, 'Left ', lp), el('label', {}, 'Right ', rp));
    cmpPanel.hidden = false;
    const extra = [{ id: 'wards-line', opacity: 1 }, { id: 'county-line', opacity: 1 }];
    cmp = await createCompare(holder, {
      left: { ...view, basemap: state.basemap, layers: [{ id: left, opacity: defaultOpacity(left) }, ...extra] },
      right: { ...view, basemap: state.basemap, layers: [{ id: right, opacity: defaultOpacity(right) }, ...extra] },
      labels: [manifest[left].title, manifest[right].title], start: pos, mapOpts: { scrollZoom: true },
      onMove: (p) => { if (state.compare) { state.compare.pos = Math.round(p); writeHash(); } },
    });
    // Legend: the left layer (the right one too if it uses different classes); no single date chip.
    const relabel = () => {
      cmp.labels[0].textContent = manifest[lp.value].title;
      cmp.labels[1].textContent = manifest[rp.value].title;
      const same = JSON.stringify(manifest[lp.value].legend) === JSON.stringify(manifest[rp.value].legend);
      legend.show(lp.value, { title: `${same ? 'Both sides' : 'Left side'}: ${manifest[lp.value].title}` });
      chip.set('');
    };
    relabel();
    lp.addEventListener('change', () => { cmp.left.setLayers([{ id: lp.value, opacity: defaultOpacity(lp.value) }, ...extra], 0); state.compare.left = lp.value; relabel(); writeHash(); });
    rp.addEventListener('change', () => { cmp.right.setLayers([{ id: rp.value, opacity: defaultOpacity(rp.value) }, ...extra], 0); state.compare.right = rp.value; relabel(); writeHash(); });
    cmp.right.map.on('moveend', () => { map.jumpTo({ center: cmp.right.map.getCenter(), zoom: cmp.right.map.getZoom() }); });
    writeHash();
  }
  function closeCompare() {
    if (cmp) { cmp.destroy(); frame.querySelector('.ex-compare-maps')?.remove(); cmp = null; }
    state.compare = null;
    cmpPanel.hidden = true;
    cmpBtn.setAttribute('aria-pressed', 'false');
    cmpBtn.textContent = 'Compare';
    if (ready) apply();
    writeHash();
  }
  cmpBtn.addEventListener('click', () => (cmp ? closeCompare() : openCompare()));

  // ---------------------------------------------------------------- shareable view
  copyBtn.addEventListener('click', async () => {
    writeHash();
    try { await navigator.clipboard.writeText(window.location.href); toolMsg.textContent = 'Link copied.'; } catch { toolMsg.textContent = `Copy this link: ${window.location.href}`; }
  });
  resetBtn.addEventListener('click', async () => {
    closeCompare();
    const d = defaults();
    Object.assign(state, d);
    await ctl.setBasemap(d.basemap);
    choose(null);
    input.value = '';
    map.jumpTo(HOME);
    apply();
    toolMsg.textContent = 'View reset.';
  });

  let ready = false;
  function writeHash() {
    if (!ready) return;
    const c = map.getCenter();
    const p = new URLSearchParams();
    p.set('bm', state.basemap);
    p.set('l', state.layers.map((l) => `${l.id}@${Number(l.opacity).toFixed(2)}`).join(','));
    p.set('v', `${c.lng.toFixed(4)},${c.lat.toFixed(4)},${map.getZoom().toFixed(2)}`);
    if (state.ward) p.set('w', state.ward);
    if (state.compare) p.set('c', `${state.compare.left},${state.compare.right},${Math.round(state.compare.pos)}`);
    history.replaceState(null, '', `#explore?${p.toString()}`);
  }

  apply();
  ready = true;
  if (state.ward) choose(state.ward, { fly: !state.center });
  if (state.compare) await openCompare(state.compare.left, state.compare.right, state.compare.pos);
  if (window.location.hash.startsWith('#explore?')) section.scrollIntoView();
  writeHash();
  window.__explorer = { ctl, state, choose, openCompare, closeCompare, get compare() { return cmp; } };
  return ctl;
}

function defaults() {
  return { basemap: 'light', layers: [{ id: 'heat-diff', opacity: 0.9 }], year: 2020, ward: null, compare: null, center: null, zoom: null };
}

function parseHash() {
  const h = window.location.hash;
  if (!h.startsWith('#explore?')) return null;
  const p = new URLSearchParams(h.slice('#explore?'.length));
  const s = defaults();
  if (BASEMAPS[p.get('bm')]) s.basemap = p.get('bm');
  if (p.has('l')) s.layers = p.get('l').split(',').filter(Boolean).map((x) => { const [id, op] = x.split('@'); return { id, opacity: Math.max(0, Math.min(1, Number(op) || 0.9)) }; });
  const g = s.layers.find((l) => l.id.startsWith('ghsl-'));
  if (g) s.year = Number(g.id.slice(5));
  if (p.has('v')) { const [lng, lat, z] = p.get('v').split(',').map(Number); if (Number.isFinite(lng)) { s.center = [lng, lat]; s.zoom = z; } }
  if (p.has('w')) s.ward = p.get('w');
  if (p.has('c')) { const [left, right, pos] = p.get('c').split(','); s.compare = { left, right, pos: Number(pos) || 50 }; }
  return s;
}

/** Point in polygon (GeoJSON Polygon or MultiPolygon), ray casting. */
function inside(pt, geom) {
  const polys = geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates;
  return polys.some((rings) => {
    let c = false;
    rings.forEach((ring, ri) => {
      let inRing = false;
      for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
        const [xi, yi] = ring[i];
        const [xj, yj] = ring[j];
        if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < ((xj - xi) * (pt[1] - yi)) / (yj - yi) + xi) inRing = !inRing;
      }
      if (ri === 0) c = inRing; else if (inRing) c = false;
    });
    return c;
  });
}
