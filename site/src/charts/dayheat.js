// A day of heat (12 November 2026): hour-by-hour land surface temperature on 27 January 2026 from the
// Copernicus hourly product (about 3 km), as a line chart. It replaces the map animation, whose 3 km cloud
// gaps made it look broken. Two lines: the median inside Nairobi County and the median of the land around it.
// Hours when more than half of the county was under cloud are drawn as open circles on a dashed line,
// because fewer cells went into those medians. Crosshair by pointer, tap and arrow keys.
import { axisBottom, axisLeft, csv, line, scaleLinear, scalePoint, select } from 'd3';
import { abs, fmtC } from '../config.js';
import { detailLine, onResize } from './common.js';

const CITY = '#3E0751';
const AROUND = '#B07A2A';

export async function dayHeat(el) {
  const rows = (await csv(abs('data/day_of_heat_hourly.csv'))).map((d) => ({
    h: d.hour_eat, c: d.county_median_c === '' ? null : +d.county_median_c, cc: +d.county_clear_pct,
    a: d.around_median_c === '' ? null : +d.around_median_c, ac: +d.around_clear_pct,
  }));
  el.querySelectorAll('noscript').forEach((n) => n.remove());
  const detail = detailLine(el, 'Move along the chart, tap it, or focus it and use the arrow keys to read an hour.');
  let idx = 6;
  const draw = (width) => {
    select(el).select('svg').remove();
    const m = { top: 24, right: 150, bottom: 34, left: 40 };
    const narrow = width < 560;
    if (narrow) m.right = 16;
    const height = Math.round(Math.max(280, Math.min(380, width * 0.45)));
    const x = scalePoint().domain(rows.map((r) => r.h)).range([m.left, width - m.right]);
    const y = scaleLinear().domain([10, 46]).range([height - m.bottom, m.top]);
    const svg = select(el).insert('svg', '.chart-detail').attr('viewBox', `0 0 ${width} ${height}`).attr('class', 'chart-svg')
      .attr('role', 'img').attr('tabindex', 0)
      .attr('aria-label', 'Line chart of land surface temperature each hour from 06:00 to 19:00 on 27 January 2026, inside Nairobi County and on the land around it. Use the arrow keys to read each hour.');
    svg.append('g').attr('class', 'grid').attr('transform', `translate(${m.left},0)`)
      .call(axisLeft(y).ticks(6).tickSize(-(width - m.left - m.right)).tickFormat((v) => `${v}°`));
    svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${height - m.bottom})`)
      .call(axisBottom(x).tickValues(rows.map((r) => r.h).filter((_, i) => !narrow || i % 2 === 0)).tickSize(4));
    for (const [key, clear, col, name] of [['a', 'ac', AROUND, 'Land around the county'], ['c', 'cc', CITY, 'Nairobi County']]) {
      const pts = rows.filter((r) => r[key] !== null);
      svg.append('path').datum(pts).attr('fill', 'none').attr('stroke', col).attr('stroke-width', 2.5)
        .attr('d', line().x((r) => x(r.h)).y((r) => y(r[key])));
      svg.selectAll(null).data(pts).join('circle').attr('cx', (r) => x(r.h)).attr('cy', (r) => y(r[key])).attr('r', 4.5)
        .attr('fill', (r) => (r[clear] < 50 ? '#FFFFFF' : col)).attr('stroke', col).attr('stroke-width', 2);
      const last = pts.at(-1);
      if (!narrow) svg.append('text').attr('class', 'label-strong').attr('x', x(last.h) + 10).attr('y', y(last[key]) + (key === 'a' ? -8 : 10))
        .attr('fill', col).style('fill', col).text(name);
    }
    if (narrow) {
      const k = svg.append('g').attr('transform', `translate(${m.left},${m.top - 8})`);
      [['Nairobi County', CITY], ['Land around it', AROUND]].forEach(([n, c], i) => {
        k.append('rect').attr('x', i * 130).attr('y', -9).attr('width', 12).attr('height', 4).attr('fill', c);
        k.append('text').attr('x', i * 130 + 16).attr('y', -4).style('fill', c).attr('class', 'label-strong').text(n);
      });
    }
    const cross = svg.append('line').attr('y1', m.top).attr('y2', height - m.bottom).attr('stroke', '#1C2530').attr('display', 'none');
    const show = (i) => {
      idx = Math.max(0, Math.min(rows.length - 1, i));
      const r = rows[idx];
      cross.attr('display', null).attr('x1', x(r.h)).attr('x2', x(r.h));
      const part = (v, c) => (v === null ? 'no reading' : `${fmtC(v)}${c < 50 ? ` (only ${c} % clear)` : ''}`);
      detail.set(`${r.h} Nairobi time: Nairobi County ${part(r.c, r.cc)}; land around it ${part(r.a, r.ac)}.`);
    };
    const hide = () => { cross.attr('display', 'none'); detail.reset(); };
    svg.append('rect').attr('x', m.left).attr('y', m.top).attr('width', width - m.left - m.right).attr('height', height - m.top - m.bottom)
      .attr('fill', 'transparent').style('touch-action', 'pan-y')
      .on('pointermove pointerdown', (ev) => {
        const b = svg.node().getBoundingClientRect();
        const px = ((ev.clientX - b.left) / b.width) * width;
        let best = 0;
        rows.forEach((r, i) => { if (Math.abs(x(r.h) - px) < Math.abs(x(rows[best].h) - px)) best = i; });
        show(best);
      })
      .on('pointerleave', hide);
    svg.on('keydown', (e) => {
      if (e.key === 'ArrowLeft') show(idx - 1); else if (e.key === 'ArrowRight') show(idx + 1);
      else if (e.key === 'Escape') hide(); else return;
      e.preventDefault();
    });
    svg.on('focus', () => show(idx)).on('blur', hide);
  };
  onResize(el, draw);
}
