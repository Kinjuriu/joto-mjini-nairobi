// Entry point: fonts, styles, reading progress, and the maps and charts, each loaded when it comes near the screen.
import '@fontsource/source-serif-4/latin-400.css';
import '@fontsource/source-serif-4/latin-600.css';
import '@fontsource/source-serif-4/latin-400-italic.css';
import '@fontsource/source-sans-3/latin-400.css';
import '@fontsource/source-sans-3/latin-600.css';
import './styles.css';
import './map/map.css';
import './story/story.css';

// Thin, static reading progress bar (the one allowed exception in DESIGN_RULES.md).
const bar = document.querySelector('.progress__bar');
const updateProgress = () => {
  const h = document.documentElement.scrollHeight - window.innerHeight;
  bar.style.width = `${h > 0 ? Math.min(100, (window.scrollY / h) * 100) : 0}%`;
};
window.addEventListener('scroll', updateProgress, { passive: true });
updateProgress();

function whenNear(el, init, margin = '800px') {
  if (!el) return;
  const io = new IntersectionObserver((entries) => {
    if (entries.some((e) => e.isIntersecting)) {
      io.disconnect();
      init(el).catch((err) => console.error(err));
    }
  }, { rootMargin: `${margin} 0px` });
  io.observe(el);
}

const blocks = [...document.querySelectorAll('.story[data-block]')];
whenNear(blocks[0], async () => (await import('./story/scrolly.js')).initStory(blocks), '400px');

whenNear(document.getElementById('season-compare'), async (el) => {
  const { createCompare } = await import('./map/compare.js');
  const { LegendCard } = await import('./ui/legend.js');
  const view = { center: [36.86, -1.29], zoom: window.innerWidth < 768 ? 9.3 : 10.4 };
  const cmp = await createCompare(el, {
    left: { ...view, basemap: 'satellite', layers: [{ id: 'county-line', opacity: 1 }, { id: 'places', opacity: 1 }] },
    right: { ...view, basemap: 'satellite', layers: [{ id: 'heat-diff', opacity: 0.85 }, { id: 'county-line', opacity: 1 }, { id: 'places', opacity: 1 }] },
    labels: ['Satellite image', 'Surface temperature'],
  });
  new LegendCard(el, cmp.right.manifest).show('heat-diff', { title: 'Right side: difference from the city median, °C' });
  window.__compare = cmp;
});

// Animated maps: play only on screen; see src/ui/anim.js.
import('./ui/anim.js').then((m) => m.initAnimations());

// Heatmap tables and the highlighted chart (chunk 4).
const charts = {
  'ward-cover': async (el) => (await import('./charts/heatmap.js')).wardCoverTable(el),
  builtup: async (el) => (await import('./charts/heatmap.js')).builtupTable(el),
  calendar: async (el) => (await import('./charts/heatmap.js')).calendar(el),
  air: async (el) => (await import('./charts/air.js')).airChart(el),
  'day-heat': async (el) => (await import('./charts/dayheat.js')).dayHeat(el),
};
document.querySelectorAll('[data-chart]').forEach((el) => whenNear(el, charts[el.dataset.chart] || (async () => {})));

// Explorer dashboard (chunk 5).
import('./explorer/explorer.css');
whenNear(document.getElementById('explore'), async (el) => (await import('./explorer/explorer.js')).initExplorer(el));
if (window.location.hash.startsWith('#explore?')) document.getElementById('explore')?.scrollIntoView();
