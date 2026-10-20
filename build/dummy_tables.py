# -*- coding: utf-8 -*-
"""
Fictitious FTO2 NC data for the Skywise migration checks (levels 1 and 2), in the dashboard's two tables.

    python3 -I build/dummy_tables.py

The data is written once, as three Postgres queries (level 2: Slate runs them, no dataset needed). The same queries, run on a
local Postgres, give the three CSV snapshots that level 1 writes into the JavaScript, so both levels show the same data.
No real NC: numbers 900000001..., MSNs, FINs (X..VT) and texts are made up; only the category names, the cost rules and
the code sheet are the real ones, so every chart and the "explain the calculation" part work as with real data.

Writes:
    03_reports/skywise/level2_dummy_queries/q_fto2_nc_dummy.sql, q_fto2_def_dummy.sql, q_fto2_dis_dummy.sql
    build/dummy/fto2_dash_nc_dummy.csv, fto2_dash_defects_dummy.csv, fto2_dash_disruptions_dummy.csv   (needs a local Postgres; skipped without one)
"""
import os
import shutil
import subprocess
import sys
import tempfile

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "02_dashboard_pack", "skywise_nc_dashboard_v48", "1_pipeline"))
sys.path.insert(0, os.path.join(ROOT, "cnq_handoever"))
sys.path.insert(0, os.path.join(ROOT, "build"))
import fto2_logic as L                    # noqa: E402
import nc_defect_parser as PARSER         # noqa: E402
import cnq.cnq_params as P                # noqa: E402
from fto2_core import NC_COLUMNS, DEF_COLUMNS, DIS_COLUMNS   # noqa: E402

SQL_DIR = os.path.join(ROOT, "03_reports", "skywise", "level2_dummy_queries")
CSV_DIR = os.path.join(ROOT, "build", "dummy")


def H(key, salt, mod):
    """A fixed pseudo-random integer 0..mod-1 from a key (Postgres: md5, no random(), so every run gives the same data)."""
    return "(('x' || substr(md5('%s:' || (%s)::text), 1, 7))::bit(28)::int %% %d)" % (salt, key, mod)


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


def taxonomy():
    """Sub-categories with their category, root cause, minor flag, minutes and material (CNQ model), official code, and how
    often each appears and how often it is a cable defect in the current data (weights for the fictitious lines)."""
    ref = pd.read_csv(os.path.join(ROOT, "04_reference", "reference_souscodes_pareto.csv"), encoding="utf-8-sig")
    ref = ref[~ref.sous_code.astype(str).str.startswith("(")]
    first = ref.groupby("sous_categorie").sous_code.first()
    fallback = {"Câble à refaire (ligne)": "Q06-001", "Composant HS": "Q11 (composant)", "Composant – cause non écrite": "Q11 (composant)",
                "Non classé": "Non codé"}
    real = pd.read_csv(os.path.join(ROOT, "05_outputs", "fto2_dash_defects.csv"), dtype=str, keep_default_na=False)
    freq = real["sub"].value_counts()
    cab = real.assign(c=real.cable.astype(int)).groupby("sub").c.mean()
    rows = []
    for sub, v in PARSER.SOUS_CATEGORIES.items():
        n = int(freq.get(sub, 0))
        if n < 3:
            continue
        t = P.DEFECT_TIMES.get(sub, (P.MIN_DEFAULT_DEFECT, 0.0))
        rows.append([sub, v[0], L.RCA_NAMES.get(v[1], "Non classé"), int(bool(PARSER.est_mineur(sub))), float(t[0]), float(t[1]),
                     fallback.get(sub) or first.get(sub) or "Non codé", int(round(100 * float(cab.get(sub, 0)))), n])
    tot = sum(r[-1] for r in rows)
    lo = 0
    for r in rows:   # the weight becomes a range of 0..9999
        hi = lo + max(1, round(r[-1] / tot * 10000)) - 1
        r[-1:] = [lo, hi]
        lo = hi + 1
    rows[-1][-1] = 9999
    return rows


def generator():
    """The shared part of both queries: every CTE, ending with n2 (NCs) and d2 (defect lines)."""
    tax = ",\n    ".join("(%s, %s, %s, %d, %s, %s, %s, %d, %d, %d)" % (q(r[0]), q(r[1]), q(r[2]), r[3], r[4], r[5], q(r[6]), r[7], r[8], r[9]) for r in taxonomy())
    rules = ",\n    ".join("(%s, %d, %d, %d, %d, %d, %s, %s, %s)" % (q(k), v[0], v[1], v[2], v[3], v[4], v[5], q(v[7]), P.AIRBUS_STANDARD.get(k, 0)) for k, v in P.RULES.items())
    conn = ", ".join(q(c) for c in P.CONNECTION_CLASSES)
    internal = ", ".join(q(c.upper()) for c in P.INTERNAL_TYPES)
    no_alert = ", ".join(q(c.upper()) for c in P.NO_ALERT_TYPES)
    stations = ["Poste câblage A", "Poste câblage B", "Sous-ensemble harnais", "Intégration", "Retouche ligne", "Finition"]
    st_case = " ".join("WHEN %s = %d THEN %s" % (H("i", "st", len(stations)), k, q(s)) for k, s in enumerate(stations))
    return """WITH
-- Fictitious FTO2 NC data, columns of the datasets fto2_dash_nc and fto2_dash_defects. No real NC: numbers 900000001...,
-- MSNs, FINs (X..VT) and texts are made up; categories, cost rules and codes are the real ones. Same data at every run.
tax (sub, cat, rca, minor, minutes, material, code, cable_pct, lo, hi) AS (VALUES
    %(tax)s
),
rules (rule, alert, write, support, work, recheck, eng_hours, label, airbus) AS (VALUES
    %(rules)s
),
days AS (   -- working days; fewer NCs in July and August, almost none during the August shutdown
    SELECT g::date AS day, row_number() OVER (ORDER BY g) AS di
    FROM generate_series(date '2026-01-05', date '2026-09-25', interval '1 day') AS t(g)
    WHERE extract(isodow FROM g) < 6
),
counts AS (
    SELECT day, CASE WHEN day BETWEEN date '2026-08-03' AND date '2026-08-21' THEN %(h_sd)s
                     WHEN extract(month FROM day) IN (7, 8) THEN 1 + %(h_su)s
                     ELSE 2 + %(h_dd)s END AS k
    FROM days
),
base AS (
    SELECT row_number() OVER (ORDER BY c.day, s.j) AS i, c.day
    FROM counts c CROSS JOIN LATERAL generate_series(1, c.k) AS s(j)
),
n0 AS (   -- one row per NC: line, perimeter, type, decision
    SELECT i, day, (900000000 + i)::text AS nc,
        CASE WHEN %(h_ln)s < 46 THEN 'A350' WHEN %(h_ln)s < 84 THEN 'A330' WHEN %(h_ln)s < 93 THEN 'A400M' ELSE 'A320' END AS line,
        CASE WHEN %(h_ps)s < 74 THEN 'FTO2' WHEN %(h_ps)s < 81 THEN 'Retour client' WHEN %(h_ps)s < 92 THEN 'Supprimée'
             WHEN %(h_ps)s < 97 THEN 'Fournisseur' ELSE 'Hors périmètre' END AS plant_scope,
        %(h_ty)s AS u_ty, %(h_ru)s AS u_ru, %(h_ph)s AS u_ph, %(h_nl)s AS u_nl, %(h_nl2)s AS u_nl2, %(h_pr)s AS u_pr, %(h_hr)s AS u_hr,
        %(h_op)s AS u_op, %(h_ld)s AS u_ld, %(h_ld2)s AS u_ld2, %(h_so)s AS u_so, %(h_sd2)s AS u_sd, %(h_sg)s AS u_sg, %(h_sc)s AS u_sc
    FROM base
),
n1 AS (
    SELECT n0.*,
        CASE plant_scope WHEN 'Retour client' THEN 'client' WHEN 'Fournisseur' THEN 'autre' WHEN 'Hors périmètre' THEN 'autre' ELSE 'serie' END AS scope,
        CASE plant_scope WHEN 'Retour client' THEN 'FFF1' WHEN 'Fournisseur' THEN 'FNZ1' WHEN 'Hors périmètre' THEN 'TOF' ELSE 'FTO2' END AS plant,
        CASE WHEN plant_scope IN ('FTO2', 'Retour client', 'Supprimée') THEN 1 ELSE 0 END AS on_aec,
        CASE WHEN plant_scope = 'Retour client' THEN 'NC Retour client' WHEN plant_scope = 'Fournisseur' THEN 'FOURNISSEUR'
             WHEN u_ty < 30 THEN 'CABLES' WHEN u_ty < 57 THEN 'TEST' WHEN u_ty < 75 THEN 'INTERNE' WHEN u_ty < 89 THEN 'CONTROLE FINAL'
             WHEN u_ty < 94 THEN 'NC Interne' WHEN u_ty < 97 THEN 'CASSE INTERNE' WHEN u_ty < 99 THEN 'DAMAGES' ELSE 'DEMANDE DE DQN' END AS type_nc,
        CASE WHEN u_ph < 90 THEN 'SERIE' WHEN u_ph < 97 THEN 'REC' ELSE 'FTI' END AS phase,
        CASE WHEN u_nl < 8 THEN 0 WHEN u_nl < 72 THEN 1 WHEN u_nl < 82 THEN 2 WHEN u_nl < 88 THEN 3 WHEN u_nl < 92 THEN 4 + u_nl2 %% 2
             WHEN u_nl < 96 THEN 6 + u_nl2 %% 4 ELSE 10 + u_nl2 %% 5 END AS k
    FROM n0
),
n1b AS (
    SELECT n1.*,
        CASE WHEN plant_scope = 'Supprimée' THEN 'DELETED' WHEN type_nc = 'DEMANDE DE DQN' THEN 'DQN'
             WHEN u_ru < 78 THEN 'RWK' WHEN u_ru < 88 THEN 'REJ_RW' WHEN u_ru < 94 THEN 'REJ' WHEN u_ru < 98 THEN 'EXC' WHEN u_ru < 99 THEN 'NDC' ELSE 'SCR' END AS rule,
        CASE line WHEN 'A350' THEN 700 + (row_number() OVER (PARTITION BY line ORDER BY i) - 1) / 6
                  WHEN 'A330' THEN 2100 + (row_number() OVER (PARTITION BY line ORDER BY i) - 1) / 5
                  WHEN 'A400M' THEN 150 + (row_number() OVER (PARTITION BY line ORDER BY i) - 1) / 4
                  ELSE 13000 + (row_number() OVER (PARTITION BY line ORDER BY i) - 1) / 3 END AS msn_n
    FROM n1
),
d0 AS (   -- one row per defect line
    SELECT n.i, n.nc, s.seq, n.scope, n.type_nc, n.line,
        %(h_sb)s AS u_sb, %(h_cb)s AS u_cb, %(h_fn)s AS u_fn, %(h_fn2)s AS u_fn2, %(h_fe)s AS u_fe,
        %(h_qt)s AS u_qt, %(h_lb)s AS u_lb, %(h_cf)s AS u_cf, %(h_dt)s AS u_dt
    FROM n1b n CROSS JOIN LATERAL generate_series(1, n.k) AS s(seq)
),
d1 AS (
    SELECT d0.*, t.sub, t.cat, t.rca, t.minor, t.minutes, t.material, t.code,
        CASE WHEN u_cb < t.cable_pct THEN 1 ELSE 0 END AS cable,
        CASE WHEN u_qt < 98 THEN 1 ELSE 2 END AS qty,
        CASE WHEN u_fe < 22 THEN '' ELSE 'X' || lpad(least(u_fn %% 40, u_fn2 %% 40)::text, 2, '0') || 'VT' END AS fin,
        CASE WHEN t.sub IN (%(conn)s) THEN 1 ELSE 0 END AS is_conn
    FROM d0 JOIN tax t ON d0.u_sb BETWEEN t.lo AND t.hi
),
d2 AS (   -- minutes of each line: the first connection error of an NC at its class time, each following one %(cnext)s min
    SELECT d1.*,
        CASE WHEN is_conn = 1 AND sum(is_conn * qty) OVER (PARTITION BY i ORDER BY seq) - is_conn * qty >= 1 THEN %(cnext)s * qty
             WHEN is_conn = 1 THEN minutes + %(cnext)s * (qty - 1)
             ELSE minutes * qty END AS line_min,
        material * qty AS line_mat,
        CASE WHEN scope = 'client' THEN (ARRAY['During installation', 'During PNE inspection', 'During the unpacking', 'During ground test', 'During inspection'])[1 + u_dt %% 5] ELSE '' END AS cr_detection
    FROM d1
),
agg AS (
    SELECT i, sum(line_min) AS mins, sum(line_mat) AS mat, max(cable) AS cable, count(*) AS lines
    FROM d2 GROUP BY i
),
firsts AS (
    SELECT i, sub AS first_sub, cr_detection AS first_det FROM d2 WHERE seq = 1
),
n2 AS (   -- the NC with the CNQ model's minutes and costs
    SELECT n.*, r.label AS decision_label, r.airbus, r.eng_hours,
        coalesce(a.lines, 0) AS lines, coalesce(a.cable, 0) AS cable, f.first_sub, f.first_det,
        r.alert * CASE WHEN upper(n.type_nc) IN (%(no_alert)s) AND n.scope <> 'client' THEN 0 ELSE %(alert)s END AS m_alert,
        r.write * CASE WHEN n.type_nc = 'CONTROLE FINAL' THEN %(wfinal)s ELSE %(write)s END AS m_write,
        r.support * %(support)s AS m_support,
        r.recheck * %(recheck)s AS m_recheck,
        CASE WHEN upper(n.type_nc) IN (%(internal)s) THEN %(factor)s ELSE 1 END AS factor,
        CASE WHEN coalesce(a.lines, 0) = 0 THEN %(noline)s ELSE a.mins END AS hands,
        CASE WHEN r.work = 1 THEN coalesce(a.mat, 0) ELSE 0 END AS mat,
        r.work, r.write, r.support, r.recheck, r.alert
    FROM n1b n JOIN rules r ON r.rule = n.rule
    LEFT JOIN agg a ON a.i = n.i LEFT JOIN firsts f ON f.i = n.i
),
n3 AS (
    SELECT n2.*,
        work * factor * greatest(%(setup)s, %(floor)s - hands) AS m_setup,
        work * factor * hands AS m_hands,
        (SELECT max(day) FROM base) AS last_day
    FROM n2
)""" % dict(
        tax=tax, rules=rules, conn=conn, internal=internal, no_alert=no_alert, cnext=P.MIN_CONNECTION_NEXT, alert=P.MIN_ALERT,
        wfinal=P.MIN_WRITE_NC_FINAL, write=P.MIN_WRITE_NC, support=P.MIN_SUPPORT, recheck=P.MIN_RECHECK_CLOSE, factor=P.INTERNAL_WORK_FACTOR,
        noline=P.MIN_HANDS_ON_NO_DEFECT, setup=P.MIN_SETUP, floor=P.MIN_WORK_FLOOR,
        h_sd=H("di", "sd", 2), h_su=H("di", "su", 4), h_dd=H("di", "dd", 5),
        h_ln=H("i", "ln", 100), h_ps=H("i", "ps", 100), h_ty=H("i", "ty", 100), h_ru=H("i", "ru", 100), h_ph=H("i", "ph", 100),
        h_nl=H("i", "nl", 100), h_nl2=H("i", "nl2", 100), h_pr=H("i", "pr", 100), h_hr=H("i", "hr", 100), h_op=H("i", "op", 100),
        h_ld=H("i", "ld", 100), h_ld2=H("i", "ld2", 100), h_so=H("i", "so", 100), h_sd2=H("i", "sd2", 100), h_sg=H("i", "sg", 100), h_sc=H("i", "sc", 100),
        h_sb=H("n.i * 100 + s.seq", "sb", 10000), h_cb=H("n.i * 100 + s.seq", "cb", 100), h_fn=H("n.i * 100 + s.seq", "fn", 1000),
        h_fn2=H("n.i * 100 + s.seq", "fn2", 1000), h_fe=H("n.i * 100 + s.seq", "fe", 100), h_qt=H("n.i * 100 + s.seq", "qt", 100),
        h_lb=H("n.i * 100 + s.seq", "lb", 100), h_cf=H("n.i * 100 + s.seq", "cf", 100), h_dt=H("n.i * 100 + s.seq", "dt", 100))


def nc_query():
    rate, eng = P.RATE_STANDARD, P.RATE_ENGINEERING
    cols = """
    nc,
    to_char(day, 'YYYY-MM-DD') AS created,
    line,
    plant_scope,
    plant,
    on_aec,
    rule,
    decision_label,
    CASE WHEN scope = 'client' THEN 'Customer return' WHEN type_nc = 'CONTROLE FINAL' THEN 'Final inspection' WHEN type_nc = 'CABLES' THEN 'Cables'
         WHEN type_nc = 'TEST' THEN 'TEST' WHEN type_nc = 'INTERNE' THEN 'In-process (internal)' WHEN type_nc = 'FOURNISSEUR' THEN 'Supplier'
         WHEN type_nc = 'CASSE INTERNE' THEN 'Breakage' WHEN type_nc = 'DAMAGES' THEN 'Damage' WHEN type_nc = 'DEMANDE DE DQN' THEN 'Design query request'
         ELSE type_nc END AS where_found,
    airbus AS cost_airbus,
    round(((alert * CASE WHEN m_alert > 0 THEN %(alert)s ELSE 0 END + write * %(wglob)s + support * %(support)s + work * %(wkglob)s + recheck * %(recheck)s) / 60.0 * %(rate)s
           + eng_hours * %(eng)s + mat)::numeric, 2) AS cost_global,
    round(((m_alert + m_write + m_support + m_setup + m_hands + m_recheck) / 60.0 * %(rate)s + eng_hours * %(eng)s + mat)::numeric, 2) AS cost_total,
    round(((m_alert + m_write + m_support + m_recheck) / 60.0 * %(rate)s)::numeric, 2) AS cost_admin,
    round(((m_setup + m_hands) / 60.0 * %(rate)s)::numeric, 2) AS cost_work,
    round(mat::numeric, 2) AS cost_material,
    round((eng_hours * %(eng)s)::numeric, 2) AS cost_engineering,
    cable,
    lines AS defect_lines,
    'Fictif – ' || coalesce(first_sub, 'NC sans ligne de défaut') || ' – ' || line AS title,
    scope,
    phase,
    msn_n::text AS msn,
    CASE line WHEN 'A350' THEN CASE WHEN u_pr < 70 THEN 'MIP A350' WHEN u_pr < 82 THEN 'MDCD' ELSE 'Other' END
              WHEN 'A330' THEN CASE WHEN u_pr < 50 THEN 'PTVU' WHEN u_pr < 90 THEN '740VU' ELSE '742VU' END
              WHEN 'A400M' THEN CASE WHEN u_pr < 55 THEN 'MIP A400M' WHEN u_pr < 85 THEN '300VU' ELSE 'OHP' END
              ELSE CASE WHEN u_pr < 60 THEN 'E-RUDDER' ELSE 'MFRL' END END AS product,
    CASE WHEN type_nc = 'TEST' THEN 'Test électrique' WHEN type_nc = 'CONTROLE FINAL' THEN 'Contrôle final' ELSE CASE %(st_case)s ELSE 'Finition' END END AS station,
    CASE WHEN u_hr < 4 THEN 8 WHEN u_hr < 16 THEN 9 WHEN u_hr < 34 THEN 10 WHEN u_hr < 48 THEN 11 WHEN u_hr < 58 THEN 12 WHEN u_hr < 65 THEN 13
         WHEN u_hr < 73 THEN 14 WHEN u_hr < 84 THEN 15 WHEN u_hr < 92 THEN 16 WHEN u_hr < 95 THEN 17 WHEN u_hr < 98 THEN 22 ELSE 23 END AS hour,
    CASE WHEN status = 'closed' THEN lead END AS lead_days,
    CASE WHEN status = 'open' THEN 1 ELSE 0 END AS is_open,
    CASE WHEN status = 'open' THEN (last_day - day) + 0.5 END AS age_days,
    CASE WHEN status = 'closed' THEN to_char(day + lead::int, 'YYYY-MM-DD') ELSE '' END AS closed,
    type_nc,
    CASE plant_scope WHEN 'Fournisseur' THEN '148971' WHEN 'Hors périmètre' THEN 'TO' ELSE 'FTO2' END AS liability,
    CASE WHEN u_sd < 50 THEN 'Electrical Assembly Installation' WHEN u_sd < 65 THEN 'Harness' WHEN u_sd < 75 THEN 'Structural and Mechanical Assembly'
         WHEN u_sd < 83 THEN 'Broken' WHEN u_sd < 90 THEN 'Incorrect connector' ELSE 'Missing part' END AS sap_defect,
    CASE WHEN u_sg < 65 THEN 'Human Factors' WHEN u_sg < 90 THEN 'Jigs, Tools, Machines, Programs & Protec' WHEN u_sg < 95 THEN 'Supplier Issue'
         ELSE 'Process and Method' END AS sap_cause_group,
    CASE WHEN u_sc < 55 THEN 'People' WHEN u_sc < 70 THEN 'Defect/Damaged/Broken' WHEN u_sc < 80 THEN 'Accident' WHEN u_sc < 90 THEN 'Wrong / unsuitable'
         ELSE 'Malfunction' END AS sap_cause,
    status,
    CASE WHEN u_so < 60 THEN 'gps' WHEN u_so < 80 THEN 'sky' ELSE 'test' END AS source,
    m_alert AS min_alert,
    m_write AS min_writing,
    m_support AS min_support,
    m_setup AS min_setup,
    m_hands AS min_hands_on,
    m_recheck AS min_recheck,
    eng_hours AS hours_engineering,
    CASE WHEN type_nc = 'CONTROLE FINAL' THEN 1 ELSE 0 END AS final_inspection,
    CASE WHEN scope = 'client' THEN 'Texte fictif de retour client.' || chr(10) || 'Moment of Detection : ' || coalesce(first_det, '')
         || chr(10) || 'Description : défaut constaté chez le client (donnée fictive).' ELSE '' END AS long_text,
    CASE WHEN m_setup + m_hands > 0 THEN 'model' ELSE '' END AS work_source,
    '' AS order_state,
    '' AS rework_orders,
    CASE WHEN m_alert > 0 THEN 'flat' ELSE '' END AS alert_source,
    '' AS aleas,
    CASE WHEN u_so >= 92 THEN 'missing_ids' ELSE 'normal' END AS origin""" % dict(
        alert=P.MIN_ALERT, wglob=P.MIN_WRITE_NC_GLOBAL, support=P.MIN_SUPPORT, wkglob=P.MIN_WORK_GLOBAL, recheck=P.MIN_RECHECK_CLOSE,
        rate=rate, eng=eng, st_case=" ".join("WHEN %s = %d THEN %s" % (H("i", "st", 6), k, q(s)) for k, s in enumerate(
            ["Poste câblage A", "Poste câblage B", "Sous-ensemble harnais", "Intégration", "Retouche ligne", "Finition"])))
    tail = """,
n4 AS (
    SELECT n3.*,
        CASE WHEN rule = 'DELETED' THEN 'deleted' WHEN u_op < 7 AND day > last_day - 75 THEN 'open' WHEN u_op < 1 THEN 'open' ELSE 'closed' END AS status,
        least((CASE WHEN u_ld < 40 THEN 1 + u_ld2 % 5 WHEN u_ld < 70 THEN 5 + u_ld2 % 10 WHEN u_ld < 88 THEN 15 + u_ld2 % 20
                    WHEN u_ld < 96 THEN 35 + u_ld2 % 30 ELSE 65 + u_ld2 % 40 END) + u_ld2 / 100.0, last_day - day) AS lead
    FROM n3
)
SELECT""" + cols + "\nFROM n4\nORDER BY nc"
    return generator() + tail


def def_query():
    rate = P.RATE_STANDARD
    return generator() + """
SELECT
    d2.nc,
    d2.seq,
    d2.cat,
    d2.rca,
    d2.sub,
    d2.minor,
    d2.cable,
    round(((n3.m_alert + n3.m_write + n3.m_support + n3.m_setup + n3.m_hands + n3.m_recheck) / 60.0 * %(rate)s + n3.eng_hours * %(eng)s + n3.mat)::numeric
          / n3.lines, 2) AS cost_alloc,
    d2.qty,
    'Fictif : ' || lower(d2.sub) || CASE WHEN d2.fin <> '' THEN ' sur ' || d2.fin ELSE '' END || ', à reprendre selon le plan.' AS text,
    d2.code AS subcode,
    d2.fin,
    CASE WHEN d2.u_lb < 93 THEN 'ai' ELSE 'parser' END AS label_src,
    CASE WHEN d2.u_lb >= 93 THEN '' WHEN d2.u_cf < 62 THEN 'high' WHEN d2.u_cf < 96 THEN 'medium' ELSE 'low' END AS ai_conf,
    CASE WHEN d2.scope <> 'client' OR d2.cat <> 'Élément Endommagé' THEN ''
         WHEN d2.cr_detection ILIKE '%%unpacking%%' THEN 'recu' WHEN d2.sub = 'Composant HS' THEN 'hs'
         WHEN d2.sub = 'Composant – cause non écrite' THEN 'nc' ELSE 'phys' END AS cr_nature,
    d2.cr_detection,
    CASE WHEN d2.scope = 'client' THEN 'Fictif : ' || lower(d2.sub) ELSE '' END AS cr_symptom
FROM d2 JOIN n3 ON n3.i = d2.i
ORDER BY d2.nc, d2.seq""" % dict(rate=rate, eng=P.RATE_ENGINEERING)


def dis_query():
    """Fictitious quality aléas with no NC (the disruption block), on the working days of the fictitious NCs."""
    k, ln, st, mn, m2, m3, er, cm = (H("day", "dk", 10), H("i", "dl", 100), H("i", "ds", 6), H("i", "dm", 10), H("i", "dm2", 30),
                                     H("i", "dm3", 120), H("i", "de", 100), H("i", "dc", 5))
    return """-- MES disruptions are made up: ids OZ9..., stations and texts are fictitious. Same data at every run.
WITH days AS (
    SELECT g::date AS day
    FROM generate_series(date '2026-01-05', date '2026-09-25', interval '1 day') AS t(g)
    WHERE extract(isodow FROM g) < 6 AND NOT (g::date BETWEEN date '2026-08-03' AND date '2026-08-21')
),
counts AS (
    SELECT day, CASE WHEN """ + k + """ < 4 THEN 1 WHEN """ + k + """ = 4 THEN 2 ELSE 0 END AS k FROM days
),
base AS (
    SELECT row_number() OVER (ORDER BY c.day, s.j) AS i, c.day
    FROM counts c CROSS JOIN LATERAL generate_series(1, c.k) AS s(j)
)
SELECT
    'OZ9' || lpad(i::text, 6, '0') AS id,
    to_char(day, 'YYYY-MM-DD') AS opened,
    CASE WHEN """ + ln + """ < 60 THEN 'A350' WHEN """ + ln + """ < 90 THEN 'A330' ELSE 'A320' END AS line,
    'Poste fictif ' || (1 + """ + st + """)::text AS station,
    (1030000000 + i * 37)::text AS work_order,
    (CASE WHEN """ + mn + """ < 5 THEN 30 WHEN """ + mn + """ < 8 THEN 15 + """ + m2 + """ ELSE 60 + """ + m3 + """ END)::double precision AS minutes,
    CASE WHEN """ + er + """ < 18 THEN 0 ELSE 1 END AS in_block,
    CASE WHEN """ + er + """ < 18 THEN 'erma' ELSE '' END AS reason,
    'Closed' AS status,
    'Fictif : ' || (ARRAY['câble abîmé au montage', 'connecteur endommagé', 'pièce non conforme reçue', 'repère manquant', 'gaine déchirée'])[1 + """ + cm + """]
        || ', repris sur place sans NC.' AS comment
FROM base
ORDER BY id"""


def run_postgres(queries):
    """Run the queries on a throw-away local Postgres (the binaries of /usr/lib/postgresql) and return DataFrames."""
    bins = sorted([os.path.join("/usr/lib/postgresql", v, "bin") for v in os.listdir("/usr/lib/postgresql")]) if os.path.isdir("/usr/lib/postgresql") else []
    if not bins or not shutil.which("su"):
        print("no local Postgres: CSV snapshots not refreshed")
        return None
    b = bins[-1]
    tmp = tempfile.mkdtemp(prefix="fto2pg_")
    os.chmod(tmp, 0o777)
    data, sock = os.path.join(tmp, "data"), tmp
    as_pg = lambda cmd: subprocess.run(["su", "postgres", "-c", cmd], capture_output=True, text=True)
    r = as_pg("%s/initdb -D %s -A trust -E UTF8 --locale=C.UTF-8 >/dev/null" % (b, data))
    if r.returncode:
        r = as_pg("%s/initdb -D %s -A trust -E UTF8 >/dev/null" % (b, data))
    assert r.returncode == 0, r.stderr
    r = as_pg("%s/pg_ctl -D %s -o \"-k %s -p 55432 -c listen_addresses=''\" -w start >/dev/null" % (b, data, sock))
    assert r.returncode == 0, r.stderr
    out = []
    try:
        for i, sql in enumerate(queries):
            f = os.path.join(tmp, "q%d.sql" % i)
            open(f, "w", encoding="utf-8").write(sql + ";\n")
            os.chmod(f, 0o644)
            r = as_pg("%s/psql -h %s -p 55432 -d postgres -v ON_ERROR_STOP=1 -q --csv -f %s -o %s/q%d.csv" % (b, sock, f, tmp, i))
            assert r.returncode == 0, r.stderr[-2000:]
            out.append(pd.read_csv(os.path.join(tmp, "q%d.csv" % i), dtype=str, keep_default_na=False, encoding="utf-8"))
    finally:
        as_pg("%s/pg_ctl -D %s -m fast stop >/dev/null" % (b, data))
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def main():
    os.makedirs(SQL_DIR, exist_ok=True)
    head = ("-- FTO2 NC dashboard, level 2 (connection check): %s, generated by build/dummy_tables.py.\n"
            "-- Fictitious data made by the query itself: no dataset needed. Paste as a Slate query on the Postgres source\n"
            "-- (postgate-airbus-2), name it %s; the code sandbox's state reads it.\n")
    qn, qd, qs = nc_query(), def_query(), dis_query()
    open(os.path.join(SQL_DIR, "q_fto2_nc_dummy.sql"), "w", encoding="utf-8").write(head % ("one row per NC", "q_fto2_nc") + qn + "\n")
    open(os.path.join(SQL_DIR, "q_fto2_def_dummy.sql"), "w", encoding="utf-8").write(head % ("one row per defect line", "q_fto2_def") + qd + "\n")
    open(os.path.join(SQL_DIR, "q_fto2_dis_dummy.sql"), "w", encoding="utf-8").write(head % ("one row per quality aléa with no NC", "q_fto2_dis") + qs + "\n")
    print("SQL:", os.path.relpath(SQL_DIR, ROOT), len(qn), len(qd), len(qs), "characters")
    res = run_postgres([qn, qd, qs])
    if res is None:
        return
    nc, df, ds = res
    assert list(ds.columns) == [c[0] for c in DIS_COLUMNS], set(ds.columns) ^ {c[0] for c in DIS_COLUMNS}
    assert list(nc.columns) == [c[0] for c in NC_COLUMNS], set(nc.columns) ^ {c[0] for c in NC_COLUMNS}
    assert list(df.columns) == [c[0] for c in DEF_COLUMNS], set(df.columns) ^ {c[0] for c in DEF_COLUMNS}
    os.makedirs(CSV_DIR, exist_ok=True)
    nc.to_csv(os.path.join(CSV_DIR, "fto2_dash_nc_dummy.csv"), index=False, encoding="utf-8")
    df.to_csv(os.path.join(CSV_DIR, "fto2_dash_defects_dummy.csv"), index=False, encoding="utf-8")
    ds.to_csv(os.path.join(CSV_DIR, "fto2_dash_disruptions_dummy.csv"), index=False, encoding="utf-8")
    print("dummy tables:", len(nc), "NCs,", len(df), "defect lines,", len(ds), "aléas ->", os.path.relpath(CSV_DIR, ROOT))


if __name__ == "__main__":
    main()
