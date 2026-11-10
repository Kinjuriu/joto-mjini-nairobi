// Hand-built SVG charts with D3: tree cover bands, and daily air temperature with the El Niño period shaded.
import {
  axisBottom, axisLeft, bisector, csv, extent, line, max, min, scaleBand, scaleLinear, scaleTime, select, timeFormat, timeMonth,
} from 'd3';
import { abs, fmtC } from './config.js';

const ORANGE = '#F9B06A';
const RED = '#A3200F';
const LINE = '#D2481E';

function tooltip(el) {
  let t = el.querySelector('.tooltip');
  if (!t) { t = document.createElement('div'); t.className = 'tooltip'; t.hidden = true; el.append(t); }
  return t;
}

function onResize(el, draw) {
  let w = 0;
  const ro = new ResizeObserver(() => { const nw = el.clientWidth; if (nw && Math.abs(nw - w) > 4) { w = nw; draw(nw); } });
  ro.observe(el);
}

export async function treeBands(el) {
  const data = (await csv(abs('data/lst_by_tree_band.csv'))).map((d) => ({
    band: `${d.tree_lo}–${d.tree_hi}`, mean: +d.mean_c, p25: +d.p25_c, p75: +d.p75_c, n: +d.n_cells,
  }));
  el.querySelectorAll('noscript').forEach((n) => n.remove());
  const tip = tooltip(el);
  const draw = (width) => {
    select(el).select('svg').remove();
    const narrow = width < 480;
    const m = { top: 14, right: narrow ? 52 : 64, bottom: 46, left: 40 };
    const height = Math.round(Math.max(280, Math.min(380, width * 0.62)));
    const x = scaleBand().domain(data.map((d) => d.band)).range([m.left, width - m.right]).padding(0.35);
    const y = scaleLinear().domain([Math.floor(min(data, (d) => d.p25) - 1), Math.ceil(max(data, (d) => d.p75) + 0.5)]).range([height - m.bottom, m.top]);
    const svg = select(el).insert('svg', ':first-child').attr('viewBox', `0 0 ${width} ${height}`).attr('aria-hidden', 'true');
    svg.append('g').attr('class', 'grid').attr('transform', `translate(${m.left},0)`)
      .call(axisLeft(y).ticks(5).tickSize(-(width - m.left - m.right)).tickFormat((v) => `${v}`))
      .call((g) => g.selectAll('text').attr('x', -6));
    svg.append('g').attr('transform', `translate(0,${height - m.bottom})`)
      .call(axisBottom(x).tickSize(0).tickFormat((d, i) => (narrow && i % 2 ? '' : d)))
      .call((g) => { g.select('.domain').attr('stroke', '#D8D2C6'); g.selectAll('text').attr('dy', '1.1em'); });
    svg.append('text').attr('x', (m.left + width - m.right) / 2).attr('y', height - 6).attr('text-anchor', 'middle').text('Tree cover in each 30 m cell (%)');
    svg.append('text').attr('x', 4).attr('y', m.top - 2).attr('dy', '-0.2em').text('°C');
    const bw = Math.min(16, x.bandwidth());
    const g = svg.selectAll('.band').data(data).join('g').attr('class', 'band');
    g.append('rect').attr('x', (d) => x(d.band) + x.bandwidth() / 2 - bw / 2).attr('width', bw)
      .attr('y', (d) => y(d.p75)).attr('height', (d) => y(d.p25) - y(d.p75)).attr('fill', ORANGE);
    g.append('rect').attr('x', (d) => x(d.band) + x.bandwidth() / 2 - 5).attr('width', 10)
      .attr('y', (d) => y(d.mean) - 5).attr('height', 10).attr('fill', RED);
    [0, data.length - 1].forEach((i) => {
      const d = data[i];
      svg.append('text').attr('class', 'label-strong').attr('x', x(d.band) + x.bandwidth() / 2 + 10).attr('y', y(d.mean)).attr('dy', '0.35em').text(fmtC(d.mean));
    });
    // Hit targets wider than the marks; focusable for keyboard users.
    g.append('rect').attr('x', (d) => x(d.band)).attr('width', x.bandwidth()).attr('y', m.top).attr('height', height - m.top - m.bottom)
      .attr('fill', 'transparent').attr('tabindex', 0).attr('role', 'img')
      .attr('aria-label', (d) => `Tree cover ${d.band} %: average ${fmtC(d.mean)}, middle half ${d.p25} to ${d.p75} °C`)
      .on('pointerenter focus', function show(ev, d) {
        tip.hidden = false;
        tip.innerHTML = `<strong>${d.band} % trees</strong><br>Average ${fmtC(d.mean)}<br>Middle half ${d.p25}–${d.p75} °C`;
        const left = Math.min(x(d.band) + x.bandwidth(), width - 150);
        tip.style.left = `${(left / width) * 100}%`;
        tip.style.top = `${(y(d.p75) / height) * 100}%`;
      })
      .on('pointerleave blur', () => { tip.hidden = true; });
  };
  onResize(el, draw);
}

export async function airTemp(el) {
  const data = (await csv(abs('data/daily_air_temp_2023_now.csv'))).map((d) => ({ date: new Date(`${d.date}T00:00:00`), tmax: +d.temperature_2m_max, en: d.el_nino === 'True' }));
  el.querySelectorAll('noscript').forEach((n) => n.remove());
  const tip = tooltip(el);
  const fmtDay = timeFormat('%-d %B %Y');
  const enStart = data.find((d) => d.en)?.date;
  const bis = bisector((d) => d.date).center;
  let idx = data.length - 1;
  const draw = (width) => {
    select(el).select('svg').remove();
    const narrow = width < 520;
    const m = { top: 22, right: 12, bottom: 30, left: 34 };
    const height = Math.round(Math.max(260, Math.min(360, width * 0.5)));
    const x = scaleTime().domain(extent(data, (d) => d.date)).range([m.left, width - m.right]);
    const y = scaleLinear().domain([Math.floor(min(data, (d) => d.tmax)) - 1, Math.ceil(max(data, (d) => d.tmax)) + 1]).range([height - m.bottom, m.top]);
    const svg = select(el).insert('svg', ':first-child').attr('viewBox', `0 0 ${width} ${height}`).attr('aria-hidden', 'true');
    if (enStart) {
      svg.append('rect').attr('x', x(enStart)).attr('width', x(data.at(-1).date) - x(enStart)).attr('y', m.top).attr('height', height - m.top - m.bottom).attr('fill', '#ECE8E1');
      svg.append('text').attr('class', 'label-strong').attr('x', x(enStart) + 4).attr('y', m.top - 6).text('El Niño, 2026');
    }
    svg.append('g').attr('class', 'grid').attr('transform', `translate(${m.left},0)`)
      .call(axisLeft(y).ticks(5).tickSize(-(width - m.left - m.right)))
      .call((g) => g.selectAll('text').attr('x', -6));
    svg.append('g').attr('transform', `translate(0,${height - m.bottom})`)
      .call(axisBottom(x).ticks(timeMonth.every(narrow ? 12 : 6)).tickFormat(timeFormat(narrow ? '%Y' : '%b %Y')).tickSize(4))
      .call((g) => g.select('.domain').attr('stroke', '#D8D2C6'));
    svg.append('path').datum(data).attr('fill', 'none').attr('stroke', LINE).attr('stroke-width', 1.2)
      .attr('d', line().x((d) => x(d.date)).y((d) => y(d.tmax)));
    const cross = svg.append('g').attr('display', 'none');
    cross.append('line').attr('y1', m.top).attr('y2', height - m.bottom).attr('stroke', '#1C1B19').attr('stroke-width', 1);
    cross.append('rect').attr('width', 8).attr('height', 8).attr('x', -4).attr('y', -4).attr('fill', '#1C1B19');
    const show = (i) => {
      idx = Math.max(0, Math.min(data.length - 1, i));
      const d = data[idx];
      cross.attr('display', null);
      cross.select('line').attr('x1', x(d.date)).attr('x2', x(d.date));
      cross.select('rect').attr('transform', `translate(${x(d.date)},${y(d.tmax)})`);
      tip.hidden = false;
      tip.innerHTML = `${fmtDay(d.date)}<br><strong>${fmtC(d.tmax)}</strong>`;
      const left = Math.min(Math.max(x(d.date) + 8, 0), width - 140);
      tip.style.left = `${(left / width) * 100}%`;
      tip.style.top = `${(m.top / height) * 100}%`;
    };
    const hide = () => { cross.attr('display', 'none'); tip.hidden = true; };
    svg.append('rect').attr('x', m.left).attr('y', m.top).attr('width', width - m.left - m.right).attr('height', height - m.top - m.bottom)
      .attr('fill', 'transparent').style('touch-action', 'pan-y')
      .on('pointermove pointerdown', (ev) => { const r = el.getBoundingClientRect(); show(bis(data, x.invert(((ev.clientX - r.left) / r.width) * width))); })
      .on('pointerleave', hide);
    el.tabIndex = 0;
    el.onkeydown = (e) => {
      const stepBy = e.shiftKey ? 30 : 1;
      if (e.key === 'ArrowLeft') show(idx - stepBy);
      else if (e.key === 'ArrowRight') show(idx + stepBy);
      else if (e.key === 'Home') show(0);
      else if (e.key === 'End') show(data.length - 1);
      else if (e.key === 'Escape') hide();
      else return;
      e.preventDefault();
    };
    el.onblur = hide;
  };
  onResize(el, draw);
}
