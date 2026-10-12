// Cost of non-quality: the same calculation as cnq_core.py, in the browser, so times can be changed live.
// The pipeline (cnq_params.py + cnq_core.py) stays the reference; tests/test_dashboard.js checks both agree.

// NC row layout in DATA.nc:     [number, month, programme, product, rule, onAec, liabilityGroup, final, customer, whereFound, status]
// line layout in DATA.lines:    [ncIndex, classIndex, qty, text]
var NC = { num: 0, month: 1, prog: 2, prod: 3, rule: 4, aec: 5, group: 6, fin: 7, cust: 8, where: 9, status: 10 };

function classMinutes(P) {
  // a derived class is always factor x its base class ("wrong reference = 2 x missing")
  return P.classes.map(function (c) { return c.of == null ? c.min : P.classes[c.of].min * c.factor; });
}

// amounts: optional {ncNumber: realAmount} for customer returns; a real amount replaces the estimate
function computeAll(DATA, P, amounts) {
  amounts = amounts || {};
  var mins = classMinutes(P);
  var n = DATA.nc.length;
  var lineMin = new Array(n).fill(0), lineMat = new Array(n).fill(0), lineCnt = new Array(n).fill(0);
  DATA.lines.forEach(function (l) {
    lineMin[l[0]] += mins[l[1]] * l[2];
    lineMat[l[0]] += P.classes[l[1]].mat * l[2];
    lineCnt[l[0]] += l[2];
  });
  var rows = DATA.nc.map(function (r, i) {
    var known = !!DATA.rules[r[NC.rule]];
    var f = DATA.rules[r[NC.rule]] || { alert: 0, write: 0, support: 0, work: 0, recheck: 0, eng: 0, part: 0 };
    var handsRaw = lineCnt[i] === 0 ? P.noDefect : lineMin[i];
    var s = {
      alert: f.alert * P.alert,
      writing: f.write * (r[NC.fin] ? P.writeFinal : P.write),
      support: f.support * P.support,
      setup: f.work * Math.max(P.setup, P.floor - handsRaw),
      hands: f.work * handsRaw,
      recheck: f.recheck * P.recheck
    };
    var engH = f.eng, eng = engH * P.rateEng, material = f.work * lineMat[i];
    var minutes3 = s.alert + s.writing + s.support + s.setup + s.hands + s.recheck;
    var minutes2 = f.alert * P.alert + f.write * P.writeGlobal + f.support * P.support + f.work * P.workGlobal + f.recheck * P.recheck;
    var model = minutes3 / 60 * P.rate + eng + material;
    var isReturn = known && r[NC.cust] === 1;
    var real = isReturn && amounts[r[NC.num]] != null && isFinite(amounts[r[NC.num]]) ? +amounts[r[NC.num]] : null;
    var l3 = real != null ? real : model + (isReturn ? (P.crExtra || 0) : 0);
    return {
      i: i, f: f, steps: s, engH: engH, eng: eng, material: material, lines: lineCnt[i], lineMin: lineMin[i],
      minutes3: minutes3, minutes2: minutes2, model: model, real: real, adjust: l3 - model, isReturn: isReturn,
      l3: l3,
      l2: minutes2 / 60 * P.rate + eng + material,
      l1: P.airbus[r[NC.rule]] || 0
    };
  });
  return { rows: rows, classMin: mins };
}

function sumBy(DATA, rows, keyFn, filterFn) {
  var out = {};
  rows.forEach(function (x) {
    var r = DATA.nc[x.i];
    if (filterFn && !filterFn(r, x)) return;
    var k = keyFn(r, x);
    var o = out[k] || (out[k] = { n: 0, l1: 0, l2: 0, l3: 0, model: 0 });
    o.n += 1; o.l1 += x.l1; o.l2 += x.l2; o.l3 += x.l3; o.model += x.model;
  });
  return out;
}

if (typeof module !== "undefined") { module.exports = { computeAll: computeAll, sumBy: sumBy, classMinutes: classMinutes, NC: NC }; }
