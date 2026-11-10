// Swipe compare map: two synced maps, the right one clipped at the handle.
// The handle is a plain vertical rule with a square grip; mouse, touch and arrow keys move it.
import { createMap, setWards, showRaster } from './maps.js';

export async function initCompare(el) {
  const leftId = el.dataset.left;
  const rightId = el.dataset.right;
  el.innerHTML = '';
  const leftEl = document.createElement('div');
  leftEl.className = 'map';
  const clip = document.createElement('div');
  clip.className = 'compare__clip';
  const rightEl = document.createElement('div');
  rightEl.className = 'map';
  clip.append(rightEl);
  const handle = document.createElement('div');
  handle.className = 'compare__handle';
  handle.tabIndex = 0;
  handle.setAttribute('role', 'slider');
  handle.setAttribute('aria-label', `Compare ${el.dataset.leftLabel} (left) with ${el.dataset.rightLabel} (right)`);
  handle.setAttribute('aria-valuemin', '0');
  handle.setAttribute('aria-valuemax', '100');
  const lab = (text, side) => {
    const s = document.createElement('span');
    s.className = `compare__label compare__label--${side}`;
    s.textContent = text;
    return s;
  };
  el.append(leftEl, clip, handle, lab(el.dataset.leftLabel, 'left'), lab(el.dataset.rightLabel, 'right'));

  const [left, right] = await Promise.all([createMap(leftEl), createMap(rightEl)]);
  showRaster(left, leftId);
  showRaster(right, rightId);
  setWards(left, 'none');
  setWards(right, 'none');
  // Only the right map shows controls, so they are not doubled.
  leftEl.querySelectorAll('.maplibregl-ctrl-top-right, .maplibregl-ctrl-bottom-right').forEach((n) => { n.style.display = 'none'; });

  let syncing = false;
  const sync = (from, to) => () => {
    if (syncing) return;
    syncing = true;
    to.jumpTo({ center: from.getCenter(), zoom: from.getZoom(), bearing: from.getBearing(), pitch: from.getPitch() });
    syncing = false;
  };
  left.on('move', sync(left, right));
  right.on('move', sync(right, left));

  let pos = 50;
  const set = (p) => {
    pos = Math.max(0, Math.min(100, p));
    clip.style.clipPath = `inset(0 0 0 ${pos}%)`;
    handle.style.left = `${pos}%`;
    handle.setAttribute('aria-valuenow', String(Math.round(pos)));
    handle.setAttribute('aria-valuetext', `${Math.round(pos)} % from the left`);
  };
  set(50);

  const fromEvent = (e) => {
    const r = el.getBoundingClientRect();
    return ((e.clientX - r.left) / r.width) * 100;
  };
  handle.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    handle.setPointerCapture(e.pointerId);
    const move = (ev) => set(fromEvent(ev));
    const up = () => { handle.removeEventListener('pointermove', move); handle.removeEventListener('pointerup', up); };
    handle.addEventListener('pointermove', move);
    handle.addEventListener('pointerup', up);
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
  return { left, right };
}
