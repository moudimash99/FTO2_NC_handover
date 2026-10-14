/* Five page concepts for the dashboard's Analyses tab. Each concept moves the existing chart cards into its own structure and
   sets its chart drawing style; "reset" puts everything back, so concepts can be switched without reloading. */
(function () {
  'use strict';
  var root = document.documentElement, AP = document.getElementById('p-ana'), AG = document.getElementById('ag');
  if (!AP || !AG) return;
  var CARDS = [].slice.call(AG.querySelectorAll('.vcard')), D = window.DASH;
  var moved = [], added = [], undo = [], cur = 'base', concept = null;

  function fr() { var b = document.getElementById('lFr'); return !b || b.getAttribute('aria-pressed') === 'true'; }
  function T(f, e) { return fr() ? f : e; }
  function fmt(n) { return Math.round(n).toLocaleString(fr() ? 'fr-FR' : 'en-GB'); }
  function keur(n) { var v = (Math.round(n / 100) / 10).toLocaleString(fr() ? 'fr-FR' : 'en-GB'); return fr() ? v + ' k€' : v + 'k EUR'; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html) e.innerHTML = html; return e; }
  function move(node, parent, before) { if (!node) return; moved.push([node, node.parentNode, node.nextSibling]); parent.insertBefore(node, before || null); }
  function add(node, parent, before) { added.push(node); parent.insertBefore(node, before || null); return node; }
  function on(target, type, fn, opt) { target.addEventListener(type, fn, opt); undo.push(function () { target.removeEventListener(type, fn, opt); }); }
  function stats() {
    var nc = D.ncs.filter(function (n) { return n[23] === 'serie'; });
    return { def: D.defects.filter(function (r) { return r[20] === 'serie'; }).length, nc: nc.length,
      cost: nc.reduce(function (a, n) { return a + n[12]; }, 0), ret: D.ncs.filter(function (n) { return n[23] === 'client'; }).length,
      open: nc.filter(function (n) { return n[30]; }).length };
  }
  // year(s) and number of months covered, read from the data
  function period() {
    var a = D.meta.from, b = D.meta.to, y1 = +a.slice(0, 4), y2 = +b.slice(0, 4);
    return { years: y1 === y2 ? String(y1) : y1 + '–' + y2, months: (y2 - y1) * 12 + (+b.slice(5, 7)) - (+a.slice(5, 7)) + 1 };
  }
  function finding(card) { var h = card.querySelector('.vhead h3'); return h ? h.textContent : ''; }
  function kicker(card) { var k = card.querySelector('.kicker'); return k ? k.textContent : ''; }
  function redraw() { var b = document.querySelector('.seg.lang [aria-pressed="true"]'); if (b) b.click(); outline(); }

  // outlined marks: the shape keeps its colour as a stroke, with a light fill
  function outline() {
    if (root.getAttribute('data-marks') !== 'outline') return;
    AP.querySelectorAll('svg.viz rect, svg.viz path, svg.viz circle').forEach(function (e) {
      if (e.hasAttribute('data-ol')) return; e.setAttribute('data-ol', '1');
      var f = e.getAttribute('fill');
      if (!f || f === 'none' || f === 'transparent' || f.indexOf('url(') === 0 || f === 'var(--track)' || e.classList.contains('lnk')) return;
      var s = e.getAttribute('stroke'); if (s && s !== 'none') return;
      e.setAttribute('stroke', f); e.setAttribute('stroke-width', '1.4'); e.setAttribute('fill-opacity', '0.16');
    });
  }

  // enlarged card (Console, Galerie)
  var open = null;
  function openCard(card) {
    if (open) closeCard(true);
    open = { card: card, bd: el('div', 'c-backdrop'), x: el('button', 'c-close', esc(T('Fermer ×', 'Close ×'))) };
    open.x.type = 'button';
    document.body.appendChild(open.bd); card.insertBefore(open.x, card.firstChild); card.classList.add('is-open');
    open.bd.addEventListener('click', function () { closeCard(); });
    open.x.addEventListener('click', function (e) { e.stopPropagation(); closeCard(); });
    redraw(); card.scrollTop = 0; open.x.focus();
  }
  function closeCard(silent) {
    if (!open) return; var c = open.card;
    c.classList.remove('is-open'); open.bd.remove(); open.x.remove(); open = null;
    if (!silent) { redraw(); c.focus && c.focus(); }
  }
  function cardKeys(e) {
    if (!open) return;
    if (e.key === 'Escape') { closeCard(); return; }
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      var vis = CARDS.filter(function (c) { return c.offsetParent !== null || c === open.card; }), i = vis.indexOf(open.card) + (e.key === 'ArrowRight' ? 1 : -1);
      if (vis[i]) openCard(vis[i]);
    }
  }

  var CONCEPTS = {
    base: { marks: null, apply: function () {} },

    story: { marks: 'minimal', apply: function () {
      var hero = add(el('section', 'c-hero'), AP, AP.firstChild);
      this.relabel = function () {
        var s = stats();
        var pr = period();
        hero.innerHTML = '<div class="eyebrow">' + esc(T('Analyses des NC série · ', 'Series NC insights · ') + pr.years) + '</div>' +
          '<h2>' + T('Ce que disent <em>' + fmt(s.def) + ' défauts</em> sur ' + pr.months + ' mois', 'What <em>' + fmt(s.def) + ' defects</em> say about ' + pr.months + ' months') + '</h2>' +
          '<div class="nums">' + [[fmt(s.nc), T('NC série', 'series NCs')], [keur(s.cost), T('coût de non-qualité', 'cost of non-quality')],
            [fmt(s.ret), T('retours clients', 'customer returns')], [fmt(s.open), T('NC encore ouvertes', 'NCs still open')]].map(function (p) {
            return '<div><b>' + esc(p[0]) + '</b><span>' + esc(p[1]) + '</span></div>'; }).join('') + '</div>';
      };
    } },

    slides: { marks: 'bold', apply: function () {
      var bar = add(el('div', 'c-slidebar'), AP, AP.firstChild), cover = add(el('section', 'c-cover'), AG, AG.firstChild), n = CARDS.length + 1, gap = 24;
      bar.innerHTML = '<div class="t"></div><div class="nav"><button type="button" data-go="-1">←</button><span class="count"></span><button type="button" data-go="1">→</button></div>';
      function idx() { return Math.round(AG.scrollLeft / (AG.clientWidth + gap)); }
      function go(i) { i = Math.max(0, Math.min(n - 1, i)); AG.scrollTo({ left: i * (AG.clientWidth + gap), behavior: 'smooth' }); }
      function count() { bar.querySelector('.count').textContent = String(idx() + 1).padStart(2, '0') + ' / ' + n; }
      on(bar, 'click', function (e) { var b = e.target.closest('[data-go]'); if (b) go(idx() + Number(b.getAttribute('data-go'))); });
      on(AG, 'scroll', count, { passive: true });
      on(document, 'keydown', function (e) {
        if (/INPUT|SELECT|TEXTAREA/.test((e.target || {}).tagName || '')) return;
        if (e.key === 'ArrowRight' || e.key === 'PageDown') { e.preventDefault(); go(idx() + 1); }
        if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); go(idx() - 1); }
      });
      this.relabel = function () {
        var s = stats();
        bar.querySelector('.t').innerHTML = 'FTO2 <span>· ' + esc(T('Analyses des NC série', 'Series NC insights')) + '</span>';
        cover.innerHTML = '<div class="k">FTO2 · ' + esc(T('Qualité', 'Quality')) + '</div><h2>' + esc(T('Non-conformités ', 'Non-conformities ') + period().years) + '</h2>' +
          '<div class="nums">' + [[fmt(s.def), T('défauts série', 'series defects')], [fmt(s.nc), T('NC série', 'series NCs')], [keur(s.cost), T('coût de non-qualité', 'cost of non-quality')]].map(function (p) {
            return '<div><b>' + esc(p[0]) + '</b><span>' + esc(p[1]) + '</span></div>'; }).join('') + '</div>' +
          '<div class="hint">' + esc(T('Flèches ← → du clavier pour avancer.', 'Use the ← → keys to move.')) + '</div>';
        count();
      };
      AG.scrollLeft = 0;
    } },

    console: { marks: null, apply: function () {
      var side = add(el('aside', 'c-side'), document.body, document.body.firstChild), tabs = document.getElementById('tabs');
      side.appendChild(el('div', 'brand')); side.appendChild(el('div', 'grp g1'));
      move(tabs, side); side.appendChild(el('div', 'grp g2'));
      move(document.getElementById('minorCtl'), side); move(document.querySelector('.seg.lang'), side);
      var kpis = add(el('div', 'c-kpis'), AP, AG);
      CARDS.forEach(function (c) {
        var b = add(el('button', 'c-expand'), c); b.type = 'button';
        b.addEventListener('click', function (e) { e.stopPropagation(); openCard(c); });
      });
      on(document, 'keydown', cardKeys);
      this.relabel = function () {
        var s = stats();
        side.querySelector('.brand').innerHTML = 'FTO2 · ' + esc(T('Qualité', 'Quality')) + '<span>' + esc(T('Non-conformités ', 'Non-conformities ') + period().years) + '</span>';
        side.querySelector('.g1').textContent = T('Pages', 'Pages'); side.querySelector('.g2').textContent = T('Affichage', 'Display');
        kpis.innerHTML = [[fmt(s.def), T('Défauts série', 'Series defects')], [fmt(s.nc), T('NC série', 'Series NCs')], [keur(s.cost), T('Coût de non-qualité', 'Cost of non-quality')],
          [fmt(s.ret), T('Retours clients', 'Customer returns')], [fmt(s.open), T('NC encore ouvertes', 'NCs still open')]].map(function (p) {
          return '<div><span>' + esc(p[1]) + '</span><b>' + esc(p[0]) + '</b></div>'; }).join('');
        CARDS.forEach(function (c) { var b = c.querySelector('.c-expand'); if (b) b.textContent = T('Agrandir ⤢', 'Enlarge ⤢'); });
      };
    } },

    gallery: { marks: 'outline', apply: function () {
      CARDS.forEach(function (c) { c.setAttribute('tabindex', '0'); });
      undo.push(function () { CARDS.forEach(function (c) { c.removeAttribute('tabindex'); }); });
      on(AG, 'click', function (e) {
        var c = e.target.closest('.vcard');
        if (c && !c.classList.contains('is-open')) { e.stopPropagation(); e.preventDefault(); openCard(c); }
      }, true);
      on(AG, 'keydown', function (e) {
        var c = e.target.classList && e.target.classList.contains('vcard') ? e.target : null;
        if (c && !c.classList.contains('is-open') && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); openCard(c); }
      });
      on(document, 'keydown', cardKeys);
    } },

    questions: { marks: null, apply: function () {
      var Q = { cal: ['Quand les défauts sont-ils déclarés\u00a0?', 'When are defects reported?'], flow: ['Où sont-ils trouvés, et que devient la pièce\u00a0?', 'Where are they found, and what happens next?'],
        bub: ['Quelles causes coûtent le plus\u00a0?', 'Which causes cost the most?'], lor: ['Le problème est-il concentré sur quelques NC\u00a0?', 'Is the problem concentrated in a few NCs?'],
        mek: ['Les lignes ont-elles les mêmes défauts\u00a0?', 'Do the lines have the same defects?'], bump: ['Quelles causes montent ou descendent\u00a0?', 'Which causes rise or fall?'],
        msn: ['Quels avions coûtent le plus\u00a0?', 'Which aircraft cost the most?'], prod: ['Quels produits coûtent le plus\u00a0?', 'Which products cost the most?'],
        lead: ['Combien de temps une NC reste-t-elle ouverte\u00a0?', 'How long does an NC stay open?'], clock: ['À quelle heure les NC sont-elles écrites\u00a0?', 'At what time are NCs written?'],
        station: ['Quel poste, quels défauts\u00a0?', 'Which station, which defects?'], act: ['Les actions MFT ont-elles un effet\u00a0?', 'Are the MFT actions working?'] };
      var list = add(el('div', 'c-qlist'), AG, AG.firstChild), active = 0;
      list.setAttribute('role', 'group');
      list.innerHTML = CARDS.map(function (c, i) { return '<button type="button" data-q="' + i + '"><b></b><span></span></button>'; }).join('');
      function pick(i) { active = i; CARDS.forEach(function (c, j) { c.classList.toggle('is-active', j === i); });
        [].forEach.call(list.children, function (b, j) { b.setAttribute('aria-pressed', String(j === i)); }); redraw(); }
      on(list, 'click', function (e) { var b = e.target.closest('[data-q]'); if (b) pick(Number(b.getAttribute('data-q'))); });
      undo.push(function () { CARDS.forEach(function (c) { c.classList.remove('is-active'); }); });
      this.relabel = function () {
        [].forEach.call(list.children, function (b, j) { var k = CARDS[j].id.replace('v-', ''), q = Q[k] || [kicker(CARDS[j]), kicker(CARDS[j])];
          var t = T(q[0], q[1]), f = finding(CARDS[j]);
          if (b.querySelector('b').textContent !== t) b.querySelector('b').textContent = t;
          if (b.querySelector('span').textContent !== f) b.querySelector('span').textContent = f; });
      };
      CARDS.forEach(function (c, j) { c.classList.toggle('is-active', j === 0); });
      [].forEach.call(list.children, function (b, j) { b.setAttribute('aria-pressed', String(j === 0)); });
    } }
  };

  function reset() {
    if (open) closeCard(true);
    undo.forEach(function (f) { f(); }); undo = [];
    for (var i = moved.length - 1; i >= 0; i--) { var m = moved[i]; m[1].insertBefore(m[0], m[2] && m[2].parentNode === m[1] ? m[2] : null); }
    moved = [];
    added.forEach(function (n) { n.remove(); }); added = [];
    root.removeAttribute('data-concept'); root.removeAttribute('data-marks'); root.removeAttribute('data-theme');
    concept = null;
  }
  function apply(k) {
    reset(); cur = k; concept = CONCEPTS[k] || CONCEPTS.base; concept.relabel = null;
    if (k !== 'base') { root.setAttribute('data-concept', k); root.setAttribute('data-theme', k === 'slides' ? 'dark' : 'light'); }
    if (concept.marks) root.setAttribute('data-marks', concept.marks);
    var t = document.getElementById('tab-ana'); if (t && t.getAttribute('aria-selected') !== 'true') t.click();
    concept.apply();
    window.scrollTo(0, 0);
    redraw();
    if (concept.relabel) concept.relabel();
  }

  // after every redraw of a chart: outline marks, refresh the concept's own labels
  var pend = null;
  var mo = new MutationObserver(function () { if (pend) return; pend = requestAnimationFrame(function () { pend = null; outline(); if (concept && concept.relabel) concept.relabel(); }); });
  CARDS.forEach(function (c) { mo.observe(c, { childList: true, subtree: true, characterData: true }); });
  ['lFr', 'lEn'].forEach(function (id) { var b = document.getElementById(id); if (b) b.addEventListener('click', function () { setTimeout(function () { if (concept && concept.relabel) concept.relabel(); }, 0); }); });

  window.FTO2_CONCEPT = apply;
})();
