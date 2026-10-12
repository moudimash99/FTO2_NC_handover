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

v4.3 (septembre 2026) — Pareto categories by what has to be fixed
-----------------------------------------------------------------
  * New column `categorie`: one of 18 categories named after the thing the
    operator has to fix (tie-wraps, sleeves, routing, plates, bonding, screws...),
    replacing the old "Workmanship" / "Installation" buckets, which mixed
    different work steps and pointed to no action. See CATEGORIES.
  * Order of the rules: cable flag first ("cable wins"), then wiring errors,
    unlocked connectors, not connected and FOD from type_reporting; then the
    object named in the text; then type_reporting as a fallback.
  * Wiring-typed defects that name no electrical item (e.g. "backshell à 180°
    au lieu de 0°", "inversion des plaquettes", "20A au lieu de 25A") are no
    longer counted as wiring errors: 770 -> 744 on the 876 FTO2 NCs.
  * categorie is a pure function of (type_reporting, defaut_cable, text), so it
    can be recomputed on any past output with categorie_of().
  * explode_dataframe() now repeats the NC's nc_cable on every defect row, so
    SQL can count cable NCs without a second table.

v4.4 (septembre 2026) — Pareto families
---------------------------------------
  * New column `famille`: the level the Pareto shows (8 families + Autres), with
    `categorie` kept underneath as the drill-down. See FAMILLES.
  * "Screws & torque" is split in two, following the official severities:
    "Loose electrical connection" (backshell, lug, terminal: Q05-001, severity 8)
    and "Screws & mechanical fixing" (Q05-002 and the like, severity 4).

v4.5 (octobre 2026) — Pareto groups, the way the line talks
-----------------------------------------------------------
  * New columns `groupe` and `sous_groupe` (drill-down). The Pareto now shows what
    happened: Branchement (inversion, erreur, déverrouillage, non connecté),
    Câblage (mise en œuvre + wrong part or position), Dommage & manquant,
    Métallisation (everything bonding), then Amont, FOD, Dossier and Non classé
    on their own. See GROUPES.
  * Cable defects are no longer one bar: they follow what happened to the cable
    (missing/damaged, cut short on the line, arrived short or misprinted).
  * groupe is a pure function of (type_reporting, categorie). `famille` is kept
    for the MFT topics.

v4.6 (octobre 2026) — sub-categories aligned on the official code sheet
-----------------------------------------------------------------------
  * Every official sub-code (123) belongs to exactly one Pareto sub-category and
    one RCA type (SOUS_CATEGORIES, reference_table()). Approved exceptions: E1
    câble à refaire (ligne), E2 composant cassé / HS / cause non écrite, E3 câble
    reçu abîmé and E4 câble non fourni -> Amont.
  * A written code always wins; otherwise the text decides (souscat_of), and a
    cause written in the text wins over its consequence.
  * New columns: souscat_source, rca_type, rca_mode. groupe / sous_groupe now come
    from the sub-category. type_reporting, categorie and famille are unchanged.

v4.7 (octobre 2026) — checked against an independent labelling of every defect
-------------------------------------------------------------------------------
  * Rule fixes from the approved tie-breaks: harness not held / pinched in its
    collar = Q06-001; "rajouter / mettre une frette", "non tyrapé" = missing collar;
    "finir la mise en oeuvre" = unfinished; plate loose / to place = Q06-010;
    collar to re-orient / align, tyraps instead of frettes = Q04; serre-modules =
    Q05-002; breaker rating, installed vs required reference = Q04-005; VT-bar
    module reference and plate lots delivered non-conforming = Q12; platine /
    capot damaged = structure; badging, OF entries, SI, drawing = Dossier; a blue
    marker / ribbon is identification, not bonding; ground lugs badly tightened =
    Q05-001; déverrouillage typos and pushed-back pins = Q01.
  * No more "Non classé": when the text decides nothing, the parser guesses from a
    few words, then the SAP type, then defaults to Cheminement
    (souscat_source = DEVINE).
  * New column mineur: Manquant – colliers (tyrap, frette, ficelle) and
    Manquant – obturateurs / bouchons (caps, cerises, plugs).
"""

from __future__ import annotations
import re
import unicodedata
import sys as _sys
import types as _types
from dataclasses import dataclass, field, asdict

# When this file is pasted into a notebook or a Code Workbook's global code
# instead of being imported, register it as a module: dataclasses need it.
if __name__ not in _sys.modules:
    _sys.modules[__name__] = _types.ModuleType(__name__)

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
    categorie: str = ""          # v4.3: Pareto category, what has to be fixed (see CATEGORIES)
    famille: str = ""            # v4.4: Pareto family, one level above categorie (see FAMILLES)
    groupe: str = ""             # v4.6: Pareto group (see GROUPES)
    sous_groupe: str = ""        # v4.6: Pareto sub-category, a fixed set of official sub-codes (see SOUS_CATEGORIES)
    souscat_source: str = ""     # v4.6: SOUS-CODE | CODE | CODE+TEXTE | TEXTE | DEVINE (v4.7: guessed)
    rca_type: str = ""           # v4.6: RCA sub-category of that sub-category
    rca_mode: str = ""           # v4.6: RCA category (mode) of that type
    mineur: bool = False         # v4.7: a small thing forgotten (tyrap / frette / ficelle, cap / cerise / plug)
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
    d.categorie = categorie_of(d.type_reporting, d.defaut_cable, d.text)   # v4.3
    d.famille = famille_of(d.categorie)                                     # v4.4
    d.sous_groupe, d.souscat_source = souscat_of(d.text, d.code, d.sub_code, d.type_reporting, d.categorie,
                                                 d.defaut_cable, d.etat_cable, d.provenance, None, d.sap_type)   # v4.6
    d.groupe = groupe_of_souscat(d.sous_groupe)
    d.rca_type = rca_type_of(d.sous_groupe)
    d.rca_mode = mode_of(d.rca_type)
    d.mineur = est_mineur(d.sous_groupe)
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
# v4.3 — PARETO CATEGORIES: what has to be fixed
#
# One category per defect, named after the object or work step the fix is
# assigned to. Listed in the order a Pareto usually shows them; the first three
# are the MFT topics and win over everything else ("cable wins", then wiring,
# then unlocked connectors).
# =========================================================================== #
CATEGORIES = {
    "Cable problems":                "A cable must be remade or re-supplied: missing, too short, damaged or cut, misprinted.",
    "Wiring errors":                 "A wire on the wrong pin, or two wires or connectors swapped.",
    "Connectors not locked":         "A connector or contact left unlocked (déverrouillé, CDVE, liseré apparent).",
    "Tie-wraps & clamps":            "Frettes, tyraps, colliers, lacote supports: missing, loose, too long, too small; harness not attached.",
    "Sleeves & protection":          "Gaines, thermo, chaussettes, amalgamant, manchons, protections: missing, loose, not held in the backshell.",
    "Routing & harness dressing":    "Path of the harness or wires: clash, tension, over-length, bend radius, wires out of the bundle.",
    "Plates, labels & markers":      "Plaquettes, étiquettes, datum markers, serial numbers: missing, upside down, torn, unreadable, off-centre.",
    "Bonding":                       "Métallisation: bonding blue missing or smeared, bonding measurement out of tolerance, ground braids.",
    "Screws & mechanical fixing":    "Vis, écrous, rondelles, serre-modules, visserie: missing, wrong length, not torqued; mechanical parts loose.",
    "Loose electrical connection":   "Backshell, connector, lug (cosse), terminal or breaker not tightened or loose.",
    "Plugs & caps":                  "Obturateurs, bouchons, capuchons, cerises, switch guards: missing or badly fitted.",
    "Contacts & crimping":           "Sertissage, contacts, cosses, auto-soudeurs, soldering: bad crimp, strand out, contact to redo.",
    "Wrong part or position":        "Wrong reference fitted (module, connector, breaker rating), keying error, part mounted in the wrong orientation or place.",
    "Damaged equipment":             "An equipment or part broken, scratched or damaged (switch, backshell, relay socket, fourreau, rail).",
    "Faulty or non-conforming part": "Equipment that does not work (HS, out of tolerance, continuity), or a part received that does not match the drawing.",
    "Structure & paint":             "Damaged structure (rampes, rivets, colonnettes, piping) or missing or damaged paint.",
    "FOD":                           "Foreign object debris.",
    "Not connected":                 "A connector or wire left unconnected.",
    "Other":                         "None of the above: documentation, harness length, unfinished work, empty or unclear text.",
}

_CR = lambda p: re.compile(p)
_CAT_DAMAGED = _CR(r"CASSEE?S?\b|\bABIMEE?S?\b|ABIMER\b|ENDOM+AGE\w*|ENDOM+AGEMENT|DETERIORE\w*|\bRAYEE?S?\b|RAILLEE?S?|RAYURES?|"
                   r"FISSURE\w*|TORDUE?S?\b|DEFORM\w*|ARRACHE\w*|ECRASEE?S?\b|\bIMPACTS?\b|\bGOUGE|SCRAPE|SCAPE|DECHIRE\w*|"
                   r"BRISE\w*|FENDUE?S?\b|\bDAMAGED\b")
_CAT_FAULTY = _CR(r"\bHS\b|H\.S\b|HORS\s+TOLERANCE|CONTINUITE|NE\s+FONCTIONNE|MAUVAIS\s+FONCTIONNEMENT|DEFAUT\s+D.?ISOL|"
                  r"DEFAUT\s+DE\s+RESISTANCE|COURT.?CIRCUIT|\bPANNES?\b|\bKO\b|\b[TA]LB\b|\bQSR\b|\bINOP|TRIPPING|DEFECTUEU\w*|"
                  r"NE\s+(?:SE\s+)?VERROUILLE\s+PAS|ENFICHAGE|PARVIENNENT\s+PAS\s+A\s+VERROUILLER|DISPARITE")
_CAT_SUPPLIED = _CR(r"\bFOURNIE?S?\b|LIVREE?S?\s+PAR\s+LE\s+FOURNISSEUR|NE\s+CORRESPONDENT\s+PAS|NON\s+CONFORMES?\s+AU\s+PLAN|"
                    r"DOC\w*\s+DECLARATIF|TROU\S*\s+DE\s+FIXATION|TROP\s+(?:PETITE?S?|COURTE?S?)\s+POUR|A\s+RECEPTION|"
                    r"LORS\s+DE\s+LA\s+RECEPTION|\bINCOMING\b|RECUE?S?\s+AVEC|DEFAUT\s+DE\s+TRAITEMENT")
_CAT_RECEIVED = _CR(r"RECUE?S?\s+AVEC|NOUS\s+AVONS\s+RECUE?\s+UN\s+LOT|A\s+RECEPTION|LORS\s+DE\s+LA\s+RECEPTION|\bINCOMING\b|"
                    r"LIVREE?S?\s+PAR\s+LE\s+FOURNISSEUR|NE\s+CORRESPONDENT\s+PAS")
_CAT_STRUCT = _CR(r"RAMPES?\b|STRUCTURE|TUYAUT\w*|RIVET|\bDZUS|COLONNETTE|PANNEAU|CLOISON|PLANCHER|PEINTURE|BIELLE")
_CAT_ELEC = _CR(r"BORNE|CABLE|\bFILS?\b|BRANCH|CONNECT|PRISE|\bPIN\b|CONTACT|SHUNT|POSITION|VOYANT|MODULE|BIFILAIRE|QUADRAX|"
                r"INDICATEUR|DISJONCTEUR")
_CAT_WIRING_KW = _CR(r"INVERSION\s+(?:DES|DE)\s+(?:PRISES|CONNECTEURS|BRANCHEMENTS?|CABLES|FILS)|"
                     r"BORNE\s*\S*[^.]{0,60}(?:ALORS\s+QUE|AU\s+LIEU\s+DE)")

# Objects named in the text, in priority order (first match wins).
_CAT_OBJECTS = [
    ("Connectors not locked", _CR(r"LISERES?\s+(?:ROUGES?\s+)?APPARENTS?")),
    ("Plates, labels & markers", _CR(r"DATUM|FLAMMES?\s+(?:\(\s*)?(?:DE\s+POSITIONNEMENT|BLEUE?S?|D.IDENTIFICATION)|"
        r"(?:RE)?CENTRER\s+(?:LA\s+|LES\s+)?PLAQUETTE|PLAQUETTES?\s+(?:\S+\s+){0,3}?(?:A\s+L.ENVERS|A\s+(?:RE)?CENTRER|"
        r"MANQUANTES?|DECHIREES?|ILLISIBLES?|EFFACEES?)|ERREUR\s+DE\s+MANCHON|MANCHONS?\s+REPERES?")),
    ("Bonding", _CR(r"METALLI|METALISATION|BONDING|TRESSES?\s+DE\s+MASSE|MESURES?\s+DE\s+MASSE|"
        r"(?:MANQU\w*|OUBLI\w*|REPRENDRE|SOUILLEE?S?\s+PAR|POSE\w*|PAS\s+DE)\s+(?:(?:DU|DE|LE|LES|DES)\s+)?BLEUS?\b|"
        r"\bBLEUS?\s+(?:MANQUANTS?|A\s+REPRENDRE|DE\s+(?:METALLISATION|PROTECTION))|"
        r"\bBLEUS?\b[^.]{0,25}\b(?:SOUS|SUR)\s+(?:LES?\s+|LA\s+|DES\s+)?(?:RONDELLE|VIS|PLATINE|ECROU)")),
    ("Routing & harness dressing", _CR(r"CLASH|RAYON\s+DE\s+COURBURE|SUR-?\s?LONGUEUR|SURLONGEUR|TROP\s+TENDUE?S?|EN\s+TENSION|"
        r"FROTT\w*|\bCONTACT\s+(?:ENTRE|AVEC)|EN\s+CONTRAINTE|(?:FAISCEAU|HARNAIS)\s+LACHE|"
        r"(?:MAUVAIS|REPRENDRE\s+(?:LE\s+)?|ERREUR\s+(?:DE\s+)?(?:SENS\s+)?)\s*CHEMINEMENT|"
        r"CHEMINEMENT\s+(?:A\s+REPRENDRE|NON\s+CONFORME|INCORRECT)|SORTIE?S?\s+(?:DE|DES|DU)\s+(?:CABLES?|HARNAIS)|"
        r"MAUVAISE?\s+SORTIE?|DOUBLE\s+SORTI|REPRENDRE\s+LA\s+SORTIE|\bTORON|MISE\s+AU\s+PROPRE|"
        r"MISE\s+EN\s+O?E?UVRE\s+DES?\s+HARNAIS|REPRENDRE\s+(?:LE\s+)?CABLAGE|CABLAGE\s+NON\s+CONFORME|RESSORT\s+DU")),
    ("Screws & torque", _CR(r"COSSES?\s+(?:NON|MAL)\s+SERREE?S?|FRANGIBLE")),
    ("Screws & torque", _CR(r"\bVIS\b|VISSERIE|ECROUS?\b|RONDELLES?|BOULON|\bDZUS|SERRE.?MODULES?|ARRET\s+DE\s+MODULE|TARAUD|"
        r"ENTRETOISE|\bINSERT\s+ASNA|FASTENER")),
    ("Tie-wraps & clamps", _CR(r"FRETT|FRETES?\b|\bFRET\b|TYRAP|TY-RAP|COLLIERS?\b|LAC+OT+E|ATTACHE\w*|SERRE-?\s?CABLE|\bCLAMPS?\b")),
    ("Plugs & caps", _CR(r"OBTURAT|BOUCHONS?\b|CAPUCHON|CERISE|SWITCH\s+GUARD")),
    ("Contacts & crimping", _CR(r"AUTO-?\s?SOUDEUR")),
    ("Sleeves & protection", _CR(r"GAINES?\b|THERMO|CHAUSSETTE|AMALGAMANT|MANCHONS?\b|RUBAN|GROMMET|TRAIT\s+APPARENT|POCHETTE|"
        r"\bPROTECTIONS?\b|EMI\s+SLEEV")),
    ("Plates, labels & markers", _CR(r"PLAQUETTE|ETIQUETTE|MARQUAGE|\bREPERES?\b|NUMERO\s+DE\s+SERIE|N.?\s?DE\s+SERIE|\bS/N\b|"
        r"IDENTIFICATION|EFFACEE?S?")),
    ("Wrong part or position", _CR(r"MAUVAIS\s+CONTACT")),
    ("Contacts & crimping", _CR(r"SERTI|(?<!EN )\bCONTACTS?\b|COSSES?\b|SOUDURE|DENUD|\bBRINS?\b|FERRULE")),
    ("Wrong part or position", _CR(r"DETROMPAGE|ORIENT\w*|MAUVAISE?\s+(?:REFERENCE|MODULE|CONNECTEUR|PRISE|MONTAGE|EQUIPEMENT|PIECE)|"
        r"ERREUR\s+(?:DE\s+)?(?:REFERENCE|MODULE|MONTAGE)|INVERSION\s+DE\s+MONTAGE|"
        r"REFERENCE\s+(?:DU|DE)\s+\w+\s+(?:N.EST\s+PAS|NON)\s+CONFORME|AU\s+LIEU\s+D|SENS\s+DES\s+PRISES|REPRENDRE\s+LE\s+SENS|"
        r"A\s+L.ENVERS|MAL\s+(?:POSITIONNEE?S?|PLACEE?S?|MONTEE?S?|INSEREE?S?)|"
        r"MONTAGE\s+(?:DE\s+LA\s+|DU\s+|DES\s+)?\S+(?:\s+\S+){0,2}\s+(?:EST\s+)?INCORRECT")),
    ("Screws & torque", _CR(r"TORQU|SERRAGE|DESSERR|NON\s+SERREE?S?|MAL\s+SERREE?S?")),
]
# A damage word on these objects means the part itself is damaged.
_CAT_DAMAGE_OVERRIDES = {"Wrong part or position", "Contacts & crimping", "Screws & torque"}
# When the text names no object, the type decides.
_CAT_TYPE_FALLBACK = {
    "MEO_FRETTAGE_COLLIER": "Tie-wraps & clamps", "MEO_GAINAGE": "Sleeves & protection",
    "MEO_CHEMINEMENT": "Routing & harness dressing", "MEO_SERRAGE": "Screws & torque", "MEO_METALLISATION": "Bonding",
    "MEO_SERTISSAGE_STANDARD": "Contacts & crimping", "MEO_SERTISSAGE_SPECIFIQUE": "Contacts & crimping",
    "MANQUANT_OBTURATION": "Plugs & caps", "MANQUANT_IDENTIFICATION": "Plates, labels & markers",
    "ERREUR_REF_ELECTRIQUE": "Wrong part or position", "ERREUR_REF_HABILLAGE": "Wrong part or position",
}


def _cat_norm(text: str) -> str:
    t = str(text if isinstance(text, str) else "").replace("Œ", "OE").replace("œ", "oe")
    return re.sub(r"\s+", " ", norm(t))


def _cat_equipment(x: str) -> str:
    return "Damaged equipment" if _CAT_DAMAGED.search(x) else "Faulty or non-conforming part"


def _cat_object(x: str) -> str | None:
    if _CAT_RECEIVED.search(x) and not _CAT_DAMAGED.search(x) and "PEINTURE" not in x:
        return "Faulty or non-conforming part"                       # arrived wrong: upstream / supplier
    for cat, pat in _CAT_OBJECTS:
        if pat.search(x):
            if cat in _CAT_DAMAGE_OVERRIDES and _CAT_DAMAGED.search(x):
                return "Damaged equipment"
            if cat in ("Contacts & crimping", "Wrong part or position") and _CAT_FAULTY.search(x) \
                    and not re.search(r"SERTI|PINCE|OUTIL", x):
                return "Faulty or non-conforming part"
            return cat
    return None


def _categorie_raw(type_reporting: str, defaut_cable, text: str) -> str:
    """Category before the v4.4 split of "Screws & torque"."""
    t = type_reporting or ""
    x = _cat_norm(text)
    if str(defaut_cable).strip().lower() in ("true", "1", "t"):
        return "Cable problems"
    if t in ("INVERSION_BRANCHEMENT", "ERREUR_BRANCHEMENT"):
        obj = None if _CAT_ELEC.search(x) else _cat_object(x)
        return obj or "Wiring errors"                                 # "au lieu de" on a plate or a breaker rating is not wiring
    if t == "OUBLI_VERROUILLAGE":
        return "Connectors not locked"
    if t == "NON_CONNECTE":
        return "Bonding" if re.search(r"BONDING|METALLI|MASSE", x) else "Not connected"
    if t == "FOD":
        return "FOD"
    if t == "PROCESS_DOSSIER":
        return "Other"
    if _CAT_WIRING_KW.search(x):
        return "Wiring errors"
    if t == "DOMMAGE_STRUCTURE":
        if not (_CAT_DAMAGED.search(x) or _CAT_SUPPLIED.search(x) or "PEINTURE" in x):
            obj = _cat_object(x)
            if obj in ("Routing & harness dressing", "Tie-wraps & clamps", "Screws & torque"):
                return obj
        if not _CAT_STRUCT.search(x):
            return _cat_equipment(x)
        if _CAT_SUPPLIED.search(x) and not _CAT_DAMAGED.search(x) and "PEINTURE" not in x:
            return "Faulty or non-conforming part"
        return "Structure & paint"
    if t == "DOMMAGE_COMPOSANT" or (t == "DOMMAGE_CABLE" and (_CAT_FAULTY.search(x) or _CAT_DAMAGED.search(x)
                                                             or re.search(r"A\s+CHANGER|REMPLACER", x))):
        return _cat_equipment(x)
    obj = _cat_object(x)
    if obj:
        return obj
    if "PEINTURE" in x:
        return "Structure & paint"
    if _CAT_FAULTY.search(x) or _CAT_SUPPLIED.search(x):
        return "Faulty or non-conforming part"
    if _CAT_DAMAGED.search(x):
        return "Structure & paint" if _CAT_STRUCT.search(x) else "Damaged equipment"
    if t in _CAT_TYPE_FALLBACK:
        return _CAT_TYPE_FALLBACK[t]
    if re.search(r"\bREPLACE\b|REMPLACE", x):
        return "Faulty or non-conforming part"
    return "Other"


# v4.4 — "Screws & torque" is split by severity on the official sheet: a loose
# electrical connection (Q05-001, severity 8, RPN 480) is not a loose screw (Q05-002, 4).
_CAT_TIGHTEN = _CR(r"TORQU|SERRAGE|DESSERR|NON\s+SERREE?S?|MAL\s+SERREE?S?")
_CAT_ELEC_PART = _CR(r"BACK\s?-?SHELL|\bBORNES?\b|CONNECTEUR|\bPRISES?\b|DISJONCTEUR|RACCORD|\bCOSSES?\b|CONTACTEUR|\bVG\b")
_CAT_MECH_PART = _CR(r"SERRE.?MODULE|\bVIS\b|VISSERIE|FRANGIBLE|ECROUS?\b|RONDELLE")


def categorie_of(type_reporting: str, defaut_cable, text: str) -> str:
    """Pareto category of one defect (one of CATEGORIES)."""
    cat = _categorie_raw(type_reporting, defaut_cable, text)
    if cat != "Screws & torque":
        return cat
    x = _cat_norm(text)
    if _CAT_TIGHTEN.search(x) and _CAT_ELEC_PART.search(x) and not _CAT_MECH_PART.search(x):
        return "Loose electrical connection"
    return "Screws & mechanical fixing"


# v4.4 — PARETO FAMILIES: the level the Pareto shows. Each family groups the
# categories fixed by the same people, against the same standard, at about the
# same severity. The three MFT topics are families of one category each.
FAMILLES = {
    "Branchement":                     ["Wiring errors"],
    "Câbles":                          ["Cable problems"],
    "Déverrouillage":                  ["Connectors not locked"],
    "Mise en œuvre harnais":           ["Tie-wraps & clamps", "Routing & harness dressing", "Sleeves & protection", "Plugs & caps"],
    "Identification":                  ["Plates, labels & markers"],
    "Pièces":                          ["Wrong part or position", "Damaged equipment", "Faulty or non-conforming part"],
    "Fixation & métallisation":        ["Bonding", "Screws & mechanical fixing", "Structure & paint"],
    "Sertissage & serrage électrique": ["Contacts & crimping", "Loose electrical connection"],
    "Autres":                          ["FOD", "Not connected", "Other"],
}
_FAMILLE_OF = {c: f for f, cats in FAMILLES.items() for c in cats}


def famille_of(categorie: str) -> str:
    """Pareto family of a category (one of FAMILLES)."""
    return _FAMILLE_OF.get(categorie, "Autres")


# =========================================================================== #
# v4.6 — PARETO SUB-CATEGORIES ALIGNED ON THE OFFICIAL CODE SHEET
#
# Every official sub-code (123) belongs to exactly one Pareto sub-category, and
# every sub-category to one Pareto group and one RCA sub-category (type). A
# sub-category can hold several sub-codes. Approved exceptions (one sub-code
# split by a written rule):
#   E1  Q06-001: a cable too short / cut too short to remake, origin not "received"
#       -> "Câble à refaire (ligne)"; the rest of Q06-001 -> "Cheminement – longueur / tension"
#   E2  Q11 component: broken / doesn't work (HS) / cause not written -> three sub-categories
#   E3  a cable received damaged -> Amont · Câble   (only when no code is written)
#   E4  a missing cable that was never supplied -> Amont · Câble   (only when no code is written)
# Labelling: a written sub-code or head code always wins. Without one, the text
# decides; when one text describes a cause and its consequence ("câble trop court
# suite à une inversion"), the defect takes the cause.
# =========================================================================== #
def _rng(head, a, b):
    return [f"{head}-{i:03d}" for i in range(a, b + 1)]


# label: (group, RCA type, official sub-codes, exception note)
SOUS_CATEGORIES = {
    "Inversion":                               ("Branchement", "INVERSION_BRANCHEMENT", ["T04"], ""),
    "Erreur de branchement":                   ("Branchement", "ERREUR_BRANCHEMENT", ["T02"], ""),
    "Déverrouillage":                          ("Branchement", "OUBLI_VERROUILLAGE", _rng("Q01", 1, 3), ""),
    "Non connecté":                            ("Branchement", "NON_CONNECTE", ["T05"], ""),
    "Frettage / colliers – pose":              ("Câblage", "MEO_FRETTAGE_COLLIER", ["Q05-004", "Q06-006", "Q06-011", "Q06-012"], ""),
    "Serrage électrique":                      ("Câblage", "MEO_SERRAGE", ["Q05-001", "Q05-005"], ""),
    "Serrage mécanique":                       ("Câblage", "MEO_SERRAGE", ["Q05-002", "Q05-003"], ""),
    "Cheminement – longueur / tension":        ("Câblage", "MEO_CHEMINEMENT", ["Q06-001"], ""),
    "Câble à refaire (ligne)":                 ("Câblage", "MEO_CHEMINEMENT", [], "E1: part of Q06-001"),
    "Cheminement – clash":                     ("Câblage", "MEO_CHEMINEMENT", ["Q06-004", "Q06-005"], ""),
    "Gainage / protection":                    ("Câblage", "MEO_GAINAGE", ["Q06-002", "Q06-003", "Q06-007", "Q06-008"], ""),
    "Identification – positionnement":         ("Câblage", "MEO_FINITION", ["Q06-010"], ""),
    "Câblage non terminé":                     ("Câblage", "MEO_FINITION", ["Q06-009"], ""),
    "Sertissage":                              ("Câblage", "MEO_SERTISSAGE_STANDARD", _rng("Q07", 1, 10), ""),
    "Sertissage spécifique":                   ("Câblage", "MEO_SERTISSAGE_SPECIFIQUE", _rng("Q08", 1, 7), ""),
    "Mesure hors tolérance":                   ("Câblage", "MESURE_NON_CONFORME", ["T06", "T08", "T08-CDVE"], ""),
    "Mauvaise réf. – colliers / frettage":     ("Câblage", "ERREUR_REF_HABILLAGE", ["Q04-007", "Q04-008", "Q04-014"], ""),
    "Mauvaise réf. – identification":          ("Câblage", "ERREUR_REF_HABILLAGE", ["Q04-013"], ""),
    "Mauvaise réf. – mécanique":               ("Câblage", "ERREUR_REF_HABILLAGE", ["Q04-003", "Q04-006"], ""),
    "Mauvaise réf. – obturation / thermo":     ("Câblage", "ERREUR_REF_HABILLAGE", ["Q04-001", "Q04-002", "Q04-010", "Q04-012"], ""),
    "Mauvaise réf. – électrique / détrompage": ("Câblage", "ERREUR_REF_ELECTRIQUE", ["Q04-004", "Q04-005", "Q04-009", "Q04-011"], ""),
    "Manquant – colliers":                     ("Dommage & manquant", "MANQUANT_HABILLAGE", ["Q03-006"], ""),
    "Manquant – gaine / thermo":               ("Dommage & manquant", "MANQUANT_HABILLAGE", ["Q03-002", "Q03-010"], ""),
    "Manquant – mécanique / freinage":         ("Dommage & manquant", "MANQUANT_HABILLAGE", ["Q03-003", "Q03-005"], ""),
    "Manquant – obturateurs / bouchons":       ("Dommage & manquant", "MANQUANT_OBTURATION", ["Q03-001", "Q03-007", "Q03-008"], ""),
    "Manquant – câble / shunt / élément":      ("Dommage & manquant", "MANQUANT_CABLE_ELEMENT", ["Q03-004", "T01", "T03"], ""),
    "Manquant – identification":               ("Dommage & manquant", "MANQUANT_IDENTIFICATION", ["Q03-009", "Q03-011", "Q03-012"], ""),
    "Dommage – câble":                         ("Dommage & manquant", "DOMMAGE_CABLE", ["Q11-001", "Q11-014"], ""),
    "Dommage – composant cassé":               ("Dommage & manquant", "DOMMAGE_COMPOSANT",
                                                ["Q11-003", "Q11-005", "Q11-006", "Q11-012", "Q11-016", "Q11-018", "Q11-019"], ""),
    "Composant HS":                            ("Dommage & manquant", "DOMMAGE_COMPOSANT", [], "E2: part of Q11 component codes"),
    "Composant – cause non écrite":            ("Dommage & manquant", "DOMMAGE_COMPOSANT", [], "E2: part of Q11 component codes"),
    "Dommage – tresse de masse":               ("Dommage & manquant", "DOMMAGE_COMPOSANT", ["Q11-009", "Q11-022"], ""),
    "Dommage – identification":                ("Dommage & manquant", "DOMMAGE_HABILLAGE", ["Q11-002"], ""),
    "Dommage – habillage":                     ("Dommage & manquant", "DOMMAGE_HABILLAGE",
                                                ["Q11-004", "Q11-007", "Q11-008", "Q11-010", "Q11-011", "Q11-013", "Q11-026"], ""),
    "Dommage – structure":                     ("Dommage & manquant", "DOMMAGE_STRUCTURE", _rng("Q10", 1, 6), ""),
    "Bleu non appliqué":                       ("Métallisation", "MEO_METALLISATION", ["Q09-001", "Q09-004"], ""),
    "Bleu mal appliqué / débordant":           ("Métallisation", "MEO_METALLISATION", ["Q09-002", "Q09-005"], ""),
    "Point de masse / mesure":                 ("Métallisation", "MEO_METALLISATION", ["Q09-003", "Q09-006", "T07", "T07-CDVE"], ""),
    "Amont · Câble":                           ("Amont", "AMONT_IMPRESSION", _rng("Q12", 1, 4) + ["Q12-007", "Q12-008"],
                                                "E3 (received damaged) and E4 (never supplied) also land here"),
    "Amont · Identification / barrette VT":    ("Amont", "AMONT_IMPRESSION", ["Q12-005", "Q12-006"], ""),
    "Dossier":                                 ("Dossier", "PROCESS_DOSSIER", _rng("Q13", 1, 5), ""),
    "FOD":                                     ("FOD", "FOD", _rng("Q16", 1, 6), ""),
    "Non classé":                              ("Non classé", "AUTRE", [], "no code written and nothing usable in the text"),
}
GROUPES = ["Branchement", "Câblage", "Dommage & manquant", "Métallisation", "Amont", "FOD", "Dossier", "Non classé"]
SUBCODE_TO_SOUSCAT = {sc: lab for lab, (_, _, scs, _) in SOUS_CATEGORIES.items() for sc in scs}
_HEAD_OF = lambda sc: sc[:3]
# sub-categories allowed under each written head code (exceptions E1/E2 stay inside their head)
HEAD_SOUSCATS = {}
for _lab, (_g, _t, _scs, _note) in SOUS_CATEGORIES.items():
    for _sc in _scs:
        HEAD_SOUSCATS.setdefault(_HEAD_OF(_sc), [])
        if _lab not in HEAD_SOUSCATS[_HEAD_OF(_sc)]:
            HEAD_SOUSCATS[_HEAD_OF(_sc)].append(_lab)
HEAD_SOUSCATS["Q06"].append("Câble à refaire (ligne)")
HEAD_SOUSCATS["Q11"] += ["Composant HS", "Composant – cause non écrite"]

# --- text features --------------------------------------------------------- #
_S = lambda p: re.compile(p)
_F_CAUSE = _S(r"(?:CAUSE\s*:|SUITE\s+A|APRES|A\s+CAUSE\s+D|DUE?S?\s+A|EN\s+RAISON\s+D|CONSECUTI\w*\s+A)\s*(?:UNE?\s+|L.\s?|LA\s+|LE\s+|LES\s+|DES?\s+|DU\s+)?")
_F_CAUSE_OF = [   # cause named after "suite à / après ..." -> sub-category of the cause
    ("Amont · Câble",          _S(r"MARQUAGES?\s+DEF+ECTUEUX|MAUVAIS\s+MARQUAGE|NON\s+LASERIS|NON\s+IMPRIM|ERREUR\s+D.?IMPRESSION")),
    ("Inversion",              _S(r"INVERSIONS?\s+(?:DE\s+|DES\s+)?(?:BRANCHEMENT|CABLE|FIL|BORNE|PRISE)|INVERSIONS?\b(?!\s+D.?ATA)")),
    ("Erreur de branchement",  _S(r"(?:ERREUR|MAUVAIS)\s+(?:DE\s+)?BRANCHEMENT")),
    ("Sertissage",             _S(r"(?:ERREUR\s+DE|MAUVAIS)\s+(?:SERTISSAGE|DENUDAGE)")),
    ("Mauvaise réf. – mécanique", _S(r"(?:L.)?UTILISATION\s+D.UNE?\s+(?:VIS|ECROU|RONDELLE)\w*\s+NON\s+CONFORME|"
                                     r"MAUVAISE\s+ORIENTATION\s+D[UE]S?\s+(?:SUPPOR|EQUERR|BARRETT|RAIL)")),
    ("Cheminement – longueur / tension", _S(r"(?:ERREUR\s+DE|MAUVAIS)\s+CHEMINEMENT")),
]
_F_TOOL_DMG = [   # damage caused by a named operation, written in the same text
    ("Frettage / colliers – pose", _S(r"(?:FRETT?ES?|COLLIERS?|TYRAPS?)\s+TROP\s+SERREE?S?")),
    ("Serrage électrique",         _S(r"(?:ABIME|ENDOMMAGE|CASSE)\w*\s+LORS\s+DU\s+(?:TORQUAGE|SERRAGE)|LORS\s+DU\s+(?:TORQUAGE|SERRAGE)")),
    ("Sertissage",                 _S(r"PAR\s+LA\s+PINCE\s+A\s+DENUDER|LORS\s+DU\s+DENUDAGE")),
]
_F_DMG = _S(r"CASSEE?S?\b|\bABIMEE?S?\b|ABIMER\b|ENDOM+AGE\w*|DETERIOR\w*|\bRAYEE?S?\b|RAILLEE?S?|RAYURES?|FISSURE\w*|TORDUE?S?\b|"
            r"DEFORM\w*|ARRACHE\w*|ECRASEE?S?\b|\bIMPACTS?\b|SCRAPE|DECHIRE\w*|BRISE\w*|FENDUE?S?\b|\bDAMAGED\b|BROKEN|ENTAILLE\w*|"
            r"SECTIONNE\w*|PERCEE?S?\b|BLESSEE?S?\b|SOUILLEE?S?|EFFACEE?S?|GOUGE\w*|\bBENT\b")
_F_HS = _S(r"\bHS\b|H\.S\b|DEFAUT\s+D.?ISOL|CONTINUITE|NE\s+FONCTIONNE|MAUVAIS\s+FONCTIONNEMENT|NE\s+(?:SE\s+)?VE?R+OUILLE\s+PAS|PARVIEN\w*\s+PAS\s+A\s+VE?R+OUILLER|DEFAUT\s+(?:DE\s+)?RESISTANCE|INTERMIT+EN|SE\s+BLOQUE|"
           r"ENFICHAGE|COURT.?CIRCUIT|PASSANTE|HORS\s+TOLERANCE|\bKO\b|\bINOP|DEFECTUEU\w*|FAUX\s+CONTACT|NE\s+S.?ALLUME|PANNE")
_F_MISS = _S(r"MANQUANTE?S?|MAQUANTE?S?|\bMANQUE\b(?!\s+DE\s+(?:SERRAGE|PLACE|TENSION|COUPLE|LONGUEUR))|MANQUAIT|\bOUBLI\w*|ABSENTE?S?\b|"
             r"NON\s+POSEE?S?|NON\s+RENSEIGNEE?S?|\bAJOUTER\b|INCOMPLETE?S?|A\s+METTRE\s+SOUS\s+(?:POCHETTE|BOUCHON|CAPUCHON)|PAS\s+DE\s+(?:FRETTE|COLLIER|TYRAP|GAINE|BLEU|OBTURATEUR|BOUCHON|PLAQUETTE|ETIQUETTE)|N.EST\s+PLUS\s+PRESENTE?|"
             r"\bRAJOUTER\b|METTRE\s+(?:UNE?|DES|LES)\s+(?:FRETTES?|TYRAPS?|COLLIERS?)|LIER\s+PAR\s+(?:UNE?|DES)\s+FRETTES?|NON\s+TYRAPEE?S?|"
             r"PAS\s+D.INDICATION|A\s+FRETTER\s+ENSEMBLE|\bFRETTER\s+(?:LES\s+)?ROUTES?|NON\s+MARQUEE?S?")
_F_NOT_SUPPLIED = _S(r"LORS\s+DE\s+LA\s+RECEPTION\s+DES\s+CABLES|A\s+LA\s+RECEPTION\s+DES\s+CABLES|PAS\s+(?:ETES?\s+)?FOURNIE?S?|NON\s+FOURNIE?S?|NON\s+LIVREE?S?|PAS\s+(?:ETE\s+)?LIVREE?S?|NON\s+RECUE?S?|"
                     r"MANQUANTE?S?\s+A\s+LA\s+RECEPTION")
_F_BLEU = _S(r"\bBLEUS?\b|METALLI|METALISATION|BONDING|MASSE")
_F_BRAID = _S(r"TRESSES?")
_F_MEASURE = _S(r"MESURE|RESISTANCE|HORS\s+TOLERANCE|PERTE\s+D.?INSERTION|M\s?OHM|MILLI\s?OHM")
_F_PLATE = _S(r"PLAQUETTE|ETIQUETTE|DATUM|FLAMMES?|\bREPERES?\b|MANCHONS?\s+REPERE|\bS/N\b|N.?\s?DE\s+SERIE|NUMERO\s+DE\s+SERIE|"
              r"IDENTIFICATION|SCELLE|INVIOLABILITE")
_F_POSITION = _S(r"DEPLAC\w*|A\s+PLACER|PLIEE?\s+SOUS|A\s+L.ENVERS|DECALEE?S?|(?:RE)?CENTR\w*|MAL\s+POSITIONN\w*|POSITIONN\w*|PLACEMENT|MAL\s+PLACEE?S?|MAUVAIS\s+COTE|"
                 r"A\s+FIXER|MAL\s+ATTACHEE?S?|NON\s+MAINTENUE?S?|TIENT\s+PAR|TOURNER|ORIENT\w*|SENS\b")
_F_WRONGREF = _S(r"MAUVAISE?\s+(?:REFERENCE|REF\b|MODULE|CONNECTEUR|PRISE|EQUIPEMENT|PIECE|VIS|CONTACT|CALIBRE|TAILLE)|"
                 r"ERREUR\s+(?:DE\s+)?(?:REFERENCE|REF\b|MODULE|GAUGE|JAUGE|MANCHON|D.?ETIQUETTE|DETROMPAGE)|AU\s+LIEU\s+D|"
                 r"N.EST\s+PAS\s+LA\s+BONNE|NOTEE?\s+EN\s+FAIT|TROP\s+(?:PETITE?S?|GRANDE?S?)|A\s+ADAPTER\s+AU|RIVETS?\s+NON\s+CONFORMES?|REMPLACER\s+(?:LES\s+)?TYRAPS?\s+PAR|TYRAPS?\s+A\s+REMPLACER\s+PAR|TROP\s+(?:COURTE?S?|LONGUE?S?)|INVERSION\s+(?:DE\s+MONTAGE|DES\s+PLAQUETTES|DE\s+MANCHON)|"
                 r"INVERSIONS?\s+(?:DE|DES)\s+(?:PLAQUETTES?|ETIQUETTES?|REPERES?|MANCHONS?)|REFERENCE\s+D[UE]S?\s+[^.]{0,40}(?:N.EST\s+PAS|NON)\s+(?:LA\s+BONNE|CONFORME)|DETROMP\w*|MONTEE?S?\s+A\s+L.ENVERS|ORIENT\w*|REFERENCE\s+(?:DU|DE)\s+\w+\s+(?:N.EST\s+PAS|NON)\s+CONFORME|EN\s+LIEU\s+ET\s+PLACE|MAUVAISE\s+IDENTIFICATION")
_F_COLLAR = _S(r"FRETT|FRETES?\b|\bFRET\b|TYRAP|TY-RAP|COLLIERS?\b|LAC+OT+E|ATTACHE\w*|SERRE-?\s?CABLE|\bCLAMPS?\b|BAND-?IT")
_F_SLEEVE = _S(r"GAINES?\b|THERMO|CHAUSSETTE|AMALGAMANT|MANCHONS?\b|RUBAN|TRAIT\s+APPARENT|POCHETTE|\bPROTECTIONS?\b|EMI\s+SLEEV|GROMMET")
_F_PLUG = _S(r"OBTURAT|BOUCHONS?\b|CAPUCHON|CERISE|SWITCH\s+GUARD|POCHETTE")
_F_MECH = _S(r"\bVIS\b|FASTENER|\bRING\b|WASHER|\bNUTS?\b|SCREW|\bBOLTS?\b|VISSERIE|ECROUS?\b|RONDELLES?|BOULON|\bDZUS|SERRE.?MODULES?|ARRET\s+DE\s+MODULE|ENTRETOISE|\bINSERT\b|FREIN\w*|"
             r"FRANGIBLE|COLONNETTE|EQUERRE|SUPPORT|BARRETTE|RAIL\b|HELICOIL|FILETAGE|TARAUD")
_F_ELEC = _S(r"BACK\s?-?SHELL|BAGUES?\s+ARRIERE|\bBORNES?\b|CONNECTEUR|\bPRISES?\b|DISJONCTEUR|RACCORD|\bCOSSES?\b|CONTACTEUR|\bVG\b|RELAIS|MODULE|"
             r"VOYANT|INTERRUPTEUR|SWITCH|PUSH|DIODE|RESISTANCE|SOCLE|EQUIPEMENT|BOUTON")
_F_CABLEOBJ = _S(r"\b(?:CABLES?|FILS?|BIFILAIRES?|TRIFILAIRES?|QUADRAX|SHUNTS?|FIBRES?)\b|\b\d{4}\s?-\s?\d{3,4}\b")
_F_SHUNT_ELEC = _S(r"SHUNTS?|\bDIODES?\b|\bCONTACTS?\b|CONNECTEUR|\bMODULES?\b|\bBORNES?\b|\bPRISES?\b|BACKSHELL|ELEMENT")
_F_STRUCT = _S(r"RAMPES?\b|STRUCTURE|TUYAUT\w*|RIVET\w*|COLONNETTE|PANNEAU|CLOISON|PLANCHER|PEINTURE|BIELLE|PLATINE|FILETAGE|TARAUD\w*|"
               r"HELICOIL|\bINSERT\b|MAIN\s+COURANTE|\bTOLE\b")
_F_TIGHT = _S(r"TORQU|SERRAGE|\bTOURNE\b|DESSERR|NON\s+SERREE?S?|MAL\s+SERREE?S?|PAS\s+SERREE?S?|\bLACHE|JEU\b|BOUGE")
_F_CLASH = _S(r"CLASH|\bCONTACT\s+(?:ENTRE|AVEC)|EN\s+CONTACT|FROTT\w*|TOUCHE")
_F_ROUTE = _S(r"CHEMINEMENT|TENSION|TENDUE?S?|SUR-?\s?LONGUEUR|SURLONGEUR|SOUS-?\s?LONGUEUR|RAYON\s+DE\s+COURBURE|TORON|"
              r"SORTIE?S?\s+(?:DE|DES|DU)|RESSORT\s+DU|MOINS\s+MOBILE|HARNAIS\s+(?:TROP|LACHE|NON\s+MAINTENU)|TROP\s+COURTE?")
_F_CRIMP = _S(r"SERTI|DENUD|\bBRINS?\b|SOUDURE|AUTO-?\s?SOUDEUR|FERRULE|\bCOSSES?\b|\bCONTACTS?\b|PINCE")
_F_CRIMP_SPEC = _S(r"QUADRAX|TWINAX|TRIAX|COAX|FIBRE|OPTIQUE|BRASURE|BUSCAN")
_F_UNFINISHED = _S(r"NON\s+TERMINE|NON\s+REPRIS|REPRENDRE\s+(?:LE\s+)?CABLAGE|NON\s+FINI|A\s+FINIR|FINIR\s+(?:LE|LA)\b|A\s+TERMINER|"
                   r"CABLAGE\s+NON\s+CONFORME")
_F_RECEIVED = _S(r"RECUE?S?\s+AVEC|NOUS\s+AVONS\s+RECUE?\s+UN\s+LOT|A\s+RECEPTION|LORS\s+DE\s+LA\s+RECEPTION|\bINCOMING\b|"
                 r"LIVREE?S?\s+PAR\s+LE\s+FOURNISSEUR|FOURNISSEUR|NE\s+CORRESPONDENT\s+PAS|\bQSR\b|\b[TA]LB\b|DATE\s+CODE")
_F_PRINT = _S(r"NON\s+LASERIS|PAS\s+(?:ETE\s+)?LASERIS|NON\s+IMPRIM|PAS\s+(?:ETE\s+)?IMPRIM|MAL\s+IMPRIM|ERREUR\s+D.?IMPRESSION|ILLISIBLE|"
              r"MAUVAISE?\s+(?:JAUGE|GAUGE|CALIBRE)|ERREUR\s+DE\s+(?:JAUGE|GAUGE)|MAUVAIS\s+TYPE|EFFACE\w*|MARQUAGE")

_BRANCH_FROM_TYPE = {"INVERSION_BRANCHEMENT": "Inversion", "ERREUR_BRANCHEMENT": "Erreur de branchement",
                     "OUBLI_VERROUILLAGE": "Déverrouillage", "NON_CONNECTE": "Non connecté"}
_DEFAULT_OF_HEAD = {"Q01": "Déverrouillage", "Q03": "Manquant – mécanique / freinage", "Q04": "Mauvaise réf. – électrique / détrompage",
                    "Q05": "Serrage électrique", "Q06": "Cheminement – longueur / tension", "Q07": "Sertissage",
                    "Q08": "Sertissage spécifique", "Q09": "Bleu mal appliqué / débordant", "Q10": "Dommage – structure",
                    "Q11": "Composant – cause non écrite", "Q12": "Amont · Câble", "Q13": "Dossier", "Q16": "FOD",
                    "T01": "Manquant – câble / shunt / élément", "T02": "Erreur de branchement", "T03": "Manquant – câble / shunt / élément",
                    "T04": "Inversion", "T05": "Non connecté", "T06": "Mesure hors tolérance", "T07": "Point de masse / mesure",
                    "T08": "Mesure hors tolérance"}


def _missing_object(x, t, c, cable):
    if _F_BLEU.search(x) and not _F_CABLEOBJ.search(x) and c in ("Bonding", "", "Other") or re.search(r"(?:MANQU\w*|OUBLI\w*|PAS)\s+(?:DE\s+|DU\s+|LE\s+)?BLEU", x):
        return "Bleu non appliqué"
    if re.search(r"(?:MANQU\w*|\bMQ\b|OUBLI\w*)\s+(?:\w+\s+){0,2}?(?:ENTRETOISES?|\bVIS\b|ECROUS?|RONDELLES?|FIL\s+FREIN|FREINAGE|INSERTS?)|"
                 r"(?:ENTRETOISES?|\bVIS\b|ECROUS?|RONDELLES?|FIL\s+FREIN|INSERTS?)\s+MANQU|SWITCH\s+GUARD", x):
        return "Manquant – mécanique / freinage"
    if cable or t == "MANQUANT_CABLE_ELEMENT" and not (_F_COLLAR.search(x) or _F_SLEEVE.search(x) or _F_PLUG.search(x) or _F_PLATE.search(x)):
        return "Manquant – câble / shunt / élément"
    if re.search(r"(?:MANQU\w*|OUBLI\w*)\s+(?:L.\s?|LES?\s+|D.\s?)?(?:IDENTIFICATION|MARQUAGE|INDICATION)|NON\s+MARQUEE?S?|NON\s+IDENTIFIEE?S?", x):
        return "Manquant – identification"
    if _F_PLUG.search(x) or t == "MANQUANT_OBTURATION":
        return "Manquant – obturateurs / bouchons"
    if _F_COLLAR.search(x) and not re.search(r"(?:MANQU\w*|OUBLI\w*)[^.]{0,25}(?:VIS|ECROU|RONDELLE)", x):
        return "Manquant – colliers"
    if _F_SLEEVE.search(x):
        return "Manquant – gaine / thermo"
    if _F_PLATE.search(x) or t == "MANQUANT_IDENTIFICATION":
        return "Manquant – identification"
    if _F_SHUNT_ELEC.search(x):
        return "Manquant – câble / shunt / élément"
    if _F_MECH.search(x):
        return "Manquant – mécanique / freinage"
    return {"Tie-wraps & clamps": "Manquant – colliers", "Sleeves & protection": "Manquant – gaine / thermo",
            "Plugs & caps": "Manquant – obturateurs / bouchons", "Plates, labels & markers": "Manquant – identification",
            "Cable problems": "Manquant – câble / shunt / élément"}.get(c, "Manquant – câble / shunt / élément")


def _damage_object(x, t, c, cable, etat):
    if (cable and (etat == "DOMMAGE" or _F_DMG.search(x))) or t == "DOMMAGE_CABLE" and _F_CABLEOBJ.search(x):
        return "Dommage – câble"
    if re.search(r"(?:RONDELLES?|ECROUS?|\bVIS\b)\s+(?:\w+\s+)?(?:ABIM|ENDOMMAG|CASS|DETERIOR)", x):
        return "Dommage – structure"                                       # Q10-006 mechanism
    if _F_BRAID.search(x) and (_F_BLEU.search(x) or "BRIN" in x):
        return "Dommage – tresse de masse"
    if _F_PLATE.search(x) and not _F_ELEC.search(x):
        return "Dommage – identification"
    if (_F_SLEEVE.search(x) or _F_COLLAR.search(x)) and not _F_ELEC.search(x) and not _F_STRUCT.search(x) or \
            re.search(r"(?:GAINES?|THERMO\w*|MANCHONS?|AMALGAMANT|COLLIERS?|BAND-?IT)\b[^.]{0,40}(?:DETERIOR|ABIM|ENDOMMAG|DECHIR|PERC|ARRACH|FEND|CASS)", x):
        return "Dommage – habillage"
    if t == "DOMMAGE_STRUCTURE" or c == "Structure & paint" or (_F_STRUCT.search(x) and not _F_ELEC.search(x)) or \
            re.search(r"PAS\s+DE\s+VIS|FILETAGE|TARAUD\w*|HELICOIL|\bINSERTS?\b|DOUILLES?|COLONN?ETTE|RIVETS?|\bVIS\b|RONDELLES?|ECROUS?", x):
        return "Dommage – structure"
    if t == "DOMMAGE_HABILLAGE":
        return "Dommage – identification" if _F_PLATE.search(x) else "Dommage – habillage"
    # component (E2): broken / doesn't work / not written
    if _F_DMG.search(x):
        return "Dommage – composant cassé"
    if _F_HS.search(x):
        return "Composant HS"
    return "Composant – cause non écrite"                                  # incl. replaced after TLB / ALB / QSR, received


def _wrongref_object(x, c):
    if re.search(r"REMPLACER\s+(?:LES\s+)?TYRAPS?\s+PAR|TYRAPS?\s+(?:A\s+REMPLACER\s+PAR|AU\s+LIEU)|TYRAPS?\s+DE\s+\d+[^.]{0,30}AU\s+LIEU", x):
        return "Mauvaise réf. – colliers / frettage"
    if re.search(r"\bVIS\b|EQUERRE|ECROU|RONDELLE|ENTRETOISE|HELICOIL|INSERT|RIVET", x) and \
            re.search(r"TROP\s+(?:COURTE?S?|LONGUE?S?)|N.EST\s+PAS\s+LA\s+BONNE|AU\s+LIEU|MAUVAISE?\s+(?:REF|VIS)|NON\s+CONFORME", x):
        return "Mauvaise réf. – mécanique"
    if _F_PLATE.search(x) and not _F_ELEC.search(x) or c == "Plates, labels & markers":
        return "Mauvaise réf. – identification"
    if _F_COLLAR.search(x):
        return "Mauvaise réf. – colliers / frettage"
    if _F_PLUG.search(x) or re.search(r"THERMO|GAINE\s+THERMO", x):
        return "Mauvaise réf. – obturation / thermo"
    if (_F_MECH.search(x) and not re.search(r"\bCONTACTS?\b|CONNECTEUR|\bPRISES?\b|DISJONCTEUR|RELAIS|BACKSHELL|DETROMP|MODULE", x)) \
            or c == "Screws & mechanical fixing":
        return "Mauvaise réf. – mécanique"
    return "Mauvaise réf. – électrique / détrompage"


def _work_object(x, t, c, cable, etat):
    """Câblage execution: the work done badly on the harness."""
    if cable and etat == "LONGUEUR":
        return "Câble à refaire (ligne)"                                   # E1
    if _F_PLATE.search(x) and c == "Plates, labels & markers":
        return "Identification – positionnement"
    if re.search(r"CHAUSSETTE|GAINE", x) and _F_TIGHT.search(x):
        return "Gainage / protection"                                      # tie-break: chaussette desserrée = Q06-002
    if _F_COLLAR.search(x) and (c == "Tie-wraps & clamps" or t == "MEO_FRETTAGE_COLLIER"):
        return "Frettage / colliers – pose"
    if _F_UNFINISHED.search(x) or t == "MEO_FINITION" and not _F_PLATE.search(x):
        return "Câblage non terminé"
    if _F_TIGHT.search(x) or t == "MEO_SERRAGE" or c in ("Loose electrical connection", "Screws & mechanical fixing"):
        if re.search(r"SUPPORTS?\b[^.]{0,40}(?:DESSERR|NON\s+SERR|MAL\s+SERR|BOUGE)", x):
            return "Serrage mécanique"
        if _F_COLLAR.search(x) and not _F_ELEC.search(x):
            return "Frettage / colliers – pose"
        if c == "Loose electrical connection" or ((_F_ELEC.search(x) or re.search(r"\b\d{1,4}V[A-Z]\d{1,4}\b|\bFIN\b", x))
                                                  and not re.search(r"\bVIS\b|SERRE.?MODULE|ECROU|RONDELLE|ARRET\s+DE\s+MODULE", x)):
            return "Serrage électrique"
        return "Serrage mécanique"
    if _F_CRIMP_SPEC.search(x) and re.search(r"SERTI|DENUD|\bCONTACTS?\b|COLLAGE|BRASURE|CLIVAGE|POLISS|FERRULE|BOOT", x) \
            and not (_F_ROUTE.search(x) and not re.search(r"SERTI|DENUD", x)):
        return "Sertissage spécifique"
    if c == "Contacts & crimping" or (t in ("MEO_SERTISSAGE_STANDARD", "MEO_SERTISSAGE_SPECIFIQUE") and _F_CRIMP.search(x)):
        return "Sertissage"
    if _F_CLASH.search(x):
        return "Cheminement – clash"
    if c == "Sleeves & protection" or (t == "MEO_GAINAGE" and not _F_ROUTE.search(x)) or (_F_SLEEVE.search(x) and not _F_ROUTE.search(x)):
        return "Gainage / protection"
    if c == "Routing & harness dressing" or t == "MEO_CHEMINEMENT" or _F_ROUTE.search(x):
        return "Cheminement – longueur / tension"
    if c == "Tie-wraps & clamps" or t == "MEO_FRETTAGE_COLLIER" or _F_COLLAR.search(x):
        return "Frettage / colliers – pose"
    if c == "Plugs & caps" or _F_PLUG.search(x):
        return "Mauvaise réf. – obturation / thermo"                        # obturateur mal monté (sens) = Q04-001
    if c == "Plates, labels & markers" or _F_PLATE.search(x):
        return "Identification – positionnement"
    if t == "MESURE_NON_CONFORME" or _F_MEASURE.search(x):
        return "Mesure hors tolérance"
    if t in ("MEO_SERTISSAGE_STANDARD",):
        return "Sertissage"
    if t == "MEO_SERTISSAGE_SPECIFIQUE" and not _F_ROUTE.search(x):
        return "Sertissage spécifique"
    return None


def _text_candidates(x, t, c, cable, etat, prov, tracker_imp, allow_upstream):
    """Sub-categories the text supports, most likely first (causality first)."""
    out = []
    add = lambda lab: lab and lab not in out and out.append(lab)
    # 1. a cause written in the same text wins over its consequence
    m = _F_CAUSE.search(x)
    if m:
        tail = x[m.end():m.end() + 60]
        if not re.match(r"(?:LA\s+)?NC\b|AU\s+(?:QSR|TLB|ALB)|(?:L.)?ALEA|(?:L.)?ANALYSE|REMISE|(?:L.)?OF\b|(?:L.)?APPLICATION", tail):
            for lab, pat in _F_CAUSE_OF:
                if pat.match(tail) or pat.search(tail[:35]):
                    if lab != "Amont · Câble" or allow_upstream:
                        add(lab)
                    break
    for lab, pat in _F_TOOL_DMG:
        if pat.search(x):
            add(lab if lab != "Serrage électrique" or _F_ELEC.search(x) else "Serrage mécanique")
            break
    # 2. groups that are what they are
    if t == "FOD" or c == "FOD":
        add("FOD")
    if t == "PROCESS_DOSSIER" or (re.search(r"MODIFICATION\s+DU\s+DESIGN|ECART[^.]{0,60}\bPLANS?\b|PLAN\s+(?:ERRONE|NON\s+CONFORME)|"
                                            r"MISE\s+A\s+JOUR\s+NON\s+FAITE|DEFINITION\s+(?:ERRONEE|NON\s+A\s+JOUR)|NON\s+BADGEE?S?|RENSEIGNEE?S?\s+SUR\s+L.OF|"
                                            r"APPLIQUER\s+LA\s+SI\b|INCOHERENCE\s+ENTRE|\bOP\s?\d+\s+NON\s+(?:VALIDEE?|BADGEE?|RENSEIGNEE?)|INCONSISTENCY\s+BETWEEN|"
                                            r"MISSING\s+ON\s+THE\s+(?:FUNCTIONAL\s+)?DRAWING|\bDQN\b", x) and not _F_DMG.search(x)):
        add("Dossier")
    # routing error named next to a short cable: the routing is the cause
    if cable and re.search(r"(?:ERREUR\s+DE|MAUVAIS)\s+CHEMINEMENT|MAL\s+CHEMINEE?S?", x):
        add("Cheminement – longueur / tension")
    # a VT bar / support badly positioned or forced = mechanical position error (Q04-003)
    if allow_upstream and re.search(r"BAR+ET+E|\bVT\b|\d{2,4}\s?VT\b|\bBARRES?\b", x) and re.search(
            r"(?:ERREUR|MAUVAIS)\w*\s+(?:DE\s+)?(?:REFERENCE\s+DE\s+)?MODULES?|DEFINITION\s+DEMANDE\s+UN\s+MODULE|"
            r"(?:BAR+ET+ES?|\bBARRES?\b)[^.]{0,60}(?:NON\s+CONFORME|N.EST\s+(?:PAS\s+)?CELUI|NE\s+CORRESPONDENT\s+PAS)", x):
        add("Amont · Identification / barrette VT")                        # Q12-006: VT bar module reference / rail
    if (re.search(r"BAR+ET+E|\bRAILS?\b|SUPPORT|EQUERRE|SHUNT\s+MECA", x) and
            re.search(r"MAL\s+POSITIONN\w*|EN\s+CONTRAINTE|EMPECHE|INTERFERENCE|MAUVAIS\s+MONTAGE", x) and not _F_PLATE.search(x)) or \
            (re.search(r"\b\d{2,4}\s?VT\b", x) and re.search(r"EN\s+CONTRAINTE|INTERFERENCE|EMPECHE\s+LE\s+MONTAGE", x)) or \
            re.search(r"MONTAGE\s+DE\s+LA\s+PLATINE[^.]{0,40}INCORRECT", x):
        add("Mauvaise réf. – mécanique")
    # a wrong part fitted or supplied, written as such (Q04-005): breaker rating, installed vs required reference
    if re.search(r"MAUVAIS\s+(?:CALIBRE|AMPERAGE)|REFERENCE\s+INSTALLEE?[^.]{0,80}REFERENCE\s+DEMANDEE?|"
                 r"FOURNI\s+UN\s+[^.]{0,40}ALORS\s+QU.IL\s+EST\s+DEMANDE|MONTAGE\s+[^.]{0,40}\bEST\s+INVERSEE?\b", x):
        add(_wrongref_object(x, "Wrong part or position"))
    # plates / label lots delivered non-conforming (Q12-005), before missing and damaged
    if allow_upstream and _F_PLATE.search(x) and re.search(
            r"(?:LIVREE?S?|RECUE?S?|LOTS?)\b[^.]{0,60}(?:NE\s+SONT\s+PAS|N.EST\s+PAS|NON)[\s-]+CONFORME|NON[\s-]CONFORMITE\s+DES\s+LOTS|"
            r"LOTS?\s+D.?(?:ETIQUETTES?|PLAQUETTES?)[^.]{0,40}INCOMPLET|(?:ETIQUETTES?|PLAQUETTES?)\s+NON\s+CONFORMES?.*\bLOTS?\b", x):
        add("Amont · Identification / barrette VT")
    # a serial number / name / label erased (Q11-002), even when the blue was being cleaned
    if re.search(r"(?:NUMERO\s+DE\s+SERIE|\bS/N\b|ETIQUETTE|PLAQUETTE|\bNOM\b)[^.]{0,60}EFFACE", x):
        add("Dommage – identification")
    # 3. upstream (print room) — exceptions E3/E4 and Q12
    imp = str(tracker_imp or "")
    from_print = prov == "RECU" or imp.startswith("Salle impression") or bool(re.search(r"MACHINE\s+A\s+DEBITER|COTE\s+IMPRESSION|SALLE\s+D.?IMPRESSION", x))
    if cable and allow_upstream:
        if from_print and (etat == "DOMMAGE" or _F_DMG.search(x)):
            add("Amont · Câble")                                           # E3
        if (_F_MISS.search(x) or t == "MANQUANT_CABLE_ELEMENT") and (_F_NOT_SUPPLIED.search(x) or imp.startswith("Salle impression")):
            add("Amont · Câble")                                           # E4
        if from_print and etat == "LONGUEUR":
            add("Amont · Câble")                                           # Q12-003
        if _F_PRINT.search(x) and not _F_DMG.search(x):
            add("Amont · Câble")                                           # Q12-001..004
        if imp.startswith("Salle impression"):
            add("Amont · Câble")                                           # the cable team blames the print room
    if cable and not from_print and (etat == "LONGUEUR" or re.search(r"COUPEE?S?\s+(?:TROP\s+)?COURTE?S?|TROP\s+COURTE?S?|SOUS-?\s?LONGUEUR|"
                                                                    r"COUPEE?S?\s+(?:LES\s+)?CABLES?\s+AU\s+NIVEAU|A\s+COUPE\s+LES\s+CABLES", x)) \
            and not _F_MISS.search(x):
        add("Câble à refaire (ligne)")                                     # E1
    if t == "AMONT_IMPRESSION" and (from_print or not cable):
        add("Amont · Identification / barrette VT" if (_F_PLATE.search(x) or re.search(r"\bVT\b|BARRETTE|RAIL", x)) and not cable
            else ("Cheminement – longueur / tension" if re.search(r"HARNAIS", x) and not cable else "Amont · Câble"))
    # 4. bonding (Q09 / T07) — a damaged braid is Q11-009 (code sheet)
    blue_marker = re.search(r"(?:REPERE|FLAMME|PLAQUETTE|ETIQUETTE|GAINE|MANCHON|RUBAN|PARTIE|\bFILS?)\w*\s+(?:\S+\s+){0,2}?BLEUE?S?", x) and \
        not re.search(r"METALLI|METALISATION|MASSE|BONDING", x)
    bond = not blue_marker and ((c == "Bonding" or t == "MEO_METALLISATION") or (_F_BLEU.search(x) and re.search(r"\bBLEUS?\b|METALLI|METALISATION|BONDING|MASSE", x)
                                                          and not _F_CABLEOBJ.search(x)))
    if re.search(r"COSSES?\s+(?:DES?\s+|DU\s+)?MASSES?", x) and _F_TIGHT.search(x):
        add("Serrage électrique")                                          # ground lugs badly tightened = Q05-001
    if _F_MEASURE.search(x) and re.search(r"HORS\s+TOLERANCE", x) and re.search(r"STRUCTURE|METALLI|MASSE", x):
        add("Point de masse / mesure")                                     # bonding resistance out of tolerance
    if _F_BRAID.search(x) and re.search(r"MASSE|METALLI", x) and (_F_DMG.search(x) or re.search(r"\bBRINS?\b", x)):
        add("Dommage – tresse de masse")
    if bond:
        if re.search(r"INVERSION|AU\s+LIEU", x) and _F_BRAID.search(x):
            add("Mauvaise réf. – électrique / détrompage")                 # braid wrong place = Q04-011
        elif _F_MEASURE.search(x) or re.search(r"NON\s+CONNECTE|NOT\s+CONNECTED|POINT\s+DE\s+MASSE", x):
            add("Point de masse / mesure")
        elif re.search(r"(?:MANQU\w*|OUBLI\w*|PAS)\s+(?:DE\s+|DU\s+|LE\s+|LES\s+)?BLEU|BLEU\w*\s+(?:MANQUANT|NON\s+APPLIQUE)|BLEU[^.]{0,30}MANQUANTE?S?|"
                       r"PROTECTION\s+NON\s+APPLIQUEE|MANQU\w*\s+(?:LE\s+)?BLEU", x):
            add("Bleu non appliqué")
        else:
            add("Bleu mal appliqué / débordant")
    # 5. branchement
    if re.search(r"\bDE?V?E?R+OU+IL+", x) and not re.search(r"OUTIL", x) or re.search(r"(?:\bPIN\b|\bCONTACTS?\b)\s+(?:\S+\s+){0,6}?RECUL", x):
        add("Déverrouillage")                                              # incl. typos (dérouillage, déverouuillé), pin pushed back
    if c == "Connectors not locked" and (re.search(r"\bGAINES?\b|GAINAGE", x) or
                                         (re.search(r"^\W*ROUTES?\b.{0,40}LISERE", x) and not re.search(r"PRISE|CONNECTEUR|\d{2,4}VC|\bFIN\b|CONTACT", x))) \
            and not re.search(r"LISERES?\s+ROUGE", x):
        add("Gainage / protection")                                        # "liseré apparent" on a sleeve = Q06-002 visible line
    if c == "Wiring errors" and re.search(r"(?:ERREUR\s+DE|MAUVAISE?)\s+REFERENCE", x) and \
            not re.search(r"BORNE|BRANCH|\bCABLES?\b|\bFILS?\b|INVERSION", x):
        add(_wrongref_object(x, "Wrong part or position"))
    if c == "Wiring errors" and _F_HS.search(x) and not re.search(r"BORNE|BRANCH|\bCABLES?\b|\bFILS?\b|INVERS|AU\s+LIEU|\bPIN\b", x):
        add("Composant HS")
    if c in ("Wiring errors", "Connectors not locked", "Not connected"):
        if c == "Connectors not locked":
            add("Déverrouillage")
        elif c == "Not connected":
            add("Non connecté")
        else:
            add("Inversion" if (t == "INVERSION_BRANCHEMENT" or "INVERS" in x) else "Erreur de branchement")
    elif c == "Cable problems" and t in _BRANCH_FROM_TYPE:
        add(_BRANCH_FROM_TYPE[t])
    # 6. missing / damaged / faulty
    missing = (bool(_F_MISS.search(x)) or (t.startswith("MANQUANT_") and not re.search(r"REPRENDRE|A\s+REFAIRE|\bMAL\s|DESSERR|\bTROP\s|ORIENT|MANQUE\s+DE\s+(?:SERRAGE|TENSION|COUPLE)", x))) \
        and not (re.search(r"MANQUAIT\s+LA\s+GLISSIERE", x) and _F_DMG.search(x)) and not re.search(r"TROUS?\s+DE\s+FIXATION[^.]{0,20}MANQU", x)
    if re.search(r"TROUS?\s+DE\s+FIXATION[^.]{0,20}(?:MANQU|NON\s+DEBOUCHE)", x):
        add("Composant – cause non écrite")                                # a part delivered without its fixing hole
    if re.search(r"PEINTURE", x) and (missing or re.search(r"N.EST\s+PLUS\s+PRESENTE", x)):
        add("Dommage – structure")
    if re.search(r"FINIR\s+(?:LA\s+)?MISE\s+EN\s+OEUVRE|FAIRE\s+LA\s+FINITION|FINIR\s+LA\s+FINITION", x):
        add("Câblage non terminé")                                         # tie-break: unfinished work = Q06-009
    if re.search(r"\bGAINES?\b|THERMO", x) and re.search(r"TROP\s+COURTE?S?|CONTACT\s+AVEC\s+(?:LE\s+)?GROMMET|GAINES?\s+DE\s+RESERVE\s+COURTE?S?", x):
        add("Gainage / protection")                                        # Q06-008: sheathing too short / touching the grommet
    if re.search(r"(?:FAISCEAU|HARNAIS|TORON)\s+LACHE", x) and not re.search(r"MANQU\w*\s+(?:\S+\s+){0,2}?(?:FRETTE|TYRAP|COLLIER)", x):
        add("Cheminement – longueur / tension")
    if _F_COLLAR.search(x) and re.search(r"DE\s+TRAVERS|(?:TYRAPS?|COLLIERS?)\s+(?:\S+\s+){0,2}?A\s+REORIENTER|ALIGNEMENT\s+DU\s+COLLIER|ENLEVER\s+LES\s+TYRAPS", x):
        add("Mauvaise réf. – colliers / frettage")                         # collar orientation = Q04-007/008
    if missing and not (c in ("Damaged equipment",) and _F_DMG.search(x) and not t.startswith("MANQUANT_")):
        add(_missing_object(x, t, c, cable and t != "MEO_CHEMINEMENT"))
    if _F_CLASH.search(x) and not _F_DMG.search(x) and re.search(r"HARNAIS|ROUTE\b|TORON|FAISCEAU|CABLAGE|\bCABLES?\b|\bFILS?\b|TRESSE|"
                                                                 r"BRANCHE|CIRCUIT|DERIVATION|FIBRE|COSSE|\b\d{1,4}[A-Z]{2}\d{0,4}\b", x):
        add("Cheminement – clash")
    if re.search(r"(?:HARNAIS|\bCABLES?\b|FIBRE|TORON|FAISCEAU|BI-?\s?FILAIRE)[^.]{0,40}(?:NON\s+ATTACHE|PAS\s+ATTACHE|PINCEE?S?\s+DANS|"
                 r"NON\s+MAINTENUE?|MAL\s+FIXEE?S?|PAS\s+POSITIONNEE?\s+DANS|COULISSE\s+DANS|NON\s+PRIS\s+DANS|PAS\s+PRIS\s+DANS\s+LA\s+FRET)|"
                 r"ATTACHER\s+(?:LA\s+|LE\s+|LES\s+)?(?:FIBRE|HARNAIS|CABLE)|PINCEE?S?\s+(?:DANS|PAR)\s+(?:LE\s+|UN\s+)?COLLIER|"
                 r"(?<!\(\s)(?<!\()REPRENDRE\s+(?:LE\s+)?CHEMINEMENT|FINIR\s+LE\s+CHEMINEMENT|"
                 r"(?:NON|PAS|MAL)\s+(?:PRISE?S?|FIXEE?S?|TENUE?S?)\s+(?:DANS|AVEC|PAR|SUR)\s+(?:LE\s+|LA\s+|LES\s+|UN\s+)?(?:COLLIERS?|LAC+OT+E|SUPPORT|FRETT?E)|"
                 r"COINCEE?S?\s+DANS\s+(?:LE\s+|LA\s+)?COLLIER|PINCEE?\s+(?:LE\s+)?DANS\s+(?:LE\s+)?COLLIER|NE\s+PREND\w*\s+PAS\s+(?:LE\s+)?(?:SUPPORT|HARNAIS)", x):
        add("Cheminement – longueur / tension")                            # Q06-001: pinched / not held in the collar
    if re.search(r"SERRE-?\s?MODULES?", x) and re.search(r"INCORRECT|MAUVAISE?|\bMAL\b|A\s+REPRENDRE|FIXATION|DESSERR", x):
        add("Serrage mécanique")
    if re.search(r"(?:PLATINE|CAPOT|RAMPE)(?:(?!CABLE|\bFIL|CONTACT|BORNE|GAINE|PLAQUETTE|ETIQUETTE|CONNECTEUR|MODULE|RELAIS|SOCLE|EQUIPEMENT|DISJONCTEUR)[^.]){0,50}?"
                 r"(?:RAYURE|RAYEE|FISSUR|ENDOMMAG|SOUILL|CASSEE|IMPACT)|(?:RAYURE|FISSURE|IMPACT)\w*[^.]{0,40}(?:PLATINE|CAPOT|RAMPE)|BELLY\s+FAIRING[^.]*(?:CASSURE|RUPTUR|FISSUR|ENDOMMAG)", x):
        add("Dommage – structure")
    damaged = t.startswith("DOMMAGE_") or c in ("Damaged equipment", "Faulty or non-conforming part") \
        or (c == "Structure & paint" and (_F_DMG.search(x) or re.search(r"PEINTURE|SOUILL", x))) \
        or (_F_DMG.search(x) and not (cable and etat == "LONGUEUR"))
    if c == "Structure & paint" and re.search(r"PEINTURE", x) and missing:
        add("Dommage – structure")
    if damaged:
        add(_damage_object(x, t, c, cable, etat))
    if re.search(r"(?:FRET\w*|TYRAPS?)\s+(?:COUPEE?S?\s+)?TROP\s+(?:LONGUE?S?|COURTE?S?)|LONGUEUR\s+(?:DES?\s+)?FRET\w*|"
                 r"NOEUDS?\s+DE\s+FRET|ORIENTATION\s+DES\s+TETES", x):
        add("Frettage / colliers – pose")                                  # fret length cut = Q06-011
    if _F_CLASH.search(x) and not _F_DMG.search(x):
        add("Cheminement – clash")
    if allow_upstream and re.search(r"RAILS?\b|BARRETTES?", x) and re.search(r"RECEPTION|\bRECUE?S?\b|LIVREE?S?", x):
        add("Amont · Identification / barrette VT")                        # Q12-006: VT bar / rail size, from the kitting room
    if re.search(r"PAS\s+PRIS\s+DANS\s+LE\s+RACCORD|NON\s+MAINTENUE?\s+DANS\s+LE\s+(?:BACKSHELL|RACCORD)", x):
        add("Gainage / protection")                                        # Q06-008: not secured to the rear connector
    # 7a. a plate whose text is wrong or illegible was printed that way (Q12-005); swapped or wrong plate mounted = Q04-013
    if allow_upstream and _F_PLATE.search(x) and re.search(r"ILLISIBLE|MAUVAIS\s+(?:S/N|N.?\s?DE\s+SERIE|NUMERO)|ERREUR\s+(?:D.?ETIQUETTE|DE\s+REFERENCE|"
                                                          r"D.?IDENTIFICATION|DE\s+GRAVURE)|NOTEE?\s+EN\s+FAIT|AU\s+LIEU\s+D", x) \
            and not re.search(r"INVERSION|MONTEE?S?\s+AU\s+LIEU|MAUVAISE?\s+PLAQUETTE\s+MONTEE|BACKSHE|ORIENT|\d\s?°|RETOURN|REPRENDRE\s+LA\s+MISE", x):
        add("Amont · Identification / barrette VT")
    # 7. wrong reference / position, identification positioning (tie-break: upside down / offset = Q06-010)
    if _F_PLATE.search(x) and (_F_POSITION.search(x) or re.search(r"(?:PLAQUETTE|ETIQUETTE)S?\s+(?:[^\s,.]+\s+){0,3}?DESSERREE?S?", x)) and not re.search(r"INVERSION|AU\s+LIEU|MAUVAISE?\s+REF|ERREUR\s+(?:DE\s+)?(?:MANCHON|REF)|NOTEE?\s+EN\s+FAIT", x):
        add("Identification – positionnement")
    if _F_PLATE.search(x) and re.search(r"(?:REFAIRE|REPRENDRE)\s+(?:LES?\s+)?(?:FRETT?ES?|FRETAGE|FRETTAGE|TYRAPS?)|\bFRETTER\b", x) \
            and not re.search(r"REMPLACER|AU\s+LIEU|ENLEVER", x):
        add("Frettage / colliers – pose")
    if t == "ERREUR_REF_ELECTRIQUE" or c == "Wrong part or position" or _F_WRONGREF.search(x):
        if not (cable and etat == "LONGUEUR"):
            add(_wrongref_object(x, c))
    # 8. execution (câblage)
    add(_work_object(x, t, c, cable, etat))
    # 9. from the keyword type alone
    if t in _BRANCH_FROM_TYPE:
        add(_BRANCH_FROM_TYPE[t])
    if cable and etat == "LONGUEUR":
        add("Câble à refaire (ligne)")
    if cable and (_F_MISS.search(x) or t == "MANQUANT_CABLE_ELEMENT"):
        add("Manquant – câble / shunt / élément")
    return out


# v4.7 — when nothing in the text decides, the parser still guesses (decision 7 Oct 2026):
# weak words first, then the SAP "Type of nonconformity", then the most common workmanship
# sub-category. These rows carry souscat_source = DEVINE so they can be counted apart.
_GUESS_WORDS = [
    ("Dossier",                          r"\bOF\b|\bSI\b|\bPLANS?\b|DRAWING|DOSSIER"),
    ("Erreur de branchement",            r"BRANCHEMENT|CONNEXION|CONNECTION|\bTEST"),
    ("Composant – cause non écrite",     r"EQUIPEMENT|EQUIPMENT|\bPIECE"),
    ("Cheminement – longueur / tension", r"CABLAGE|HARNAIS|ROUTE"),
    ("Dommage – câble",                  r"\bCABLES?\b|\bFILS?\b"),
]
_GUESS_SAP = {"SWAP": "Inversion", "INCORRECT CONNECTOR": "Mauvaise réf. – électrique / détrompage",
              "INCORRECT PART FITTED": "Mauvaise réf. – électrique / détrompage", "CABLE ROUTING": "Cheminement – longueur / tension",
              "CLASH / CLEARANCE": "Cheminement – clash", "ELECTRICAL CRIMPING": "Sertissage", "ELECTRICAL BONDING": "Point de masse / mesure",
              "MEASURE OUT OF TOLERANCE": "Mesure hors tolérance", "MEASURE OUT OF TOLERANCES": "Mesure hors tolérance",
              "BROKEN": "Dommage – composant cassé", "WIRING DAMAGE": "Dommage – câble", "DAMAGED HARNESS": "Dommage – câble",
              "FAULT IN CONTINUITY": "Composant HS", "PART NOT INSTALLED": "Manquant – câble / shunt / élément",
              "MISSING PART/COMPONENT / INCOMPLETE KIT": "Manquant – câble / shunt / élément",
              "MISSING PART/COMPONENT/INCOMPLETE KIT": "Manquant – câble / shunt / élément", "MISSING IDENTIFICATION": "Manquant – identification",
              "DRILLING": "Dommage – structure", "RIVETING": "Dommage – structure", "STRUCTURAL AND MECHANICAL ASSEMBLY": "Dommage – structure",
              "FOD FOUND WITHOUT DAMAGE": "FOD", "PART LOST DURING PRODUCTION": "FOD"}
_GUESS_DEFAULT = "Cheminement – longueur / tension"


def _guess(x, sap_type):
    for lab, pat in _GUESS_WORDS:
        if re.search(pat, x):
            return lab
    return _GUESS_SAP.get(_cat_norm(sap_type or "").strip(), _GUESS_DEFAULT)


def souscat_of(text, code=None, sub_code=None, type_reporting="", categorie="", defaut_cable=False,
               etat_cable="", provenance="", tracker_imputation=None, sap_type=None):
    """-> (sous_categorie, source). source: SOUS-CODE | CODE | CODE+TEXTE | TEXTE | DEVINE."""
    x = _cat_norm(text)
    t, c = type_reporting or "", categorie or ""
    cable = str(defaut_cable).strip().lower() in ("true", "1", "t")
    etat = etat_cable if isinstance(etat_cable, str) else ""
    sc = (sub_code or "").strip().upper() if isinstance(sub_code, str) else ""
    if sc in SUBCODE_TO_SOUSCAT:
        return SUBCODE_TO_SOUSCAT[sc], "SOUS-CODE"
    m = re.match(r"^\s*([QT]\d{2})", str(code or "").upper())
    head = m.group(1) if m and m.group(1) in HEAD_SOUSCATS else None
    cands = _text_candidates(x, t, c, cable, etat, provenance, tracker_imputation, allow_upstream=head is None) \
        if x.strip(" *-:.") else []
    if head:                                                               # the written code always wins
        allowed = HEAD_SOUSCATS[head]
        for lab in cands:
            if lab in allowed:
                return lab, "CODE+TEXTE"
        guess = {"Q11": lambda: _damage_object(x, "DOMMAGE_COMPOSANT", c, cable, etat),
                 "Q10": lambda: "Dommage – structure",
                 "Q04": lambda: _wrongref_object(x, c),
                 "Q03": lambda: _missing_object(x, t, c, cable),
                 "Q05": lambda: _work_object(x, "MEO_SERRAGE", c, False, ""),
                 "Q06": lambda: _work_object(x, t, c, cable, etat)}.get(head)
        lab = guess() if guess else None
        return (lab if lab in allowed else _DEFAULT_OF_HEAD[head]), "CODE"
    if cands:
        return cands[0], "TEXTE"
    return _guess(x, sap_type if isinstance(sap_type, str) else ""), "DEVINE"


# v4.7 — minor defects (decision 7 Oct 2026): only a small thing forgotten, not a wrong choice.
MINEURS = {"Manquant – colliers", "Manquant – obturateurs / bouchons"}


def est_mineur(souscat: str) -> bool:
    return souscat in MINEURS


def groupe_of_souscat(souscat: str) -> str:
    return SOUS_CATEGORIES.get(souscat, ("Non classé",))[0]


def rca_type_of(souscat: str) -> str:
    return SOUS_CATEGORIES.get(souscat, (None, "AUTRE"))[1]


def reference_table():
    """The 123 official sub-codes, each with its one sub-category, group and RCA type (list of dicts)."""
    return [{"sous_code": sc, "sous_categorie": lab, "groupe": g, "rca_type": t, "rca_mode": mode_of(t)}
            for lab, (g, t, scs, _) in SOUS_CATEGORIES.items() for sc in scs]



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
        if "categorie" in df.columns:                                 # v4.3: keep the category in step with the type
            df.at[i, "categorie"] = categorie_of(new, r.get("defaut_cable"), r["text"])
            if "famille" in df.columns:
                df.at[i, "famille"] = famille_of(df.at[i, "categorie"])
    if "sous_groupe" in df.columns:                                    # v4.6: E3/E4 and Q12-003 read the tracker
        for i, r in df[df["tracker_imputation"].notna()].iterrows():
            lab, src = souscat_of(r["text"], r.get("code"), r.get("sub_code"), r["type_reporting"], r.get("categorie"),
                                  r.get("defaut_cable"), r.get("etat_cable"), r.get("provenance"), r["tracker_imputation"],
                                  r.get("sap_type"))
            df.at[i, "sous_groupe"], df.at[i, "souscat_source"] = lab, src
            df.at[i, "groupe"], df.at[i, "rca_type"] = groupe_of_souscat(lab), rca_type_of(lab)
            df.at[i, "rca_mode"] = mode_of(df.at[i, "rca_type"])
            if "mineur" in df.columns:
                df.at[i, "mineur"] = est_mineur(lab)
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
    rows = [{id_col: nc_id, "nc_cable": p["nc_cable"], **d}          # v4.3: NC-level cable flag on every defect row
            for nc_id, p in zip(df[id_col], parsed) for d in p["defects"]]
    return nc_df, pd.DataFrame(rows)


if __name__ == "__main__" and len(_sys.argv) > 1 and _sys.argv[1].lower().endswith((".csv", ".txt")):
    # command line only: python nc_defect_parser.py <SAP extract.csv>
    import pandas as pd
    df = pd.read_csv(_sys.argv[1], low_memory=False)
    nc_df, dd = explode_dataframe(df, manual_count_col="Ext_Nb_Defauts")
    print(f"{len(df)} NCs -> {len(dd)} defects\n")
    print("MODE -> TYPE (tree):")
    print(dd.groupby(["mode_erreur", "type_reporting"]).size().to_string())
    print("\nConfidence:"); print(dd["confidence"].value_counts().to_string())
    print("\nResolved by:"); print(dd["resolved_by"].value_counts().to_string())
    print("\nCable NCs (v4.2):"); print(nc_df["nc_cable"].value_counts(dropna=False).to_string())
    print("\nPareto categories (v4.3):"); print(dd["categorie"].value_counts().to_string())
    print("\nPareto groups (v4.6):"); print(dd["groupe"].value_counts().to_string())
    print("\nPareto families (v4.4):"); print(dd["famille"].value_counts().to_string())
