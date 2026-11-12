// Legend card (bottom right of every map, design brief v2 section 2) and date chip (top centre).
// Both read tiles/manifest.json, so a legend can never disagree with the tiles it describes.

let uid = 0;

// Position of a difference (°C from the city median) on the 9-class diverging strip, in percent.
const BREAKS = [-6, -4, -2, -0.5, 0.5, 2, 4, 6];
function stripPos(d) {
  const edges = [-8, ...BREAKS, 8];
  const i = Math.max(0, Math.min(8, edges.findIndex((e, k) => d >= e && d < edges[k + 1])));
  return ((i + (d - edges[i]) / (edges[i + 1] - edges[i])) / 9) * 100;
}
/** Marks on the colour bar for averages that are not places (for example the average resident's ground). */
function markersHTML(markers, median) {
  if (!markers?.length || median == null) return '';
  return `<ul class="legend-card__markers">${markers.map((mk, i) => {
    const pos = Math.max(2, Math.min(98, stripPos(mk.c - median)));
    return `<li style="--pos:${pos}%" class="legend-card__marker legend-card__marker--${i}"><span class="legend-card__marker-tick"></span>${mk.label}</li>`;
  }).join('')}</ul>`;
}

/** Card with layer name, an "i" button for the description and source, swatches and units. */
export class LegendCard {
  constructor(container, manifest) {
    this.manifest = manifest;
    this.el = document.createElement('section');
    this.el.className = 'legend-card';
    this.el.setAttribute('aria-label', 'Map legend');
    container.append(this.el);
    this.id = `legend-${(uid += 1)}`;
    this.collapsed = window.matchMedia('(max-width: 767px)').matches;
  }

  /** key: a manifest layer id; opts.title overrides the title; opts.note adds a line. */
  show(key, opts = {}) {
    const m = this.manifest[key];
    if (!key || !m) { this.el.hidden = true; return; }
    this.el.hidden = false;
    const L = m.legend || {};
    const title = opts.title || m.title;
    const classes = L.classes || [];
    const info = `${m.description} Source: ${m.source}.`;
    const diverging = classes.length === 9;
    let body = '';
    if (L.type === 'imagery') {
      body = key === 's2-false'
        ? '<ul class="legend-card__list"><li><span class="legend-card__sw" style="background:#3FD13F"></span>Living plants</li>'
          + '<li><span class="legend-card__sw" style="background:#B65BB0"></span>Roofs, roads, bare ground</li></ul>'
        : '<p class="legend-card__unit">Satellite image</p>';
    } else if (diverging) {
      // Strip with ticks at -6, -2, +2, +6 and words at the ends: no labels can collide.
      const sw = classes.map((c) => `<span style="background:${c.color}"></span>`).join('');
      body = `<div class="legend-card__strip" aria-hidden="true">${sw}</div>`
        + '<div class="legend-card__ticks" aria-hidden="true"><span style="left:11.1%">−6</span><span style="left:33.3%">−2</span>'
        + '<span style="left:50%">0</span><span style="left:66.7%">+2</span><span style="left:88.9%">+6</span></div>'
        + '<div class="legend-card__ends" aria-hidden="true"><span>Cooler</span><span>Hotter</span></div>'
        + markersHTML(opts.markers, m.median_c)
        + `<ul class="sr-only">${classes.map((c) => `<li>${c.label}</li>`).join('')}</ul>`;
    } else {
      body = `<ul class="legend-card__list">${classes.map((c) => `<li><span class="legend-card__sw" style="background:${c.color}"></span>${c.label}</li>`).join('')}</ul>`;
    }
    const unit = L.unit ? `<p class="legend-card__unit">${L.unit}${L.note ? `. ${L.note}` : ''}${opts.note ? `. ${opts.note}` : ''}</p>` : '';
    // Layout of NASA's legend card: title row with an "i" button and a collapse button, then the colours.
    this.el.innerHTML = `<div class="legend-card__head"><h3 class="legend-card__title">${title}</h3>`
      + `<button type="button" class="info-btn" aria-expanded="false" aria-controls="${this.id}-info" aria-label="About this layer">i</button>`
      + `<button type="button" class="legend-card__toggle" aria-expanded="${!this.collapsed}" aria-controls="${this.id}-body" aria-label="Show or hide the legend"><span aria-hidden="true"></span></button></div>`
      + `<p class="legend-card__info" id="${this.id}-info" hidden>${info}</p>`
      + `<div class="legend-card__body" id="${this.id}-body"${this.collapsed ? ' hidden' : ''}>${body}${unit}</div>`;
    const btn = this.el.querySelector('.info-btn');
    const inf = this.el.querySelector('.legend-card__info');
    btn.addEventListener('click', () => {
      const open = btn.getAttribute('aria-expanded') !== 'true';
      btn.setAttribute('aria-expanded', String(open));
      inf.hidden = !open;
    });
    const tog = this.el.querySelector('.legend-card__toggle');
    tog.addEventListener('click', () => {
      this.collapsed = !this.collapsed;
      tog.setAttribute('aria-expanded', String(!this.collapsed));
      this.el.querySelector('.legend-card__body').hidden = this.collapsed;
    });
  }
}

/** Small white chip at the top centre saying what time the layer shows. */
export class DateChip {
  constructor(container) {
    this.el = document.createElement('p');
    this.el.className = 'date-chip';
    this.el.setAttribute('aria-live', 'polite');
    container.append(this.el);
  }

  set(text) {
    this.el.hidden = !text;
    this.el.textContent = text || '';
  }
}
