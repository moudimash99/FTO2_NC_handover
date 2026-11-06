// A stand-in for Slate, to try the dashboard's Slate set-ups on the laptop (tests/slate/make_pages.py puts it into a page).
// It does what Slate does for the dashboard's code sandbox, as far as the page can tell:
//   - the sandbox state is the state box's JSON; a value "{{q_...}}" or "{{f_...}}" is replaced by that query's or function's result;
//   - a function is its text run as a function body, each {{name}} in it replaced by the JSON of that query or variable; it runs
//     again when a variable it reads changes, and its result goes to the state keys bound to it;
//   - an event's text runs the same way ({{w_fto2_dashboard.state.key}} reads the sandbox state) and sets its variable.
// SlateFunctions gives the page watch (the value at once, then each change), getState, setState (an object merged into the
// state) and triggerEvent.
// A function that answers {error} or throws makes a page error, so that a snapshot taken on this page shows it.
// Setup: window.FAKE_SLATE_SETUP = {state, queries: {name: result}, functions: {name: text}, events: {name: {text, variable}},
// variables: {name: value}, delay: ms}.
(function () {
  var S = window.FAKE_SLATE_SETUP, delay = S.delay == null ? 80 : S.delay;
  var vars = JSON.parse(JSON.stringify(S.variables || {})), results = {}, state = {}, watchers = {}, busy = 0, runs = {};
  function bindingsOf(text) { var out = [], re = /\{\{\s*([\w.]+)\s*\}\}/g, m; while ((m = re.exec(text))) out.push(m[1]); return out; }
  function valueOf(name) {
    if (Object.prototype.hasOwnProperty.call(S.queries, name)) return S.queries[name];
    if (Object.prototype.hasOwnProperty.call(vars, name)) return vars[name];
    if (Object.prototype.hasOwnProperty.call(results, name)) return results[name];
    var w = name.match(/^w_fto2_dashboard\.state\.(\w+)$/); if (w) return state[w[1]];
    return undefined;
  }
  function render(text) {   // a text with its bindings replaced by their values, as JSON
    return text.replace(/\{\{\s*([\w.]+)\s*\}\}/g, function (_, name) { var v = valueOf(name); return v === undefined ? 'null' : JSON.stringify(v); });
  }
  function fail(msg) { setTimeout(function () { throw new Error('[fake Slate] ' + msg); }, 0); }
  function set(key, v) { state[key] = v; (watchers[key] || []).forEach(function (cb) { cb(v); }); }
  function bound(name) { return Object.keys(S.state).filter(function (k) { return S.state[k] === '{{' + name + '}}'; }); }
  function run(name) {   // a function, after Slate's short delay; a newer run of the same function replaces a waiting one
    busy++; var id = (runs[name] || 0) + 1; runs[name] = id;
    setTimeout(function () {
      busy--; if (runs[name] !== id) return;
      var v;
      try { v = new Function(render(S.functions[name]))(); } catch (e) { fail(name + ' threw: ' + (e && e.message)); return; }
      if (v && v.error) fail(name + ' answered an error: ' + v.error);
      if (v !== undefined) v = JSON.parse(JSON.stringify(v));   // Slate hands values over as JSON (a gap in a list becomes null)
      results[name] = v;
      bound(name).forEach(function (k) { set(k, v); });
    }, delay);
  }
  // the state at the start: literal values, then the queries' results
  Object.keys(S.state).forEach(function (k) {
    var t = S.state[k], b = typeof t === 'string' ? t.match(/^\{\{\s*(\w+)\s*\}\}$/) : null;
    state[k] = b ? (Object.prototype.hasOwnProperty.call(S.queries, b[1]) ? S.queries[b[1]] : null) : t;
  });
  window.SlateFunctions = {
    watch: function (k, cb) { (watchers[k] = watchers[k] || []).push(cb); if (state[k] !== undefined) cb(state[k]); },   // the value at once, then each change
    getState: function () { return state; },
    setState: function (o) { Object.keys(o || {}).forEach(function (k) { if (o[k] !== state[k]) set(k, JSON.parse(JSON.stringify(o[k]))); }); },
    triggerEvent: function (ev) {
      var E = S.events[ev]; if (!E) { fail('no event ' + ev); return; }
      busy++;
      setTimeout(function () {
        busy--;
        var v; try { v = new Function(render(E.text))(); } catch (e) { fail('event ' + ev + ' threw: ' + (e && e.message)); return; }
        vars[E.variable] = v;
        Object.keys(S.functions).forEach(function (f) { if (bindingsOf(S.functions[f]).indexOf(E.variable) >= 0) run(f); });
      }, Math.min(delay, 20));
    },
    _busy: function () { return busy; }
  };
  // the functions run once the queries are there (the page's own data arrives a little later, as in Slate)
  Object.keys(S.functions).forEach(run);
})();
