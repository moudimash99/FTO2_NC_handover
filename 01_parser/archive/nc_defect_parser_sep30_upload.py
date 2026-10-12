"""
nc_defect_parser
================
Splits Skywise NC long descriptions (description_long_text) into individual
defects, counts them per NC, and classifies each defect into a two-level
two-axis taxonomy (objet x mode) aligned on the official FTO2 code sheet.

Pure-stdlib core (regex + unicodedata) so parse_nc() can be lifted as-is
into a PySpark UDF in a Foundry Code Repository. pandas is only needed
for the DataFrame helper at the bottom.

Handles the four formats observed in the data:
  1. DEF lists ......... "DEF 3-T04 : 3RN3B INVERSION DE BRANCHEMENT ..."
  2. Numbered lists .... "13 - FIN 411VC007 A : Manque 4 obturateurs"
  3. Cable lists ....... "- N° 2424-0135 - Type : QG 18 - Longueur : 250 CM"
  4. Narrative ......... single free-text "NonConformity 0001 :" block(s)

Also: strips quoted replies ("> X*" lines) that duplicate earlier content,
and flags texts redacted for classification (nb_defauts=None for those).

Classification (v4.1 — cable provenance)
-------------------------------
One target: the official FTO2 retouching sub-code. Everything else is a lookup.

    sub-code (123)  --many-to-one-->  type_reporting (26)  --function-->  mode_erreur (6)

Types are NATURE-PURE: every type lives inside exactly one mode, so the two
levels form a strict tree (mode -> type). A missing frettage and a loose
frettage are different types because they are different problems.

Resolution order for a defect, descending confidence:
    1. explicit sub-code present            -> lookup            HIGH
    2. head code that maps to one type      -> lookup            HIGH
    3. multi-type head code + keyword       -> constrained match MEDIUM
    4. no code, keyword on a reliable type  -> free match        MEDIUM
    5. no code, keyword on any other type   -> free match        LOW
    6. narrative NC, SAP nonconformity type -> prior             LOW
    7. nothing                              -> AUTRE             NONE

v4.1 (septembre 2026) — cable NCs
---------------------------------
Measured against the cable team's tracker ("Suivi NCs - NC câbles et
analyses"): agreement 53% (v4) -> 81% (v4.1 text only) -> 92% (v4.1 + tracker).
Outside the tracker's NCs, 4 labels change out of ~2,560, all checked by hand.
  * Cable spec boilerplate ("d'une longueur de 220cm", "Type : DR", "3161-0665")
    is stripped before keyword matching; it used to trigger the length rule.
  * provenance: RECU (arrived that way) | LIGNE (caused on the line) | NON_PRECISE,
    from explicit phrases only. "Constaté par la production" is detection, not cause.
  * A cable stated too short is AMONT_IMPRESSION if it arrived short and
    MEO_CHEMINEMENT if it was cut short on the line (MEO_SERTISSAGE_STANDARD when
    crimping caused it). If the text doesn't say, v4's label is kept, confidence LOW.
  * The length rule only reads clauses about a cable, so "frette trop longue" or
    "vis trop courte" are left to their own rules.
  * A cable that arrived damaged is AMONT_IMPRESSION; damage from stripping or
    crimping is reported as MEO_SERTISSAGE_STANDARD (the cause, not the symptom).
  * apply_cable_tracker(): where the text gives no origin, take it from the
    tracker's Imputation; where both are explicit and disagree, set
    provenance_conflict=True and change nothing.

v4.2 (septembre 2026) — "is it actually a cable NC?"
----------------------------------------------------
  * New binary flag, independent of type_reporting: defaut_cable / cable_preuve
    per defect, nc_cable (CABLE | MIXTE | NON) and nb_defauts_cable per NC.
    Count cable NCs on nc_cable == "CABLE", on non-deleted NCs only.
  * Measured on the 876 FTO2 NCs (S01–S37) against the cable team's tracker,
    every disagreement read by hand: the flag keeps 178 of the tracker's 183
    NCs (the other 5: a rail, plaquettes, a ramp NC, and two harness NCs whose
    text describes an installation error); of the 32 other NCs it flags, 31 are
    real cable NCs and 1 is not. Rules were adjusted on this same data (3
    fixes), so expect a little less on new NCs.
  * Two v4 keyword rules mislabelled defects that are not print defects:
    "câble en sur-longueur" at final inspection is slack left on the harness
    (now MEO_CHEMINEMENT) and "vis trop courte" is a wrong screw (now
    ERREUR_REF_HABILLAGE, it used to land in AMONT_IMPRESSION, DOMMAGE_STRUCTURE
    or MEO_FRETTAGE_COLLIER depending on the nearby words). 37 defects move, 28
    of them out of AMONT_IMPRESSION ("Kitting factory"): 79 -> 51.
"""

from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass, field, asdict

# --------------------------------------------------------------------------- #
# Text normalisation
# --------------------------------------------------------------------------- #

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")

def norm(s: str) -> str:
    """Accent-stripped uppercase — all keyword matching happens on this."""
    return strip_accents(s).upper()

def clean_text(raw: str) -> str:
    """Remove quoted-reply lines ('> X*') that duplicate earlier content."""
    lines = [l for l in str(raw).replace("\r\n", "\n").split("\n")
             if not l.strip().startswith("> X")]
    return "\n".join(lines)

REDACTED_MARKER = "Removed for classification"

# --------------------------------------------------------------------------- #
# Splitting
# --------------------------------------------------------------------------- #

SEP_RE       = re.compile(r"(?:--\s*){6,}")                       # dashed separators
TS_RE        = re.compile(r"\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2} CET")
DEF_RE       = re.compile(r"D[EÉ]F(?:AUT)?\.?\s*(\d{1,3})(?=\s*[-–:.]|\s+[A-Z]{1,4}\s?\d{0,2}\s*:)", re.I)
CODE_HEAD_RE = re.compile(r"^\s*[-–]?\s*([A-Za-z]{1,4}\s?[0-9O]{0,2})\s*:?\s*")
QTY_TXT_RE   = re.compile(r"(?:QUANTIT[EÉ]|QTE)\s*:?\s*(\d{1,2})", re.I)

def _norm_code(c: str) -> str | None:
    c = re.sub(r"\s+", "", c.upper())
    c = re.sub(r"^([QTP])\1+", r"\1", c)
    if len(c) >= 2:
        c = c[0] + c[1:].replace("O", "0")
    if re.fullmatch(r"[QTP]\d{1,2}", c) and c[1:] != "0":
        return c
    return None

def _severity_at(text: str, pos: int) -> str | None:
    """Last RETOUCHES MAJEURES/MINEURES header before this position."""
    last = None
    for m in SEV_HDR_RE.finditer(text, 0, pos):
        last = m.group(1).upper().rstrip("S") + "E" if not m.group(1).upper().endswith("E") else m.group(1).upper()
    if last:
        last = "MAJEURE" if last.startswith("MAJEURE") else "MINEURE"
    return last

def _split_def_list(text: str) -> list[tuple[int, str | None, int, str]]:
    marks = list(DEF_RE.finditer(text))
    out, seen = [], set()
    for i, m in enumerate(marks):
        seq = int(m.group(1))
        if seq in seen:
            continue
        seen.add(seq)
        chunk = text[m.end(): marks[i+1].start() if i+1 < len(marks) else len(text)]
        stop = SEP_RE.search(chunk) or TS_RE.search(chunk)
        if stop:
            chunk = chunk[:stop.start()]
        code = None
        h = CODE_HEAD_RE.match(chunk)
        if h and any(ch.isdigit() or ch in "Oo" for ch in h.group(1)):
            code = _norm_code(h.group(1))
            if code:
                chunk = chunk[h.end():]
        q = QTY_TXT_RE.search(strip_accents(chunk))
        qty = int(q.group(1)) if q else 1
        out.append((seq, code, qty, " ".join(chunk.split()), _severity_at(text, m.start())))
    return out
NUM_RE       = re.compile(r"^\s*(\d{1,2})\s*[)\-–]\s+(?=\S)", re.M)
SEV_HDR_RE   = re.compile(r"RETOUCHES?\s+(MAJEURES?|MINEURES?)", re.I)
CABLE_RE     = re.compile(r"^\s*[-*]?\s*N\s?°", re.M)
BLOCK_RE     = re.compile(r"Non\s?Conformity\s+\d+\s*:")
FAL_FMT_RE   = re.compile(r"Decision Tree Instructions|Caract[eé]risation du d[eé]faut", re.I)
FAL_DESC_RE  = re.compile(r"Caract[eé]risation du d[eé]faut\s*:\s*([^\n]+)|Commentaire\s*:\s*([^\n]+)", re.I)
CUE_RE       = re.compile(r"D[EÉeé]FAUTS?\s+SUIVANTS|POINTS?\s+SUIVANTS", re.I)
DASH_RE      = re.compile(r"^\s*\*?\s*[-•]\s+(?=\S)", re.M)
FIN_RE       = re.compile(r"\b(\d{1,4}[A-Z]{2,4}\d{0,4}[A-Z]{0,2})\b")

# --- DEFAUTS v1 template (the writing standard) ---
TPL_HDR_RE   = re.compile(r"###\s*DEFAUTS\s*v1\b", re.I)
TPL_LINE_RE  = re.compile(
    r"^\s*DEF\s*(\d{1,3})\s*-\s*([A-Z]{1,3}\d{0,2}(?:-\d{1,3})?)\s*-\s*([^:\n]+?)"
    r"(?:\s*-\s*CABLE\s+(\S+))?(?:\s*-\s*QTE\s+(\d{1,3}))?\s*:\s*(.*)$",
    re.I | re.M)
TPL_TOTAL_RE = re.compile(r"###\s*TOTAL\s*:\s*(\d+)", re.I)

@dataclass
class Defect:
    seq: int                # position within the NC (1-based)
    code: str | None        # Q/T code if present (e.g. 'T04')
    fin: str | None         # first FIN-like reference found on the item
    text: str               # defect text (wrapped lines re-joined)
    source_format: str      # def_list | numbered_list | cable_list | narrative
    type_reporting: str = ""     # one of 26 nature-pure types (see TYPES)
    mode_erreur: str = ""        # one of 6 modes — a function of type_reporting
    sub_code: str | None = None  # official sub-code (e.g. Q03-006) when carried
    confidence: str = ""         # HIGH | MEDIUM | LOW | NONE
    resolved_by: str = ""        # SUBCODE | HEADCODE | HEAD+KW | KW | SAP_PRIOR | -
    cdve: bool = False           # CDVE circuit variant
    severite_off: str | None = None  # MAJEURE/MINEURE from official severity (sub-code known)
    sap_type: str | None = None  # SAP 'Type of nonconformity' line (NC-level prior)
    provenance: str = ""         # RECU (arrived that way) | LIGNE (caused on the line) | NON_PRECISE
    provenance_force: str = ""   # EXPLICITE (actor/cause named) | INDICE ("coupé trop court" alone) | "" 
    etat_cable: str = ""         # LONGUEUR | DOMMAGE when the text states the cable's own length/damage
    defaut_cable: bool = False   # v4.2: a cable itself must be re-made / re-supplied (see cable_signal)
    cable_preuve: str = ""       # v4.2: DEMANDE (new cable asked) | ETAT (missing/short/damaged/misprinted) | SPEC (n° + length)
    loc: str | None = None  # location slot as written (FIN, 'ZONE ...', or None)
    qty: int = 1            # QTE slot (identical defects on one line)
    severite: str | None = None  # MAJEURE/MINEURE when section headers present

def _slice_items(text: str, marker_iter) -> list[tuple[str | None, str]]:
    """Slice text between successive markers; stop each item at a dashed
    separator or a task-log timestamp so wrapped lines stay attached."""
    marks = list(marker_iter)
    items = []
    for i, m in enumerate(marks):
        start = m.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        chunk = text[start:end]
        stop = SEP_RE.search(chunk) or TS_RE.search(chunk)
        if stop:
            chunk = chunk[:stop.start()]
        code = m.group(2).replace(" ", "").upper() if (m.lastindex and m.lastindex >= 2 and m.group(2)) else None
        items.append((code, " ".join(chunk.split())))
    return items

def _unique_blocks(text: str) -> list[str]:
    """Unique 'NonConformity NNNN :' narratives (SAP logs often repeat them)."""
    parts = BLOCK_RE.split(text)[1:]
    keys, out = [], []
    for p in parts:
        narr = SEP_RE.split(p)[0]
        key = re.sub(r"\W+", "", norm(narr))[:300]
        if not key:
            continue
        narr = re.sub(r"^\s*Type of nonconformity\s*:[^*\n]*[*]?", "", narr).strip()
        narr = " ".join(narr.split())
        dup = False
        for j, e in enumerate(keys):
            if key.startswith(e) or e.startswith(key):   # same block, one has extra tail
                dup = True
                if len(key) > len(e):                    # keep the richer version
                    keys[j], out[j] = key, narr
                break
        if not dup:
            keys.append(key); out.append(narr)
    return out

def split_defects(raw_text: str) -> list[Defect]:
    text = clean_text(raw_text)

    # FAL 'decision tree' notifications: structured single-defect format whose
    # numbered lines are repair INSTRUCTIONS, not defects -> always one defect.
    if FAL_FMT_RE.search(text):
        m = FAL_DESC_RE.search(text)
        desc = next((g for g in (m.groups() if m else []) if g), None) or                " ".join(text.split())[:200]
        fin = FIN_RE.search(norm(desc))
        return [Defect(seq=1, code=None, fin=fin.group(1) if fin else None,
                       text=" ".join(desc.split())[:300], source_format="fal_single")]

    # DEFAUTS v1 template: strict grammar, highest-confidence path
    if TPL_HDR_RE.search(text):
        out = []
        for m in TPL_LINE_RE.finditer(text):
            seq, code, loc, cable, qte, txt = m.groups()
            loc = loc.strip()
            fin = FIN_RE.search(norm(loc))
            body = (f"CABLE {cable} " if cable else "") + txt.strip()
            cu = code.upper()
            out.append(Defect(seq=int(seq), code=cu[:3],
                              sub_code=cu if "-" in cu else None,
                              cdve=cu.endswith("CDVE") or cu in {"Q01-003","Q05-005","Q07-006","Q07-007",
                                   "Q07-008","Q07-009","Q07-010","Q09-004","Q09-005","Q09-006",
                                   "Q11-016","Q11-018","Q11-019","Q11-022","Q11-026","Q12-007","Q12-008"},
                              fin=fin.group(1) if fin else None,
                              text=body[:300], source_format="template_v1",
                              loc=loc if loc != "-" else None,
                              qty=int(qte) if qte else 1))
        if out:
            return out

    def_items = _split_def_list(text)
    if def_items:
        out = []
        for (seq, code, qty, chunk, sev) in def_items:
            fin = FIN_RE.search(norm(chunk))
            out.append(Defect(seq=seq, code=code, fin=fin.group(1) if fin else None,
                              text=chunk[:300], source_format="def_list", qty=qty,
                              severite=sev))
        return out

    items = []
    if not items:
        nums = [int(m.group(1)) for m in NUM_RE.finditer(text)]
        # plausibility guard: a real checklist counts up; stray '1 -' lines don't
        if len(nums) >= 3 and max(nums) <= 60 and len(nums) >= 0.6 * max(nums):
            items = _slice_items(text, NUM_RE.finditer(text))
            fmt = "numbered_list"

    if not items:
        cables = CABLE_RE.findall(text)
        if len(cables) > 1:
            items = _slice_items(text, CABLE_RE.finditer(text))
            fmt = "cable_list"

    if not items:
        cue = CUE_RE.search(text)
        if cue:
            end = len(text)
            stop = SEP_RE.search(text, cue.end()) or TS_RE.search(text, cue.end())
            if stop:
                end = stop.start()
            region = text[cue.end():end]
            marks = list(DASH_RE.finditer(region))
            if len(marks) >= 2:
                fmt = "dash_list"
                for i, m in enumerate(marks):
                    chunk = region[m.end(): marks[i+1].start() if i+1 < len(marks) else len(region)]
                    items.append((None, " ".join(chunk.split())))

    if not items:
        fmt = "narrative"
        blocks = _unique_blocks(text)
        if not blocks:  # NCs without a 'NonConformity' header (~11% of data)
            head = TS_RE.split(text)[0] if TS_RE.search(text) else text
            blocks = [" ".join(head.split())[:400]] if head.strip() else []
        items = [(None, b) for b in blocks]

    marks = list(NUM_RE.finditer(text)) if fmt == "numbered_list" else []
    out = []
    for i, (code, t) in enumerate(items, 1):
        fin = FIN_RE.search(norm(t))
        sev = _severity_at(text, marks[i-1].start()) if fmt == "numbered_list" and i <= len(marks) else None
        out.append(Defect(seq=i, code=code, fin=fin.group(1) if fin else None,
                          text=t[:300], source_format=fmt, severite=sev))
    return out

# --------------------------------------------------------------------------- #
# CLASSIFICATION v3 — two independent axes, both derived from the official
# FTO2 retouching code sheet (which is itself a NATURE x OBJECT matrix).
#
#   MODE  (6)  = f(nature / head code)  -> the countermeasure family
#   OBJET (15) = f(object / sub-code)   -> the process owner
#
# Resolution order per axis: official code -> keyword -> undetermined.
# Confidence is the pair of sources, never a guess:
#   HIGH   both axes from code
#   MEDIUM one from code + one from keywords, or both from keywords
#   LOW    one axis undetermined
#   NONE   both undetermined  (-> objet/mode = "INDETERMINE")

# =========================================================================== #
# CLASSIFICATION — v4
# =========================================================================== #

MODES = ("SELECTION", "OMISSION", "EXECUTION", "MANIPULATION", "AMONT", "PROCESS")

# The 26 reporting types, grouped by mode. The prefix tells you the mode.
TYPES: dict[str, str] = {
    # SELECTION — picked the wrong one of several similar options
    "INVERSION_BRANCHEMENT":    "SELECTION",
    "ERREUR_BRANCHEMENT":       "SELECTION",
    "ERREUR_REF_ELECTRIQUE":    "SELECTION",
    "ERREUR_REF_HABILLAGE":     "SELECTION",
    # OMISSION — a step or a part was left out
    "OUBLI_VERROUILLAGE":       "OMISSION",
    "MANQUANT_OBTURATION":      "OMISSION",
    "MANQUANT_HABILLAGE":       "OMISSION",
    "MANQUANT_CABLE_ELEMENT":   "OMISSION",
    "MANQUANT_IDENTIFICATION":  "OMISSION",
    "NON_CONNECTE":             "OMISSION",
    "FOD":                      "OMISSION",
    # EXECUTION — the gesture was done, not to standard (MEO = mise en oeuvre)
    "MEO_SERRAGE":              "EXECUTION",
    "MEO_CHEMINEMENT":          "EXECUTION",
    "MEO_GAINAGE":              "EXECUTION",
    "MEO_FRETTAGE_COLLIER":     "EXECUTION",
    "MEO_SERTISSAGE_STANDARD":  "EXECUTION",
    "MEO_SERTISSAGE_SPECIFIQUE":"EXECUTION",
    "MEO_METALLISATION":        "EXECUTION",
    "MEO_FINITION":             "EXECUTION",
    "MESURE_NON_CONFORME":      "EXECUTION",
    # MANIPULATION — damaged in handling
    "DOMMAGE_CABLE":            "MANIPULATION",
    "DOMMAGE_COMPOSANT":        "MANIPULATION",
    "DOMMAGE_HABILLAGE":        "MANIPULATION",
    "DOMMAGE_STRUCTURE":        "MANIPULATION",
    # AMONT — arrived wrong from upstream
    "AMONT_IMPRESSION":         "AMONT",
    # PROCESS — documentation / traceability
    "PROCESS_DOSSIER":          "PROCESS",
}

def _expand(spec: dict[str, str]) -> dict[str, str]:
    """'Q07-001..010' style ranges -> individual sub-codes."""
    out = {}
    for k, v in spec.items():
        for tok in k.split():
            if ".." in tok:
                head, rng = tok.split("-", 1)
                a, b = rng.split("..")
                for i in range(int(a), int(b) + 1):
                    out[f"{head}-{i:03d}"] = v
            else:
                out[tok] = v
    return out

# Official sub-code -> type. 123 entries. Authoritative copy: mapping_v4_codes_types.csv
SUBCODE_TYPE: dict[str, str] = _expand({
    "T04":                                              "INVERSION_BRANCHEMENT",
    "T02":                                              "ERREUR_BRANCHEMENT",
    "Q04-004 Q04-005 Q04-009 Q04-011":                  "ERREUR_REF_ELECTRIQUE",
    "Q04-001 Q04-002 Q04-003 Q04-006 Q04-007 Q04-008 Q04-010 Q04-012 Q04-013 Q04-014": "ERREUR_REF_HABILLAGE",
    "Q01-001..003":                                     "OUBLI_VERROUILLAGE",
    "Q03-001 Q03-007 Q03-008":                          "MANQUANT_OBTURATION",
    "Q03-002 Q03-003 Q03-005 Q03-006 Q03-010":          "MANQUANT_HABILLAGE",
    "Q03-004 T01 T03":                                  "MANQUANT_CABLE_ELEMENT",
    "Q03-009 Q03-011 Q03-012":                          "MANQUANT_IDENTIFICATION",
    "T05":                                              "NON_CONNECTE",
    "Q16-001..006":                                     "FOD",
    "Q05-001 Q05-002 Q05-003 Q05-005":                  "MEO_SERRAGE",
    "Q06-001 Q06-004 Q06-005":                          "MEO_CHEMINEMENT",
    "Q06-002 Q06-003 Q06-007 Q06-008":                  "MEO_GAINAGE",
    "Q05-004 Q06-006 Q06-011 Q06-012":                  "MEO_FRETTAGE_COLLIER",
    "Q07-001..010":                                     "MEO_SERTISSAGE_STANDARD",
    "Q08-001..007":                                     "MEO_SERTISSAGE_SPECIFIQUE",
    "Q09-001..006 T07 T07-CDVE":                        "MEO_METALLISATION",
    "Q06-009 Q06-010":                                  "MEO_FINITION",
    "T06 T08 T08-CDVE":                                 "MESURE_NON_CONFORME",
    "Q11-001 Q11-014":                                  "DOMMAGE_CABLE",
    "Q11-003 Q11-005 Q11-006 Q11-009 Q11-012 Q11-016 Q11-018 Q11-019 Q11-022": "DOMMAGE_COMPOSANT",
    "Q11-002 Q11-004 Q11-007 Q11-008 Q11-010 Q11-011 Q11-013 Q11-026": "DOMMAGE_HABILLAGE",
    "Q10-001..006":                                     "DOMMAGE_STRUCTURE",
    "Q12-001..008":                                     "AMONT_IMPRESSION",
    "Q13-001..005":                                     "PROCESS_DOSSIER",
})
assert len(SUBCODE_TYPE) == 123, len(SUBCODE_TYPE)

# Official sub-code severity (>= 8 on the FMEA scale = MAJEURE)
SUBCODE_MAJEURE: frozenset[str] = frozenset(_expand({
    "Q01-003 Q04-004 Q05-001 Q05-005 Q07-001..010 Q08-001..005 Q08-007 "
    "Q11-001 Q11-014 Q11-006 Q11-019 Q16-001..005 T01 T02 T03 T04 T05 T07-CDVE T08-CDVE": 1}).keys())

# Head code -> type when the head is single-type (16 of 21 heads).
HEAD_TYPE: dict[str, str] = {}
for _sc, _t in SUBCODE_TYPE.items():
    _h = _sc.split("-")[0]
    HEAD_TYPE.setdefault(_h, set()).add(_t)
HEAD_CANDIDATES: dict[str, tuple[str, ...]] = {h: tuple(sorted(s)) for h, s in HEAD_TYPE.items()}
HEAD_TYPE = {h: next(iter(s)) for h, s in HEAD_TYPE.items() if len(s) == 1}

def mode_of(t: str) -> str:
    return TYPES.get(t, "NON_CLASSE")

# --------------------------------------------------------------------------- #
# Keyword rules: text -> type. One target. Ordered: specific before generic.
# Each pattern encodes object + symptom together, so it can only land on a
# type that exists — no impossible (object, mode) pairs, no patch-ups.
# Patterns run on norm(text): uppercase, accents stripped.
# --------------------------------------------------------------------------- #
_R = lambda p: re.compile(p)
RULES: list[tuple[str, re.Pattern]] = [
    # ---- SELECTION -------------------------------------------------------------
    ("INVERSION_BRANCHEMENT",   _R(r"INVERSION|INVERSE\b|INVERSEE?S?\b|CROISE|INVERTED|SWAPPED|PERMUT")),
    ("ERREUR_BRANCHEMENT",      _R(r"AU LIEU DE|MAUVAISE BORNE|ERREUR (DE )?(BORNE|BRANCHEMENT|CABLAGE|CONNEXION)|"
                                   r"MAUVAIS(E)? (BORNE|BROCHE|PIN)|WRONG (PIN|TERMINAL)")),
    ("ERREUR_REF_ELECTRIQUE",   _R(r"(MAUVAIS(E)?|ERREUR( DE)?) (REF|REFERENCE)[^.]{0,30}(CONTACT|PRISE|CONNECTEUR|DISJONCT|RELAIS|MODULE|VG|COSSE)|"
                                   r"(CONTACT|PRISE|CONNECTEUR|DISJONCT|RELAIS|MODULE VG)[^.]{0,30}(MAUVAIS(E)? REF|ERREUR( DE)? REF)|"
                                   r"AMPERAGE|MAUVAIS CALIBRE|DETROMPAGE|CLE DE CODAGE|POLARISATION|ERGOT")),
    ("ERREUR_REF_HABILLAGE",    _R(r"PLAQUETTE|ERREUR (DE )?REF|MAUVAISE REF|WRONG (REF|PART)|MAUVAIS SENS|MAL ORIENTE|ORIENTATION|A L ?'?ENVERS|"
                                   r"MAUVAISE TAILLE|PAS LA BONNE|INCORRECT PART|DIAMETRE|\bVIS\b[^.]{0,25}TROP\s+(?:COURTE|LONGUE)S?")),   # v4.2: a short screw is a wrong part, not a print defect
    # ---- OMISSION (object-specific first) --------------------------------------
    ("NON_CONNECTE",            _R(r"NON (CONNECTE|BRANCHE|RACCORDE)|PAS (CONNECTE|BRANCHE)|NOT (CONNECTED|PLUGGED)|DISCONNECTED|DECONNECTE")),
    ("OUBLI_VERROUILLAGE",      _R(r"DEVERR?OUILL|NON VERR?OUILL|UNLOCKED|FAUX CONTACT|MAL ENGAGE|MAL EMBOITE|NON CLIPS|PAS CLIPS|NON ENCLIQUET")),
    ("FOD",                     _R(r"\bFOD\b|CORPS ETRANGER|POUSSIERE|BRIN METALLIQUE|COPEAU|LIMAILLE|OUTIL OUBLIE|OBJET OUBLIE")),
    ("MANQUANT_IDENTIFICATION", _R(r"(ETIQUETTE|MARQUAGE|REPERE|REPERAGE|MANCHETTE|FLAMME|PLAQUE|IDENTIFICATION)[^.]{0,25}(MANQU|ABSENT|MQ\b)|"
                                   r"(MANQU|ABSEN)[^.]{0,25}(ETIQUETTE|MARQUAGE|REPERE|MANCHETTE|FLAMME|IDENTIFICATION)")),
    ("MANQUANT_OBTURATION",     _R(r"(OBTURATEUR|BOUCHON|CAPUCHON|CACHE|SACHET|SWITCH GUARD|PROTECTION)[^.]{0,25}(MANQU|ABSENT|MQ\b)|"
                                   r"(MANQU|ABSEN)[^.]{0,25}(OBTURATEUR|BOUCHON|CAPUCHON|CACHE|SACHET|SWITCH GUARD|PROTECTION)")),
    ("MANQUANT_CABLE_ELEMENT",  _R(r"(?:MANQU|ABSEN)[^.]{0,15}FAISCEAUX|(CABLE|FIL|SHUNT|CONTACT|DIODE|RESISTANCE|CONNECTEUR|MODULE)[^.]{0,40}(MANQUANT|MANQUE|NON RECU|NON LIVRE|ABSENT|INTROUVABLE|MQ\b)|"
                                   r"(MANQUANT|MANQUE|NE TROUVE PAS|ABSENCE)[^.]{0,25}(CABLE|FIL|SHUNT|CONTACT|MODULE)|"
                                   r"CABLES? NE .{0,30}(LIVRE|RECU|TROUVE|FOURNI)|\bSHUNT")),
    ("MANQUANT_HABILLAGE",      _R(r"(GAINE|FRETTE|FRET\b|FREIN|COLLIER|TYRAP|VIS\b|ECROU|RONDELLE|ENTRETOISE|CLAMP|SUPPORT|THERMO)[^.]{0,25}(MANQU|ABSENT|MQ\b)|"
                                   r"(MANQU|ABSEN)[^.]{0,25}(GAINE|FRETTE|FRET\b|FREIN|COLLIER|TYRAP|VIS\b|ECROU|RONDELLE|CLAMP|SUPPORT|THERMO)|"
                                   r"MANQUANT|\bMANQUE\b|\bMQ\b|NON RECU|NON LIVRE|OUBLI|MISSING|NOT INSTALLED|NON MONTE|PAS MONTE|NON POSE|NON INSTALLE")),
    # ---- EXECUTION -------------------------------------------------------------
    ("MEO_SERTISSAGE_STANDARD",  _R(r"ARRET DE BLINDAGE")),        # team codes this Q07, must beat 'BLINDAGE' below
    ("MEO_SERTISSAGE_SPECIFIQUE", _R(r"QUADRAX|TWINAX|TRIAX|BUSCAN|\bCOAX|FIBRE OPTIQUE|OPTIQUE|BRASURE|SOUDURE|BLINDAGE|TRESSE(?! DE MASSE)|RACCORD SLIM")),
    ("MEO_SERTISSAGE_STANDARD", _R(r"\bDES?SERTI\w*|\bSERTI\w*|CRIMP|DENUDAGE|MANCHON AUTOSOUD|COSSE|BRINS? (COUPE|CASSE)|"
                                   r"CONTACT A (REFAIRE|CHANGER|REPRENDRE|RESERTIR)|MISE EN OEUVRE (DU )?CONTACT|CONTACT MAL (SERTI|MIS)")),
    ("MEO_METALLISATION",       _R(r"METALLISATION|BONDING|\bBLEU\b|POINT DE MASSE|TRESSE DE MASSE|VASELINE|OXYDATION|REPRISE DE MASSE|MASSE NON CONFORME")),
    ("MESURE_NON_CONFORME",     _R(r"MESURE[^.]{0,30}(NON CONFORME|HORS TOLERANCE|\bNC\b|KO)|RESISTANCE[^.]{0,25}(NON CONFORME|ELEVEE|TROP)|"
                                   r"LINEIQUE|PERTE OPTIQUE|INSERTION LOSS|\bOHMS?\b|VALEUR HORS|HORS TOLERANCE")),
    ("MEO_SERRAGE",             _R(r"TORQU|COUPLE|SERRAGE|DESSERRE|MAL SERRE|NON SERRE|\bLOOSE\b|TROP SERRE|SOUS SERRE|TORQUESEAL|PAS SERRE")),
    ("MEO_FRETTAGE_COLLIER",    _R(r"FREIN|FRET(T?E|T?AGE)|FIL FREIN|LAQUE|POINT DE PEINTURE|NOEUD|CABESTAN|BAND-?IT|COLLIER|TYRAP|CLAMP|"
                                   r"COLLIER (MAL|NON) POSITIONNE|MAL POSE")),
    ("MEO_GAINAGE",             _R(r"GAINE|GAINAGE|BACKSHELL|BACK SHELL|MANCHON|RETREINT|AMALGAMANT|THERMORETRACT|TRESSAGE|CHAUSSETTE|\bEMI\b|"
                                   r"MAL (GAINE|RETREINT)|NON MAINTENU")),
    ("MEO_CHEMINEMENT",         _R(r"CHEMINEMENT|CONTRAINTE|INTERFER|ROUTAGE|EN CONTACT AVEC|FROTTE|CLASH|LISERE|EN TENSION|TENDUS?\b|"
                                   r"VRILLE|PINCE DANS|SUR-?\s?LONGUEURS?\b|SURLONGEUR|MAUVAISE DESTINATION|TROP LACHE|MAL CHEMINE")),   # v4.2: slack left on the harness
    ("MEO_FINITION",            _R(r"NON REPRIS|A REPRENDRE|REPRENDRE FINITION|FINITION (DU|A|NON|DE)|NON TERMINE|PAS FINI|NON FINALISE|"
                                   r"ROUTE NON REPRISE|CABLAGE NON TERMINE|A FINIR|A TERMINER|MARQUAGE (DECALE|ILLISIBLE)")),
    # ---- MANIPULATION ----------------------------------------------------------
    ("DOMMAGE_STRUCTURE",       _R(r"STRUCTURE|PLANCHER|MAIN COURANTE|TUYAUT|COLONNE|RAMPE|PLATINE (ABIME|RAYE|CHOC)|FILETAGE|INSERT ABIME|"
                                   r"IMPACT|CHOC SUR")),
    ("DOMMAGE_CABLE",           _R(r"(CABLE|FIL|FAISCEAU|HARNAIS)[^.]{0,30}(COUPE|ABIME|ENDOMMAG|BLESS|ECRASE|RAYE|DENUDE|PERCE|SECTIONNE)|"
                                   r"(COUPE|ABIME|ENDOMMAG|BLESS|ECRASE|RAYE|DENUDE|PERCE)[^.]{0,30}(CABLE|FIL|FAISCEAU)|"
                                   r"SCRATCH|WIRING DAMAGE|CABLE CUT")),
    ("DOMMAGE_HABILLAGE",       _R(r"(GAINE|MANCHON|ETIQUETTE|COLLIER|BAND-?IT|AMALGAMANT|THERMO|CHAUSSETTE)[^.]{0,25}(ABIME|DECHIRE|ENDOMMAG|CASSE|DECOLLE|ARRACHE)|"
                                   r"(ABIME|DECHIRE|ENDOMMAG|DECOLLE)[^.]{0,25}(GAINE|MANCHON|ETIQUETTE|COLLIER|AMALGAMANT)")),
    ("DOMMAGE_COMPOSANT",       _R(r"CASSE|BRISE|ARRACHE|FISSUR|TORDU|DEFORM|BROKEN|\bHS\b|DEFECTUEU|DEFAILLAN|NE FONCTIONNE|"
                                   r"PAS DE CONTINUITE|MODULE VG|DISJONCTEUR|REMPLACER|\bKNOB\b|BOUTON|ABIME|ENDOMMAG|RAYE")),
    # ---- AMONT -----------------------------------------------------------------
    ("AMONT_IMPRESSION",        _R(r"TROP (COURT|LONG)|SURLONGUEUR|SOUS LONGUEUR|COURT DE L|LONGUEUR|ERREUR (D )?IMPRESSION|JAUGE|"
                                   r"\bG(18|20|22|24)\b|TYPE DE CABLE|RECU (COUPE|ABIME|ENDOMMAGE|PERCE)|HARNESS LENGTH|ILLISIBLE|"
                                   r"(NUMERO|MARQUAGE|REPERAGE)[^.]{0,30}EFFACE|NON LASERIS|NON IMPRIME|MAUVAISE JAUGE|"
                                   r"(?:NE SONT|N.?EST|NE SONT) PAS (?:LASERIS|IMPRIME|MARQUE)|PAS LASERIS|"
                                   r"(?:N°|NUMERO|IDENTIFICATION)[^.]{0,30}NON CONFORM|NON CONFORMITE CONCERNANT SON (?:N|NUMERO|IDENTIFICATION)")),
    # ---- PROCESS ---------------------------------------------------------------
    ("PROCESS_DOSSIER",         _R(r"BADG|TAMPON|TRACABILIT|CT ?176|CT ?129|DOCUMENTATION|FICHE SUIVEUSE|GAMME NON|ORDRE DES OPERATIONS|"
                                   r"GR NON REMPLI|SAISIE OUTILLAGE|\bOF\b NON|SCHEMATIC|PLAN (INCOHERENT|FAUX)")),
]

# Types whose free-keyword recall was measured >= 0.90 on the coded test set.
# Keyword hits on these are MEDIUM; on anything else, LOW. (Set updated by
# the self-test at the bottom of the file; do not edit by hand.)
RELIABLE_KW: frozenset[str] = frozenset({
    "INVERSION_BRANCHEMENT", "ERREUR_BRANCHEMENT", "OUBLI_VERROUILLAGE",
    "MANQUANT_CABLE_ELEMENT", "NON_CONNECTE", "MEO_SERRAGE", "MEO_METALLISATION",
})

# SAP 'Type of nonconformity' -> type. NC-level; used only as a last resort on
# single-defect narrative NCs where the NC-level label is about this one defect.
SAP_PRIOR: dict[str, str] = {
    "MISSING PART/COMPONENT / INCOMPLETE KIT": "MANQUANT_HABILLAGE",
    "PART NOT INSTALLED":                      "MANQUANT_HABILLAGE",
    "HARNESS LENGTH":                          "AMONT_IMPRESSION",
    "ELECTRICAL CRIMPING":                     "MEO_SERTISSAGE_STANDARD",
    "WIRING DAMAGE":                           "DOMMAGE_CABLE",
    "CABLE ROUTING":                           "MEO_CHEMINEMENT",
    "INCORRECT CONNECTOR":                     "ERREUR_REF_ELECTRIQUE",
    "INCORRECT PART FITTED":                   "ERREUR_REF_HABILLAGE",
    "BROKEN":                                  "DOMMAGE_COMPOSANT",
    "CONTACT TWISTED / BROKEN":                "DOMMAGE_COMPOSANT",
    "CONNECTION":                              "ERREUR_BRANCHEMENT",
    "STRUCTURAL AND MECHANICAL ASSEMBLY":      "DOMMAGE_STRUCTURE",
}
SAP_TYPE_RE = re.compile(r"Type of nonconformity\s*:\s*([^\r\n*]+)", re.I)


# --------------------------------------------------------------------------- #
# v4.1 — cable NCs: spec boilerplate, provenance, length and damage statements
#
# Why: cable NCs carry a spec line ("d'une longueur de 220cm", "Type : DR",
# "3161-0665") that used to trigger the length rule on every cable, and pushed
# "câble ... endommagé" beyond the damage-rule window. And "trop court" was
# always read as an upstream print-room defect, even when the text says the
# operator cut it. Rule: a label only moves when the text gives evidence.
# --------------------------------------------------------------------------- #
_SPEC_SUBS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\(?\s*\b\d+\s*(?:CM|MM)\s+MANQUANTS?\s*\)?|\bMANQUE\s+(?:DE\s+)?\d+\s*(?:CM|MM)\b"), " TROP COURT "),
    (re.compile(r"D.?UNE\s+LONGUEUR\s+(?:DE\s+)?:?\s*\d+[.,]?\d*\s*(?:CM|MM|M)?\b"), " "),
    (re.compile(r"\bLONG(?:UEUR)?\s*:?\s*\d+[.,]?\d*\s*(?:CM|MM)?\b|\bLG\s*:?\s*\d+\s*(?:CM|MM)?\b|\bL\s*:?\s*\d+\s*(?:CM|MM)\b|\bL\d+\s*CM\b"), " "),
    (re.compile(r"\bTYPE\s*:?\s*[A-Z]{1,4}\s*\d{0,3}\b|\bJAUGE\s*:?\s*\d+\b"), " "),
    (re.compile(r"\b\d{4}\s?[-–]\s?\d{3,4}\b"), " REF "),
]
def _strip_spec(t: str) -> str:
    for pat, rep in _SPEC_SUBS:
        t = pat.sub(rep, t)
    return re.sub(r"\s+", " ", t)

# Provenance — explicit phrases only.
PROV_RECU = re.compile(
    r"\bRECU(?:E|S|ES|T)?\s+(?:TROP|COUPE|ABIME|ENDOMMAGE|AVEC|NON|SANS|EN\s+MAUVAISE|EN\s+SOUS)|RECEPTIONN|"
    r"\bLIVRES?\s+(?:PAR\s+ERREUR\s+)?(?:TROP|ABIME|ENDOMMAGE|COUPE|SANS|NON|EN\s+MAUVAISE)|"
    r"FOURNIE?S?\s+(?:EN|AVEC|TROP)|\bSERVIE?S?\s+(?:AVEC|EN)|VENANT\s+DE\s+L.?IMPRESSION|DE\s+L.?IMPRESSION|"
    r"RAPID\s?SHARE|FIN\s+DE\s+BOBINE|NON\s+(?:IMPRIME|LASERIS|MARQUE)|PAS\s+(?:ETE\s+)?LIVRE|NON\s+LIVRE|NON\s+RECU|DEBALLAGE|"
    r"\b(?:AVONS|ONT|AVOIR)\s+RECUE?S?\b|\bRECU\s+(?:LE|LES|DES|UN|UNE)\s+CABLE|PAS\s+(?:ETES?\s+)?FOURNIS?|NON\s+FOURNIS?")
PROV_LIGNE = re.compile(
    r"COUPES?\s+(?:TROP\s+)?COURTS?|COUPES?\s+AU\s+MAUVAIS|"
    r"(?:L.?OPERAT(?:EUR|RICE)|LA\s+PROD(?:UCTION)?|LE\s+COMPAGNON|LES\s+OPERATEURS)\s+(?:A|ONT|S.?EST)\s+(?:\w+\s+){0,2}"
    r"(?:COUPES?|ABIMES?|ENDOMMAGES?|PERDUS?|JETES?|MAL|INSTALLES?|OUBLIES?|ARRACHES?|CASSES?|PINCES?|SECTIONNES?)|"
    r"(?<!CONSTATE )(?<!CONSTATEE )(?<!CONSTATES )(?<!SIGNALE )(?<!DETECTE )\bPAR\s+(?:LA\s+)?PROD(?:UCTION)?\b|"
    r"(?<!CONSTATE )(?<!CONSTATEE )(?<!SIGNALE )(?<!DETECTE )\bPAR\s+L.?OPERAT(?:EUR|RICE)|"
    r"MAL\s+CHEMINE|MAUVAIS\s+CHEMINEMENT|ERREUR\s+DE\s+CHEMINEMENT|LORS\s+DU\s+CHEMINEMENT|"
    r"SUITE\s+A\s+(?:UNE?\s+|LA\s+)?(?:RETOUCHE|REPARATION|ERREUR|MAUVAIS)|"
    r"ERREUR\s+DE\s+SERTISSAGE|AU\s+SERTISSAGE|REMISE\s+EN\s+CONFORMITE\s+DU\s+SERTISSAGE|TRAIT\s+DE\s+COUPE|ERREUR\s+DE\s+COUPE|"
    r"COINCE|SUR\s+L.?ARBRE|JETES?\s+A\s+LA|POUBELLE|PERDUS?\s+PAR")
_WEAK_LIGNE = re.compile(r"COUPES?\s+(?:TROP\s+)?COURTS?|COUPES?\s+AU\s+MAUVAIS")
def provenance_strength(text_norm: str, prov: str) -> str:
    if prov == "RECU": return "EXPLICITE"
    if prov == "LIGNE":
        return "EXPLICITE" if PROV_LIGNE.search(_WEAK_LIGNE.sub(" ", text_norm)) else "INDICE"
    return ""

def provenance_of(text_norm: str) -> str:
    r, l = bool(PROV_RECU.search(text_norm)), bool(PROV_LIGNE.search(text_norm))
    if r and not l: return "RECU"
    if l and not r: return "LIGNE"
    return "NON_PRECISE"

# A length defect stated about a CABLE (after spec stripping). Clause-scoped: the
# clause must name a cable/wire (or a cable type code) and no other part, so
# "frette trop longue", "vis trop courte", "gaine trop courte" are left alone.
_SHORT_RE = re.compile(r"RECU(?:E|S|ES|T)?\s+TROP\b(?!\s+(?:ABIME|ENDOMMAGE|TARD|LONG))|TROP\s+COURTE?S?|\bCOURTE?S?\b(?!-?CIRCUIT)|"
                       r"SOUS-?LONGUEUR|RACCOURCI|LONGUEUR\s+(?:INSUFFISANTE|ERRONEE|NON\s+CONFORME)")
_LONG_RE  = re.compile(r"TROP\s+LONGUE?S?|SURLONGUEUR|SUR-LONGUEUR")
_CABLE_OBJ = re.compile(r"\b(?:CABLES?|CABLAGE|FILS?|BIFILAIRES?|TRIFILAIRES?|QUADRAX|"
                        r"(?:DRC?|ADB?|ADC|KL|VN[A-D]|ML[A-C]|DK|QG|BF|WX|MLB|MLA|VNC|DG)\s?\d{1,3})\b")
_OTHER_OBJ = re.compile(r"\b(?:FRET\w*|FRETT\w*|VIS|GAINES?|COLLIERS?|MANCHONS?|TYRAPS?|CLAMPS?|SUPPORTS?|ENTRETOISES?|"
                        r"PLAQUETTES?|RONDELLES?|ECROUS?|THERMO\w*|AMALGAMANT|BACKSHELL|OBTURATEURS?)\b")
_CLAUSE_SPLIT = re.compile(r"[.;*•\n]|\s-\s|\s–\s")
def _cable_length(text_norm: str) -> tuple[str | None, str]:
    """-> ('SHORT'|'LONG'|None, clause). Only clauses about a cable, nothing else."""
    for cl in _CLAUSE_SPLIT.split(text_norm):
        if not _CABLE_OBJ.search(cl) or _OTHER_OBJ.search(cl):
            continue
        if _SHORT_RE.search(cl): return "SHORT", cl
        if _LONG_RE.search(cl):  return "LONG", cl
    return None, ""
LENGTH_RE = _SHORT_RE   # kept for backward reference

# A plain statement that the cable itself is damaged / cut.
_DMG = r"(?:ABIMES?|ENDOMMAGES?|COUPES?|DETERIORES?|SECTIONNES?|CASSES?|BLESSES?|ECRASES?)(?!\s+(?:TROP\s+)?COURT)(?!\s+AU\s+MAUVAIS)"
CABLE_DAMAGE_RE = re.compile(
    r"\b(?:CABLES?|FILS?|FAISCEAUX?|BIFILAIRES?)\b(?:(?!\bQUE\b|\bQU.|GROMMET|PRISE|CONNECTEUR|CONTACT|COSSE|GAINE|MODULE|EQUIPEMENT|BORNIER|PLATINE)[^.]){0,60}?\b(?:EST|SONT|A\s+ETE|ONT\s+ETE|RETROUVES?|RECUS?|LIVRES?|S.?EST)\s+"
    r"(?:\w+\s+)?" + _DMG + r"|"
    r"\b(?:UNS?|DES|DEUX|TROIS|\d+|LES?)\s+(?:CABLES?|FILS?|BIFILAIRES?)\s+(?:REF\s+)?(?:[A-Z]{1,4}\s?\d{1,3}\s+)?" + _DMG + r"|"
    r"\b(?:CABLES?|FILS?|BIFILAIRES?)\s+(?:REF\s+)?(?:[A-Z]{1,4}\s?\d{1,3}\s+)?" + _DMG + r"|"
    r"\b(?:CABLES?|FILS?)\b(?:(?!\bQUE\b|\bQU.|GROMMET|PRISE|CONNECTEUR|CONTACT|COSSE|GAINE|MODULE)[^.]){0,40}?"
    r"(?:A|AVEC|PRESENTE)\s+UN\s+DEFAUT\s+(?:SUR\s+)?(?:L.?|D.?)?ISOLANT|ISOLANT\s+(?:ABIME|ENDOMMAGE|PERCE|DECHIRE)")
# an explicit missing-cable statement keeps priority over a length word in the same text
_MISSING_CABLE_RE = re.compile(r"(?:CABLES?|FILS?|FAISCEAUX)\b[^.]{0,40}(?:MANQUANTS?|MANQUE|NON\s+RECUS?|NON\s+LIVRES?|ABSENTS?|INTROUVABLES?|PAS\s+(?:ETES?\s+)?FOURNIS?)")

SELECTION_TYPES = {"INVERSION_BRANCHEMENT", "ERREUR_BRANCHEMENT", "ERREUR_REF_ELECTRIQUE", "ERREUR_REF_HABILLAGE"}

def _cable_state(text_norm: str, prov: str, allowed: tuple[str, ...] | None) -> str | None:
    """Cable length / cable damage statements. Runs after SELECTION rules, before the rest."""
    def ok(tp): return allowed is None or tp in allowed
    if _MISSING_CABLE_RE.search(text_norm):
        return None
    kind, clause = _cable_length(text_norm)
    if kind == "SHORT" or (kind == "LONG" and prov == "RECU"):
        if prov == "RECU":
            tp = "AMONT_IMPRESSION"
        elif prov == "LIGNE":
            tp = "MEO_SERTISSAGE_STANDARD" if re.search(r"SERTISS", text_norm) else "MEO_CHEMINEMENT"
        else:
            tp = "AMONT_IMPRESSION"          # v4 default; confidence stays LOW (origin not stated)
        if ok(tp): return tp
    if CABLE_DAMAGE_RE.search(text_norm):
        if prov == "RECU":
            tp = "AMONT_IMPRESSION"
        elif re.search(r"DENUDAGE|PINCE\s+A\s+DENUDER|SERTISS", text_norm):
            tp = "MEO_SERTISSAGE_STANDARD"   # damage caused by stripping/crimping: report the cause
        else:
            tp = "DOMMAGE_CABLE"
        if ok(tp): return tp
    return None


def _kw(text_norm: str, allowed: tuple[str, ...] | None = None, prov: str | None = None) -> str | None:
    t = _strip_spec(text_norm)
    if prov is None:
        prov = provenance_of(t)
    pre_done = False
    for typ, pat in RULES:
        if not pre_done and typ not in SELECTION_TYPES:
            pre_done = True
            cs = _cable_state(t, prov, allowed)
            if cs:
                return cs
        if allowed is not None and typ not in allowed:
            continue
        if pat.search(t):
            if typ == "DOMMAGE_CABLE" and prov == "RECU" and (allowed is None or "AMONT_IMPRESSION" in allowed):
                return "AMONT_IMPRESSION"                            # arrived damaged = upstream
            return typ
    return None


def classify(d: Defect) -> Defect:
    """Resolve type_reporting, mode_erreur, confidence, resolved_by."""
    t = norm(d.text)
    head = (d.code or "").upper()[:3]
    typ = None
    _ts = _strip_spec(t)
    d.provenance = provenance_of(_ts)
    d.provenance_force = provenance_strength(_ts, d.provenance)
    _k, _ = _cable_length(_ts)
    d.etat_cable = "LONGUEUR" if _k else ("DOMMAGE" if CABLE_DAMAGE_RE.search(_ts) else "")

    if d.sub_code and d.sub_code in SUBCODE_TYPE:                   # 1
        typ, d.confidence, d.resolved_by = SUBCODE_TYPE[d.sub_code], "HIGH", "SUBCODE"
        d.severite_off = "MAJEURE" if d.sub_code in SUBCODE_MAJEURE else "MINEURE"
    elif head in HEAD_TYPE:                                          # 2
        typ, d.confidence, d.resolved_by = HEAD_TYPE[head], "HIGH", "HEADCODE"
    elif head in HEAD_CANDIDATES:                                    # 3
        typ = _kw(t, HEAD_CANDIDATES[head], d.provenance)
        if typ:
            d.confidence, d.resolved_by = "MEDIUM", "HEAD+KW"
        else:                                                        # head known, object not: mode is still certain
            typ = HEAD_CANDIDATES[head][0]
            d.confidence, d.resolved_by = "LOW", "HEAD_DEFAULT"
    else:
        typ = _kw(t, None, d.provenance)                             # 4 / 5
        if typ:
            d.confidence = "MEDIUM" if typ in RELIABLE_KW else "LOW"
            d.resolved_by = "KW"
            if typ in ("AMONT_IMPRESSION", "MEO_CHEMINEMENT", "DOMMAGE_CABLE") and d.provenance != "NON_PRECISE":
                d.confidence = "MEDIUM"                               # object and origin both stated
        elif d.sap_type and d.source_format in ("narrative", "fal_single"):   # 6
            p = SAP_PRIOR.get(norm(d.sap_type).strip())
            if p:
                typ, d.confidence, d.resolved_by = p, "LOW", "SAP_PRIOR"

    if typ is None:                                                  # 7
        typ, d.confidence, d.resolved_by = "AUTRE", "NONE", "-"
    d.type_reporting = typ
    d.mode_erreur = mode_of(typ)
    d.cable_preuve = cable_signal(d.text)                            # v4.2, independent of the type
    d.defaut_cable = bool(d.cable_preuve)
    return d


# =========================================================================== #
# v4.2 — IS IT A CABLE NC?  (binary, orthogonal to type_reporting)
#
# A defect is a cable defect when a cable itself has to be re-made or
# re-supplied: MISSING, SHORT, DAMAGED/CUT, or wrongly PRINTED (marking, gauge).
# A good cable that is badly routed, on the wrong pin, not crimped, left with
# slack, or missing its gaine/frette is NOT: it is fixed on the line with the
# same cable. Cable = wire, bifilaire, trifilaire, quadrax, fibre, or a shunt
# with a cable number; recognised by word, type code (AD24, DR22, KL24...) or
# cable number (2792-0936).
#
# Evidence, strongest first:
#   DEMANDE  a new cable is asked for (re-fabrication, à changer, à commander...)
#   ETAT     the cable is stated missing / short / damaged / misprinted
#   SPEC     a cable number with a length: only written to order a (re)print
#
# NC level (parse_nc -> nc_cable):  CABLE = every defect is a cable defect
# (the NCs the cable team logs), MIXTE = a test / final-inspection list with
# at least one cable line, NON = none.
#
# What the text cannot know (join these in the pipeline, not here):
#   - SAP status / decision: deleted NCs and "TCLO, câbles OK" still read as cable NCs;
#   - twins: a test NC and the NC raised to request the same cable are two NCs
#     for one event (same cable number or FIN, a few days apart).
# =========================================================================== #
_CBL_WORD = r"(?:CABLES?|FIBRES?|FILS?(?!\s+(?:A\s+)?FREIN)|BI-?\s?FILAIRES?|TRI-?\s?FILAIRES?|QUADRAX|SHUNTS?(?!\s+MECA))"
_CBL_TYPE = r"(?:ADB?|ADC|DRB?|DRC|KL|VN[A-D]|ML[A-C]|DK|QG|BF|WX|WJ|DG|MMG)\s?\d{1,3}"
_CBL_NUM  = r"\d{4}\s?-\s?\d{3,4}[A-Z]?"
_CBL_OBJ  = re.compile(rf"(?:\b{_CBL_WORD}\b|\b{_CBL_TYPE}\b|\b{_CBL_NUM}\b)")

_C_MISSING = (r"(?:MANQUANTE?S?|MAQUANTE?S?|\bMANQUE\b|\bMQ\b|NON\s+RECUE?S?|NON\s+LIVREE?S?|PAS\s+(?:ETE\s+)?LIVREE?S?|"
              r"N.?ONT\s+PAS\s+ETE\s+LIVRE|ABSENTE?S?|INTROUVABLES?|NON\s+FOURNIE?S?|PAS\s+(?:ETE\s+)?FOURNIE?S?|PERDUE?S?|JETEE?S?)")
_C_SHORT   = (r"(?:TROP\s+COURTE?S?|\bCOURTE?S?\b(?!-?\s?CIRCUIT)|SOUS-?\s?LONGUEUR|(?:RECUE?S?|LIVREE?S?)\s+(?:PAR\s+ERREUR\s+)?TROP\b|"
              r"LONGUEUR\s+(?:INSUFFISANTE|NON\s+CONFORME|ERRONEE))")
_C_DAMAGE  = (r"(?:ABIMEE?S?|ABIMER|ENDOMMAGEE?S?|DETERIOREE?S?|SECTIONNEE?S?|ENTAILLEE?S?|CASSEE?S?|BLESSEE?S?|ECRASEE?S?|PERCEE?S?|"
              r"COUPEE?S?\b|AME\s+APPARENTE|DEFAUT\s+D.?ISOLANT|ISOLANT\s+(?:ABIME|ENDOMMAGE|PERCE|DECHIRE))")
_C_PRINT   = (r"(?:NON\s+IMPRIMEE?S?|PAS\s+(?:ETE\s+)?IMPRIMEE?S?|NON\s+LASERISEE?S?|PAS\s+(?:ETE\s+)?LASERISEE?S?|ILLISIBLES?|"
              r"MAUVAISE\s+[JC]H?AUGE|MAUVAIS\s+TYPE|ERREUR\s+D.?IMPRESSION|MAL\s+IMPRIMEE?S?|"
              r"NON\s+CONFORMITE\s+CONCERNANT\s+SON|MAUVAIS\s+SENS)")
_C_STATE   = rf"(?:{_C_MISSING}|{_C_SHORT}|{_C_DAMAGE}|{_C_PRINT})"

_C_REMAKE = re.compile(
    r"RE\s?-?\s?FABRI\w*|REFABRI\w*|\bFABRICATION\s+DES?\s+CABLES?|NOUVEAU\s+CABLE|"
    r"REMPLACEMENT\s+(?:DU|DES|DE\s+CES?)\s+(?:\w+\s+){0,2}CABLES?|REMPLACER\s+(?:LE|LES|CE|CES)\s+CABLES?|"
    rf"(?:{_CBL_WORD}|{_CBL_NUM})[^.]{{0,40}}\bA\s+(?:COMMANDER|CHANGER|REMPLACER)\b|"
    r"COMMANDER\s+(?:UN|LE|LES|CES|DES)?\s*(?:NOUVEAUX?\s+)?CABLES?|CHANGER\s+(?:LE|LES|CE|CES)\s+(?:\d+\s+)?CABLES?|"
    rf"(?:{_CBL_WORD}|{_CBL_NUM})[^.]{{0,40}}\b(?:DOIT|DOIVENT)\s+ETRE\s+(?:CHANGEE?S?|REMPLACEE?S?|REFAITE?S?)|"
    r"REEDITER|REIMPRIM\w*|FOURNIR\s+UN\s+CABLE|APPROVISIONNEMENT\s+DES?\s+(?:\w+\s+){0,2}CABLES?|"
    r"MISE\s+A\s+DISPOSITION\s+DES\s+CABLES|RECOMMANDER\s+L.?ENSEMBLE\s+DES\s+CABLES|"
    r"RELANCER\s+LA\s+FABRICATION\s+DU\s+HARNAIS|CABLE\s+DEJA\s+COMMANDE")

# The state belongs to another object when that object sits between the cable and
# the state word, or right before/after it ("contact manquant câble ...",
# "manque la gaine sur le câble", "cerises manquantes sur les câbles").
_C_OTHER = (r"(?:GAINES?|FRETT?\w*|TYRAPS?|COLLIERS?|CERISES?|RUBAN|AMALGAMANT|\bVIS\b|CONTACTS?|OBTURATEURS?|MANCHONS?|"
            r"THERMO\w*|GROMMETS?|PLAQUETTES?|ETIQUETTES?|BACKSHELL|CLAMPS?|SUPPORTS?|EQUIPEMENTS?|PRISES?|CONNECTEURS?|"
            r"BOUCHONS?|CAPUCHONS?|AUTO-?\s?SOUDEURS?|MODULES?|ENCODER|ARRET\s+DE\s+BLINDAGE)")
_C_GAP = rf"(?:(?!{_C_OTHER}|\bQUE\b|\bQU.)[^.;*]){{0,70}}?"
_C_CABLE_THEN_STATE = re.compile(rf"(?:\b{_CBL_WORD}\b|\b{_CBL_TYPE}\b|\b{_CBL_NUM}\b){_C_GAP}{_C_STATE}")
_C_STATE_THEN_CABLE = re.compile(rf"(?:{_C_MISSING}|{_C_DAMAGE}|{_C_PRINT})\s+(?:(?!{_C_OTHER})\w+\s+){{0,2}}?"
                                 rf"(?:(?:UN|LE|LES|DES|DEUX|TROIS|\d+)\s+)?(?:\b{_CBL_WORD}\b|\b{_CBL_TYPE}\b|\b{_CBL_NUM}\b)")
_C_SPEC_LEN = re.compile(rf"\b{_CBL_NUM}\b[^.*]{{0,60}}?(?:\b\d{{2,4}}\s?CM\b|LONG\w*\s*:?\s*\d|\bLG\s*:?\s*\d|\bL\s?[:-]?\s?\d{{2,4}}\b)|"
                         rf"(?:LONG\w*|\bLG|\bL)\s*[:-]?\s*\d{{2,4}}\s?(?:CM)?[^.*]{{0,40}}?\b{_CBL_NUM}\b")
_C_NOT = re.compile(r"SUR-?\s?LONGUEUR|EN\s+TENSION|TENDUS?\b|CLASH|MAUVAIS\s+CHEMINEMENT\s+D.UN|DOUBLE\s+SORTI|"
                    r"A\s+DEPOSER|AU\s+LIEU\s+DE\s+(?:\d|LA\s+BORNE|BORNE)|NON\s+SERTI|"
                    r"MANQUE\s+(?:LA\s+|LE\s+|LES\s+)?(?:GAINE|FRETTE|TYRAP|RUBAN)")
_C_OTHER_STATE = re.compile(rf"\b{_C_OTHER}\s+(?:\w+\s+){{0,2}}?{_C_STATE}")
_C_STATE_OTHER = re.compile(rf"{_C_MISSING}\s+(?:(?:LA|LE|LES|DES|UN|UNE|DE|\d+)\s+|L.)?{_C_OTHER}")


def cable_signal(text: str) -> str:
    """'' if this defect is not a cable defect, else its evidence: DEMANDE | ETAT | SPEC."""
    t = re.sub(r"\s+", " ", norm(text if isinstance(text, str) else ""))
    if not _CBL_OBJ.search(t):
        return ""
    if _C_REMAKE.search(t):
        return "DEMANDE"
    c = _C_NOT.sub(" ", t)
    c = _C_STATE_OTHER.sub(" ", c)
    c = _C_OTHER_STATE.sub(" ", c)
    if _C_CABLE_THEN_STATE.search(c) or _C_STATE_THEN_CABLE.search(c):
        return "ETAT"
    if _C_SPEC_LEN.search(t):
        return "SPEC"
    return ""


def nc_cable_of(flags: list[bool]) -> str | None:
    """NC level from its defects' flags: CABLE | MIXTE | NON (None when there is no defect)."""
    if not flags:
        return None
    n = sum(bool(f) for f in flags)
    return "NON" if n == 0 else ("CABLE" if n == len(flags) else "MIXTE")



# =========================================================================== #
# PUBLIC API
# =========================================================================== #

def parse_nc(raw_text: str) -> dict:
    """One NC in -> {'nb_defauts': int|None, 'is_redacted': bool, 'flags': [...],
    'nc_cable': 'CABLE'|'MIXTE'|'NON'|None, 'nb_defauts_cable': int|None, 'defects': [...]}"""
    if raw_text is None or REDACTED_MARKER in str(raw_text):
        return {"nb_defauts": None, "is_redacted": True, "flags": ["REDACTED"], "defects": [],
                "nc_cable": None, "nb_defauts_cable": None}
    sap = SAP_TYPE_RE.search(str(raw_text))
    sap_type = sap.group(1).strip() if sap else None
    defects = split_defects(raw_text)
    for d in defects:
        d.sap_type = sap_type
        classify(d)
    nb = sum(d.qty for d in defects)
    flags = []
    if defects and defects[0].source_format == "template_v1":
        flags.append("TEMPLATE_V1")
        tot = TPL_TOTAL_RE.search(clean_text(raw_text))
        if tot and int(tot.group(1)) != nb:
            flags.append(f"TOTAL_MISMATCH(declared={tot.group(1)},parsed={nb})")
    return {"nb_defauts": nb, "is_redacted": False, "flags": flags,
            "nc_cable": nc_cable_of([d.defaut_cable for d in defects]),
            "nb_defauts_cable": sum(d.qty for d in defects if d.defaut_cable),
            "defects": [asdict(d) for d in defects]}


def apply_cable_tracker(defects_df, tracker_df, nc_col="notification_number"):
    """Use the cable team's analysed Imputation where our text gives no origin.

    tracker_df: the 'Suivi NCs - NC câbles et analyses' sheet (columns 'NC',
    'Motifs', 'Imputation'). Returns a copy of defects_df with:
      tracker_motif, tracker_imputation  — the team's labels, for reference
      provenance_source                  — TEXTE | TRACKER | "" 
      provenance_conflict                — True when our text is explicit and
                                           contradicts the team: review, don't overwrite
    Only keyword-resolved defects that state the cable's own length/damage are
    re-derived; head-coded defects and everything else are left untouched.
    """
    import pandas as pd
    df = defects_df.copy()
    tr = tracker_df.copy()
    tr.columns = [str(c).strip().replace("\n", " ") for c in tr.columns]
    tr["_nc"] = tr["NC"].astype(str).str.strip().str.lstrip("0")
    tr = tr.dropna(subset=["NC"]).drop_duplicates("_nc")
    imp2prov = lambda s: ("RECU" if str(s).startswith("Salle impression") else
                          "LIGNE" if str(s).startswith("Production") else "")
    tmap = dict(zip(tr["_nc"], zip(tr["Motifs"], tr["Imputation"])))
    df["_nc"] = df[nc_col].astype(str).str.lstrip("0")
    df["tracker_motif"] = df["_nc"].map(lambda n: tmap.get(n, (None, None))[0])
    df["tracker_imputation"] = df["_nc"].map(lambda n: tmap.get(n, (None, None))[1])
    df["provenance_source"] = df["provenance"].where(df["provenance"].isin(["RECU", "LIGNE"]), "").map(lambda x: "TEXTE" if x else "")
    df["provenance_conflict"] = False
    for i, r in df[df["tracker_imputation"].notna()].iterrows():
        tp = imp2prov(r["tracker_imputation"])
        if not tp or r.get("resolved_by") not in ("KW", "HEAD+KW") or r.get("etat_cable") not in ("LONGUEUR", "DOMMAGE"):
            continue
        if r["type_reporting"] not in ("AMONT_IMPRESSION", "MEO_CHEMINEMENT", "DOMMAGE_CABLE", "MEO_SERTISSAGE_STANDARD"):
            continue                                          # the type came from another rule (e.g. missing cable): leave it
        if r["provenance"] in ("RECU", "LIGNE") and r.get("provenance_force") == "EXPLICITE":
            if r["provenance"] != tp:
                df.at[i, "provenance_conflict"] = True       # both sides explicit: bring it back to the team
            continue
        # our text is silent (or only "coupé trop court"): take the team's analysis
        df.at[i, "provenance"], df.at[i, "provenance_source"] = tp, "TRACKER"
        if r["etat_cable"] == "LONGUEUR":
            new = "AMONT_IMPRESSION" if tp == "RECU" else (
                  "MEO_SERTISSAGE_STANDARD" if "SERTISS" in norm(str(r["text"])) else "MEO_CHEMINEMENT")
        else:
            new = "AMONT_IMPRESSION" if tp == "RECU" else r["type_reporting"]
            if tp == "LIGNE" and new == "AMONT_IMPRESSION":
                new = "DOMMAGE_CABLE"
        df.at[i, "type_reporting"], df.at[i, "mode_erreur"] = new, mode_of(new)
        df.at[i, "confidence"] = "MEDIUM"
    return df.drop(columns="_nc")


def explode_dataframe(df, text_col="description_long_text",
                      id_col="notification_number", manual_count_col=None):
    """Returns (nc_df, defects_df): NC-level counts + one row per defect."""
    import pandas as pd
    parsed = df[text_col].apply(parse_nc)
    nc_df = df.copy()
    nc_df["nb_defauts"]  = parsed.apply(lambda p: p["nb_defauts"])
    nc_df["is_redacted"] = parsed.apply(lambda p: p["is_redacted"])
    nc_df["flags"]       = parsed.apply(lambda p: ";".join(p.get("flags", [])))
    nc_df["nc_cable"]    = parsed.apply(lambda p: p["nc_cable"])          # v4.2: count cable NCs on == "CABLE"
    nc_df["nb_defauts_cable"] = parsed.apply(lambda p: p["nb_defauts_cable"])
    nc_df["nb_defauts_final"] = nc_df["nb_defauts"]
    if manual_count_col and manual_count_col in nc_df:
        nc_df.loc[nc_df["is_redacted"], "nb_defauts_final"] = \
            nc_df.loc[nc_df["is_redacted"], manual_count_col]
    rows = [{id_col: nc_id, **d} for nc_id, p in zip(df[id_col], parsed) for d in p["defects"]]
    return nc_df, pd.DataFrame(rows)


if __name__ == "__main__":
    import sys, pandas as pd
    df = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "aaf.txt", low_memory=False)
    nc_df, dd = explode_dataframe(df, manual_count_col="Ext_Nb_Defauts")
    print(f"{len(df)} NCs -> {len(dd)} defects\n")
    print("MODE -> TYPE (tree):")
    print(dd.groupby(["mode_erreur", "type_reporting"]).size().to_string())
    print("\nConfidence:"); print(dd["confidence"].value_counts().to_string())
    print("\nResolved by:"); print(dd["resolved_by"].value_counts().to_string())
    print("\nCable NCs (v4.2):"); print(nc_df["nc_cable"].value_counts(dropna=False).to_string())
