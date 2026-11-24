// A school day in Nairobi (22 November 2026, Stephane): official class hours for day schools, the Landsat pass
// and the hour Nairobi's ground was hottest on 27 January 2026, on one time line. Hand-built SVG, no hover needed.
// Hours: Basic Education Regulations, 2015, Regulation 84 (class 08:00 to 15:30, co-curricular 15:30 to 16:45,
// no day school may require learners to report before 07:15). Peak hour read from data/day_of_heat_hourly.csv.
import { csv, select } from 'd3';
import { abs } from '../config.js';
import { onResize } from './common.js';

const T0 = 6, T1 = 18;
const fmt = (h) => `${String(Math.floor(h)).padStart(2, '0')}:${String(Math.round((h % 1) * 60)).padStart(2, '0')}`;

export async function schoolDay(el) {
  const rows = (await csv(abs('data/day_of_heat_hourly.csv'))).filter((d) => d.county_median_c !== '');
  const peak = rows.reduce((a, b) => (+b.county_median_c > +a.county_median_c ? b : a));
  const peakH = Number(peak.hour_eat.slice(0, 2));
  el.querySelectorAll('noscript').forEach((n) => n.remove());
  const draw = (width) => {
    select(el).select('svg').remove();
    const narrow = width < 520;
    const m = { left: 8, right: 8 };
    const height = narrow ? 230 : 200;
    const x = (h) => m.left + ((h - T0) / (T1 - T0)) * (width - m.left - m.right);
    const svg = select(el).append('svg').attr('viewBox', `0 0 ${width} ${height}`).attr('class', 'chart-svg')
      .attr('role', 'img')
      .attr('aria-label', `Time line of a school day from 06:00 to 18:00: learners may not be asked to report before 07:15; class hours run from 08:00 to 15:30 and co-curricular activities from 15:30 to 16:45; Landsat passes at about 10:43; on 27 January 2026 Nairobi County's ground was hottest at ${peak.hour_eat}, ${(+peak.county_median_c).toFixed(1)} °C.`);
    const bandY = narrow ? 110 : 92, bandH = 40, axisY = bandY + bandH + 22;
    // bands
    svg.append('rect').attr('x', x(8)).attr('y', bandY).attr('width', x(15.5) - x(8)).attr('height', bandH).attr('fill', '#79C1E9').attr('fill-opacity', 0.55);
    svg.append('text').attr('class', 'label-strong').attr('x', x(8) + 8).attr('y', bandY + 25).text(narrow ? 'Class hours' : 'Class hours, 08:00 to 15:30');
    svg.append('rect').attr('x', x(15.5)).attr('y', bandY).attr('width', x(16.75) - x(15.5)).attr('height', bandH).attr('fill', '#79C1E9').attr('fill-opacity', 0.22);
    svg.append('text').attr('x', x(16.75)).attr('y', bandY + bandH + 16).attr('text-anchor', 'end').text(narrow ? 'Games, clubs' : 'Games and clubs to 16:45');
    // earliest reporting
    svg.append('line').attr('x1', x(7.25)).attr('x2', x(7.25)).attr('y1', bandY).attr('y2', bandY + bandH).attr('stroke', '#1C2530').attr('stroke-width', 2);
    svg.append('text').attr('x', narrow ? x(7.25) - 4 : x(7.25)).attr('y', bandY + bandH + 16).attr('text-anchor', narrow ? 'start' : 'middle').text('07:15 earliest arrival');
    // Landsat pass, with the small Landsat 9 picture
    const ls = 10 + 43 / 60;
    const top = narrow ? 50 : 50;
    svg.append('line').attr('x1', x(ls)).attr('x2', x(ls)).attr('y1', top).attr('y2', bandY + bandH).attr('stroke', '#1C2530').attr('stroke-dasharray', '3 3');
    const sat = narrow ? 44 : 56;
    svg.append('image').attr('href', abs('figures/landsat9.png')).attr('x', x(ls) - sat / 2).attr('y', top - sat * 0.57 - 4)
      .attr('width', sat).attr('height', sat * 0.57).attr('preserveAspectRatio', 'xMidYMid meet').on('error', function () { select(this).remove(); });
    svg.append('text').attr('x', x(ls) - 6).attr('y', top + 16).attr('text-anchor', 'end').text(narrow ? 'Landsat 10:43' : 'Landsat, about 10:43');
    // hottest hour
    svg.append('line').attr('x1', x(peakH)).attr('x2', x(peakH)).attr('y1', narrow ? 84 : 70).attr('y2', bandY + bandH).attr('stroke', '#A1201A').attr('stroke-width', 2.5);
    svg.append('circle').attr('cx', x(peakH)).attr('cy', narrow ? 84 : 70).attr('r', 5).attr('fill', '#A1201A');
    const label = narrow ? `Hottest, ${peak.hour_eat}: ${(+peak.county_median_c).toFixed(1)} °C` : `Ground hottest, ${peak.hour_eat}: ${(+peak.county_median_c).toFixed(1)} °C`;
    const right = x(peakH) + 8 + label.length * 7.5 > width;   // keep the label inside the chart
    svg.append('text').attr('class', 'label-strong').attr('x', right ? x(peakH) - 9 : x(peakH) + 8).attr('y', narrow ? 88 : 74)
      .attr('text-anchor', right ? 'end' : 'start').style('fill', '#A1201A').text(label);
    // axis
    const ax = svg.append('g').attr('class', 'axis');
    ax.append('line').attr('x1', x(T0)).attr('x2', x(T1)).attr('y1', axisY).attr('y2', axisY).attr('stroke', '#4A5563');
    for (let h = T0; h <= T1; h += narrow ? 3 : 2) {
      ax.append('line').attr('x1', x(h)).attr('x2', x(h)).attr('y1', axisY).attr('y2', axisY + 5).attr('stroke', '#4A5563');
      ax.append('text').attr('x', x(h)).attr('y', axisY + 19).attr('text-anchor', h === T0 ? 'start' : h === T1 ? 'end' : 'middle').text(fmt(h));
    }
  };
  onResize(el, draw);
}
