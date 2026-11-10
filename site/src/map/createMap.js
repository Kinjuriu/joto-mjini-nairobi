// The one map module every map on the site uses (design brief v2, section 1).
//
// createMap(container, options) returns a controller that:
//   - creates a Mapbox GL JS map with one of our basemaps and waits for the style;
//   - finds the basemap's first symbol layer, so every data layer goes beneath the labels;
//   - knows our layers from tiles/manifest.json (raster XYZ folders) plus a few vector overlays;
//   - cross-fades layer opacity (about 400 ms) and flies between chapters (about 1.8 s),
//     with instant changes under prefers-reduced-motion;
//   - re-adds our sources and layers after a basemap switch, because setStyle drops them.
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { ACCENT, MAPBOX_TOKEN, REDUCED_MOTION, SATELLITE, abs, absTemplate, diffStep, getManifest } from '../config.js';

export const BASEMAPS = {
  satellite: { url: 'mapbox://styles/mapbox/satellite-streets-v12', imagery: true, label: 'Satellite' },
  light: { url: 'mapbox://styles/mapbox/light-v11', imagery: false, label: 'Light' },
  dark: { url: 'mapbox://styles/mapbox/dark-v11', imagery: false, label: 'Dark' },
};

const FADE_MS = 400;
const FLY_MS = 1800;
const FONT = ['DIN Pro Medium', 'Arial Unicode MS Regular'];
const FONT_BOLD = ['DIN Pro Bold', 'Arial Unicode MS Bold'];
// Basemap label layers that add clutter over data.
const HIDE = ['poi-label', 'transit-label', 'airport-label', 'natural-point-label', 'water-point-label'];

// Default stacking of our data layers, bottom to top (all beneath the basemap labels).
export const DEFAULT_ORDER = ['s2-true', 's2-false', 'landcover', 'trees', 'population', 'growth-1990-2020',
  'ghsl-1975', 'ghsl-1990', 'ghsl-2000', 'ghsl-2010', 'ghsl-2020', 'ghsl-2025',
  'heat-cool-abs', 'heat-cool-season', 'heat-hottest-day', 'heat-abs', 'heat-diff', 'wards-fill', 'buildings',
  'wards-line', 'county-line'];

const opacityProp = { raster: 'raster-opacity', fill: 'fill-opacity', line: 'line-opacity', symbol: 'text-opacity' };

export class MissingTokenError extends Error {}

// Mapbox satellite raster tiles can be refused (HTTP 429 was seen on 10 November 2026). Probe one tile once
// per session; if imagery is refused, "Satellite" becomes Mapbox Light with our own Sentinel-2 true-colour
// composite (10 m, January to March 2026) beneath its roads and labels. DECISIONS D33.
let satProbe;
export function satelliteAvailable() {
  if (SATELLITE === 'sentinel2') return Promise.resolve(false);
  if (SATELLITE === 'mapbox') return Promise.resolve(true);
  if (!satProbe) {
    const cached = sessionStorage.getItem('joto-sat');
    satProbe = cached !== null ? Promise.resolve(cached === '1')
      : fetch(`https://api.mapbox.com/v4/mapbox.satellite/10/616/515.webp?access_token=${MAPBOX_TOKEN}`)
        .then((r) => r.ok).catch(() => false)
        .then((ok) => { sessionStorage.setItem('joto-sat', ok ? '1' : '0'); return ok; });
  }
  return satProbe;
}
async function styleUrl(name, manifest) {
  if (name === 'satellite' && !(await satelliteAvailable()) && manifest['s2-true']) return { url: BASEMAPS.light.url, s2: true };
  return { url: BASEMAPS[name].url, s2: false };
}

/** Show a plain notice in a map container when the map cannot load. */
export function mapNotice(container, text) {
  const el = document.createElement('p');
  el.className = 'map-notice';
  el.textContent = text;
  container.append(el);
}

export async function createMap(container, opts = {}) {
  if (!MAPBOX_TOKEN) {
    mapNotice(container, 'Map pending: the Mapbox access token is missing (VITE_MAPBOX_TOKEN in site/.env.local).');
    throw new MissingTokenError('VITE_MAPBOX_TOKEN missing');
  }
  mapboxgl.accessToken = MAPBOX_TOKEN;
  const manifest = await getManifest();
  const basemap = opts.basemap || 'light';
  const first = await styleUrl(basemap, manifest);
  const map = new mapboxgl.Map({
    container,
    style: first.url,
    center: opts.center || [36.86, -1.29],
    zoom: opts.zoom ?? 10.3,
    minZoom: 8,
    maxZoom: 17.5,
    projection: 'mercator',
    scrollZoom: opts.scrollZoom ?? true,
    dragRotate: false,
    pitchWithRotate: false,
    touchPitch: false,
    attributionControl: false,
    fadeDuration: 0,
    preserveDrawingBuffer: !!opts.preserveDrawingBuffer,
  });
  map.touchZoomRotate.disableRotation();
  map.keyboard.disableRotation();
  map.addControl(new mapboxgl.AttributionControl({ compact: true, customAttribution: opts.attribution || '' }), 'bottom-left');
  if (opts.navigation !== false) map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), opts.navPosition || 'top-right');
  if (opts.scale) map.addControl(new mapboxgl.ScaleControl({ unit: 'metric' }), 'bottom-left');
  const ctl = new MapController(map, manifest, basemap, opts);
  ctl.s2Imagery = first.s2;
  await ctl.ready;
  return ctl;
}

export class MapController {
  constructor(map, manifest, basemap, opts) {
    this.map = map;
    this.manifest = manifest;
    this.basemap = basemap;
    this.opts = opts;
    this.state = new Map();     // layer id -> desired opacity
    this.specs = new Map();     // layer id -> {source id, source spec, layer spec(s)}
    this.hideTimers = new Map();
    this.highlight = [];
    this.listeners = [];
    this.ready = new Promise((resolve) => {
      map.once('style.load', () => { this._install(); resolve(this); });
    });
    map.on('style.load', () => { if (this._installed) this._install(); });
  }

  get reduced() { return REDUCED_MOTION.matches; }
  get imagery() { return BASEMAPS[this.basemap].imagery; }

  /** First symbol layer of the basemap style: data layers go beneath it, so names stay on top. */
  firstSymbolId() {
    const layers = this.map.getStyle().layers;
    const ours = new Set([...this.specs.keys()].flatMap((id) => this.specs.get(id).layers.map((l) => l.id)));
    const l = layers.find((x) => x.type === 'symbol' && !ours.has(x.id));
    return l ? l.id : undefined;
  }

  _install() {
    this._installed = true;
    this._styleLabels();
    if (this.s2Imagery) this._addS2Imagery();
    // Re-add every layer we know about, at its current opacity, without transition.
    for (const id of this.specs.keys()) this._addToMap(id);
    for (const [id, op] of this.state) this._applyOpacity(id, op, 0);
    this.reorder(DEFAULT_ORDER);
    this.listeners.forEach((fn) => fn('style'));
  }

  /** Fallback imagery: our Sentinel-2 true colour beneath the first road layer of the light style. */
  _addS2Imagery() {
    const { map } = this;
    const m = this.manifest['s2-true'];
    if (map.getLayer('basemap-s2')) return;
    if (!map.getSource('src-basemap-s2')) {
      map.addSource('src-basemap-s2', { type: 'raster', tiles: [absTemplate(m.tiles)], tileSize: 256, minzoom: m.minzoom,
        maxzoom: m.maxzoom, bounds: m.bounds, attribution: m.source });
    }
    const before = map.getStyle().layers.find((l) => /^(tunnel|road|bridge|admin|building)/.test(l.id));
    map.addLayer({ id: 'basemap-s2', type: 'raster', source: 'src-basemap-s2', paint: { 'raster-resampling': 'linear', 'raster-fade-duration': 0 } },
      before ? before.id : this.firstSymbolId());
    for (const l of map.getStyle().layers) {
      if (l.type === 'fill' && /^(landuse|national-park|building)/.test(l.id)) map.setLayoutProperty(l.id, 'visibility', 'none');
    }
  }

  /** Dark text with a white halo on every basemap label: readable over imagery and data. */
  _styleLabels() {
    const { map } = this;
    for (const l of map.getStyle().layers) {
      if (l.type !== 'symbol') continue;
      if (HIDE.some((h) => l.id.startsWith(h))) { map.setLayoutProperty(l.id, 'visibility', 'none'); continue; }
      if (!map.getLayoutProperty(l.id, 'text-field')) continue;
      map.setPaintProperty(l.id, 'text-color', '#1C1B19');
      map.setPaintProperty(l.id, 'text-halo-color', 'rgba(255,255,255,0.95)');
      map.setPaintProperty(l.id, 'text-halo-width', l.id.startsWith('road') ? 1.5 : 1.8);
      map.setPaintProperty(l.id, 'text-halo-blur', 0);
    }
  }

  /** Generic API from the brief: add a data layer beneath the labels (or on top). */
  addDataLayer(id, source, paint, { beforeLabels = true, type = 'raster', layout = {}, sourceLayer, filter, minzoom, maxzoom, sourceId } = {}) {
    const sid = sourceId || `src-${id}`;
    const layer = { id, type, source: sid, paint: { ...paint, [opacityProp[type]]: 0 }, layout: { ...layout, visibility: 'none' } };
    if (sourceLayer) layer['source-layer'] = sourceLayer;
    if (filter) layer.filter = filter;
    if (minzoom !== undefined) layer.minzoom = minzoom;
    if (maxzoom !== undefined) layer.maxzoom = maxzoom;
    this.specs.set(id, { sourceId: sid, source, layers: [layer], beforeLabels });
    this._addToMap(id);
  }

  _addToMap(id) {
    const { map } = this;
    const sp = this.specs.get(id);
    if (!map.getSource(sp.sourceId)) map.addSource(sp.sourceId, sp.source);
    const before = sp.beforeLabels ? this.firstSymbolId() : undefined;
    for (const l of sp.layers) {
      if (map.getLayer(l.id)) continue;
      const spec = typeof sp.themed === 'function' ? sp.themed(l, this) : l;
      map.addLayer(spec, before);
    }
  }

  /** Make sure a named layer exists (from the manifest or the overlay catalogue). */
  use(id) {
    if (this.specs.has(id)) return true;
    const m = this.manifest[id];
    if (m && m.kind === 'raster') {
      this.addDataLayer(id, {
        type: 'raster', tiles: [absTemplate(m.tiles)], tileSize: 256, minzoom: m.minzoom, maxzoom: m.maxzoom,
        bounds: m.bounds, attribution: m.source,
      }, { 'raster-resampling': m.resampling === 'nearest' ? 'nearest' : 'linear', 'raster-fade-duration': 0 });
      return true;
    }
    const o = OVERLAYS[id];
    if (!o) { console.warn(`Unknown layer ${id}`); return false; }
    const src = o.source(this);
    const sid = o.sourceId || `src-${id}`;
    const layers = o.layers(this).map((l) => ({ ...l, source: sid, layout: { ...(l.layout || {}), visibility: 'none' } }));
    this.specs.set(id, { sourceId: sid, source: src, layers, beforeLabels: o.beforeLabels !== false, themed: o.themed });
    this._addToMap(id);
    return true;
  }

  _applyOpacity(id, opacity, ms) {
    const { map } = this;
    const sp = this.specs.get(id);
    if (!sp) return;
    clearTimeout(this.hideTimers.get(id));
    for (const l of sp.layers) {
      if (!map.getLayer(l.id)) continue;
      const prop = opacityProp[l.type];
      const full = l.maxOpacity ?? 1;
      if (opacity > 0) map.setLayoutProperty(l.id, 'visibility', 'visible');
      map.setPaintProperty(l.id, `${prop}-transition`, { duration: ms, delay: 0 });
      if (l.type === 'symbol') map.setPaintProperty(l.id, 'icon-opacity-transition', { duration: ms, delay: 0 });
      map.setPaintProperty(l.id, prop, opacity * full);
    }
    if (opacity === 0) {
      const hide = () => sp.layers.forEach((l) => map.getLayer(l.id) && map.setLayoutProperty(l.id, 'visibility', 'none'));
      if (ms === 0) hide(); else this.hideTimers.set(id, setTimeout(hide, ms + 60));
    }
  }

  setLayerOpacity(id, opacity, ms = FADE_MS) {
    if (!this.use(id)) return;
    this.state.set(id, opacity);
    this._applyOpacity(id, opacity, this.reduced ? 0 : ms);
    this.listeners.forEach((fn) => fn('layers'));
  }

  /** Show exactly these layers (others fade out). layers: [{id, opacity}] or ids. */
  setLayers(layers, ms = FADE_MS) {
    const want = new Map(layers.map((l) => (typeof l === 'string' ? [l, 1] : [l.id, l.opacity ?? 1])));
    // The ward highlight is controlled by highlightWards(), not by the chapter's layer list.
    for (const id of [...this.state.keys()]) if (id !== 'ward-highlight' && !want.has(id) && this.state.get(id) > 0) this.setLayerOpacity(id, 0, ms);
    for (const [id, op] of want) this.setLayerOpacity(id, op, ms);
    this.reorder(DEFAULT_ORDER);
  }

  async setBasemap(name) {
    if (!BASEMAPS[name] || name === this.basemap) return;
    this.basemap = name;
    // Overlays styled per basemap (outline colours) are rebuilt from their specs on style.load.
    for (const [id, sp] of this.specs) if (OVERLAYS[id]?.rebuild) {
      sp.layers = OVERLAYS[id].layers(this).map((l) => ({ ...l, source: sp.sourceId, layout: { ...(l.layout || {}), visibility: 'none' } }));
    }
    const st = await styleUrl(name, this.manifest);
    this.s2Imagery = st.s2;
    await new Promise((resolve) => { this.map.once('style.load', () => setTimeout(resolve, 0)); this.map.setStyle(st.url, { diff: false }); });
    this.listeners.forEach((fn) => fn('basemap'));
  }

  /** Move to a chapter: basemap, layers, camera. */
  async setChapter(ch, { instant = false } = {}) {
    const quick = instant || this.reduced;
    if (ch.basemap && ch.basemap !== this.basemap) await this.setBasemap(ch.basemap);
    if (ch.highlight !== undefined) this.highlightWards(ch.highlight || []);
    this.setLayers(ch.layers || [], quick ? 0 : FADE_MS);
    if (ch.center) {
      const cam = { center: ch.center, zoom: ch.zoom, bearing: 0, pitch: 0, padding: ch.padding || { top: 0, bottom: 0, left: 0, right: 0 } };
      if (quick) this.map.jumpTo(cam);
      else this.map.flyTo({ ...cam, duration: ch.duration || FLY_MS, essential: false, curve: 1.3 });
    }
  }

  /** Stack our data layers in this order (first = lowest), all beneath the basemap labels. */
  reorder(ids) {
    const before = this.firstSymbolId();
    for (const id of ids) {
      const sp = this.specs.get(id);
      if (!sp || !sp.beforeLabels) continue;
      for (const l of sp.layers) if (this.map.getLayer(l.id)) this.map.moveLayer(l.id, before);
    }
  }

  highlightWards(names) {
    this.highlight = names;
    if (!names.length) { if (this.state.get('ward-highlight')) this.setLayerOpacity('ward-highlight', 0, 0); return; }
    this.use('ward-highlight');
    const f = ['in', ['get', 'ward_name'], ['literal', names]];
    for (const l of this.specs.get('ward-highlight').layers) {
      l.filter = f;
      if (this.map.getLayer(l.id)) this.map.setFilter(l.id, f);
    }
    this.setLayerOpacity('ward-highlight', 1, 0);
  }

  onChange(fn) { this.listeners.push(fn); }
}

// ---------------------------------------------------------------- vector overlays
const vec = (name) => (c) => ({
  type: 'vector', tiles: [absTemplate(c.manifest[name].tiles)], minzoom: c.manifest[name].minzoom, maxzoom: c.manifest[name].maxzoom,
  bounds: c.manifest[name].bounds, attribution: c.manifest[name].source,
});
const lineColour = (c) => (c.imagery ? 'rgba(255,255,255,0.85)' : 'rgba(28,27,25,0.55)');

export const OVERLAYS = {
  'county-line': {
    source: () => ({ type: 'geojson', data: abs('data/county.geojson') }),
    rebuild: true,
    layers: (c) => [{ id: 'county-line', type: 'line', paint: { 'line-color': c.imagery ? '#FFFFFF' : '#1C1B19', 'line-width': 1.6 } }],
  },
  'wards-line': {
    sourceId: 'src-wards', source: vec('wards'), rebuild: true,
    layers: (c) => [{ id: 'wards-line', type: 'line', 'source-layer': 'wards',
      paint: { 'line-color': lineColour(c), 'line-width': ['interpolate', ['linear'], ['zoom'], 10, 0.5, 14, 1.2] } }],
  },
  'wards-fill': {
    sourceId: 'src-wards', source: vec('wards'),
    layers: (c) => [{ id: 'wards-fill', type: 'fill', 'source-layer': 'wards', maxOpacity: 0.92,
      paint: { 'fill-color': diffStep(['-', ['to-number', ['get', 'pop_weighted_lst_c'], 0], c.manifest['heat-diff'].median_c ?? 0]),
        'fill-outline-color': 'rgba(255,255,255,0.9)' } }],
  },
  'ward-labels': {
    source: vec('ward-labels'), beforeLabels: false,
    layers: () => [{ id: 'ward-labels', type: 'symbol', 'source-layer': 'ward-labels', minzoom: 10,
      layout: { 'text-field': ['get', 'ward_name'], 'text-font': FONT_BOLD, 'text-size': ['interpolate', ['linear'], ['zoom'], 10, 10, 11, 11.5, 14, 14.5],
        'text-transform': 'uppercase', 'text-letter-spacing': 0.04, 'text-max-width': 7, 'symbol-sort-key': ['-', ['get', 'area_km2']],
        'text-padding': 3 },
      paint: { 'text-color': '#1C1B19', 'text-halo-color': 'rgba(255,255,255,0.95)', 'text-halo-width': 2 } }],
  },
  'ward-highlight': {
    sourceId: 'src-wards', source: vec('wards'), beforeLabels: false,
    layers: () => [
      { id: 'ward-highlight-halo', type: 'line', 'source-layer': 'wards', filter: ['in', ['get', 'ward_name'], ['literal', []]],
        paint: { 'line-color': '#FFFFFF', 'line-width': 5 } },
      { id: 'ward-highlight', type: 'line', 'source-layer': 'wards', filter: ['in', ['get', 'ward_name'], ['literal', []]],
        paint: { 'line-color': ACCENT, 'line-width': 2.5 } }],
  },
  buildings: {
    source: vec('buildings'),
    layers: () => [
      { id: 'buildings', type: 'fill', 'source-layer': 'buildings', minzoom: 14,
        paint: { 'fill-color': diffStep(['to-number', ['get', 'diff_c'], 0]) } },
      { id: 'buildings-line', type: 'line', 'source-layer': 'buildings', minzoom: 14,
        paint: { 'line-color': 'rgba(28,27,25,0.45)', 'line-width': 0.5 } }],
  },
  places: {
    source: vec('places'), beforeLabels: false,
    layers: () => [{ id: 'places', type: 'symbol', 'source-layer': 'places', minzoom: 10.5, filter: ['==', ['get', 'is_green'], true],
      layout: { 'text-field': ['get', 'name'], 'text-font': FONT, 'text-size': 12.5, 'text-max-width': 8 },
      paint: { 'text-color': '#1F4D2E', 'text-halo-color': 'rgba(255,255,255,0.95)', 'text-halo-width': 1.8 } }],
  },
  'comparison-areas': {
    source: () => ({ type: 'geojson', data: abs('data/comparison_areas.geojson') }), beforeLabels: false,
    layers: () => [
      { id: 'comparison-areas-halo', type: 'line', paint: { 'line-color': '#FFFFFF', 'line-width': 4 } },
      { id: 'comparison-areas', type: 'line', paint: { 'line-color': '#1C1B19', 'line-width': 2, 'line-dasharray': [2, 1.5] } }],
  },
};
