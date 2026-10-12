"""
nc_defect_parser
================
Splits Skywise NC long descriptions (description_long_text) into individual
defects, counts them per NC, and classifies each defect into a two-level
taxonomy (famille / sous-categorie).

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
DEF_RE       = re.compile(r"DEF\s*(\d{1,3})\s*[-–]?\s*([QTP]\s?\d{1,2})?\s*:", re.I)
NUM_RE       = re.compile(r"^\s*(\d{1,2})\s*[-–]\s+(?=\S)", re.M)
CABLE_RE     = re.compile(r"^\s*[-*]?\s*N\s?°", re.M)
BLOCK_RE     = re.compile(r"NonConformity\s+\d+\s*:")
FIN_RE       = re.compile(r"\b(\d{1,4}[A-Z]{2,4}\d{0,4}[A-Z]{0,2})\b")

# --- DEFAUTS v1 template (the writing standard) ---
TPL_HDR_RE   = re.compile(r"###\s*DEFAUTS\s*v1\b", re.I)
TPL_LINE_RE  = re.compile(
    r"^\s*DEF\s*(\d{1,3})\s*-\s*([A-Z]{1,3}\d{0,2})\s*-\s*([^:\n]+?)"
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
    famille: str = ""       # filled by classify()
    sous_categorie: str = ""
    loc: str | None = None  # location slot as written (FIN, 'ZONE ...', or None)
    qty: int = 1            # QTE slot (identical defects on one line)

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
    seen, out = set(), []
    for p in parts:
        narr = SEP_RE.split(p)[0]
        key = re.sub(r"\W+", "", norm(narr))[:300]
        if key and key not in seen:
            seen.add(key)
            narr = re.sub(r"^\s*Type of nonconformity\s*:[^*\n]*[*]?", "", narr).strip()
            out.append(" ".join(narr.split()))
    return out

def split_defects(raw_text: str) -> list[Defect]:
    text = clean_text(raw_text)

    # DEFAUTS v1 template: strict grammar, highest-confidence path
    if TPL_HDR_RE.search(text):
        out = []
        for m in TPL_LINE_RE.finditer(text):
            seq, code, loc, cable, qte, txt = m.groups()
            loc = loc.strip()
            fin = FIN_RE.search(norm(loc))
            body = (f"CABLE {cable} " if cable else "") + txt.strip()
            out.append(Defect(seq=int(seq), code=code.upper(),
                              fin=fin.group(1) if fin else None,
                              text=body[:300], source_format="template_v1",
                              loc=loc if loc != "-" else None,
                              qty=int(qte) if qte else 1))
        if out:
            return out

    items = _slice_items(text, DEF_RE.finditer(text))
    fmt = "def_list"

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
        fmt = "narrative"
        blocks = _unique_blocks(text)
        if not blocks:  # NCs without a 'NonConformity' header (~11% of data)
            head = TS_RE.split(text)[0] if TS_RE.search(text) else text
            blocks = [" ".join(head.split())[:400]] if head.strip() else []
        items = [(None, b) for b in blocks]

    out = []
    for i, (code, t) in enumerate(items, 1):
        fin = FIN_RE.search(norm(t))
        out.append(Defect(seq=i, code=code, fin=fin.group(1) if fin else None,
                          text=t[:300], source_format=fmt))
    return out

# --------------------------------------------------------------------------- #
# Taxonomy — famille -> sous-categorie, first matching rule wins.
# Patterns run on norm(text): UPPERCASE, accents stripped.
# Order matters: specific before generic.
# --------------------------------------------------------------------------- #

RULES: list[tuple[str, str, re.Pattern]] = [
    # 1 BRANCHEMENT — le câblage logique est faux (bonne pièce, mauvais point)
    ("BRANCHEMENT", "ERREUR_PLAQUETTE_REF", re.compile(r"PLAQUETTE|ERREUR (DE )?REF|MAUVAISE REF")),
    ("BRANCHEMENT", "INVERSION_BORNES",     re.compile(r"INVERSION|INVERSE|CROISE")),
    ("BRANCHEMENT", "MAUVAISE_BORNE",       re.compile(r"AU LIEU DE|MAUVAISE BORNE|ERREUR (DE )?(BORNE|BRANCHEMENT|CABLAGE|CONNEXION)")),
    ("BRANCHEMENT", "NON_CONNECTE",         re.compile(r"NON (CONNECTE|BRANCHE|RACCORDE)|PAS (CONNECTE|BRANCHE)")),
    # 2 CONNEXION — bon point, geste de connexion non conforme
    ("CONNEXION", "DEVERROUILLAGE",   re.compile(r"DEVERROUILL|NON VERROUILL")),
    ("CONNEXION", "SERTISSAGE",       re.compile(r"SERTISS")),
    ("CONNEXION", "BLINDAGE_TRESSE",  re.compile(r"BLINDAGE|TRESSE|RACCORD SLIM|REPRISE DE MASSE")),
    ("CONNEXION", "FREINAGE_FRETTES", re.compile(r"FREIN|FRET(T?E|T?AGE)")),
    ("CONNEXION", "SERRAGE_COUPLE",   re.compile(r"TORQU|COUPLE|SERRAGE|DESSERRE|MAL SERRE")),
    # 3 INTEGRITE — dommage physique / panne
    ("INTEGRITE", "CABLE_ENDOMMAGE", re.compile(r"\bCOUPE?E?S?\b|ABIME|ENDOMMAG|BLESS|PINCE|DETERIOR|DENUDE|ECRASE|RAYE")),
    ("INTEGRITE", "COMPOSANT_CASSE", re.compile(r"CASSE|BRISE|ARRACHE|FISSUR|TORDU")),
    ("INTEGRITE", "COMPOSANT_HS",    re.compile(r"\bHS\b|DEFECTUEU|DEFAILLAN|NE FONCTIONNE|PAS DE CONTINUITE|CONTINUITE")),
    # 4 MANQUANT — quelque chose n'est pas là
    ("MANQUANT", "CABLE_MANQUANT", re.compile(r"CABLE[^.]{0,40}(MANQUANT|MANQUE|NON RECU|NON LIVRE|ABSENT)|(MANQUANT|MANQUE)[^.]{0,20}CABLE")),
    ("MANQUANT", "PIECE_MANQUANTE", re.compile(r"MANQUANT|\bMANQUE\b|\bMQ\b|NON RECU|NON LIVRE|ABSENT|OUBLI")),
    # 5 AMONT_FABRICATION — le défaut est arrivé avec la pièce
    ("AMONT_FABRICATION", "LONGUEUR_NC",    re.compile(r"TROP (COURT|LONG)|SURLONGUEUR|COURT DE L|LONGUEUR")),
    ("AMONT_FABRICATION", "DEFAUT_RECU",    re.compile(r"RECU (COUPE|ABIME|ENDOMMAGE|PERCE)|ERREUR (D )?IMPRESSION")),
    # 6 INSTALLATION — intégration mécanique / environnement
    ("INSTALLATION", "CHEMINEMENT_CONTRAINTE", re.compile(r"CHEMINEMENT|CONTRAINTE|INTERFER|ROUTAGE|EN CONTACT AVEC|FROTTE")),
    ("INSTALLATION", "FIXATION_VISSERIE",      re.compile(r"CLAMP|FIXATION|\bVIS\b|RONDELLE|ECROU|RIVET|SUPPORT|COLLIER")),
    ("INSTALLATION", "METALLISATION_BONDING",  re.compile(r"METALLISATION|BONDING|\bBLEU\b")),
    ("INSTALLATION", "FOD_PROPRETE",           re.compile(r"\bFOD\b|POUSSIERE|BRIN METALLIQUE|COPEAU|PROPRETE")),
    # 7 IDENTIFICATION
    ("IDENTIFICATION", "ETIQUETTE_MARQUAGE", re.compile(r"ETIQUETTE|MARQUAGE|REPERAGE|\bSATO\b|IDENTIFICATION")),
]

# Q/T codes with stable observed semantics -> applied BEFORE keywords.
CODE_MAP: dict[str, tuple[str, str]] = {
    "T04": ("BRANCHEMENT", "INVERSION_BORNES"),
    "T02": ("BRANCHEMENT", "MAUVAISE_BORNE"),
    "Q04": ("BRANCHEMENT", "ERREUR_PLAQUETTE_REF"),
    "Q01": ("CONNEXION",   "DEVERROUILLAGE"),
    "T01": ("MANQUANT",    "CABLE_MANQUANT"),
    "T03": ("MANQUANT",    "CABLE_MANQUANT"),
}

# Proposed extensions for template mode ONLY — placeholders to reconcile with the
# official code sheet at the standardisation workshop. Legacy parsing is untouched.
TEMPLATE_CODE_MAP: dict[str, tuple[str, str]] = {**CODE_MAP,
    "Q05": ("CONNEXION",   "SERTISSAGE"),
    "Q07": ("CONNEXION",   "SERTISSAGE"),
    "Q08": ("CONNEXION",   "BLINDAGE_TRESSE"),
    "Q11": ("INTEGRITE",   "COMPOSANT_CASSE"),
    "M01": ("MANQUANT",    "PIECE_MANQUANTE"),
    "L01": ("AMONT_FABRICATION", "LONGUEUR_NC"),
    "R01": ("AMONT_FABRICATION", "DEFAUT_RECU"),
    "C01": ("INTEGRITE",   "COMPOSANT_CASSE"),
    "C02": ("INTEGRITE",   "CABLE_ENDOMMAGE"),
    "H01": ("INTEGRITE",   "COMPOSANT_HS"),
    "F01": ("INSTALLATION","FIXATION_VISSERIE"),
    "F02": ("INSTALLATION","CHEMINEMENT_CONTRAINTE"),
    "F03": ("INSTALLATION","METALLISATION_BONDING"),
    "FOD": ("INSTALLATION","FOD_PROPRETE"),
    "E01": ("IDENTIFICATION","ETIQUETTE_MARQUAGE"),
    "N01": ("BRANCHEMENT", "NON_CONNECTE"),
    "FRE": ("CONNEXION",   "FREINAGE_FRETTES"),
    "TOR": ("CONNEXION",   "SERRAGE_COUPLE"),
}

def classify(d: Defect) -> Defect:
    if d.source_format == "template_v1" and d.code in TEMPLATE_CODE_MAP:
        d.famille, d.sous_categorie = TEMPLATE_CODE_MAP[d.code]
        return d
    if d.code in CODE_MAP:
        d.famille, d.sous_categorie = CODE_MAP[d.code]
        return d
    t = norm(d.text)
    for fam, sub, pat in RULES:
        if pat.search(t):
            d.famille, d.sous_categorie = fam, sub
            return d
    d.famille, d.sous_categorie = "AUTRE", "AUTRE"
    return d

# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def parse_nc(raw_text: str) -> dict:
    """One NC in -> {'nb_defauts': int|None, 'is_redacted': bool, 'defects': [...]}"""
    if raw_text is None or REDACTED_MARKER in str(raw_text):
        return {"nb_defauts": None, "is_redacted": True, "flags": ["REDACTED"], "defects": []}
    defects = [classify(d) for d in split_defects(raw_text)]
    nb = sum(d.qty for d in defects)
    flags = []
    if defects and defects[0].source_format == "template_v1":
        flags.append("TEMPLATE_V1")
        tot = TPL_TOTAL_RE.search(clean_text(raw_text))
        if tot and int(tot.group(1)) != nb:
            flags.append(f"TOTAL_MISMATCH(declared={tot.group(1)},parsed={nb})")
    return {"nb_defauts": nb, "is_redacted": False, "flags": flags,
            "defects": [asdict(d) for d in defects]}

def explode_dataframe(df, text_col="description_long_text",
                      id_col="notification_number", manual_count_col=None):
    """Returns (nc_df, defects_df).

    nc_df      = input + nb_defauts / is_redacted / nb_defauts_final
    defects_df = one row per individual defect, keyed by id_col.
    If manual_count_col is given (e.g. 'Ext_Nb_Defauts'), nb_defauts_final
    falls back to it for redacted texts."""
    import pandas as pd
    parsed = df[text_col].apply(parse_nc)
    nc_df = df.copy()
    nc_df["nb_defauts"]  = parsed.apply(lambda p: p["nb_defauts"])
    nc_df["is_redacted"] = parsed.apply(lambda p: p["is_redacted"])
    nc_df["flags"]       = parsed.apply(lambda p: ";".join(p.get("flags", [])))
    nc_df["nb_defauts_final"] = nc_df["nb_defauts"]
    if manual_count_col and manual_count_col in nc_df:
        nc_df.loc[nc_df["is_redacted"], "nb_defauts_final"] = \
            nc_df.loc[nc_df["is_redacted"], manual_count_col]
    rows = []
    for nc_id, p in zip(df[id_col], parsed):
        for d in p["defects"]:
            rows.append({id_col: nc_id, **d})
    return nc_df, pd.DataFrame(rows)


if __name__ == "__main__":
    import sys, pandas as pd
    df = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "aaf.txt")
    nc_df, defects_df = explode_dataframe(df, manual_count_col="Ext_Nb_Defauts")
    print(f"{len(df)} NCs -> {len(defects_df)} defects")
    print(defects_df.groupby(["famille", "sous_categorie"]).size()
          .sort_values(ascending=False).to_string())
