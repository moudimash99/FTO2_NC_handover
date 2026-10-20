# -*- coding: utf-8 -*-
"""
Cost of non-quality (CNQ) - parameters.

This is the ONLY place where times, rates and rules live.
To change a number: edit it here, commit, rebuild the pipeline. Nothing else changes.

Every value carries a "basis" so a reader knows how far to trust it:
  LOCAL     = AEC's own estimate of its process (described by the quality team, Oct 2026)
  TEAM      = the team's code table from the old Excel tool (estimates, never timed)
  OFFICIAL  = Airbus cost model MC.QU.02 (UG2600252, issue 1)
  BORROWED  = taken from another study because AEC has no figure
  WO        = planned time on FTO2's rework orders (SAP order type S03, September 2026); to confirm on a full year
  MES       = MES disruptions (aléas) of plant FTO2, Jan-Sep 2026: time lost declared by the operator
  ASSUMED   = an assumption nobody at AEC has confirmed yet
Nothing in this file is a measured time.
"""

MODEL_VERSION = "cnq-2026.10.20"

# ---------------------------------------------------------------- who is "us"
AEC_PLANT_CODE = "FTO2"            # liability == this code -> the NC is AEC non-quality
FINAL_INSPECTION_TYPES = ["CONTROLE FINAL"]   # values of the NC type that mean "found at final inspection"
CUSTOMER_RETURN_PERIMETERS = ["Retour client"]  # values of `perimetre` that mean "customer return"
# English label shown on the charts for each NC type (anything else is shown as written)
WHERE_FOUND_LABELS = {
    "CONTROLE FINAL": "Final inspection", "INTERNE": "In-process (internal)", "CABLES": "Cables", "FOURNISSEUR": "Supplier",
    "CLIENT": "Customer return", "DEMANDE DE DQN": "Design query request", "DAMAGES": "Damage", "CASSE": "Breakage",
    "CASSE INTERNE": "Breakage", "UNKNOWN": "Not recorded",
}

# ---------------------------------------------------------------- rates (EUR per hour)
RATE_STANDARD = 50.00       # operator, quality inspector, technical support. OFFICIAL (France rate) - to be replaced by AEC rates from Finance
RATE_ENGINEERING = 78.16    # engineering study on design queries. OFFICIAL

# ---------------------------------------------------------------- fixed times per NC (minutes)
MIN_ALERT = 41              # operator raises the alert (alea).                     MES (mean time lost declared on the 214 quality aléas
                            #   that led to an NC, Jan-Sep 2026; median 30). Was 30 (LOCAL) until 19 Oct 2026.
MIN_WRITE_NC = 30           # quality inspector writes the NC.                      LOCAL
MIN_WRITE_NC_FINAL = 60     # ... when the NC is found at final inspection.         LOCAL
MIN_SUPPORT = 60            # technical support checks, estimates, work order.      LOCAL
MIN_SETUP = 50              # around the work: badging, fetching, setting up.       LOCAL
MIN_WORK_FLOOR = 60         # the work on a reworked NC is never under 1 hour.      LOCAL (team notes, Oct 2026: "rework minimum / average 1 h")
MIN_RECHECK_CLOSE = 30      # re-check and closing the NC.                          LOCAL
MIN_HANDS_ON_NO_DEFECT = 10 # hands-on time when a reworked NC has no defect line.  LOCAL ("a 10 minute job")
MIN_DEFAULT_DEFECT = 10     # hands-on time for a defect class missing from DEFECT_TIMES. ASSUMED

# ---------------------------------------------------------------- rules set from the rework orders (19 Oct 2026)
# The operator alert is charged only when an operator raises one. NCs found at test or at final inspection start
# without an operator alert (0 of 52 test NCs and 4 of 23 final-inspection NCs had a disruption, Jul-Sep 2026).
# Customer returns always get it: the customer's operator raises it, and FTO2 is the direct cause.
# Values of the NC type, both vocabularies (GPS and pipeline):
NO_ALERT_TYPES = ["TEST", "CONTROLE FINAL"]                                                                  # MES
# Rejections: about half get a rework order (median 1 h 40 planned, Sept 2026). A rejection whose NC has a rework
# order (an AW_/WO_/RS_ number in linked_document different from the NC's own work_order) uses rule "REJ_RW",
# which charges the work. Without the two columns in the NC dataset, every rejection stays "REJ" (no work).
REWORK_ORDER_PREFIXES = ["AW", "WO", "RS"]                                                                   # WO
# Connection errors: the first one in an NC takes its class time, each following one takes MIN_CONNECTION_NEXT.
# Rework orders of test NCs plan about 77 min + 15 min per connection error (11 NCs, Sept 2026).
CONNECTION_CLASSES = ["Inversion", "Erreur de branchement", "Non connecté"]
MIN_CONNECTION_NEXT = 15    # each connection error after the first one in the same NC.                     WO
# Internal NCs: the rework orders plan twice the model's work (setup + hands-on): 1,896 min against 951 on the
# 11 complete Sept 2026 orders, per-NC median ratio 2.0. The work of these NCs is multiplied by this factor.
INTERNAL_TYPES = ["INTERNE", "NC INTERNE"]
INTERNAL_WORK_FACTOR = 2.0  #                                                                               WO
# Planned time of the NC's rework order (SAP order type S03, linked through linked_document as above). When the NC
# dataset carries it (columns order_state, order_minutes_setup, order_minutes_work, made by cnq_orders.nc_order_times
# from the work-order operations), an NC whose rework orders are all closed and planned gets that time instead of
# the model's setup + hands-on: no connection rule, no internal factor; alert, writing, support, re-check and material
# stay. The planned time catches the exceptional NCs (34 h on one NC, Sept 2026). The quality re-check is not on the
# order. Planned = confirmed for 98% of operations (no measured durations).
USE_ORDER_TIME = True       #                                                                               WO
ORDER_TYPES = ["S03"]       # rework orders ("Parasitic flow")
ORDER_UNIT_MINUTES = {"IM": 0.6, "MIN": 1.0, "H": 60.0}   # SAP standard-value units: IM = 1/100 hour
# kind of an operation, from its short text, first match wins; "close" also marks the order as finished
ORDER_OP_KINDS = [("close", r"attestation|cl[ôo]ture|autoclos"), ("inspect", r"inspection|contr[ôo]l"),
                  ("prep", r"pr[ée]paration|analys"), ("test", r"test")]                         # else "work"
ORDER_SETUP_KINDS = ["close", "inspect", "prep"]   # these go to the setup step, work and test to hands-on
# MES aléas (disruptions). An aléa leads to an NC when the NC is on the same work order and was created between 2 h
# before and 72 h after the aléa opened (an aléa goes to the first such NC): 214 of 322 quality aléas, Jan-Sep 2026.
# When the NC dataset carries the declared time lost of the quality aléas that led to the NC (column alea_minutes, made
# by cnq_disruptions.nc_alea_times), the alert step is that time instead of MIN_ALERT, and it is charged even on NCs
# found at test or final inspection (an aléa was raised). A declared 0 means not filled: MIN_ALERT stays. Customer
# returns keep MIN_ALERT (their aléa is at the customer). The quality aléas that led to no NC form the disruption
# block, shown beside the cost and never added to it; possible ERMA aléas (MIP / 1101VB) are left out until checked.
USE_ALEA_TIME = True        #                                                                               MES
ALEA_TYPES = ["QLS"]        # type_desc prefix of the quality aléas ("QLS - Probleme qualite")
ALEA_LINK_HOURS = (-2, 72)  # NC created from 2 h before to 72 h after the aléa
ALEA_ERMA_DESIGNATION = r"1101VB|MIP"   # in wo_designation (or "1101" in ds_material): possible ERMA aléa, out of the block

# ---------------------------------------------------------------- the two comparison levels shown next to the detailed cost
# Level 2 "Global": every NC gets the average times, whatever its defects.
MIN_WRITE_NC_GLOBAL = 30    # average time to write an NC.                          LOCAL (team notes: "NC average 30 min")
MIN_WORK_GLOBAL = 60        # average work on a reworked NC.                        LOCAL (team notes: "rework average 1 h")

# ---------------------------------------------------------------- customer returns
# A customer return on AEC is costed like any NC of its decision. Two ways to go further:
#   CUSTOMER_RETURN_EXTRA : a flat amount added to every customer return (analysis, reply to the customer,
#                           logistics). 0 until the team sets a figure.                         ASSUMED
#   column `customer_return_cost` in the NC dataset: the real amount of a return, when known.
#                           It REPLACES the estimate for that NC.
CUSTOMER_RETURN_EXTRA = 0.0
CUSTOMER_RETURN_COST_COLUMN = "customer_return_cost"

# Level 1 "Airbus transnational": the standard cost per NC of the official model MC.QU.02.01 (section 3 summary),
# applied as it is. It uses 66.25 EUR/h, the Airbus standard hours, +5 % on creation and +25 % for returned NCs.
# It contains no material. EUR per NC, by rule:
AIRBUS_STANDARD = {
    "RWK": 542.42,      # "Rework as per DDS".                                      OFFICIAL
    "EXC": 542.42,      # no exchange line in the official model: taken as a rework. ASSUMED
    "ACC": 252.27,      # "Acceptable as is, quality as per DAC".                   OFFICIAL
    "DQN": 951.33,      # "Acceptable as is, engineering assessment".               OFFICIAL figure, ASSUMED match
    "REJ": 252.27,      # no reject line: taken as creation + assessment + decision. ASSUMED
    "REJ_RW": 252.27,   # rejection with a rework order: same official figure as a rejection. ASSUMED
    "SCR": 252.27,      # same.                                                     ASSUMED
    "PNC": 252.27,      # same.                                                     ASSUMED
    "NDC": 69.56,       # creation step only (66.25 x 1.05).                        ASSUMED
    "DELETED": 69.56,   # creation step only.                                       ASSUMED
    "UNKNOWN": 69.56,   # creation step only.                                       ASSUMED
}

# ---------------------------------------------------------------- which steps are charged for each decision
# rule key = decision_status of the NC, except deleted NCs which always use "DELETED", and rejections whose NC has a
# rework order, which use "REJ_RW".
# columns: alert, write, support, work (setup + hands-on + material), recheck, engineering hours, part value counted
RULES = {
    #            alert write support work recheck eng_h part   label                         basis
    "RWK":     (1,    1,    1,      1,   1,      0.0,  0,     "Rework to drawing",          "LOCAL - the process AEC described"),
    "EXC":     (1,    1,    1,      0,   1,      0.0,  1,     "Exchange",                   "WO - no rework order at FTO2 (0 of 20 in 2026): no work, swapped part counted"),
    "REJ":     (1,    1,    1,      0,   1,      0.0,  1,     "Rejection",                  "ASSUMED - no work, part value counted"),
    "REJ_RW":  (1,    1,    1,      1,   1,      0.0,  1,     "Rejection with a rework order", "WO - the NC has a rework order: work charged, part value counted"),
    "SCR":     (1,    1,    1,      0,   1,      0.0,  1,     "Scrap",                      "ASSUMED - no work, part value counted"),
    "DQN":     (1,    1,    1,      0,   1,      8.0,  0,     "Request for design change",  "Rule from AEC: carries the engineering study. 8 h is OFFICIAL, not an AEC figure"),
    "ACC":     (1,    1,    1,      0,   1,      0.0,  0,     "Accept as is",               "ASSUMED"),
    "PNC":     (1,    1,    1,      0,   1,      0.0,  0,     "Potential non-conformity",   "ASSUMED"),
    "NDC":     (1,    1,    0,      0,   0,      0.0,  0,     "No decision",                "ASSUMED - alert and writing only"),
    "DELETED": (1,    1,    0,      0,   0,      0.0,  0,     "Deleted NC",                 "Rule from AEC: should not have been filed, administrative cost only"),
    "UNKNOWN": (1,    1,    0,      0,   0,      0.0,  0,     "Unknown decision code",      "ASSUMED - alert and writing only; shows up in the data-gap query"),
}
RULE_FIELDS = ("alert", "write", "support", "work", "recheck", "eng_hours", "part", "label", "basis")

# ---------------------------------------------------------------- hands-on minutes and material per defect class
# key = `sous_groupe` written by the defect parser (v4.7).
# reference_code = the line of the team's code table the figure is taken from.
# (minutes, material_eur, english_label, reference_code, basis)
DEFECT_TIMES = {
    # --- Branchement (connections)
    "Inversion":                                 (35, 0.00,  "Swapped connection",                     "T04",     "BORROWED - 2021 BU1 study, no time in the team table"),
    "Erreur de branchement":                     (35, 0.00,  "Wrong connection",                       "T02",     "BORROWED - 2021 BU1 study, no time in the team table"),
    "Non connecté":                              (35, 0.00,  "Not connected",                          "T05",     "BORROWED - 2021 BU1 study, no time in the team table"),
    "Déverrouillage":                            (10, 0.00,  "Contact not locked",                     "Q01-001", "TEAM"),
    # --- Câblage (wiring workmanship)
    "Cheminement – clash":                       (1,  0.00,  "Routing: clash",                         "Q06-007", "TEAM"),
    "Cheminement – longueur / tension":          (2,  7.20,  "Routing: length or tension",             "Q06-001", "TEAM"),
    "Câblage non terminé":                       (2,  63.77, "Wiring not finished",                    "Q06-012", "TEAM - material looks too high, check"),
    "Câble à refaire (ligne)":                   (60, 0.00,  "Cable to remake (line)",                 "Q06-004", "TEAM"),
    "Frettage / colliers – pose":                (1,  1.30,  "Ties and clamps: fitting",               "Q05-018", "TEAM"),
    "Mauvaise réf. – colliers / frettage":       (5,  0.00,  "Wrong reference: clamp or tie",          "Q04-015", "TEAM"),
    "Gainage / protection":                      (5,  3.58,  "Sleeving and protection",                "Q06-002", "TEAM"),
    "Identification – positionnement":           (2,  45.20, "Identification: position",               "Q06-014", "TEAM - material looks too high, check"),
    "Mauvaise réf. – identification":            (2,  4.43,  "Wrong reference: identification",        "Q04-030", "TEAM"),
    "Mauvaise réf. – mécanique":                 (2,  0.00,  "Wrong reference: mechanical part",       "Q04-003", "TEAM"),
    "Mauvaise réf. – obturation / thermo":       (1,  0.00,  "Wrong reference: plug or heat-shrink",   "Q04-001", "TEAM"),
    "Mauvaise réf. – électrique / détrompage":   (3,  0.18,  "Wrong reference: electrical or keying",  "Q04-018", "TEAM"),
    "Serrage mécanique":                         (3,  0.52,  "Tightening: mechanical",                 "Q05-002", "TEAM"),
    "Serrage électrique":                        (3,  0.00,  "Tightening: electrical",                 "Q05-001", "TEAM"),
    "Sertissage":                                (1,  0.00,  "Crimping",                               "Q07-002", "TEAM"),
    "Sertissage spécifique":                     (10, 0.00,  "Crimping: special contacts",             "Q08-001", "TEAM"),
    # --- Dommage & manquant (damage and missing)
    "Composant HS":                              (15, 0.00,  "Component out of order",                 "Q11-005", "TEAM"),
    "Composant – cause non écrite":              (15, 0.00,  "Component: cause not written",           "Q11-005", "TEAM"),
    "Dommage – composant cassé":                 (15, 0.00,  "Damage: broken component",               "Q11-005", "TEAM"),
    "Dommage – câble":                           (60, 2.01,  "Damage: cable",                          "Q11-001", "TEAM"),
    "Dommage – habillage":                       (7,  0.00,  "Damage: sleeving or dressing",           "Q11-006", "TEAM"),
    "Dommage – identification":                  (1,  1.32,  "Damage: identification",                 "Q11-002", "TEAM"),
    "Dommage – structure":                       (20, 0.85,  "Damage: structure",                      "Q10-001", "TEAM - very mixed class (1 to 120 min in the table)"),
    "Manquant – colliers":                       (3,  0.00,  "Missing: clamps or ties",                "Q03-006", "TEAM"),
    "Manquant – câble / shunt / élément":        (15, 0.00,  "Missing: cable, shunt or part",          "Q03-004", "TEAM"),
    "Manquant – gaine / thermo":                 (1,  0.00,  "Missing: sleeve or heat-shrink",         "Q03-002", "TEAM"),
    "Manquant – identification":                 (2,  0.00,  "Missing: identification",                "Q03-014", "TEAM"),
    "Manquant – mécanique / freinage":           (2,  0.00,  "Missing: mechanical part or locking",    "Q03-003", "TEAM"),
    "Manquant – obturateurs / bouchons":         (1,  0.00,  "Missing: plugs or caps",                 "Q03-001", "TEAM"),
    # --- Dossier, FOD
    "Dossier":                                   (2,  0.00,  "Paperwork",                              "Q13-004", "TEAM"),
    "FOD":                                       (5,  0.00,  "FOD",                                    "Q16-004", "TEAM"),
    # --- Métallisation (bonding)
    "Bleu mal appliqué / débordant":             (10, 0.00,  "Bonding protection badly applied",       "Q09-002", "TEAM"),
    "Bleu non appliqué":                         (2,  0.00,  "Bonding protection not applied",         "Q09-001", "TEAM"),
    "Point de masse / mesure":                   (5,  0.00,  "Ground point or measurement",            "Q09-003", "TEAM"),
    # --- Amont (upstream)
    "Amont · Câble":                             (5,  0.00,  "Upstream: cable",                        "Q12-003", "TEAM"),
    "Amont · Identification / barrette VT":      (5,  0.00,  "Upstream: identification or terminal block", "Q12-006", "TEAM"),
    # --- classes of parser v4.8 / the long-text labelling with no line in the team table (Oct 2026): default time, to be set by the team
    "Dommage – tresse de masse":                 (10, 0.00,  "Damage: ground braid",                   "Q11-009", "ASSUMED - no team time, default 10 min"),
    "Mesure hors tolérance":                     (10, 0.00,  "Measurement out of tolerance",           "T06",     "ASSUMED - no team time, default 10 min"),
    "Non classé":                                (10, 0.00,  "Not classified",                         "",        "ASSUMED - defect not described, default 10 min"),
}
DEFECT_FIELDS = ("minutes", "material_eur", "label_en", "reference_code", "basis")

# ---------------------------------------------------------------- team rules linking classes (notes of October 2026)
#   "Wrong reference = 2 x missing"            (take the wrong part off, then fit the right one)
#   "Q11, damaged electrical element = 2 x missing"   (take the damaged part off, then fit a new one)
# The minutes of the class on the left are ALWAYS factor x the minutes of the class on the right:
# change the "missing" time above and these follow. Material is not affected.
DERIVED_TIMES = {
    # class                                      (base class,                              factor)
    "Mauvaise réf. – colliers / frettage":       ("Manquant – colliers",                   2),
    "Mauvaise réf. – identification":            ("Manquant – identification",             2),
    "Mauvaise réf. – mécanique":                 ("Manquant – mécanique / freinage",       2),
    "Mauvaise réf. – obturation / thermo":       ("Manquant – obturateurs / bouchons",     2),
    "Mauvaise réf. – électrique / détrompage":   ("Manquant – câble / shunt / élément",    2),
    "Dommage – composant cassé":                 ("Manquant – câble / shunt / élément",    2),
    "Composant HS":                              ("Manquant – câble / shunt / élément",    2),
    "Composant – cause non écrite":              ("Manquant – câble / shunt / élément",    2),
    "Dommage – câble":                           ("Manquant – câble / shunt / élément",    2),
    "Dommage – habillage":                       ("Manquant – gaine / thermo",             2),
    "Dommage – identification":                  ("Manquant – identification",             2),
}
for _cls, (_base, _factor) in DERIVED_TIMES.items():
    _m, _mat, _en, _ref, _basis = DEFECT_TIMES[_cls]
    DEFECT_TIMES[_cls] = (DEFECT_TIMES[_base][0] * _factor, _mat, _en, DEFECT_TIMES[_base][3],
                          "TEAM RULE - %d x \"%s\"" % (_factor, DEFECT_TIMES[_base][2]))

# Open points from the same notes, NOT modelled yet:
#   - Routing ("Cheminement") depends on access: one time per class cannot capture it.
#   - Printing defects (Q12, the "Amont" classes): time = printing time, plus possibly a full rework. To be decided.
