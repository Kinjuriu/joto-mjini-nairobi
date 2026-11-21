// Three bar charts for the children and schools part of the story (20 November 2026, DECISIONS D60).
// Hand-built SVG with direct labels: every number is printed on the chart, so nothing depends on hover.
// Each row has its label above the bar, which works the same at 375 px and 1440 px.
//   peopleByHeat:   people living on each fifth of the county's land, coolest to hottest (people_by_heat.csv)
//   childrenByLevel: children by school level and adults, split between the hotter and cooler halves (children_by_level.csv)
//   schoolsTrees:   median tree cover within 200 m of schools on each fifth of the land (schools_by_heat.csv)
import { csv, select } from 'd3';
import { abs, fmtInt } from '../config.js';
import { onResize } from './common.js';

// Coolest to hottest: the two blues and two oranges of the heat-diff ramp, with a neutral middle that shows on white.
const FIFTH_COLOURS = ['#3B7CA6', '#8DBAD6', '#B9B2A6', '#F4A26B', '#D9542B'];
const HOT = '#C2311F';
const COOL = '#2F6E99';
const TREE = '#2E6B3A';
const NAMES = { 'coolest fifth': 'Coolest fifth', 'second fifth': 'Second fifth', 'middle fifth': 'Middle fifth', 'fourth fifth': 'Fourth fifth', 'hottest fifth': 'Hottest fifth' };
const pct = (v) => `${Number(v).toFixed(1)} %`;
const range = (r) => (r.from_c === '' ? `below ${Number(r.to_c).toFixed(1)} °C` : r.to_c === '' ? `${Number(r.from_c).toFixed(1)} °C and above` : `${Number(r.from_c).toFixed(1)} to ${Number(r.to_c).toFixed(1)} °C`);

function frame(el, height, label) {
  select(el).select('svg').remove();
  return select(el).append('svg').attr('class', 'chart-svg').attr('role', 'img').attr('aria-label', label)
    .attr('viewBox', `0 0 ${el.clientWidth} ${height}`);
}

/** One row: bold label, then a bar, then the value in dark text to the right of the bar (room is kept for it). */
const VALUE_ROOM = 180;
function row(svg, { y, width, label, frac, colour, value, sub }) {
  const w = Math.max(2, frac * (width - VALUE_ROOM));
  svg.append('text').attr('class', 'label-strong').attr('x', 0).attr('y', y).text(label);
  svg.append('rect').attr('x', 0).attr('y', y + 8).attr('width', w).attr('height', 18).attr('fill', colour);
  svg.append('text').attr('x', w + 8).attr('y', y + 22).attr('class', 'label-strong').text(value);
  if (sub) svg.append('text').attr('x', 0).attr('y', y + 44).text(sub);
}

export async function peopleByHeat(el) {
  const rows = await csv(abs('data/people_by_heat.csv'));
  el.querySelectorAll('noscript').forEach((n) => n.remove());
  const max = Math.max(...rows.map((r) => +r.people));
  const draw = (width) => {
    const step = 56;
    const svg = frame(el, rows.length * step + 6, `Bar chart of the people living on each fifth of Nairobi County's land, from the coolest to the hottest: ${rows.map((r) => `${NAMES[r.group]}, ${fmtInt(r.people)} people (${pct(r.share_pct)})`).join('; ')}.`);
    rows.forEach((r, i) => row(svg, { y: 16 + i * step, width: width - 4, frac: +r.people / max, colour: FIFTH_COLOURS[i],
      label: `${NAMES[r.group]}, ${range(r)}`, value: `${fmtInt(r.people)} people, ${pct(r.share_pct)}` }));
  };
  onResize(el, draw);
}

export async function childrenByLevel(el) {
  const rows = await csv(abs('data/children_by_level.csv'));
  el.querySelectorAll('noscript').forEach((n) => n.remove());
  const draw = (width) => {
    const step = 72;
    const gap = 18;   // space before the adults row, which is there for comparison
    const height = rows.length * step + gap + 4;
    const svg = frame(el, height, `Stacked bars of children in each school age group, and adults, living on the hotter and cooler halves of Nairobi: ${rows.map((r) => `${r.level} (${r.ages}), ${fmtInt(r.hotter_half)} on the hotter half (${pct(r.hotter_half_share_pct)}) and ${fmtInt(r.cooler_half)} on the cooler half`).join('; ')}.`);
    const W = width - 4;
    rows.forEach((r, i) => {
      const y = 16 + i * step + (r.key === 'adults_18_plus' ? gap : 0);
      const tot = +r.hotter_half + +r.cooler_half;
      const hw = (W * +r.hotter_half) / tot;
      if (r.key === 'adults_18_plus') svg.append('line').attr('x1', 0).attr('x2', W).attr('y1', y - 22).attr('y2', y - 22).attr('stroke', '#D9DEE4');
      svg.append('text').attr('class', 'label-strong').attr('x', 0).attr('y', y).text(`${r.level}, ages ${r.ages}`);
      svg.append('rect').attr('x', 0).attr('y', y + 8).attr('width', hw).attr('height', 18).attr('fill', HOT);
      svg.append('rect').attr('x', hw).attr('y', y + 8).attr('width', W - hw).attr('height', 18).attr('fill', COOL);
      svg.append('text').attr('x', 8).attr('y', y + 22).attr('class', 'label-strong').style('fill', '#FFFFFF').text(pct(r.hotter_half_share_pct));
      svg.append('text').attr('x', 0).attr('y', y + 44)
        .text(`${fmtInt(r.hotter_half)} on the hotter half; ${fmtInt(r.cooler_half)} on the cooler half`);
    });
  };
  onResize(el, draw);
}

export async function schoolsTrees(el) {
  const rows = await csv(abs('data/schools_by_heat.csv'));
  el.querySelectorAll('noscript').forEach((n) => n.remove());
  const draw = (width) => {
    const step = 74;
    const svg = frame(el, rows.length * step + 4, `Bar chart of the median tree cover within 200 metres of schools on each fifth of Nairobi County's land: ${rows.map((r) => `${NAMES[r.group]}, ${fmtInt(r.n_schools)} schools, ${pct(r.median_tree_pct)} tree cover`).join('; ')}.`);
    rows.forEach((r, i) => row(svg, { y: 16 + i * step, width: width - 4, frac: +r.median_tree_pct / 70, colour: TREE,
      label: `${NAMES[r.group]}, ${range(r)}: ${fmtInt(r.n_schools)} schools`, value: pct(r.median_tree_pct),
      sub: +r.share_under_10pct_trees === 0 ? 'No school here has less than a tenth under trees'
        : `Less than a tenth under trees at ${pct(r.share_under_10pct_trees)} of these schools` }));
  };
  onResize(el, draw);
}
