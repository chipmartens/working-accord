// The Working Accord. Every page works without this file; it only adds menu, motion, timeline arrows and form checks.
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const still = matchMedia('(prefers-reduced-motion: reduce)').matches;

// Smooth scrolling (Lenis). Off for reduced motion; anchors offset for the fixed bar.
if (window.Lenis && !still) {
  const lenis = new Lenis({ lerp: 0.09, wheelMultiplier: 1 });
  const raf = t => { lenis.raf(t); requestAnimationFrame(raf); };
  requestAnimationFrame(raf);
  document.addEventListener('click', e => {
    const a = e.target.closest('a[href*="#"]');
    if (!a || a.origin !== location.origin || a.pathname !== location.pathname) return;
    const el = document.getElementById(decodeURIComponent(a.hash.slice(1)));
    if (!el) return;
    e.preventDefault();
    lenis.scrollTo(el, { offset: -88 });
    if (!el.hasAttribute('tabindex') && !/^(A|BUTTON|INPUT|SELECT|TEXTAREA)$/.test(el.tagName)) el.setAttribute('tabindex', '-1');
    el.focus({ preventScroll: true });
    history.pushState(null, '', a.hash);
  });
}

// Menu overlay
const btn = $('#menuBtn'), menu = $('#menu');
if (btn && menu) {
  const setMenu = open => {
    menu.hidden = !open;
    btn.setAttribute('aria-expanded', open);
    btn.textContent = open ? 'Close' : 'Menu';
    document.body.style.overflow = open ? 'hidden' : '';
    if (open) $('a', menu).focus();
  };
  btn.addEventListener('click', () => setMenu(menu.hidden));
  $$('a', menu).forEach(a => a.addEventListener('click', () => setMenu(false)));
  addEventListener('keydown', e => { if (e.key === 'Escape' && !menu.hidden) { setMenu(false); btn.focus(); } });
}

// Bar goes solid past the photo hero (home) or right away (inner pages)
const bar = $('#bar'), heroImg = $('.hero-img');
const onScroll = () => {
  const y = scrollY;
  bar.classList.toggle('solid', !heroImg || y > innerHeight * 0.8);
  if (heroImg && !still && y < innerHeight) heroImg.style.transform = `scale(1.04) translateY(${y * 0.12}px)`;
};
addEventListener('scroll', onScroll, { passive: true });
onScroll();

// Reveal on scroll
if ('IntersectionObserver' in window && !still) {
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  }), { rootMargin: '0px 0px -8% 0px' });
  $$('.reveal').forEach(el => io.observe(el));
} else {
  $$('.reveal').forEach(el => el.classList.add('in'));
}

// Pinned media follows the story in the middle of the screen
const media = $$('.work-media img');
if (media.length) {
  const storyIO = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return;
    $$('.story').forEach(s => s.classList.toggle('on', s === e.target));
    media.forEach(m => m.classList.toggle('on', m.dataset.i === e.target.dataset.i));
  }), { rootMargin: '-45% 0px -45% 0px' });
  $$('.story').forEach(s => storyIO.observe(s));
}

// Timeline arrows
const tl = $('#timeline');
if (tl) {
  const prev = $('#tlPrev'), next = $('#tlNext');
  const step = () => $('li', tl).getBoundingClientRect().width + 36;
  const sync = () => {
    prev.disabled = tl.scrollLeft < 8;
    next.disabled = tl.scrollLeft + tl.clientWidth > tl.scrollWidth - 8;
  };
  prev.addEventListener('click', () => tl.scrollBy({ left: -step(), behavior: still ? 'auto' : 'smooth' }));
  next.addEventListener('click', () => tl.scrollBy({ left: step(), behavior: still ? 'auto' : 'smooth' }));
  tl.addEventListener('scroll', sync, { passive: true });
  tl.addEventListener('keydown', e => {
    if (e.key === 'ArrowRight') { e.preventDefault(); next.click(); }
    if (e.key === 'ArrowLeft') { e.preventDefault(); prev.click(); }
  });
  sync();
}

// Sign form: checks on blur and submit, sends nothing (concept)
const form = $('#signForm');
if (form) {
  const done = $('#done'), orgField = $('.employer-only');
  const rules = {
    fName: v => v.trim().length > 1 || 'Add your name so the signature counts.',
    fEmail: v => !v.trim() ? 'Add your email.' : /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()) || 'That email looks incomplete. Check for a missing @ or dot.',
    fOrg: v => orgField.hidden || v.trim().length > 1 || 'Employers sign as an organization. Add its name.',
  };
  const check = id => {
    const input = $('#' + id), res = rules[id](input.value), ok = res === true;
    const err = $('#' + input.getAttribute('aria-describedby'));
    input.closest('.field').classList.toggle('bad', !ok);
    input.setAttribute('aria-invalid', !ok);
    err.hidden = ok;
    if (!ok) err.textContent = res;
    return ok;
  };
  Object.keys(rules).forEach(id => $('#' + id).addEventListener('blur', () => $('#' + id).value && check(id)));
  $$('input[name="as"]', form).forEach(r => r.addEventListener('change', () => {
    orgField.hidden = form.as.value !== 'employer';
    $('#employerNote').hidden = orgField.hidden;
  }));
  form.addEventListener('submit', e => {
    e.preventDefault();
    const bad = Object.keys(rules).filter(id => !check(id));
    if (bad.length) { $('#' + bad[0]).focus(); done.hidden = true; return; }
    const who = form.as.value === 'employer' ? $('#fOrg').value.trim() : $('#fName').value.trim();
    done.textContent = `Concept only: nothing was sent or stored. On the live site, ${who} would get a confirmation email before being listed.`;
    done.hidden = false;
    done.focus();
  });
}

// On the job: sector filter (all examples are in the HTML; this only hides rows)
const exList = $('#exList');
if (exList) {
  const chips = $$('.ex-filter .chip'), count = $('#exCount');
  const apply = sector => {
    let n = 0;
    $$('.ex', exList).forEach(li => { const show = sector === 'all' || li.dataset.sector === sector; li.hidden = !show; if (show) n++; });
    chips.forEach(c => c.setAttribute('aria-pressed', c.dataset.sector === sector));
    count.textContent = `Showing ${n} ${n === 1 ? 'example' : 'examples'}`;
  };
  chips.forEach(c => c.addEventListener('click', () => apply(c.dataset.sector)));
  apply('all');
}
