// The scrolling map story (chunk 3). Cards scroll over a full-screen sticky map; when a card's middle is
// nearest the middle of the screen, the map flies to that chapter and cross-fades its layers.
//
// Both story blocks share ONE Mapbox map (each map instance is a billed map load): the map element moves
// into whichever block is on screen and is resized there. The chapter applied is always the card nearest
// the middle of the screen, so fast jumps (End key, scrollbar drag) land on the right state.
import { createMap } from '../map/createMap.js';
import { DateChip, LegendCard } from '../ui/legend.js';
import { CHAPTERS } from './chapters.js';

const MOBILE = window.matchMedia('(max-width: 767px)');

const padding = () => (MOBILE.matches
  ? { top: 120, bottom: Math.round(window.innerHeight * 0.44), left: 0, right: 0 }
  // Desktop and tablet: keep the place clear of the card (card width plus its 40 px margin and a gap).
  : { top: 0, bottom: 0, left: Math.min(480, (document.querySelector('.story .card')?.offsetWidth || 440) + 60), right: 0 });

export async function initStory(blocks) {
  const byId = new Map(CHAPTERS.map((c) => [c.id, c]));
  const frames = new Map(blocks.map((b) => [b.dataset.block, b.querySelector('.story__frame')]));
  const cards = blocks.flatMap((b) => [...b.querySelectorAll('.card[data-chapter]')]);

  const holder = Object.assign(document.createElement('div'), { className: 'story-map map-frame' });
  const mapEl = Object.assign(document.createElement('div'), { className: 'story-map__map' });
  holder.append(mapEl);
  let block = blocks[0].dataset.block;
  frames.get(block).append(holder);
  const first = CHAPTERS.find((c) => c.block === block);
  const ctl = await createMap(mapEl, {
    basemap: first.basemap, center: first.center, zoom: MOBILE.matches ? first.mobileZoom : first.zoom,
    scrollZoom: false, navigation: !MOBILE.matches,
  });
  const legend = new LegendCard(holder, ctl.manifest);
  const chip = new DateChip(holder);
  frames.forEach((f) => f.classList.add('is-ready'));

  let applied = null;
  let wanted = null;
  let busy = false;

  const run = async () => {
    if (busy) return;
    busy = true;
    while (wanted && wanted !== applied) {
      const id = wanted;
      const ch = byId.get(id);
      const prev = applied ? byId.get(applied) : null;
      // Same block, next or previous card: fly. Anything else (a jump): move instantly.
      const near = prev && prev.block === ch.block && Math.abs(CHAPTERS.indexOf(prev) - CHAPTERS.indexOf(ch)) === 1;
      applied = id;
      cards.forEach((c) => c.classList.toggle('is-active', c.dataset.chapter === id));
      legend.show(ch.legend, { title: ch.legendTitle });
      chip.set(ch.chip);
      await ctl.setChapter({
        basemap: ch.basemap, layers: ch.layers, highlight: ch.highlight || [],
        center: ch.center, zoom: MOBILE.matches ? ch.mobileZoom : (window.innerWidth < 1100 ? ch.zoom - 0.6 : ch.zoom), padding: padding(),
      }, { instant: !near });
    }
    busy = false;
  };

  const update = () => {
    // Trigger line: the middle of the screen on desktop; lower on phones, where cards sit at the bottom.
    const mid = window.innerHeight * (MOBILE.matches ? 0.72 : 0.5);
    // The block with most of itself on screen holds the map.
    let best = null;
    let bestVis = 0;
    for (const b of blocks) {
      const r = b.getBoundingClientRect();
      const vis = Math.min(r.bottom, window.innerHeight) - Math.max(r.top, 0);
      if (vis > bestVis) { bestVis = vis; best = b; }
    }
    if (!best || bestVis <= 0) return;
    if (best.dataset.block !== block) {
      block = best.dataset.block;
      frames.get(block).append(holder);
      ctl.map.resize();
    }
    let card = null;
    let dist = Infinity;
    for (const c of best.querySelectorAll('.card[data-chapter]')) {
      const r = c.getBoundingClientRect();
      const d = Math.abs((r.top + r.bottom) / 2 - mid);
      if (d < dist) { dist = d; card = c; }
    }
    if (card) { wanted = card.dataset.chapter; run(); }
  };

  let raf = 0;
  const onScroll = () => { if (!raf) raf = requestAnimationFrame(() => { raf = 0; update(); }); };
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', () => { ctl.map.resize(); applied = null; update(); });
  update();

  // For QA scripts: which chapter is on the map.
  window.__story = { ctl, get chapter() { return applied; }, chapters: CHAPTERS };
  return ctl;
}
