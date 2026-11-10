// Legend card (bottom right of every map, design brief v2 section 2) and date chip (top centre).
// Both read tiles/manifest.json, so a legend can never disagree with the tiles it describes.

let uid = 0;

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
      body = '<p class="legend-card__unit">Satellite image</p>';
    } else if (diverging) {
      // Strip with ticks at -6, -2, +2, +6 and words at the ends: no labels can collide.
      const sw = classes.map((c) => `<span style="background:${c.color}"></span>`).join('');
      body = `<div class="legend-card__strip" aria-hidden="true">${sw}</div>`
        + '<div class="legend-card__ticks" aria-hidden="true"><span style="left:11.1%">−6</span><span style="left:33.3%">−2</span>'
        + '<span style="left:50%">0</span><span style="left:66.7%">+2</span><span style="left:88.9%">+6</span></div>'
        + '<div class="legend-card__ends" aria-hidden="true"><span>Cooler</span><span>Hotter</span></div>'
        + `<ul class="sr-only">${classes.map((c) => `<li>${c.label}</li>`).join('')}</ul>`;
    } else {
      body = `<ul class="legend-card__list">${classes.map((c) => `<li><span class="legend-card__sw" style="background:${c.color}"></span>${c.label}</li>`).join('')}</ul>`;
    }
    const unit = L.unit ? `<p class="legend-card__unit">${L.unit}${L.note ? `. ${L.note}` : ''}${opts.note ? `. ${opts.note}` : ''}</p>` : '';
    this.el.innerHTML = `<div class="legend-card__head"><h3 class="legend-card__title">${title}</h3>`
      + `<button type="button" class="info-btn" aria-expanded="false" aria-controls="${this.id}-info" aria-label="About this layer">i</button></div>`
      + `<p class="legend-card__info" id="${this.id}-info" hidden>${info}</p>`
      + `<div class="legend-card__body${this.collapsed && !diverging ? ' is-collapsed' : ''}">${body}${unit}</div>`
      + (this.collapsed && !diverging && L.type !== 'imagery'
        ? '<button type="button" class="legend-card__more" aria-expanded="false">Show classes</button>' : '');
    const btn = this.el.querySelector('.info-btn');
    const inf = this.el.querySelector('.legend-card__info');
    btn.addEventListener('click', () => {
      const open = btn.getAttribute('aria-expanded') !== 'true';
      btn.setAttribute('aria-expanded', String(open));
      inf.hidden = !open;
    });
    const more = this.el.querySelector('.legend-card__more');
    if (more) {
      more.addEventListener('click', () => {
        const b = this.el.querySelector('.legend-card__body');
        const open = b.classList.toggle('is-collapsed') === false;
        more.setAttribute('aria-expanded', String(open));
        more.textContent = open ? 'Hide classes' : 'Show classes';
      });
    }
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
