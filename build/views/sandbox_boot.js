// ================================================================ Slate glue of the code sandbox (way 2): model in, filters out
// In: the sandbox's state key "model", bound to the Slate function f_fto2_views (state.json). No double brace in this file:
// Slate would read it as a binding.
// Out: a change of filter writes the state key "filters", then fires the sandbox event "fto2Filters"; the Slate event
// w_fto2_views.fto2Filters sets the variable v_fto2_filters, which the function reads: a new model comes back in.
(function () {
  var MSG = {
    wait: 'Calcul des vues dans Slate… / Computing the views in Slate…',
    noapi: 'État Slate introuvable : ce JavaScript doit tourner dans un code sandbox Slate dont l’état lie "model" à la fonction f_fto2_views (voir state.json). / No Slate state: this JavaScript must run in a Slate code sandbox whose state binds "model" to the function f_fto2_views (see state.json).',
    slow: 'Toujours sans modèle après 30 s : vérifiez la fonction f_fto2_views (elle doit s’exécuter sans erreur) et les requêtes q_fto2_nc et q_fto2_def. / Still no model after 30 s: check that the function f_fto2_views runs without error, and the queries q_fto2_nc and q_fto2_def.',
    bad: 'Le modèle reçu n’a pas la forme attendue (meta, syn, det) : l’état "model" doit être lié à f_fto2_views. / The model received has not the expected shape (meta, syn, det): the state key "model" must be bound to f_fto2_views.'
  };
  function showError(msg) {
    var e = document.getElementById('fto2-err');
    if (e) { e.hidden = false; e.textContent = 'Les vues n\'ont pas pu s\'afficher / The views could not load: ' + msg; }
    var w = document.getElementById('fto2-wait'); if (w) w.hidden = true;
    if (window.console) console.error('[FTO2 views]', msg);
  }
  function status(msg, warn) {
    var e = document.getElementById('fto2-wait'); if (!e) return;
    e.hidden = !msg; e.textContent = msg || ''; e.className = 'fto2-wait' + (warn ? ' warn' : '');
  }
  window.addEventListener('error', function (ev) { showError((ev && ev.message) || 'unknown error'); });
  function parse(v) { if (typeof v !== 'string') return v; var s = v.trim(); if (!s) return null; try { return JSON.parse(s); } catch (e) { return null; } }

  function boot() {
    var api = window.SlateFunctions, root = document.getElementById('fto2-root');
    if (!root) { showError('HTML part missing (no #fto2-root): paste fto2_views_sandbox.html into the HTML tab.'); return; }
    if (!api || !api.watch) { showError(MSG.noapi); return; }
    if (!api.setState || !api.triggerEvent) { showError('SlateFunctions.setState / triggerEvent missing: the filters cannot reach Slate.'); return; }
    var sent = null, fired = false, got = false, V = FTO2ViewsRender.create(root, send);
    // setState: an object merged into the state, or (key, value); both forms are accepted, the first one Slate takes is kept
    function write(F) {
      if (api.setState.length >= 2) { api.setState('filters', F); return; }
      var st = {}; try { st = (api.getState && api.getState()) || {}; } catch (e) {}
      var nx = {}; Object.keys(st).forEach(function (k) { nx[k] = st[k]; }); nx.filters = F;
      api.setState(nx);
    }
    function fire() { if (fired) return; fired = true; api.triggerEvent('fto2Filters'); }
    function send(F) {
      sent = JSON.stringify(F); fired = false;
      try { write(F); } catch (e) { showError('SlateFunctions.setState: ' + (e && e.message || e)); return; }
      setTimeout(fire, 400);   // the event reads the state: fired once the state shows the new filters (watch below), at the latest after 0.4 s
    }
    api.watch('filters', function (v) { if (sent && JSON.stringify(parse(v)) === sent) setTimeout(fire, 0); }, true);
    function take(v) {
      var m = parse(v);
      if (!m) { if (!got) status(MSG.wait); return; }
      if (m.error && !got) { showError(m.error); return; }   // later errors show in the filter bar, over the last good model
      if (!m.error && !(m.meta && m.syn && m.det)) { showError(MSG.bad); return; }
      if (!m.error) { got = true; status(''); var e = document.getElementById('fto2-err'); if (e) e.hidden = true; }
      V.setModel(m);
    }
    api.watch('model', take, true);
    if (!got && api.getState) { try { var st = api.getState(); if (st && st.model) take(st.model); } catch (e) {} }   // a model already there when the page loads
    setTimeout(function () { if (!got) status(MSG.slow, true); }, 30000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
