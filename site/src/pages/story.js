// The Story page (22 November 2026, Stephane): the long article with its charts. Same fonts, styles and chart code
// as the storyboard, but no maps, so it loads quickly.
import '@fontsource/source-serif-4/latin-400.css';
import '@fontsource/source-serif-4/latin-600.css';
import '@fontsource/source-serif-4/latin-400-italic.css';
import '@fontsource/source-sans-3/latin-400.css';
import '@fontsource/source-sans-3/latin-600.css';
import '../styles.css';
import '../story/story.css';

const bar = document.querySelector('.progress__bar');
const toTop = document.querySelector('.to-top');
const onScroll = () => {
  const h = document.documentElement.scrollHeight - window.innerHeight;
  if (bar) bar.style.width = `${h > 0 ? Math.min(100, (window.scrollY / h) * 100) : 0}%`;
  if (toTop) toTop.hidden = window.scrollY < window.innerHeight;
};
window.addEventListener('scroll', onScroll, { passive: true });
onScroll();

function whenNear(el, init, margin = '800px') {
  if (!el) return;
  const io = new IntersectionObserver((entries) => {
    if (entries.some((e) => e.isIntersecting)) { io.disconnect(); init(el).catch((err) => console.error(err)); }
  }, { rootMargin: `${margin} 0px` });
  io.observe(el);
}

const charts = {
  'ward-cover': async (el) => (await import('../charts/heatmap.js')).wardCoverTable(el),
  'day-heat': async (el) => (await import('../charts/dayheat.js')).dayHeat(el),
  'people-heat': async (el) => (await import('../charts/children.js')).peopleByHeat(el),
  'children-level': async (el) => (await import('../charts/children.js')).childrenByLevel(el),
  'schools-trees': async (el) => (await import('../charts/children.js')).schoolsTrees(el),
  'school-day': async (el) => (await import('../charts/schoolday.js')).schoolDay(el),
};
document.querySelectorAll('[data-chart]').forEach((el) => whenNear(el, charts[el.dataset.chart] || (async () => {})));
