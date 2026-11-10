// Swipe compare: two synchronised maps, the right one clipped at the handle.
// The handle is a plain vertical rule with a square grip; it works with mouse, touch and the arrow keys
// (role="slider"). Used by interlude 1 and by the explorer's Compare mode.
import { createMap } from './createMap.js';

export async function createCompare(container, { left, right, labels = ['', ''], start = 50, mapOpts = {}, onMove } = {}) {
  container.classList.add('compare');
  const a = Object.assign(document.createElement('div'), { className: 'compare__map compare__map--left' });
  const b = Object.assign(document.createElement('div'), { className: 'compare__map compare__map--right' });
  container.append(a, b);
  const common = { center: left.center, zoom: left.zoom, scrollZoom: mapOpts.scrollZoom ?? false, ...mapOpts };
  const [L, R] = await Promise.all([
    createMap(a, { ...common, basemap: left.basemap, navigation: false }),
    createMap(b, { ...common, basemap: right.basemap }),
  ]);
  L.setLayers(left.layers, 0);
  R.setLayers(right.layers, 0);

  // Keep the two cameras together; whichever map the reader moves leads.
  let syncing = false;
  const sync = (from, to) => () => {
    if (syncing) return;
    syncing = true;
    to.map.jumpTo({ center: from.map.getCenter(), zoom: from.map.getZoom(), bearing: 0, pitch: 0 });
    syncing = false;
  };
  L.map.on('move', sync(L, R));
  R.map.on('move', sync(R, L));

  const labelEls = labels.map((t, i) => {
    const el = Object.assign(document.createElement('p'), { className: `compare__label compare__label--${i ? 'right' : 'left'}`, textContent: t });
    container.append(el);
    return el;
  });
  const handle = document.createElement('div');
  handle.className = 'compare__handle';
  handle.tabIndex = 0;
  handle.setAttribute('role', 'slider');
  handle.setAttribute('aria-label', `Swipe between ${labels[0]} (left) and ${labels[1]} (right)`);
  handle.setAttribute('aria-valuemin', '0');
  handle.setAttribute('aria-valuemax', '100');
  handle.innerHTML = '<span class="compare__grip" aria-hidden="true"></span>';
  container.append(handle);

  let pos = start;
  const set = (p) => {
    pos = Math.max(0, Math.min(100, p));
    b.style.clipPath = `inset(0 0 0 ${pos}%)`;
    handle.style.left = `${pos}%`;
    handle.setAttribute('aria-valuenow', String(Math.round(pos)));
    handle.setAttribute('aria-valuetext', `${Math.round(pos)} % of the width shows ${labels[0]}`);
    if (onMove) onMove(pos);
  };
  set(pos);
  const fromEvent = (e) => {
    const r = container.getBoundingClientRect();
    return ((e.clientX - r.left) / r.width) * 100;
  };
  handle.addEventListener('pointerdown', (e) => {
    handle.setPointerCapture(e.pointerId);
    const move = (ev) => set(fromEvent(ev));
    const up = () => { handle.removeEventListener('pointermove', move); handle.removeEventListener('pointerup', up); };
    handle.addEventListener('pointermove', move);
    handle.addEventListener('pointerup', up);
    e.preventDefault();
  });
  handle.addEventListener('keydown', (e) => {
    const step = e.shiftKey ? 10 : 2;
    if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') set(pos - step);
    else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') set(pos + step);
    else if (e.key === 'Home') set(0);
    else if (e.key === 'End') set(100);
    else return;
    e.preventDefault();
  });

  return {
    left: L, right: R, handle, labels: labelEls,
    get position() { return pos; },
    setPosition: set,
    destroy() { L.map.remove(); R.map.remove(); container.replaceChildren(); container.classList.remove('compare'); },
  };
}
