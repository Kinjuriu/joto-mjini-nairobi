// MapLibre setup: local Protomaps basemap, pre-coloured raster layers, wards and buildings.
import { AttributionControl, Map as MLMap, NavigationControl, addProtocol, setWorkerUrl } from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import { Protocol } from 'pmtiles';
import { layers as basemapLayers, namedFlavor } from '@protomaps/basemaps';
import { ATTRIBUTION, RASTERS, REDUCED_MOTION, abs, absTemplate, countyBounds, heatStep } from './config.js';

setWorkerUrl(workerUrl);

let protocolAdded = false;
function ensureProtocol() {
  if (protocolAdded) return;
  addProtocol('pmtiles', new Protocol().tile);
  protocolAdded = true;
}

// Neutral grey basemap so that colour belongs to the data; paper-coloured background.
const flavor = { ...namedFlavor('grayscale'), background: '#F7F4EE', earth: '#F1EEE8' };

function baseStyle() {
  const all = basemapLayers('protomaps', flavor, { lang: 'en' });
  const labelIds = new Set(basemapLayers('protomaps', flavor, { labelsOnly: true, lang: 'en' }).map((l) => l.id));
  return {
    base: all.filter((l) => !labelIds.has(l.id)),
    labels: all.filter((l) => labelIds.has(l.id)),
  };
}

export function fadeMs() { return REDUCED_MOTION.matches ? 0 : 200; }

function style() {
  const { base, labels } = baseStyle();
  const sources = {
    protomaps: { type: 'vector', url: `pmtiles://${abs('data/nairobi_basemap.pmtiles')}`, attribution: ATTRIBUTION },
    county: { type: 'geojson', data: abs('data/county.geojson') },
    wards: { type: 'geojson', data: abs('data/wards.geojson'), attribution: 'Wards: geoBoundaries (Omare and Omare), CC BY 4.0', promoteId: 'ward_id' },
  };
  const dataLayers = [];
  for (const [id, r] of Object.entries(RASTERS)) {
    sources[id] = { type: 'raster', url: `pmtiles://${abs(r.file)}`, tileSize: 256, attribution: r.attribution };
    dataLayers.push({
      id, type: 'raster', source: id, layout: { visibility: 'none' },
      paint: { 'raster-opacity': 0.88, 'raster-resampling': 'nearest', 'raster-fade-duration': 0,
        'raster-opacity-transition': { duration: fadeMs() } },
    });
  }
  return {
    version: 8,
    glyphs: absTemplate('basemap-assets/fonts/{fontstack}/{range}.pbf'),
    sprite: abs('basemap-assets/sprites/light'),
    sources,
    layers: [
      ...base,
      ...dataLayers,
      { id: 'ward-fill', type: 'fill', source: 'wards', layout: { visibility: 'none' },
        paint: { 'fill-color': heatStep('pop_weighted_lst_c'), 'fill-opacity': 0.92 } },
      { id: 'ward-line', type: 'line', source: 'wards', layout: { visibility: 'none' },
        paint: { 'line-color': '#1C1B19', 'line-width': ['interpolate', ['linear'], ['zoom'], 9, 0.4, 13, 1.2], 'line-opacity': 0.55 } },
      { id: 'county-line', type: 'line', source: 'county',
        paint: { 'line-color': '#1C1B19', 'line-width': ['interpolate', ['linear'], ['zoom'], 9, 1, 13, 2] } },
      { id: 'ward-selected', type: 'line', source: 'wards', filter: ['==', ['get', 'ward_id'], ''],
        paint: { 'line-color': '#1C1B19', 'line-width': 3 } },
      ...labels,
    ],
  };
}

export async function createMap(container, { interactive = true, cooperative = true, center, zoom } = {}) {
  ensureProtocol();
  container.querySelectorAll('noscript').forEach((n) => n.remove());
  const bounds = await countyBounds();
  const map = new MLMap({
    container,
    style: style(),
    ...(center ? { center, zoom } : { bounds, fitBoundsOptions: { padding: 16 } }),
    interactive,
    cooperativeGestures: interactive && cooperative,
    attributionControl: false,
    maxBounds: [[bounds[0][0] - 0.6, bounds[0][1] - 0.5], [bounds[1][0] + 0.6, bounds[1][1] + 0.5]],
    minZoom: 8,
    maxZoom: 17,
    dragRotate: false,
    pitchWithRotate: false,
    fadeDuration: 0,
  });
  map.addControl(new AttributionControl({ compact: false, customAttribution: 'Analysis: Joto Mjini' }), 'bottom-right');
  if (interactive) map.addControl(new NavigationControl({ showCompass: false }), 'top-right');
  map.touchZoomRotate?.disableRotation?.();
  map.countyBounds = bounds;
  await new Promise((resolve) => map.once('load', resolve));
  return map;
}

// Show one raster layer (or none) and hide the rest.
export function showRaster(map, id) {
  for (const key of Object.keys(RASTERS)) {
    if (!map.getLayer(key)) continue;
    map.setLayoutProperty(key, 'visibility', key === id ? 'visible' : 'none');
  }
}

export function setWards(map, mode) {
  map.setLayoutProperty('ward-fill', 'visibility', mode === 'fill' ? 'visible' : 'none');
  map.setLayoutProperty('ward-line', 'visibility', mode === 'outline' || mode === 'fill' ? 'visible' : 'none');
}

export function addBuildings(map) {
  if (map.getSource('bldg-lst')) return;
  map.addSource('bldg-lst', { type: 'vector', url: `pmtiles://${abs('data/buildings.pmtiles')}`, attribution: 'Buildings: Overture Maps Foundation' });
  map.addLayer({
    id: 'bldg-lst', type: 'fill', source: 'bldg-lst', 'source-layer': 'buildings', minzoom: 12,
    layout: { visibility: 'none' },
    paint: { 'fill-color': heatStep('lst_c'), 'fill-outline-color': 'rgba(28,27,25,0.35)' },
  }, 'ward-fill');
}

export function moveTo(map, view) {
  const opts = REDUCED_MOTION.matches ? { duration: 0 } : { duration: 1500, essential: false };
  if (view.bounds) map.fitBounds(view.bounds, { padding: 20, ...opts, animate: !REDUCED_MOTION.matches });
  else if (REDUCED_MOTION.matches) map.jumpTo({ center: view.center, zoom: view.zoom });
  else map.flyTo({ center: view.center, zoom: view.zoom, ...opts });
}
