// Animated maps (the agreed exception to "no autoplay", DECISIONS D37): muted and looping, playing only while
// at least half on screen and pausing when scrolled away, with a visible Pause/Play button. Under
// prefers-reduced-motion they show the poster frame and wait for the reader to press Play.
// Without JavaScript the browser's own controls are shown and nothing plays by itself.
import { REDUCED_MOTION } from '../config.js';

export function initAnimations(root = document) {
  root.querySelectorAll('figure.anim video').forEach((video) => {
    const fig = video.closest('figure');
    video.removeAttribute('controls');
    video.muted = true;
    video.loop = true;
    video.playsInline = true;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'anim__btn';
    fig.querySelector('.anim__frame').append(btn);
    let userPaused = REDUCED_MOTION.matches;
    let onScreen = false;
    const label = () => {
      const playing = !video.paused;
      btn.textContent = playing ? 'Pause' : 'Play';
      btn.setAttribute('aria-label', `${playing ? 'Pause' : 'Play'} animation: ${video.getAttribute('aria-label') || ''}`);
    };
    const sync = () => {
      if (onScreen && !userPaused) {
        if (video.preload === 'none') video.preload = 'auto';
        video.play().catch(() => {});
      } else video.pause();
    };
    video.addEventListener('play', label);
    video.addEventListener('pause', label);
    btn.addEventListener('click', () => {
      userPaused = !video.paused;
      if (userPaused) video.pause(); else { onScreen = true; video.play().catch(() => {}); }
    });
    new IntersectionObserver((es) => { onScreen = es[0].intersectionRatio >= 0.5; sync(); }, { threshold: [0, 0.5, 1] }).observe(video);
    REDUCED_MOTION.addEventListener('change', () => { if (REDUCED_MOTION.matches) { userPaused = true; video.pause(); } });
    label();
  });
}
