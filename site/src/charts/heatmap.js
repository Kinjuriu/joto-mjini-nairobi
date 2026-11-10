// Heatmap tables in the spirit of NASA's land cover table, following DESIGN_RULES.md: squared cells,
// the number printed in each cell, one colour ramp per table (or per column where stated), title,
// subtitle, source and date around it in HTML. One tab stop per table: arrow keys move a highlighted
// cell and the line under the table reads it out; a tap or click does the same.
import { csv, scaleQuantize, select } from 'd3';
import { abs, DIFF_BREAKS, DIFF_COLOURS } from '../config.js';
import { detailLine, onResize, sign, textOn } from './common.js';

const NEUTRAL_TO_RED = ['#F3EFE8', '#EBD9C8', '#E2BBA0', '#D9967A', '#C96F57', '#B2463A', '#8F2620'];
const GREENS = ['#F1F4EA', '#D9EBC7', '#B6D8A0', '#8CC07A', '#5A9E5C', '#3B8048', '#2E6B3F'];
const SANDS = ['#F7F3EA', '#EFE6CF', '#E3D3A6', '#D3BC7C', '#BC9F57', '#9C803C', '#7A6129'];
const diffColour = (v) => DIFF_COLOURS[DIFF_BREAKS.filter((b) => v >= b).length];

/**
 * Generic table: rows x cols, value(row, col) -> number, colour(col) -> scale fn, fmt(col) -> string fn.
 */
function drawTable(el, { rows, cols, value, colour, fmt, describe, rowLabelWidth = 150, cell = 52, cellH = 30, groupBreak }) {
  el.querySelectorAll('noscript').forEach((n) => n.remove());
  const detail = detailLine(el, 'Tap a cell, or focus the table and use the arrow keys, to read a value.');
  let cur = [0, 0];
  const draw = (width) => {
    select(el).select('svg').remove();
    const lw = width < 520 ? Math.min(rowLabelWidth, 112) : rowLabelWidth;
    const cw = Math.max(34, Math.min(cell, Math.floor((width - lw - 4) / cols.length)));
    const ch = width < 520 ? Math.max(24, cellH - 4) : cellH;
    const headH = 44;
    const gap = groupBreak !== undefined ? 14 : 0;
    const height = headH + rows.length * ch + gap + 4;
    const W = lw + cols.length * cw + 2;
    const svg = select(el).insert('svg', '.chart-detail').attr('viewBox', `0 0 ${W} ${height}`).attr('width', W)
      .attr('class', 'heatmap').attr('role', 'grid').attr('tabindex', 0)
      .attr('aria-label', `${el.dataset.title || 'Table'}. Use the arrow keys to move between cells.`);
    const yOf = (i) => headH + i * ch + (groupBreak !== undefined && i >= groupBreak ? gap : 0);
    cols.forEach((c, j) => {
      svg.append('text').attr('class', 'heatmap__col').attr('x', lw + j * cw + cw / 2).attr('y', headH - 10)
        .attr('text-anchor', 'middle').text(c.label);
      if (c.label2) svg.append('text').attr('class', 'heatmap__col heatmap__col--2').attr('x', lw + j * cw + cw / 2).attr('y', headH - 26).attr('text-anchor', 'middle').text(c.label2);
    });
    rows.forEach((r, i) => {
      svg.append('text').attr('class', 'heatmap__row').attr('x', lw - 8).attr('y', yOf(i) + ch / 2).attr('dy', '0.35em')
        .attr('text-anchor', 'end').text(r.label);
      cols.forEach((c, j) => {
        const v = value(r, c);
        const fill = v === null || Number.isNaN(v) ? '#FFFFFF' : colour(c)(v);
        const gEl = svg.append('g').attr('class', 'heatmap__cell').attr('data-i', i).attr('data-j', j)
          .attr('transform', `translate(${lw + j * cw},${yOf(i)})`)
          .on('click', () => select_(i, j));
        gEl.append('rect').attr('width', cw - 2).attr('height', ch - 2).attr('fill', fill);
        gEl.append('text').attr('x', (cw - 2) / 2).attr('y', (ch - 2) / 2).attr('dy', '0.35em').attr('text-anchor', 'middle')
          .style('fill', textOn(fill)).text(v === null ? '' : fmt(c)(v));
      });
    });
    const hl = svg.append('rect').attr('class', 'heatmap__focus').attr('width', cw - 2).attr('height', ch - 2).attr('display', 'none');
    function select_(i, j) {
      cur = [i, j];
      hl.attr('display', null).attr('x', lw + j * cw).attr('y', yOf(i));
      detail.set(describe(rows[i], cols[j], value(rows[i], cols[j])));
    }
    svg.on('keydown', (e) => {
      let [i, j] = cur;
      if (e.key === 'ArrowDown') i += 1; else if (e.key === 'ArrowUp') i -= 1;
      else if (e.key === 'ArrowRight') j += 1; else if (e.key === 'ArrowLeft') j -= 1;
      else if (e.key === 'Home') j = 0; else if (e.key === 'End') j = cols.length - 1;
      else if (e.key === 'Escape') { hl.attr('display', 'none'); detail.reset(); return; } else return;
      e.preventDefault();
      select_(Math.max(0, Math.min(rows.length - 1, i)), Math.max(0, Math.min(cols.length - 1, j)));
    });
    svg.on('focus', () => select_(...cur));
  };
  onResize(el, draw);
}

/** Table 1: built-up share of each sub-county, GHSL epochs. */
export async function builtupTable(el) {
  const data = await csv(abs('data/builtup_by_subcounty.csv'), (d) => ({ ...d, epoch: +d.epoch, built_pct: +d.built_pct }));
  const epochs = [...new Set(data.map((d) => d.epoch))];
  const subs = [...new Set(data.map((d) => d.subcounty))];
  const get = new Map(data.map((d) => [`${d.subcounty}|${d.epoch}`, d.built_pct]));
  const sc = scaleQuantize().domain([0, 42]).range(NEUTRAL_TO_RED);
  drawTable(el, {
    rows: subs.map((s) => ({ label: s, key: s })),
    cols: epochs.map((e) => ({ label: e === 2025 ? '2025*' : String(e), key: e })),
    value: (r, c) => get.get(`${r.key}|${c.key}`),
    colour: () => sc,
    fmt: () => (v) => v.toFixed(0),
    describe: (r, c, v) => `${r.key}, ${c.key}${c.key === 2025 ? ' (JRC projection)' : ''}: ${v.toFixed(1)} % of the ground built up.`,
    rowLabelWidth: 140, cell: 56,
  });
}

/** Table 2: land cover in the 10 hottest and 10 coolest wards by where people live. */
export async function wardCoverTable(el) {
  const data = await csv(abs('data/ward_cover_extremes.csv'), (d) => ({ ...d, tree_pct: +d.tree_pct, grass_pct: +d.grass_pct, built_pct: +d.built_pct, bare_pct: +d.bare_pct, diff_c: +d.diff_c }));
  const pct = (range) => scaleQuantize().domain([0, 100]).range(range);
  const cols = [
    { key: 'tree_pct', label: 'Trees', colour: pct(GREENS), unit: '% tree cover' },
    { key: 'grass_pct', label: 'Grass', colour: pct(SANDS), unit: '% grassland' },
    { key: 'built_pct', label: 'Built', colour: pct(NEUTRAL_TO_RED), unit: '% built-up' },
    { key: 'bare_pct', label: 'Bare', colour: pct(SANDS), unit: '% bare ground' },
    { key: 'diff_c', label: '°C', label2: 'vs median', colour: diffColour, unit: '°C from the city median, where people live' },
  ];
  drawTable(el, {
    rows: data.map((d) => ({ label: d.ward_name, d })),
    cols,
    value: (r, c) => r.d[c.key],
    colour: (c) => c.colour,
    fmt: (c) => (c.key === 'diff_c' ? (v) => sign(v) : (v) => v.toFixed(0)),
    describe: (r, c, v) => `${r.d.ward_name} (${r.d.group === 'hottest' ? 'one of the 10 hottest' : 'one of the 10 coolest'} wards where people live): `
      + `${c.key === 'diff_c' ? `${sign(v)} °C from the city median, where people live` : `${v.toFixed(1)} ${c.unit}`}.`,
    rowLabelWidth: 190, cell: 60, groupBreak: 10,
  });
}

/** Table 3: calendar of daily maximum air temperature, difference from the 1991 to 2020 normal. */
export async function calendar(el) {
  const data = await csv(abs('data/daily_tmax_anomaly.csv'), (d) => ({ date: d.date, y: +d.date.slice(0, 4), m: +d.date.slice(5, 7), day: +d.date.slice(8, 10), tmax: +d.tmax_c, a: +d.anomaly_c, en: d.el_nino === 'True' }));
  el.querySelectorAll('noscript').forEach((n) => n.remove());
  const months = [...new Set(data.map((d) => `${d.y}-${String(d.m).padStart(2, '0')}`))];
  const byKey = new Map(data.map((d) => [`${d.y}-${String(d.m).padStart(2, '0')}|${d.day}`, d]));
  const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const MONTH = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  const detail = detailLine(el, 'Tap a day, or focus the calendar and use the arrow keys, to read its value.');
  // Diverging steps for daily anomalies (°C): narrower than the map's, because daily air temperature varies less.
  const breaks = [-3, -2, -1, -0.25, 0.25, 1, 2, 3];
  const col = (v) => DIFF_COLOURS[breaks.filter((b) => v >= b).length];
  let cur = [months.length - 1, 0];
  const draw = (width) => {
    select(el).select('svg').remove();
    const lw = 64;
    const bw = 92;
    const cw = Math.max(8, Math.min(20, Math.floor((width - lw - bw) / 31)));
    const ch = Math.max(9, Math.min(14, cw));
    const top = 22;
    const W = lw + 31 * cw + bw;
    const H = top + months.length * ch + 6;
    const svg = select(el).insert('svg', '.chart-detail').attr('viewBox', `0 0 ${W} ${H}`).attr('width', W).attr('class', 'heatmap heatmap--calendar')
      .attr('role', 'grid').attr('tabindex', 0).attr('aria-label', 'Calendar of daily high air temperature compared with normal, January 2023 to the latest month. Use the arrow keys to move between days.');
    [1, 10, 20, 31].forEach((d) => svg.append('text').attr('class', 'heatmap__col').attr('x', lw + (d - 0.5) * cw).attr('y', top - 8).attr('text-anchor', 'middle').text(d));
    months.forEach((mk, i) => {
      const [y, m] = mk.split('-').map(Number);
      if (m === 1 || i === 0) svg.append('text').attr('class', 'heatmap__row heatmap__row--year').attr('x', 2).attr('y', top + i * ch + ch / 2).attr('dy', '0.35em').text(y);
      svg.append('text').attr('class', 'heatmap__row').attr('x', lw - 6).attr('y', top + i * ch + ch / 2).attr('dy', '0.35em').attr('text-anchor', 'end').text(MON[m - 1]);
      for (let d = 1; d <= 31; d += 1) {
        const r = byKey.get(`${mk}|${d}`);
        if (!r) continue;
        svg.append('rect').attr('x', lw + (d - 1) * cw).attr('y', top + i * ch).attr('width', cw - 1).attr('height', ch - 1).attr('fill', col(r.a))
          .on('click', () => sel(i, d - 1));
      }
    });
    // El Niño bracket on the right, from the first El Niño month to the last month.
    const first = months.findIndex((mk) => data.some((d) => d.en && mk === `${d.y}-${String(d.m).padStart(2, '0')}`));
    if (first >= 0) {
      const x = lw + 31 * cw + 8;
      const y0 = top + first * ch;
      const y1 = top + months.length * ch - 1;
      svg.append('path').attr('class', 'heatmap__bracket').attr('d', `M${x},${y0} h6 V${y1} h-6`);
      svg.append('text').attr('class', 'heatmap__bracket-label').attr('x', x + 12).attr('y', (y0 + y1) / 2).attr('dy', '-0.2em').text('El Niño,');
      svg.append('text').attr('class', 'heatmap__bracket-label').attr('x', x + 12).attr('y', (y0 + y1) / 2).attr('dy', '1em').text('2026');
    }
    const hl = svg.append('rect').attr('class', 'heatmap__focus').attr('width', cw - 1).attr('height', ch - 1).attr('display', 'none');
    function sel(i, j) {
      cur = [i, j];
      const r = byKey.get(`${months[i]}|${j + 1}`);
      hl.attr('display', null).attr('x', lw + j * cw).attr('y', top + i * ch);
      if (!r) { detail.set(''); return; }
      detail.set(`${r.day} ${MONTH[r.m - 1]} ${r.y}: daily high ${r.tmax.toFixed(1)} °C, ${sign(r.a)} °C from the 1991 to 2020 normal for that day${r.en ? ' (El Niño period)' : ''}.`);
    }
    svg.on('keydown', (e) => {
      let [i, j] = cur;
      if (e.key === 'ArrowDown') i += 1; else if (e.key === 'ArrowUp') i -= 1;
      else if (e.key === 'ArrowRight') j += 1; else if (e.key === 'ArrowLeft') j -= 1;
      else if (e.key === 'Escape') { hl.attr('display', 'none'); detail.reset(); return; } else return;
      e.preventDefault();
      sel(Math.max(0, Math.min(months.length - 1, i)), Math.max(0, Math.min(30, j)));
    });
    svg.on('focus', () => sel(...cur));
  };
  onResize(el, draw);
  // Colour key under the calendar: one swatch per class, labelled at the class edges.
  const key = el.parentElement.querySelector('.calendar-key');
  if (key) {
    const labels = ['−3 or cooler', '−3 to −2', '−2 to −1', '−1 to −0.25', 'about normal', '+0.25 to +1', '+1 to +2', '+2 to +3', '+3 or warmer'];
    key.innerHTML = `<ul>${DIFF_COLOURS.map((c, i) => `<li><span style="background:${c}"></span>${labels[i]}</li>`).join('')}</ul><p>°C difference from the 1991 to 2020 normal</p>`;
    key.removeAttribute('aria-hidden');
  }
  return { breaks, colours: DIFF_COLOURS };
}
