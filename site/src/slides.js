// Slides: fonts and styles only. Native scrolling; Page Down, Page Up and the arrow keys move one slide.
import '@fontsource/source-serif-4/latin-400.css';
import '@fontsource/source-serif-4/latin-600.css';
import '@fontsource/source-sans-3/latin-400.css';
import '@fontsource/source-sans-3/latin-600.css';
import './slides.css';

const slides = [...document.querySelectorAll('.slide')];
const current = () => slides.findIndex((s) => s.getBoundingClientRect().bottom > window.innerHeight / 2);
document.addEventListener('keydown', (e) => {
  const map = { ArrowRight: 1, ArrowDown: 1, PageDown: 1, ' ': 1, ArrowLeft: -1, ArrowUp: -1, PageUp: -1 };
  if (!(e.key in map)) return;
  e.preventDefault();
  const i = Math.max(0, Math.min(slides.length - 1, current() + map[e.key]));
  slides[i].scrollIntoView({ block: 'start' });
});
