# -*- coding: utf-8 -*-
"""
Run every Slate query on the sample outputs (in SQLite) and check that the charts add up
to the totals computed by the pipeline.   python tests/test_queries.py
"""
import json, os, re, sqlite3
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
con = sqlite3.connect(":memory:")
pd.read_csv(os.path.join(ROOT, "sample_output", "fto2_nc_cnq.csv"), low_memory=False).to_sql("fto2_nc_cnq", con, index=False)
pd.read_csv(os.path.join(ROOT, "sample_output", "fto2_defects_cnq.csv"), low_memory=False).to_sql("fto2_defects_cnq", con, index=False)
exp = json.load(open(os.path.join(HERE, "expected_totals.json")))

sql = open(os.path.join(ROOT, "slate", "slate_queries.sql"), encoding="utf-8").read()
blocks = re.split(r"^--@ ", sql, flags=re.M)[1:]
res = {}
for b in blocks:
    name = b.split()[0]
    body = "\n".join(l for l in b.split("\n")[1:] if not l.strip().startswith("--")).strip().rstrip(";")
    res[name] = pd.read_sql_query(body, con)
    print("%-32s %3d rows" % (name, len(res[name])))

near = lambda a, b, tol=10: abs(a - b) <= tol     # charts round each bar to the euro
assert near(res["q01_kpis"].cost_aec[0], exp["cost_aec"], 1)
assert res["q01_kpis"].nc_on_aec[0] == exp["nc_on_aec"]
for q, col in [("q02_cost_by_component", "cost"), ("q03_cost_by_month", "cost_total"), ("q04_cost_by_week", "cost_total"),
               ("q05_cost_by_where_found", "cost_total"), ("q06_cost_by_programme", "cost_total"), ("q07_cost_by_decision", "cost_total")]:
    assert near(res[q][col].sum(), exp["cost_aec"], 30), (q, res[q][col].sum())
assert near(res["q08_aside_by_liability"].cost_total.sum(), exp["cost_all"])
lv = res["q00_three_levels"].cost.tolist()
assert near(lv[0], exp["level1_airbus_aec"], 1) and near(lv[1], exp["level2_global_aec"], 1) and near(lv[2], exp["level3_detailed_aec"], 1)
assert len(res["q09b_customer_returns_list"]) == res["q09_customer_returns_by_month"].nc_count.sum()
for q in ("q10_pareto_by_group", "q13_pareto_by_category"):
    assert near(res[q].cost_direct.sum(), exp["cost_direct_lines"], 20), q
    assert res[q].defect_lines.sum() == exp["defect_lines_costed"], q
print("\nAll queries run and reconcile with the pipeline totals.")
print(res["q01_kpis"].T.to_string(header=False))
