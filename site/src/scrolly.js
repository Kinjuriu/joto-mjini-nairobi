// Scrollytelling: one sticky map; Scrollama (IntersectionObserver, native scroll) switches chapters.
import scrollama from 'scrollama';
import { renderLegend } from './legend.js';
import { createMap, moveTo, setWards, showRaster } from './maps.js';

export async function initScrolly(section) {
  const mapEl = section.querySelector('[data-scrolly-map]');
  const legendEl = section.querySelector('[data-legend-scrolly]');
  const steps = [...section.querySelectorAll('.step')];
  const map = await createMap(mapEl, { interactive: false });

  let current = null;
  const apply = (step) => {
    if (step === current) return;
    current = step;
    steps.forEach((s) => s.classList.toggle('is-active', s === step));
    const layer = step.dataset.layer;
    showRaster(map, layer === 'none' ? null : layer);
    setWards(map, step.dataset.wards || 'none');
    renderLegend(legendEl, layer === 'none' ? 'wards' : layer);
    if (step.dataset.view === 'county') moveTo(map, { bounds: map.countyBounds });
    else if (step.dataset.center) {
      const [lng, lat] = step.dataset.center.split(',').map(Number);
      moveTo(map, { center: [lng, lat], zoom: Number(step.dataset.zoom) });
    }
  };
  apply(steps[0]);

  const offset = () => (window.innerWidth <= 860 ? 0.75 : 0.6);
  const scroller = scrollama();
  scroller.setup({ step: steps, offset: offset() })
    .onStepEnter(({ element }) => apply(element));
  window.addEventListener('resize', () => scroller.resize());

  // Scrollama can miss a step when the page jumps past it (keyboard, links, fast flicks).
  // On scroll, also apply the last step whose top is above the trigger line.
  let ticking = false;
  window.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      ticking = false;
      const line = window.innerHeight * offset();
      let pick = null;
      for (const st of steps) if (st.getBoundingClientRect().top <= line) pick = st;
      if (pick) apply(pick);
    });
  }, { passive: true });
  return map;
}
