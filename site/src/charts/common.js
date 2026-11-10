// Shared bits for the hand-built SVG charts: resize handling, colour helpers and a detail line that shows the
// value under the pointer, finger or keyboard focus (nothing is hover-only).

export function onResize(el, draw) {
  let w = 0;
  const ro = new ResizeObserver(() => { const nw = el.clientWidth; if (nw && Math.abs(nw - w) > 4) { w = nw; draw(nw); } });
  ro.observe(el);
}

/** Dark or light text, whichever reads better on a fill colour. */
export function textOn(hex) {
  const n = parseInt(hex.slice(1), 16);
  const [r, g, b] = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => { const c = v / 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; });
  const L = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return L > 0.25 ? '#1C1B19' : '#FFFFFF';
}

/** The line under a chart that reads out the selected value (aria-live). */
export function detailLine(el, idle) {
  let d = el.querySelector('.chart-detail');
  if (!d) {
    d = document.createElement('p');
    d.className = 'chart-detail';
    d.setAttribute('aria-live', 'polite');
    el.append(d);
  }
  d.textContent = idle;
  return { set: (t) => { d.textContent = t; }, reset: () => { d.textContent = idle; } };
}

export const sign = (v, digits = 1) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(digits)}`;
