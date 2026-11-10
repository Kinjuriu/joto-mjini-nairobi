// Legends drawn from data/legends.json: square swatches with hairline borders, values labelled directly.
import { getJSON } from './config.js';

const fmt = (v, unit) => {
  if (unit.startsWith('share')) return `${Math.round(v * 100)} %`;
  if (unit.startsWith('people')) return new Intl.NumberFormat('en-GB').format(v);
  return `${v}`;
};

export async function renderLegend(el, key, { title } = {}) {
  if (!el) return;
  const legends = await getJSON('data/legends.json');
  const lk = key === 'buildings' || key === 'wards' ? 'lst_hot_season' : key;
  const L = legends[lk];
  if (!L) { el.innerHTML = ''; return; }
  const unit = L.unit;
  const isTemp = unit === 'deg C';
  // Labels sit at the boundaries between swatches: each swatch is labelled with its lower bound.
  const sign = (v) => (v > 0 ? `+${v}` : `${v}`.replace('-', '−'));
  const items = L.classes.map((c, i) => {
    let label = '';
    if (i > 0) label = key === 'lst_anomaly' ? sign(c.from) : fmt(c.from, unit);
    if (i === 0 && !L.clamp_ends) label = fmt(c.from, unit);
    return `<div class="legend__item"><div class="legend__swatch" style="background:${c.colour}"></div><div class="legend__label">${label}&nbsp;</div></div>`;
  }).join('');
  let heading = title || L.title;
  if (key === 'buildings') heading = 'Buildings: land surface temperature of the area around each building';
  if (key === 'wards') heading = 'Wards: land surface temperature under their people';
  const unitText = isTemp ? '°C' : unit === 'people per km2' ? 'people per km²' : '';
  const below = !L.clamp_ends ? `No colour: under ${fmt(L.classes[0].from, unit)}` : '';
  el.innerHTML = `<div class="legend__title">${heading.replace('deg C', '°C')}${unitText ? `, ${unitText}` : ''}</div>`
    + `<div class="legend__row">${items}</div>`
    + (below ? `<div class="legend__label">${below}</div>` : '');
}
