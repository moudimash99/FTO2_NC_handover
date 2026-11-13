"""The Skywise run in another year: is the year really one line of the settings?

    python3 -I tests/next_year_rehearsal.py [folder]

The laptop's data of 2026 is moved 53 weeks later (371 days: the same weekdays and the same week numbers), into 2027: the
NCs, the aléas, the production plan, the shutdown calendar, the cable requests, the MFT actions. The NCs of 2025 are moved one
year later, into 2026, and the production plan keeps the aircraft of 2026. The settings are a copy of config/ with one line
changed: annee = 2027. Then the same run as tests/notebook_rehearsal.py, and these checks:

  - each NC comes out as in the laptop build of 2026 (line, scope, product, defect lines, cost...), created 371 days later;
  - the production volume is the plan's, in the months and the weeks of 2027;
  - the comparison year is 2026, with its deliveries counted in the production plan.

With a folder: also writes there the Skywise page fed with these tables (FTO2_NC_Dashboard.html), for
tests/next_year_page.js, which checks the page itself (the years it shows, its totals, the bell).

Exits 1 if a check fails.
"""
import json
import os
import shutil
import sys
import tempfile

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tests.shift import shift_dates  # noqa: E402

DATA_YEAR, YEAR, DAYS = 2026, 2027, 371
PLAN, CALENDAR, CABLES, ACTIONS = "1_plan_msn.csv", "1_calendrier_production.csv", "1_demandes_cables.csv", "1_actions_mft.csv"


def read(path):
    return pd.read_csv(path, sep=";", dtype=str, keep_default_na=False, encoding="utf-8-sig")


def write(table, path):
    table.to_csv(path, sep=";", index=False, encoding="utf-8")


def settings(folder):
    """A copy of config/ for the year 2027: the year's line, and the year's tables with their dates moved."""
    shutil.copytree(os.path.join(ROOT, "config"), folder)
    p = read(os.path.join(folder, "2_parametres.csv"))
    assert (p.nom == "annee").sum() == 1, "config/2_parametres.csv has no line 'annee'"
    p.loc[p.nom == "annee", "valeur"] = str(YEAR)
    write(p, os.path.join(folder, "2_parametres.csv"))
    for name in (CALENDAR, ACTIONS):
        t = read(os.path.join(folder, name))
        write(shift_dates(t, DAYS, [c for c in t.columns if c in ("debut", "fin", "benefices_attendus") or c.startswith("debut_")]), os.path.join(folder, name))
    c = shift_dates(read(os.path.join(folder, CABLES)), DAYS, ["date"])
    c["mois"] = c["date"].str[:7]
    write(c, os.path.join(folder, CABLES))
    # the production plan: every aircraft 53 weeks later, and the aircraft finished before 2027 as they are (the plan keeps
    # its older rows), under another MSN so that they stay apart
    plan = read(os.path.join(folder, PLAN))
    dated = [c for c in plan.columns if c.startswith(("prevu_", "reel_"))]
    later = shift_dates(plan, DAYS, dated + ["export_du"])
    older = plan[plan[dated].max(axis=1) < "%d-01-01" % YEAR].copy()
    older["msn"] = "P" + older["msn"]
    write(pd.concat([later, older], ignore_index=True), os.path.join(folder, PLAN))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else None
    work = tempfile.mkdtemp(prefix="fto2_next_year_")
    os.environ["FTO2_CONFIG"] = os.path.join(work, "config")   # set before the backend is loaded: it reads its settings once
    try:
        settings(os.environ["FTO2_CONFIG"])
        from tests import notebook_rehearsal as R
        from fto2 import config
        assert config.year() == YEAR and config.comparison_year() == YEAR - 1
        nc_t, def_t, dis_t = R.run(days=DAYS, days_before=365, data_year=DATA_YEAR)
        written = R.Dataset.written
        bad = check(nc_t, def_t, dis_t, written)
        if out:
            R.write_page(out, nc_t, def_t, dis_t)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("OK: the run works in %d as it does in %d" % (YEAR, DATA_YEAR) if not bad else "DIFFERENCES above")
    sys.exit(1 if bad else 0)


def check(nc_t, def_t, dis_t, written):
    bad = []

    def expect(ok, text):
        print(("  ok   " if ok else "  FAIL ") + text)
        if not ok:
            bad.append(text)

    lap = pd.read_csv(os.path.join(ROOT, "05_outputs", "fto2_dash_nc.csv"), dtype=str, keep_default_na=False).set_index("nc")
    got = nc_t.astype(str).replace({"nan": "", "None": ""}).set_index("nc")
    both = sorted(set(got.index) & set(lap.index))
    print("\n%d: %d NCs written; laptop build of %d: %d; in both: %d" % (YEAR, len(got), DATA_YEAR, len(lap), len(both)))
    expect(len(both) > 1000, "the NCs of the year are there (%d)" % len(both))
    moved = (pd.to_datetime(got.loc[both, "created"].str[:10]) - pd.to_datetime(lap.loc[both, "created"].str[:10])).dt.days
    expect(bool((moved == DAYS).all()), "every NC is created %d days later" % DAYS)
    after = got.loc[both, "created"].str[:4]
    expect(set(after) <= {str(YEAR), str(YEAR - 1)} and (after == str(YEAR)).mean() > 0.9, "the NCs are of %d (a few of the lists: late %d)" % (YEAR, YEAR - 1))
    for c in ["line", "plant", "scope", "phase", "product", "type_nc", "liability", "on_aec", "defect_lines", "cost_total", "cost_work", "cost_part",
              "min_setup", "min_hands_on", "source", "rework_orders", "order_state", "aleas"]:
        a, b = got.loc[both, c], lap.loc[both, c]
        num = pd.to_numeric(a, errors="coerce"), pd.to_numeric(b, errors="coerce")
        diff = ~((a == b) | ((num[0] - num[1]).abs() < 0.01))
        expect(not diff.sum(), "%s: the same for every NC" % c + ("" if not diff.sum() else " (%d differ, e.g. %s)" % (diff.sum(), list(zip(a[diff].index[:3], a[diff][:3], b[diff][:3])))))
    lap_def = pd.read_csv(os.path.join(ROOT, "05_outputs", "fto2_dash_defects.csv"), dtype=str, keep_default_na=False)
    expect(int(def_t.nc.astype(str).isin(both).sum()) == int(lap_def.nc.isin(both).sum()), "the same defect lines on those NCs")
    lap_dis = pd.read_csv(os.path.join(ROOT, "05_outputs", "fto2_dash_disruptions.csv"), dtype=str, keep_default_na=False)
    expect(abs(len(dis_t) - len(lap_dis)) <= 3, "as many aléas with no NC (%d; laptop %d, which holds a few more NCs)" % (len(dis_t), len(lap_dis)))

    def blocks(t):
        t = t.astype({"morceau": int})
        return {p: json.loads("".join(g.sort_values("morceau").texte)) for p, g in t.groupby("partie")}
    ref = blocks(written["fto2_dash_ref"])["dashboard"]
    was = blocks(pd.read_csv(os.path.join(ROOT, "05_outputs", "fto2_dash_ref.csv"), dtype={"texte": str}, keep_default_na=False))["dashboard"]
    s, e, y = ref["settings"], ref["eqmsn"], ref["y25"]
    expect(ref["from"] == "%d-01-01" % YEAR and s["annee"] == YEAR and s["annee_ref"] == YEAR - 1, "the pages get the year %d and its comparison year %d" % (YEAR, YEAR - 1))
    expect(e["months"] == ["%d-%02d" % (YEAR, m) for m in range(1, 13)], "the production volume is by month of %d" % YEAR)
    tot = lambda v: sum(sum(x) for x in v.values())
    now, then = tot(e["wd"]), tot(was["eqmsn"]["wd"])
    expect(abs(now / then - 1) < 0.03, "the year's volume is the plan's: %.1f MSN (%.1f in %d; public holidays fall on other days)" % (now, then, DATA_YEAR))
    wk, wk0 = e["wdw"]["line"], was["eqmsn"]["wdw"]["line"]
    expect(all(abs(sum(wk[l]) / sum(wk0[l]) - 1) < 0.03 for l in wk0), "and week by week, for the alarms: " + ", ".join("%s %.1f" % (l, sum(wk[l])) for l in sorted(wk)))
    expect(e["forecastFrom"].startswith(str(YEAR)) and e["asof"].startswith(str(YEAR)), "the plan's date and its forecast months are of %d (%s, from %s)" % (YEAR, e["asof"], e["forecastFrom"]))
    months = {r[0][:4] for r in y["rows"]}
    expect(months == {str(YEAR - 1)}, "the comparison year's NCs are those of %d (%d NCs)" % (YEAR - 1, sum(r[5] for r in y["rows"])))
    delivered = tot(y["prod"] or {})
    expect(y.get("delivered") == "plan" and abs(delivered / then - 1) < 0.10, "its deliveries are counted in the production plan: %d products (%.1f MSN built that year)" % (delivered, then))
    return bad


if __name__ == "__main__":
    main()
