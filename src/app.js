(function () {
  var EMBED = !document.querySelector('meta[name="kj-preview"]');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hasGsap = typeof window.gsap !== 'undefined';
  if (hasGsap && window.ScrollTrigger) gsap.registerPlugin(ScrollTrigger);

  /* Smooth scroll */
  var lenis = null;
  if (!reduce && typeof window.Lenis !== 'undefined') {
    lenis = new Lenis({ lerp: 0.1 });
    if (hasGsap && window.ScrollTrigger) {
      lenis.on('scroll', ScrollTrigger.update);
      gsap.ticker.add(function (t) { lenis.raf(t * 1000); });
      gsap.ticker.lagSmoothing(0);
    } else {
      (function raf(t) { lenis.raf(t); requestAnimationFrame(raf); })(0);
    }
  }
  function toTop() { if (lenis) lenis.scrollTo(0, { immediate: true }); else window.scrollTo(0, 0); }

  /* ---------- Clips ---------- */
  function playIn(el) {
    if (!el) return;
    el.querySelectorAll('video').forEach(function (v) {
      if (v.dataset.src) { v.src = v.dataset.src; delete v.dataset.src; }
      if (reduce) return; // keep the poster still for people who prefer less motion
      var p = v.play(); if (p && p.catch) p.catch(function () {});
    });
  }
  function pauseIn(el) { if (el) el.querySelectorAll('video').forEach(function (v) { v.pause(); }); }

  /* ---------- Index ---------- */
  var stage = document.querySelector('.stage');
  var frames = stage ? stage.querySelectorAll('figure') : [];
  var items = document.querySelectorAll('.list li');
  var current = -1;

  function show(i) {
    if (i === current || !items[i]) return;
    current = i;
    items.forEach(function (li, k) { li.classList.toggle('on', k === i); });
    frames.forEach(function (f, k) {
      if (k === i) {
        f.querySelectorAll('img[data-src]').forEach(function (img) { img.src = img.dataset.src; delete img.dataset.src; });
        f.classList.remove('on'); void f.offsetWidth; f.classList.add('on');
        playIn(f);
      } else { f.classList.remove('on'); pauseIn(f); }
    });
    document.body.classList.toggle('home-light', items[i].hasAttribute('data-light'));
  }
  /* The home page always opens on the first project (Nongfu Spring).
     It changes only when someone points at, focuses or scrolls to another name, and then stays there. */
  items.forEach(function (li, i) {
    var a = li.querySelector('a');
    a.addEventListener('mouseenter', function () { show(i); });
    a.addEventListener('focus', function () { show(i); });
  });
  /* Phones: the list stays put in the middle of the screen; each 64px of scroll moves the highlight one name */
  var STEP = 64, phoneQ = window.matchMedia('(hover: none) and (max-width: 899px)'), ticking = false;
  window.addEventListener('scroll', function () {
    if (ticking || !isHome() || !phoneQ.matches) return; ticking = true;
    requestAnimationFrame(function () {
      ticking = false;
      show(Math.max(0, Math.min(items.length - 1, Math.round(window.scrollY / STEP))));
    });
  }, { passive: true });
  show(0);

  /* ---------- Films ---------- */
  /* Our own films play in place, with sound. startFilm can begin at any second (used by the contact sheet). */
  function startFilm(a, t) {
    var v = a.querySelector('video');
    if (!v) {
      v = document.createElement('video');
      v.src = a.dataset.video; v.controls = true; v.playsInline = true; v.preload = 'auto';
      a.appendChild(v); a.classList.add('playing');
    }
    document.querySelectorAll('.film video').forEach(function (o) { if (o !== v) o.pause(); });
    function go() { if (t != null) { try { v.currentTime = t; } catch (e) {} } var p = v.play(); if (p && p.catch) p.catch(function () {}); }
    if (v.readyState >= 1) go(); else v.addEventListener('loadedmetadata', go, { once: true });
  }
  document.querySelectorAll('.cs-f').forEach(function (b) {
    b.addEventListener('click', function () {
      var page = b.closest('.view');
      var a = page && page.querySelector('.film[data-key="' + b.dataset.key + '"]');
      if (!a) return;
      var r = a.getBoundingClientRect();
      var y = window.scrollY + r.top - Math.max(16, (window.innerHeight - r.height) / 2);
      if (lenis) lenis.scrollTo(y, { duration: 0.9 }); else window.scrollTo({ top: y, behavior: reduce ? 'auto' : 'smooth' });
      startFilm(a, parseFloat(b.dataset.t));
    });
  });
  document.querySelectorAll('.film[data-video]').forEach(function (a) {
    a.addEventListener('keydown', function (ev) { if ((ev.key === 'Enter' || ev.key === ' ') && !a.querySelector('video')) { ev.preventDefault(); startFilm(a, null); } });
  });
  document.querySelectorAll('.film').forEach(function (a) {
    a.addEventListener('click', function (ev) {
      if (a.dataset.video) { if (!a.querySelector('video')) startFilm(a, null); return; }
      if (!EMBED || !a.dataset.embed) return; // falls back to opening the film in a new tab
      ev.preventDefault();
      if (a.querySelector('iframe')) return;
      var f = document.createElement('iframe');
      f.src = a.dataset.embed;
      f.title = a.getAttribute('aria-label') || 'Film';
      f.allow = 'autoplay; fullscreen; picture-in-picture';
      f.allowFullscreen = true;
      a.appendChild(f);
    });
  });

  /* ---------- Hero frames: projects with several film frames cycle through them ---------- */
  var heroTimer = null;
  function cycleHero(p) {
    clearInterval(heroTimer);
    var box = p && p.querySelector('.p-frames[data-cycle]');
    if (!box || reduce) return;
    var imgs = box.querySelectorAll('img'), k = 0;
    var wide = window.matchMedia('(min-width: 700px)');
    heroTimer = setInterval(function () {
      if (document.hidden || (box.classList.contains('tri') && wide.matches)) return;
      imgs[k].classList.remove('on');
      k = (k + 1) % imgs.length;
      imgs[k].classList.add('on');
    }, 2600);
  }

  /* ---------- Routing ---------- */
  var views = document.querySelectorAll('.view');
  var navLinks = document.querySelectorAll('.nav a');
  function isHome() { var h = location.hash.slice(1); return !h || h === 'work'; }
  function route() {
    var h = location.hash.slice(1) || 'work';
    var target = document.getElementById('v-' + h) || document.getElementById('v-work');
    views.forEach(function (v) { v.hidden = v !== target; });
    if (stage) stage.hidden = target.id !== 'v-work';
    if (target.id !== 'v-work') document.body.classList.remove('home-light');
    else if (items[current]) document.body.classList.toggle('home-light', items[current].hasAttribute('data-light'));
    navLinks.forEach(function (a) { a.toggleAttribute('aria-current', a.getAttribute('href') === '#' + (target.id === 'v-work' ? 'work' : h) || (a.getAttribute('href') === '#work' && target.classList.contains('project'))); });
    document.title = target.dataset.title || 'Kuo Jinn, Creative Lead, Singapore';
    toTop();
    if (hasGsap && window.ScrollTrigger) { ScrollTrigger.getAll().forEach(function (t) { t.kill(); }); }
    views.forEach(function (v) { if (v !== target && v.classList.contains('project')) pauseIn(v); });
    if (stage) { if (target.id === 'v-work') playIn(stage.querySelector('figure.on')); else pauseIn(stage); }
    if (target.classList.contains('project')) {
      playIn(target.querySelector('.p-frames'));
      target.querySelectorAll('.film.post').forEach(function (el) { playIn(el); });
    }
    cycleHero(target.classList.contains('project') ? target : null);
    if (target.classList.contains('project')) enter(target);
    if (hasGsap && window.ScrollTrigger) ScrollTrigger.refresh();
  }

  function enter(p) {
    if (!hasGsap || reduce) return;
    var light = p.classList.contains('light');
    var words = p.querySelectorAll('.p-title h2 .w > span');
    gsap.fromTo(words, { yPercent: 105 }, { yPercent: 0, duration: 1.05, ease: 'expo.out', stagger: 0.07, delay: 0.1 });
    if (!light) gsap.fromTo(p.querySelector('.p-frames'), { scale: 1.14 }, { scale: 1, duration: 2.2, ease: 'expo.out' });
    if (!window.ScrollTrigger) return;
    if (!light) gsap.to(p.querySelector('.p-frames'), { yPercent: 14, ease: 'none', scrollTrigger: { trigger: p.querySelector('.p-hero'), start: 'top top', end: 'bottom top', scrub: true } });

  }

  window.addEventListener('hashchange', route);
  route();
})();
