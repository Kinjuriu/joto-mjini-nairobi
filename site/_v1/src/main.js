// Entry point: fonts, styles, reading progress, and maps and charts loaded when they come near the screen.
import '@fontsource/source-serif-4/latin-400.css';
import '@fontsource/source-serif-4/latin-600.css';
import '@fontsource/source-serif-4/latin-400-italic.css';
import '@fontsource/source-sans-3/latin-400.css';
import '@fontsource/source-sans-3/latin-600.css';
import 'maplibre-gl/dist/maplibre-gl.css';
import './styles.css';

import { renderLegend } from './legend.js';

// Thin, static reading progress bar.
const bar = document.querySelector('.progress__bar');
const updateProgress = () => {
  const h = document.documentElement.scrollHeight - window.innerHeight;
  bar.style.width = `${h > 0 ? Math.min(100, (window.scrollY / h) * 100) : 0}%`;
};
window.addEventListener('scroll', updateProgress, { passive: true });
updateProgress();

document.querySelectorAll('[data-legend]').forEach((el) => renderLegend(el, el.dataset.legend));

// Load each heavy component only when it comes near the screen.
function whenNear(el, init, margin = '600px') {
  if (!el) return;
  const io = new IntersectionObserver((entries) => {
    if (entries.some((e) => e.isIntersecting)) {
      io.disconnect();
      init(el).catch((err) => { console.error(err); showError(el, err); });
    }
  }, { rootMargin: margin });
  io.observe(el);
}

function showError(el, err) {
  const p = document.createElement('p');
  p.className = 'placeholder';
  p.textContent = `This map or chart could not load (${err.message}). The numbers are in the text.`;
  el.append(p);
}

document.querySelectorAll('[data-compare]').forEach((el) => whenNear(el, async (e) => (await import('./compare.js')).initCompare(e), '200px'));
whenNear(document.querySelector('#tour'), async (e) => (await import('./scrolly.js')).initScrolly(e));
whenNear(document.querySelector('#explore'), async (e) => (await import('./explorer.js')).initExplorer(e));
whenNear(document.querySelector('[data-chart="tree-bands"]'), async (e) => (await import('./charts.js')).treeBands(e));
whenNear(document.querySelector('[data-chart="air-temp"]'), async (e) => (await import('./charts.js')).airTemp(e));

// A shared link with a ward or layer opens at the explorer.
if (/(^|[#&])(ward|layer)=/.test(window.location.hash)) {
  window.addEventListener('load', () => document.querySelector('#explore')?.scrollIntoView());
}
