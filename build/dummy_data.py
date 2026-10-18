"""Fictitious data for the chart gallery (Galerie tab of the local dashboard).

Nothing here describes FTO2. Counts, costs, aircraft, MSNs, stations, products, FINs, production volumes, objectives and
actions are drawn at random with a fixed seed, around plausible orders of magnitude, so that charts can be judged before
the real data exists. Only the names of the categories, root causes (RCA) and sub-categories are real: they are the
reference taxonomy (04_reference/sous_categories.csv), not data.

make(root) writes 05_outputs/dummy/*.csv (with a README) and returns the compact structure embedded in the page.
"""
import csv, datetime as dt, math, os, random

SEED = 7
START = dt.date(2026, 1, 5)          # a Monday
N_WEEKS = 38
LINES = {  # aircraft per week, NCs per aircraft, first MSN
    "A350": (2.0, 2.6, 9001), "A330": (1.3, 2.4, 8001), "A320": (3.6, 0.55, 7001), "A400M": (0.3, 3.2, 6001)}
CAT_W = {"MEO Câblage": 38, "Élément Manquant": 16, "Erreur Branchement": 14, "Élément Endommagé": 12,
         "Déverrouillage": 8, "Grounding/Bonding": 5, "Kitting Factory": 3, "FOD": 2, "Autre": 2}
TREND = {"Élément Endommagé": 0.9, "Grounding/Bonding": 1.0, "Déverrouillage": 0.6, "MEO Câblage": -0.35, "Erreur Branchement": -0.3}  # drift over the year
CAT_COST = {"MEO Câblage": 24, "Erreur Branchement": 58, "Élément Manquant": 38, "Élément Endommagé": 85,
            "Déverrouillage": 19, "Grounding/Bonding": 17, "Kitting Factory": 14, "FOD": 12, "Autre": 15}
WHERE = [("poste", 40), ("cf", 31), ("test", 24), ("client", 5)]
DECISION = [("Retouche", 78), ("Rebut / rejet", 12), ("Échange", 7), ("Demande de DQN", 3)]
STATIONS = ["Poste %d" % (10 * i) for i in range(1, 13)]
PRODUCTS = [  # name, line, units per aircraft, insertions per unit
    ("Produit A", "A350", 2, 7200), ("Produit B", "A350", 4, 2400), ("Produit C", "A350", 1, 5100),
    ("Produit D", "A330", 2, 6300), ("Produit E", "A330", 3, 1800), ("Produit F", "A320", 1, 3900),
    ("Produit G", "A320", 2, 1500), ("Produit H", "A400M", 1, 6800), ("Produit I", "A350", 6, 650), ("Produit J", "A330", 1, 4200)]
TARGETS = {"A350": (3.2, 600, 7), "A330": (2.8, 750, 5), "A320": (0.9, 220, 6), "A400M": (5.0, 1100, 7)}
BUDGET = 130000
CONN_TARGET = 0.6   # connection errors per 10,000 insertions
ACTIONS = [  # line, label FR, label EN, targeted RCA, start week index, duration in weeks (0 = open), status
    ("A350", "Détrompeurs sur borniers jumeaux", "Mistake-proofing on twin terminal blocks", "Inversion", 10, 9, "done"),
    ("A330", "Gabarit de frettage au poste 40", "Lacing jig at station 40", "Frettage Incorrect", 14, 12, "done"),
    ("A350", "Contrôle de verrouillage par traction", "Pull test for contact locking", "Déverrouillage", 18, 0, "late"),
    ("A320", "Kit d'obturateurs pré-compté", "Pre-counted blanking-plug kit", "Obturateur Manquant", 12, 6, "done"),
    ("A330", "Protection des câbles en zone de stockage", "Cable protection in the storage area", "Câble Endommagé", 20, 0, "open"),
    ("A350", "Étiquettes d'identification pré-imprimées", "Pre-printed identification labels", "Identification Manquante", 24, 0, "open"),
    ("A330", "Outil de sertissage à contrôle d'effort", "Force-monitored crimping tool", "Défaut de Sertissage sur câble standard", 27, 0, "planned"),
    ("A400M", "Revue du cheminement avec le BE", "Routing review with design office", "Mauvais Cheminement", 8, 14, "done"),
    ("A350", "Couple de serrage affiché au poste", "Torque value shown at the station", "Serrage Incorrect", 30, 0, "planned")]


def _pick(R, pairs):
    t = R.uniform(0, sum(w for _, w in pairs))
    for v, w in pairs:
        t -= w
        if t <= 0:
            return v
    return pairs[-1][0]


def _poisson(R, lam):
    if lam <= 0:
        return 0
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= R.random()
        if p <= L:
            return k
        k += 1


def _week_label(d):
    y, w, _ = d.isocalendar()
    return "%d-W%02d" % (y, w)


def make(root, seed=SEED):
    R = random.Random(seed)
    tax = list(csv.DictReader(open(os.path.join(root, "04_reference", "sous_categories.csv"), encoding="utf-8-sig")))
    rcas = {}
    for t in tax:
        rcas.setdefault(t["categorie"], {}).setdefault(t["rca_nom"], []).append(t["sous_categorie"])
    rca_w = {c: [(r, 1.0 / (i + 1) ** 0.8) for i, r in enumerate(rs)] for c, rs in rcas.items()}
    cats = [(c, w) for c, w in CAT_W.items() if c in rcas]
    fins = {l: ["%d%s%s" % (R.randint(1, 9), R.choice("ABCDEFGHJKLMNPRSTVWXYZ"), R.choice("ABCDEFGHJKLMNPRSTVWXYZ")) for _ in range(60)] for l in LINES}
    fin_w = [1.0 / (i + 1) ** 1.1 for i in range(60)]
    st_w = [(s, 1.0 / (i + 1) ** 0.6) for i, s in enumerate(STATIONS)]
    act_start = {(a[0], a[3]): a[4] for a in ACTIONS}

    weeks, prod, aircraft = [], [], []
    msn = {l: v[2] for l, v in LINES.items()}
    for wi in range(N_WEEKS):
        mon = START + dt.timedelta(weeks=wi)
        weeks.append(_week_label(mon))
        shut = 0.15 if 30 <= wi <= 32 else 1.0
        for l, (rate, _, _) in LINES.items():
            n = _poisson(R, rate * shut * (0.85 + 0.3 * wi / N_WEEKS))
            prod.append([weeks[-1], l, n])
            for _ in range(n):
                aircraft.append((wi, mon, l, msn[l]))
                msn[l] += 1

    ncs, defects = [], []
    rank = {l: 0 for l in LINES}
    for wi, mon, l, m in aircraft:
        rank[l] += 1
        lam = LINES[l][1] * (1 + 0.6 * math.exp(-rank[l] / 10.0))
        cats_w = [(c, w * (1 + TREND.get(c, 0) * (wi / N_WEEKS - 0.5))) for c, w in cats]
        if (l == "A330" and 13 <= wi <= 14) or (l == "A350" and 22 <= wi <= 23):
            lam *= 3.4                                   # a bad stretch, so the control chart has something to show
        for _ in range(_poisson(R, lam)):
            day = mon + dt.timedelta(days=min(5, int(R.random() * 5.2)))
            hour = _pick(R, [(h, w) for h, w in zip(range(5, 24), [2, 6, 9, 11, 12, 10, 7, 5, 6, 9, 10, 9, 7, 5, 3, 2, 2, 1, 1])])
            where = _pick(R, WHERE)
            dec = _pick(R, DECISION)
            med = {"Retouche": 5, "Rebut / rejet": 13, "Échange": 9, "Demande de DQN": 28}[dec]
            days = round(math.exp(math.log(med) + R.gauss(0, 0.7)), 1)
            age = (START + dt.timedelta(weeks=N_WEEKS) - day).days
            if days > age or R.random() < 0.035:
                days = None
            nd = 1 + min(24, int(-math.log(1 - R.random()) * (3.4 if where == "cf" else 2.2)))
            idx = len(ncs)
            rework = 0.0
            for _ in range(nd):
                c = _pick(R, cats_w)
                r = _pick(R, rca_w[c])
                k = act_start.get((l, r))
                if k is not None and wi >= k and R.random() < 0.6:
                    c = _pick(R, cats_w)                  # the action works: most of these defects do not happen
                    r = _pick(R, rca_w[c])
                sub = R.choice(rcas[c][r])
                fin = fins[l][min(59, int(_pick(R, list(enumerate(fin_w)))))] if R.random() < 0.8 else ""
                cost = round(CAT_COST[c] * math.exp(R.gauss(0, 0.45)), 2)
                rework += cost
                defects.append([idx, c, r, sub, fin, cost])
            mat = round(R.uniform(60, 420), 2) if dec in ("Rebut / rejet", "Échange") else 0.0
            eng = round(R.uniform(150, 600), 2) if dec == "Demande de DQN" else 0.0
            ncs.append(["F-%05d" % (idx + 1), day.isoformat(), l, str(m), _pick(R, st_w),
                        R.choice([p[0] for p in PRODUCTS if p[1] == l] or ["Produit H"]), hour, dec, days, where,
                        8.0, 12.0, 15.0 if R.random() < 0.3 else 0.0, round(rework, 2), 6.0, mat, eng])

    built = {}
    for wi, mon, l, m in aircraft:
        built[l] = built.get(l, 0) + 1
    products = [[p[0], p[1], built.get(p[1], 0) * p[2], p[3]] for p in PRODUCTS]
    stations = [[s, int(len(aircraft) * R.uniform(0.6, 1.0) * 3)] for s in STATIONS]
    actions = []
    for i, a in enumerate(ACTIONS):
        s = START + dt.timedelta(weeks=a[4])
        e = (s + dt.timedelta(weeks=a[5])).isoformat() if a[5] else ""
        actions.append(["A%02d" % (i + 1), a[0], a[1], a[2], a[3], s.isoformat(), e, a[6]])
    data = {"from": START.isoformat(), "to": (START + dt.timedelta(weeks=N_WEEKS, days=-1)).isoformat(), "seed": seed,
            "weeks": weeks, "lines": list(LINES), "prod": prod, "ncs": ncs, "defects": defects, "products": products,
            "stations": stations, "targets": {l: list(v) for l, v in TARGETS.items()}, "budget": BUDGET, "connTarget": CONN_TARGET,
            "firstMsn": {l: v[2] for l, v in LINES.items()}, "actions": actions}
    _save(root, data)
    return data


def _save(root, data):
    out = os.path.join(root, "05_outputs", "dummy")
    os.makedirs(out, exist_ok=True)
    def w(name, head, rows):
        with open(os.path.join(out, name), "w", encoding="utf-8-sig", newline="") as f:
            c = csv.writer(f)
            c.writerow(head)
            c.writerows(rows)
    w("dummy_ncs.csv", ["nc", "date", "ligne", "msn", "poste", "produit", "heure", "decision", "jours_cloture", "detection",
                        "cout_alerte", "cout_redaction", "cout_support", "cout_reprise", "cout_controle", "cout_matiere", "cout_ingenierie"], data["ncs"])
    w("dummy_defects.csv", ["nc", "categorie", "rca", "sous_categorie", "fin", "cout"],
      [[data["ncs"][d[0]][0]] + d[1:] for d in data["defects"]])
    w("dummy_production.csv", ["semaine", "ligne", "avions"], data["prod"])
    w("dummy_products.csv", ["produit", "ligne", "unites", "insertions_par_unite"], data["products"])
    w("dummy_stations.csv", ["poste", "unites_passees"], data["stations"])
    w("dummy_actions.csv", ["action", "ligne", "libelle_fr", "libelle_en", "rca_visee", "debut", "fin", "statut"], data["actions"])
    w("dummy_targets.csv", ["ligne", "nc_par_avion", "cout_par_avion", "jours_cloture", "erreurs_pour_10000_insertions", "budget_cnq_annuel"],
      [[l] + v + [data["connTarget"], data["budget"]] for l, v in data["targets"].items()])
    open(os.path.join(out, "README.txt"), "w", encoding="utf-8").write(
        "DONNEES FICTIVES / DUMMY DATA\n\n"
        "Ces fichiers sont tires au hasard (graine %d) par build/dummy_data.py pour la galerie de graphiques.\n"
        "Aucun chiffre ne decrit FTO2. Seuls les noms de categories, causes (RCA) et sous-categories sont reels (taxonomie).\n\n"
        "These files are drawn at random (seed %d) by build/dummy_data.py for the chart gallery.\n"
        "No figure describes FTO2. Only the category, root-cause and sub-category names are real (the taxonomy).\n" % (data["seed"], data["seed"]))


if __name__ == "__main__":
    d = make(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(len(d["ncs"]), "NCs,", len(d["defects"]), "defects,", sum(p[2] for p in d["prod"]), "aircraft")
