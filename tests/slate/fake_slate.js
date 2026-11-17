// A stand-in for Slate, to try the pages' Slate set-ups on the laptop (tests/slate/make_pages.py puts it into a page).
// It does what Slate does for a page's code sandbox, as far as the page can tell:
//   - the sandbox state is the state box's JSON; a value "{{q_...}}" or "{{f_...}}" is replaced by that query's or function's result;
//   - a function is its text run as a function body, each {{name}} in it replaced by the JSON of that query or variable; it runs
//     again when a variable it reads changes, and its result goes to the state keys bound to it;
//   - an event's text runs the same way ({{w_<sandbox>.state.key}} reads the sandbox state, {{slEventValue}} is the value the
//     page fired the event with) and sets its variable.
// SlateFunctions gives the page watch (the value at once, then each change), getState, setState (an object merged into the
// state) and triggerEvent (a name and a value).
// A function that answers {error} or throws makes a page error, so that a snapshot taken on this page shows it.
// Setup: window.FAKE_SLATE_SETUP = {state, queries: {name: result}, functions: {name: text}, events: {name: {text, variable}},
// variables: {name: value}, delay: ms}.
// For the checks (tests/slate/check_state_keys.js): SlateFunctions._events() lists the events fired [{event, value}],
// _variable(name) reads a variable, _query(name, result) gives a query a new result, as when Slate runs it again (after an
// action's Submit), and _busy() says how many functions and events are still running.
(function () {
  var S = window.FAKE_SLATE_SETUP, delay = S.delay == null ? 80 : S.delay;
  var vars = JSON.parse(JSON.stringify(S.variables || {})), results = {}, state = {}, watchers = {}, busy = 0, runs = {}, fired = [];
  function has(o, k) { return Object.prototype.hasOwnProperty.call(o, k); }
  function bindingsOf(text) { var out = [], re = /\{\{\s*([\w.]+)\s*\}\}/g, m; while ((m = re.exec(text))) out.push(m[1]); return out; }
  function valueOf(name, extra) {
    if (extra && has(extra, name)) return extra[name];
    if (has(S.queries, name)) return S.queries[name];
    if (has(vars, name)) return vars[name];
    if (has(results, name)) return results[name];
    var w = name.match(/^w_\w+\.state\.(\w+)$/); if (w) return state[w[1]];
    return undefined;
  }
  function render(text, extra) {   // a text with its bindings replaced by their values, as JSON
    return text.replace(/\{\{\s*([\w.]+)\s*\}\}/g, function (_, name) { var v = valueOf(name, extra); return v === undefined ? 'null' : JSON.stringify(v); });
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
  function reads(name) { return Object.keys(S.functions).filter(function (f) { return bindingsOf(S.functions[f]).indexOf(name) >= 0; }); }
  // the state at the start: literal values, then the queries' results
  Object.keys(S.state).forEach(function (k) {
    var t = S.state[k], b = typeof t === 'string' ? t.match(/^\{\{\s*(\w+)\s*\}\}$/) : null;
    state[k] = b ? (has(S.queries, b[1]) ? S.queries[b[1]] : null) : t;
  });
  window.SlateFunctions = {
    watch: function (k, cb) { (watchers[k] = watchers[k] || []).push(cb); if (state[k] !== undefined) cb(state[k]); },   // the value at once, then each change
    getState: function () { return state; },
    setState: function (o) { Object.keys(o || {}).forEach(function (k) { if (o[k] !== state[k]) set(k, JSON.parse(JSON.stringify(o[k]))); }); },
    triggerEvent: function (ev, value) {
      var E = S.events[ev]; if (!E) { fail('no event ' + ev); return; }
      fired.push({ event: ev, value: value === undefined ? null : JSON.parse(JSON.stringify(value)) });
      busy++;
      setTimeout(function () {
        busy--;
        var v; try { v = new Function(render(E.text, { slEventValue: value === undefined ? null : value }))(); } catch (e) { fail('event ' + ev + ' threw: ' + (e && e.message)); return; }
        vars[E.variable] = v;
        reads(E.variable).forEach(run);
      }, Math.min(delay, 20));
    },
    _events: function () { return JSON.parse(JSON.stringify(fired)); },
    _variable: function (name) { return has(vars, name) ? JSON.parse(JSON.stringify(vars[name])) : undefined; },
    _query: function (name, result) {   // a query run again: its state keys and the functions reading it follow
      S.queries[name] = result;
      bound(name).forEach(function (k) { set(k, JSON.parse(JSON.stringify(result))); });
      reads(name).forEach(run);
    },
    _busy: function () { return busy; }
  };
  // the functions run once the queries are there (the page's own data arrives a little later, as in Slate)
  Object.keys(S.functions).forEach(run);
})();
