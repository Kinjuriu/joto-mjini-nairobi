// The one map module every map on the site uses (design brief v2, section 1).
//
// createMap(container, options) returns a controller that:
//   - creates a Mapbox GL JS map with one of our basemaps and waits for the style;
//   - finds the basemap's first symbol layer, so every data layer goes beneath the labels;
//   - knows our layers from tiles/manifest.json (raster XYZ folders) plus a few vector overlays;
//   - cross-fades layer opacity (about 400 ms) and flies between chapters (about 1.8 s),
//     with instant changes under prefers-reduced-motion;
//   - switches between imagery and the light map by showing or hiding one imagery layer (no style reload);
//   - dims everything outside Nairobi County and shows a scale bar and the coordinates under the pointer.
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { ACCENT, MAPBOX_TOKEN, REDUCED_MOTION, SATELLITE, abs, absTemplate, diffStep, getManifest } from '../config.js';

export const BASEMAPS = {
  satellite: { imagery: true, label: 'Satellite' },
  light: { imagery: false, label: 'Light' },
};
// One Mapbox style for every map. "Satellite" and "Light" are the same style with an imagery layer shown or
// hidden, so switching never reloads the style (reloading made the story map blank out and redraw).
const STYLE = 'mapbox://styles/mapbox/light-v11';
// Keep every map on Nairobi and its surroundings, so nobody gets lost over the rest of Kenya.
const BOUNDS = [[36.2, -1.95], [37.55, -0.6]];
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
  'ward-groups', 'ward-dim', 'forest-mask', 'county-mask', 'wards-line', 'county-line', 'forests'];

// Chapter-level styling added 12 November 2026: only some ward names, ward groups, pulsing circles.
const inNames = (names) => ['in', ['get', 'ward_name'], ['literal', names]];

const opacityProp = { raster: 'raster-opacity', fill: 'fill-opacity', line: 'line-opacity', symbol: 'text-opacity' };

export class MissingTokenError extends Error {}

// Imagery. Mapbox satellite is sharpest, but its tiles were refused for this account (HTTP 429 on every
// request, 10 November 2026). We probe one tile once per session: if it is refused we use Sentinel-2
// cloudless 2023 by EOX (10 m, cloud-free, natural colour, covers the whole region). DECISIONS D42.
let satProbe;
export function satelliteAvailable() {
  if (SATELLITE === 'sentinel2') return Promise.resolve(false);
  if (SATELLITE === 'mapbox') return Promise.resolve(true);
  if (!satProbe) {
    let cached = null;
    try { cached = sessionStorage.getItem('joto-sat'); } catch { /* storage blocked */ }
    satProbe = cached !== null ? Promise.resolve(cached === '1')
      : fetch(`https://api.mapbox.com/v4/mapbox.satellite/12/2463/2063.webp?access_token=${MAPBOX_TOKEN}`)
        .then((r) => r.ok).catch(() => false)
        .then((ok) => { try { sessionStorage.setItem('joto-sat', ok ? '1' : '0'); } catch { /* ignore */ } return ok; });
  }
  return satProbe;
}
const EOX = {
  type: 'raster', tileSize: 256, maxzoom: 15,
  tiles: ['https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2023_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg'],
  attribution: '<a href="https://s2maps.eu" target="_blank" rel="noopener">Sentinel-2 cloudless 2023 by EOX</a> (contains modified Copernicus Sentinel data 2023)',
};
const MAPBOX_SAT = { type: 'raster', url: 'mapbox://mapbox.satellite', tileSize: 256 };

/** Latitude and longitude under the pointer (or the map centre on touch), like NASA's dashboard. */
class CoordControl {
  onAdd(map) {
    this.map = map;
    this.el = document.createElement('div');
    this.el.className = 'mapboxgl-ctrl map-coords';
    this.el.setAttribute('aria-hidden', 'true');
    const fmt = ({ lng, lat }) => `${Math.abs(lat).toFixed(4)}° ${lat < 0 ? 'S' : 'N'}, ${Math.abs(lng).toFixed(4)}° ${lng < 0 ? 'W' : 'E'}`;
    const centre = () => { this.el.textContent = fmt(map.getCenter()); };
    map.on('mousemove', (e) => { this.el.textContent = fmt(e.lngLat); });
    map.on('mouseout', centre);
    map.on('move', () => { if (!this.hover) centre(); });
    map.getCanvasContainer().addEventListener('mouseenter', () => { this.hover = true; });
    map.getCanvasContainer().addEventListener('mouseleave', () => { this.hover = false; centre(); });
    centre();
    return this.el;
  }
  onRemove() { this.el.remove(); }
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
  const basemap = opts.basemap || 'satellite';
  const mapboxSat = await satelliteAvailable();
  const map = new mapboxgl.Map({
    container,
    style: STYLE,
    center: opts.center || [36.86, -1.29],
    zoom: opts.zoom ?? 10.3,
    minZoom: opts.minZoom ?? 9,
    maxZoom: 17.5,
    maxBounds: opts.maxBounds === false ? undefined : BOUNDS,
    cooperativeGestures: !!opts.cooperativeGestures,
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
  if (opts.scale !== false) {
    const pos = opts.furniturePosition || 'bottom-left';
    map.addControl(new mapboxgl.ScaleControl({ unit: 'metric', maxWidth: 110 }), pos);
    map.addControl(new CoordControl(), pos);
  }
  const ctl = new MapController(map, manifest, basemap, opts);
  ctl.imagerySource = mapboxSat ? MAPBOX_SAT : EOX;
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
    this._addImagery();
    this.use('county-mask');
    this._applyBasemap();
    // Re-add every layer we know about, at its current opacity, without transition.
    for (const id of this.specs.keys()) this._addToMap(id);
    for (const [id, op] of this.state) this._applyOpacity(id, op, 0);
    this.reorder(DEFAULT_ORDER);
    this.listeners.forEach((fn) => fn('style'));
  }

  /** The imagery layer sits just above the style's background, beneath roads, boundaries and labels. */
  _addImagery() {
    const { map } = this;
    if (map.getLayer('basemap-imagery')) return;
    if (!map.getSource('src-basemap-imagery')) map.addSource('src-basemap-imagery', this.imagerySource);
    const layers = map.getStyle().layers;
    const above = layers.find((l) => l.type !== 'background');
    map.addLayer({ id: 'basemap-imagery', type: 'raster', source: 'src-basemap-imagery', layout: { visibility: 'none' },
      paint: { 'raster-fade-duration': 0, 'raster-resampling': 'linear' } }, above ? above.id : undefined);
    // Style layers that would cover the imagery (land use fills, water, hillshade, building fills).
    this.coverIds = layers.filter((l) => (l.type === 'fill' || l.type === 'hillshade' || l.type === 'fill-extrusion')).map((l) => l.id);
    this.roadIds = layers.filter((l) => l.type === 'line' && /^(road|bridge|tunnel|aeroway)/.test(l.id)).map((l) => l.id);
  }

  /** Show or hide the imagery and restyle our outlines for the basemap, without reloading the style. */
  _applyBasemap() {
    const { map } = this;
    const img = this.imagery;
    if (map.getLayer('basemap-imagery')) map.setLayoutProperty('basemap-imagery', 'visibility', img ? 'visible' : 'none');
    for (const id of this.coverIds || []) if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', img ? 'none' : 'visible');
    for (const id of this.roadIds || []) if (map.getLayer(id)) map.setPaintProperty(id, 'line-opacity', img ? 0.45 : 1);
    for (const [id, sp] of this.specs) {
      const o = OVERLAYS[id];
      if (!o?.rebuild) continue;
      const fresh = o.layers(this);
      sp.layers.forEach((l, i) => {
        const f = fresh[i];
        if (!f) return;
        for (const [k, v] of Object.entries(f.paint || {})) {
          if (k.endsWith('opacity')) continue;
          l.paint[k] = v;
          if (map.getLayer(l.id)) map.setPaintProperty(l.id, k, v);
        }
        if (f.maxOpacity !== undefined) l.maxOpacity = f.maxOpacity;
      });
    }
    if (this.specs.has('county-mask')) this._applyOpacity('county-mask', 1, 0);
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
    for (const id of [...this.state.keys()]) if (!['ward-highlight', 'highlight-labels', 'county-mask'].includes(id) && !want.has(id) && this.state.get(id) > 0) this.setLayerOpacity(id, 0, ms);
    for (const [id, op] of want) this.setLayerOpacity(id, op, ms);
    this.reorder(DEFAULT_ORDER);
  }

  /** Switch between imagery and the light map. Instant: no style reload, our layers stay where they are. */
  setBasemap(name) {
    if (!BASEMAPS[name] || name === this.basemap) return;
    this.basemap = name;
    this._applyBasemap();
    this.listeners.forEach((fn) => fn('basemap'));
  }

  /** Move to a chapter: basemap, layers, camera. */
  async setChapter(ch, { instant = false } = {}) {
    const quick = instant || this.reduced;
    if (ch.basemap) this.setBasemap(ch.basemap);
    if (ch.highlight !== undefined) this.highlightWards(ch.highlight || []);
    this.setGroups(ch.groups || null);
    this.setLayers(ch.layers || [], quick ? 0 : FADE_MS);
    this.setLabelFilter(ch.labelWards || null);
    for (const id of ch.top || []) {   // chapter-specific stacking, for example tree cover above the ward groups
      const sp = this.specs.get(id);
      const before = this.map.getLayer('ward-dim') ? 'ward-dim' : this.firstSymbolId();
      if (sp) sp.layers.forEach((l) => this.map.getLayer(l.id) && this.map.moveLayer(l.id, before));
    }
    this.setPulses(ch.pulses || []);
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

  /** Show only these ward names (null: all). */
  setLabelFilter(names) {
    const f = names ? inNames(names) : null;
    const sp = this.specs.get('ward-labels');
    if (!sp) return;
    sp.layers.forEach((l) => { l.filter = f; if (this.map.getLayer(l.id)) this.map.setFilter(l.id, f); });
  }

  /** Colour two groups of wards (for example the five hottest and five coolest) and dim the rest. */
  setGroups(g) {
    this.groups = g;
    const names = g ? [...g.hot, ...g.cool] : [];
    for (const id of ['ward-groups', 'ward-dim']) {
      if (!g && !this.specs.has(id)) continue;
      this.use(id);
      const f = id === 'ward-dim' ? ['!', inNames(names)] : inNames(names);
      this.specs.get(id).layers.forEach((l) => { l.filter = f; if (this.map.getLayer(l.id)) this.map.setFilter(l.id, f); });
      if (this.map.getLayer('ward-groups')) {
        this.map.setPaintProperty('ward-groups', 'fill-color', g ? ['case', inNames(g.hot), '#C2311F', '#2F6E99'] : '#000000');
      }
    }
  }

  /** Pulsing circles with a label (heat divide chapter). Still under reduced motion (CSS). */
  setPulses(list) {
    (this.pulses || []).forEach((m) => m.remove());
    this.pulses = list.map((p) => {
      const el = document.createElement('div');
      el.className = `pulse pulse--${p.tone}`;
      el.innerHTML = `<span class="pulse__ring"></span><span class="pulse__ring pulse__ring--2"></span><span class="pulse__dot"></span>`
        + `<span class="pulse__label">${p.label}</span>`;
      el.setAttribute('aria-hidden', 'true');
      return new mapboxgl.Marker({ element: el, anchor: 'center' }).setLngLat(p.at).addTo(this.map);
    });
  }

  highlightWards(names) {
    this.highlight = names;
    if (!names.length) {
      if (this.state.get('ward-highlight')) this.setLayerOpacity('ward-highlight', 0, 0);
      if (this.state.get('highlight-labels')) this.setLayerOpacity('highlight-labels', 0, 0);
      return;
    }
    this.use('ward-highlight');
    const f = ['in', ['get', 'ward_name'], ['literal', names]];
    for (const l of this.specs.get('ward-highlight').layers) {
      l.filter = f;
      if (this.map.getLayer(l.id)) this.map.setFilter(l.id, f);
    }
    this.setLayerOpacity('ward-highlight', 1, 0);
    this.use('highlight-labels');
    this.specs.get('highlight-labels').layers.forEach((l) => { l.filter = f; if (this.map.getLayer(l.id)) this.map.setFilter(l.id, f); });
    this.setLayerOpacity('highlight-labels', 1, 0);
  }

  onChange(fn) { this.listeners.push(fn); }
}

// ---------------------------------------------------------------- vector overlays
const vec = (name) => (c) => ({
  type: 'vector', tiles: [absTemplate(c.manifest[name].tiles)], minzoom: c.manifest[name].minzoom, maxzoom: c.manifest[name].maxzoom,
  bounds: c.manifest[name].bounds, attribution: c.manifest[name].source,
});
const lineColour = (c) => (c.imagery ? 'rgba(255,255,255,0.8)' : 'rgba(28,27,25,0.5)');

// Everything outside Nairobi County, as one polygon with the county cut out (to dim the surroundings).
let maskData;
function countyMask() {
  if (!maskData) {
    maskData = fetch(abs('data/county.geojson')).then((r) => r.json()).then((g) => {
      const holes = [];
      for (const f of g.features || [g]) {
        const geom = f.geometry || f;
        const polys = geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates;
        polys.forEach((p) => holes.push(p[0].slice().reverse()));
      }
      return { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [[[20, -15], [50, -15], [50, 15], [20, 15], [20, -15]], ...holes] } };
    });
  }
  return maskData;
}

export const OVERLAYS = {
  'county-mask': {
    source: (c) => {
      const src = { type: 'geojson', data: { type: 'FeatureCollection', features: [] } };
      countyMask().then((f) => c.map.getSource('src-county-mask')?.setData(f));
      return src;
    },
    rebuild: true,
    layers: (c) => [{ id: 'county-mask', type: 'fill', paint: { 'fill-color': c.imagery ? '#0B1620' : '#FFFFFF' }, maxOpacity: c.imagery ? 0.42 : 0.55 }],
  },
  'county-line': {
    source: () => ({ type: 'geojson', data: abs('data/county.geojson') }),
    rebuild: true,
    layers: (c) => [{ id: 'county-line', type: 'line', paint: { 'line-color': c.imagery ? '#FFFFFF' : '#1C1B19', 'line-width': 2.2 } }],
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
        paint: { 'line-color': '#FFFFFF', 'line-width': 9 } },
      { id: 'ward-highlight', type: 'line', 'source-layer': 'wards', filter: ['in', ['get', 'ward_name'], ['literal', []]],
        paint: { 'line-color': '#1C2530', 'line-width': 4.5 } }],
  },
  'highlight-labels': {
    source: vec('ward-labels'), beforeLabels: false,
    layers: () => [{ id: 'highlight-labels', type: 'symbol', 'source-layer': 'ward-labels', filter: ['in', ['get', 'ward_name'], ['literal', []]],
      layout: { 'text-field': ['get', 'ward_name'], 'text-font': FONT_BOLD, 'text-size': 22, 'text-transform': 'uppercase',
        'text-letter-spacing': 0.05, 'text-allow-overlap': true, 'text-ignore-placement': true },
      paint: { 'text-color': '#1C2530', 'text-halo-color': '#FFFFFF', 'text-halo-width': 3 } }],
  },
  'ward-groups': {
    sourceId: 'src-wards', source: vec('wards'),
    layers: () => [{ id: 'ward-groups', type: 'fill', 'source-layer': 'wards', maxOpacity: 0.55, filter: ['in', ['get', 'ward_name'], ['literal', []]],
      paint: { 'fill-color': '#000000' } }],
  },
  'ward-dim': {
    sourceId: 'src-wards', source: vec('wards'),
    layers: () => [{ id: 'ward-dim', type: 'fill', 'source-layer': 'wards', maxOpacity: 0.72, paint: { 'fill-color': '#0B1620' } }],
  },
  'forest-mask': {
    source: (c) => {
      const src = { type: 'geojson', data: { type: 'FeatureCollection', features: [] } };
      fetch(abs('data/forests.geojson')).then((r) => r.json()).then((g) => {
        const holes = g.features.filter((f) => f.properties.kind === 'forest').map((f) => f.geometry.coordinates[0].slice().reverse());
        c.map.getSource('src-forest-mask')?.setData({ type: 'Feature', properties: {},
          geometry: { type: 'Polygon', coordinates: [[[20, -15], [50, -15], [50, 15], [20, 15], [20, -15]], ...holes] } });
      });
      return src;
    },
    layers: () => [{ id: 'forest-mask', type: 'fill', maxOpacity: 0.62, paint: { 'fill-color': '#0B1620' } }],
  },
  forests: {
    source: () => ({ type: 'geojson', data: abs('data/forests.geojson') }), beforeLabels: false,
    layers: () => [
      { id: 'forests-line', type: 'line', filter: ['==', ['get', 'kind'], 'forest'], paint: { 'line-color': '#FFFFFF', 'line-width': 3 } },
      { id: 'forests-label', type: 'symbol', filter: ['==', ['get', 'kind'], 'label'],
        layout: { 'text-field': ['get', 'name'], 'text-font': FONT_BOLD, 'text-size': 20, 'text-allow-overlap': true, 'text-max-width': 9 },
        paint: { 'text-color': '#123B22', 'text-halo-color': '#FFFFFF', 'text-halo-width': 3 } }],
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
    layers: () => [{ id: 'places', type: 'symbol', 'source-layer': 'places', minzoom: 10, filter: ['==', ['get', 'is_green'], true],
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
