// Daily maximum air temperature since January 2023 with the El Niño period shaded (layout of NASA's highlighted
// rainfall chart). Crosshair on hover and on tap; the chart takes keyboard focus and the arrow keys step a day
// (Shift steps a month); the record day is labelled directly.
import { axisBottom, axisLeft, bisector, csv, extent, line, max, min, scaleLinear, scaleTime, select, timeFormat, timeMonth } from 'd3';
import { abs, fmtC } from '../config.js';
import { detailLine, onResize } from './common.js';

// Stephane's chart colours: line rgb(62,7,81), highlighted period rgb(121,193,233).
const LINE = '#3E0751';
const SHADE = '#79C1E9';

export async function airChart(el) {
  const data = (await csv(abs('data/daily_tmax_anomaly.csv'))).map((d) => ({
    date: new Date(`${d.date}T00:00:00`), tmax: +d.tmax_c, normal: +d.normal_c, en: d.el_nino === 'True',
  }));
  el.querySelectorAll('noscript').forEach((n) => n.remove());
  const fmtDay = timeFormat('%-d %B %Y');
  const enStart = data.find((d) => d.en)?.date;
  const rec = data.reduce((a, b) => (b.tmax > a.tmax ? b : a));
  const bis = bisector((d) => d.date).center;
  const detail = detailLine(el, 'Move along the chart, tap it, or focus it and use the arrow keys to read a day.');
  let idx = data.length - 1;
  const draw = (width) => {
    select(el).select('svg').remove();
    const narrow = width < 560;
    const m = { top: 30, right: 14, bottom: 30, left: 36 };
    const height = Math.round(Math.max(280, Math.min(400, width * 0.46)));
    const x = scaleTime().domain(extent(data, (d) => d.date)).range([m.left, width - m.right]);
    const y = scaleLinear().domain([Math.floor(min(data, (d) => d.tmax)) - 1, Math.ceil(max(data, (d) => d.tmax)) + 1]).range([height - m.bottom, m.top]);
    const svg = select(el).insert('svg', '.chart-detail').attr('viewBox', `0 0 ${width} ${height}`)
      .attr('class', 'chart-svg').attr('role', 'img').attr('tabindex', 0)
      .attr('aria-label', `Line chart of Nairobi's daily high air temperature from ${fmtDay(data[0].date)} to ${fmtDay(data.at(-1).date)}. The El Niño period from May 2026 is shaded. Highest: ${fmtC(rec.tmax)} on ${fmtDay(rec.date)}. Use the arrow keys to read each day.`);
    if (enStart) {
      svg.append('rect').attr('x', x(enStart)).attr('width', x(data.at(-1).date) - x(enStart)).attr('y', m.top).attr('height', height - m.top - m.bottom).attr('fill', SHADE).attr('fill-opacity', 0.4);
      svg.append('text').attr('class', 'label-strong').attr('x', x(enStart) + 6).attr('y', m.top - 10).text('El Niño, 2026');
    }
    svg.append('g').attr('class', 'grid').attr('transform', `translate(${m.left},0)`)
      .call(axisLeft(y).ticks(5).tickSize(-(width - m.left - m.right)).tickFormat((v) => `${v}°`))
      .call((g) => g.selectAll('text').attr('x', -6));
    svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${height - m.bottom})`)
      .call(axisBottom(x).ticks(timeMonth.every(narrow ? 12 : 6)).tickFormat(timeFormat(narrow ? '%Y' : '%b %Y')).tickSize(4))
      .call((g) => g.select('.domain').attr('stroke', '#D8D2C6'));
    svg.append('path').datum(data).attr('fill', 'none').attr('stroke', LINE).attr('stroke-width', 1.2)
      .attr('d', line().x((d) => x(d.date)).y((d) => y(d.tmax)));
    // Direct label for the record day.
    svg.append('rect').attr('x', x(rec.date) - 3).attr('y', y(rec.tmax) - 3).attr('width', 6).attr('height', 6).attr('fill', LINE);
    const lx = x(rec.date) < width - 200 ? x(rec.date) + 8 : x(rec.date) - 8;
    svg.append('text').attr('class', 'label-strong').attr('x', lx).attr('y', y(rec.tmax)).attr('dy', '0.35em')
      .attr('text-anchor', x(rec.date) < width - 200 ? 'start' : 'end').text(`Highest: ${fmtC(rec.tmax)}, ${timeFormat('%-d %b %Y')(rec.date)}`);
    const cross = svg.append('g').attr('display', 'none');
    cross.append('line').attr('y1', m.top).attr('y2', height - m.bottom).attr('stroke', '#1C1B19').attr('stroke-width', 1);
    cross.append('rect').attr('width', 8).attr('height', 8).attr('x', -4).attr('y', -4).attr('fill', '#1C1B19');
    const tip = cross.append('text').attr('class', 'label-strong').attr('y', m.top + 14);
    const show = (i) => {
      idx = Math.max(0, Math.min(data.length - 1, i));
      const d = data[idx];
      cross.attr('display', null);
      cross.select('line').attr('x1', x(d.date)).attr('x2', x(d.date));
      cross.select('rect').attr('transform', `translate(${x(d.date)},${y(d.tmax)})`);
      const right = x(d.date) < width - 150;
      tip.attr('x', x(d.date) + (right ? 6 : -6)).attr('text-anchor', right ? 'start' : 'end').text(fmtC(d.tmax));
      detail.set(`${fmtDay(d.date)}: daily high ${fmtC(d.tmax)}; normal for the day ${fmtC(d.normal)}${d.en ? '; El Niño period' : ''}.`);
    };
    const hide = () => { cross.attr('display', 'none'); detail.reset(); };
    svg.append('rect').attr('x', m.left).attr('y', m.top).attr('width', width - m.left - m.right).attr('height', height - m.top - m.bottom)
      .attr('fill', 'transparent').style('touch-action', 'pan-y')
      .on('pointermove pointerdown', (ev) => { const r = svg.node().getBoundingClientRect(); show(bis(data, x.invert(((ev.clientX - r.left) / r.width) * width))); })
      .on('pointerleave', hide);
    svg.on('keydown', (e) => {
      const stepBy = e.shiftKey || e.key.startsWith('Page') ? 30 : 1;
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') show(idx - stepBy);
      else if (e.key === 'ArrowRight' || e.key === 'PageDown') show(idx + stepBy);
      else if (e.key === 'Home') show(0);
      else if (e.key === 'End') show(data.length - 1);
      else if (e.key === 'Escape') hide();
      else return;
      e.preventDefault();
    });
    svg.on('focus', () => show(idx)).on('blur', hide);
  };
  onResize(el, draw);
}
