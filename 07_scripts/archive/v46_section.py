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
_F_CAUSE = _S(r"(?:SUITE\s+A|APRES|A\s+CAUSE\s+D|DUE?S?\s+A|EN\s+RAISON\s+D|CONSECUTI\w*\s+A)\s+(?:UNE?\s+|L.\s?|LA\s+|LE\s+|LES\s+|DES?\s+|DU\s+)?")
_F_CAUSE_OF = [   # cause named after "suite à / après ..." -> sub-category of the cause
    ("Amont · Câble",          _S(r"MARQUAGES?\s+DEF+ECTUEUX|MAUVAIS\s+MARQUAGE|NON\s+LASERIS|NON\s+IMPRIM|ERREUR\s+D.?IMPRESSION")),
    ("Inversion",              _S(r"INVERSIONS?\s+(?:DE\s+|DES\s+)?(?:BRANCHEMENT|CABLE|FIL|BORNE|PRISE)|INVERSIONS?\b(?!\s+D.?ATA)")),
    ("Erreur de branchement",  _S(r"(?:ERREUR|MAUVAIS)\s+(?:DE\s+)?BRANCHEMENT")),
    ("Sertissage",             _S(r"(?:ERREUR\s+DE|MAUVAIS)\s+SERTISSAGE")),
    ("Cheminement – longueur / tension", _S(r"(?:ERREUR\s+DE|MAUVAIS)\s+CHEMINEMENT")),
]
_F_TOOL_DMG = [   # damage caused by a named operation, written in the same text
    ("Frettage / colliers – pose", _S(r"(?:FRETT?ES?|COLLIERS?|TYRAPS?)\s+TROP\s+SERREE?S?")),
    ("Serrage électrique",         _S(r"(?:ABIME|ENDOMMAGE|CASSE)\w*\s+LORS\s+DU\s+(?:TORQUAGE|SERRAGE)|LORS\s+DU\s+(?:TORQUAGE|SERRAGE)")),
    ("Sertissage",                 _S(r"PAR\s+LA\s+PINCE\s+A\s+DENUDER|LORS\s+DU\s+DENUDAGE")),
]
_F_DMG = _S(r"CASSEE?S?\b|\bABIMEE?S?\b|ABIMER\b|ENDOM+AGE\w*|DETERIOR\w*|\bRAYEE?S?\b|RAILLEE?S?|RAYURES?|FISSURE\w*|TORDUE?S?\b|"
            r"DEFORM\w*|ARRACHE\w*|ECRASEE?S?\b|\bIMPACTS?\b|SCRAPE|DECHIRE\w*|BRISE\w*|FENDUE?S?\b|\bDAMAGED\b|BROKEN|ENTAILLE\w*|"
            r"SECTIONNE\w*|PERCEE?S?\b|BLESSEE?S?\b")
_F_HS = _S(r"\bHS\b|H\.S\b|DEFAUT\s+D.?ISOL|CONTINUITE|NE\s+FONCTIONNE|MAUVAIS\s+FONCTIONNEMENT|NE\s+(?:SE\s+)?VERROUILLE\s+PAS|"
           r"ENFICHAGE|COURT.?CIRCUIT|PASSANTE|HORS\s+TOLERANCE|\bKO\b|\bINOP|DEFECTUEU\w*|FAUX\s+CONTACT|NE\s+S.?ALLUME|PANNE")
_F_MISS = _S(r"MANQUANTE?S?|MAQUANTE?S?|\bMANQUE\b(?!\s+DE\s+(?:SERRAGE|PLACE|TENSION|COUPLE|LONGUEUR))|MANQUAIT|\bOUBLI\w*|ABSENTE?S?\b|"
             r"NON\s+POSEE?S?|PAS\s+DE\s+(?:FRETTE|COLLIER|TYRAP|GAINE|BLEU|OBTURATEUR|BOUCHON|PLAQUETTE|ETIQUETTE)|N.EST\s+PLUS\s+PRESENTE?")
_F_NOT_SUPPLIED = _S(r"PAS\s+(?:ETES?\s+)?FOURNIE?S?|NON\s+FOURNIE?S?|NON\s+LIVREE?S?|PAS\s+(?:ETE\s+)?LIVREE?S?|NON\s+RECUE?S?|"
                     r"MANQUANTE?S?\s+A\s+LA\s+RECEPTION")
_F_BLEU = _S(r"\bBLEUS?\b|METALLI|METALISATION|BONDING|MASSE")
_F_BRAID = _S(r"TRESSES?")
_F_MEASURE = _S(r"MESURE|RESISTANCE|HORS\s+TOLERANCE|PERTE\s+D.?INSERTION|M\s?OHM|MILLI\s?OHM")
_F_PLATE = _S(r"PLAQUETTE|ETIQUETTE|DATUM|FLAMMES?|\bREPERES?\b|MANCHONS?\s+REPERE|\bS/N\b|N.?\s?DE\s+SERIE|NUMERO\s+DE\s+SERIE|"
              r"IDENTIFICATION|\bETEC\b|SCELLE|INVIOLABILITE")
_F_POSITION = _S(r"A\s+L.ENVERS|DECALEE?S?|(?:RE)?CENTR\w*|MAL\s+POSITIONN\w*|POSITIONN\w*|PLACEMENT|MAL\s+PLACEE?S?|MAUVAIS\s+COTE|"
                 r"A\s+FIXER|MAL\s+ATTACHEE?S?|NON\s+MAINTENUE?S?|TIENT\s+PAR|TOURNER|ORIENT\w*|SENS\b")
_F_WRONGREF = _S(r"MAUVAISE?\s+(?:REFERENCE|REF\b|MODULE|CONNECTEUR|PRISE|EQUIPEMENT|PIECE|VIS|CONTACT|CALIBRE|TAILLE)|"
                 r"ERREUR\s+(?:DE\s+)?(?:REFERENCE|REF\b|MODULE|GAUGE|JAUGE|MANCHON|D.?ETIQUETTE|DETROMPAGE)|AU\s+LIEU\s+D|"
                 r"N.EST\s+PAS\s+LA\s+BONNE|NOTEE?\s+EN\s+FAIT|TROP\s+(?:COURTE?S?|LONGUE?S?)|INVERSION\s+(?:DE\s+MONTAGE|DES\s+PLAQUETTES|DE\s+MANCHON)|"
                 r"DETROMP\w*|MONTEE?S?\s+A\s+L.ENVERS|ORIENT\w*|REFERENCE\s+(?:DU|DE)\s+\w+\s+(?:N.EST\s+PAS|NON)\s+CONFORME")
_F_COLLAR = _S(r"FRETT|FRETES?\b|\bFRET\b|TYRAP|TY-RAP|COLLIERS?\b|LAC+OT+E|ATTACHE\w*|SERRE-?\s?CABLE|\bCLAMPS?\b|BAND-?IT")
_F_SLEEVE = _S(r"GAINES?\b|THERMO|CHAUSSETTE|AMALGAMANT|MANCHONS?\b|RUBAN|TRAIT\s+APPARENT|POCHETTE|\bPROTECTIONS?\b|EMI\s+SLEEV|GROMMET")
_F_PLUG = _S(r"OBTURAT|BOUCHONS?\b|CAPUCHON|CERISE|SWITCH\s+GUARD")
_F_MECH = _S(r"\bVIS\b|VISSERIE|ECROUS?\b|RONDELLES?|BOULON|\bDZUS|SERRE.?MODULES?|ARRET\s+DE\s+MODULE|ENTRETOISE|\bINSERT\b|FREIN\w*|"
             r"FRANGIBLE|COLONNETTE|EQUERRE|SUPPORT|BARRETTE|RAIL\b|HELICOIL|FILETAGE|TARAUD")
_F_ELEC = _S(r"BACK\s?-?SHELL|\bBORNES?\b|CONNECTEUR|\bPRISES?\b|DISJONCTEUR|RACCORD|\bCOSSES?\b|CONTACTEUR|\bVG\b|RELAIS|MODULE|"
             r"VOYANT|INTERRUPTEUR|SWITCH|PUSH|DIODE|RESISTANCE|SOCLE|EQUIPEMENT|BOUTON")
_F_CABLEOBJ = _S(r"\b(?:CABLES?|FILS?|BIFILAIRES?|TRIFILAIRES?|QUADRAX|SHUNTS?|FIBRES?)\b|\b\d{4}\s?-\s?\d{3,4}\b")
_F_SHUNT_ELEC = _S(r"SHUNTS?|\bDIODES?\b|\bCONTACTS?\b|CONNECTEUR|\bMODULES?\b|\bBORNES?\b|\bPRISES?\b|BACKSHELL|ELEMENT")
_F_STRUCT = _S(r"RAMPES?\b|STRUCTURE|TUYAUT\w*|RIVET\w*|COLONNETTE|PANNEAU|CLOISON|PLANCHER|PEINTURE|BIELLE|PLATINE|FILETAGE|TARAUD\w*|"
               r"HELICOIL|\bINSERT\b|MAIN\s+COURANTE|\bTOLE\b")
_F_TIGHT = _S(r"TORQU|SERRAGE|DESSERR|NON\s+SERREE?S?|MAL\s+SERREE?S?|PAS\s+SERREE?S?|\bLACHE|JEU\b|BOUGE")
_F_CLASH = _S(r"CLASH|\bCONTACT\s+(?:ENTRE|AVEC)|EN\s+CONTACT|FROTT\w*|TOUCHE")
_F_ROUTE = _S(r"CHEMINEMENT|TENSION|TENDUE?S?|SUR-?\s?LONGUEUR|SURLONGEUR|RAYON\s+DE\s+COURBURE|TORON|SORTIE?S?\s+(?:DE|DES|DU)|"
              r"RESSORT\s+DU|LONGUEUR|TROP\s+COURTE?|HARNAIS")
_F_CRIMP = _S(r"SERTI|DENUD|\bBRINS?\b|SOUDURE|AUTO-?\s?SOUDEUR|FERRULE|\bCOSSES?\b|\bCONTACTS?\b|PINCE")
_F_CRIMP_SPEC = _S(r"QUADRAX|TWINAX|TRIAX|COAX|FIBRE|OPTIQUE|BRASURE|BUSCAN")
_F_UNFINISHED = _S(r"NON\s+TERMINE|NON\s+REPRIS|REPRENDRE\s+(?:LE\s+)?CABLAGE|NON\s+FINI|A\s+FINIR|FINIR\s+LE|CABLAGE\s+NON\s+CONFORME")
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
    if cable or t == "MANQUANT_CABLE_ELEMENT" and not (_F_COLLAR.search(x) or _F_SLEEVE.search(x) or _F_PLUG.search(x) or _F_PLATE.search(x)):
        return "Manquant – câble / shunt / élément"
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
            "Cable problems": "Manquant – câble / shunt / élément"}.get(c, "Manquant – mécanique / freinage")


def _damage_object(x, t, c, cable, etat):
    if (cable and (etat == "DOMMAGE" or _F_DMG.search(x))) or t == "DOMMAGE_CABLE" and _F_CABLEOBJ.search(x):
        return "Dommage – câble"
    if _F_BRAID.search(x) and (_F_BLEU.search(x) or "BRIN" in x):
        return "Dommage – tresse de masse"
    if _F_PLATE.search(x) and not _F_ELEC.search(x):
        return "Dommage – identification"
    if (_F_SLEEVE.search(x) or _F_COLLAR.search(x)) and not _F_ELEC.search(x) and not _F_STRUCT.search(x):
        return "Dommage – habillage"
    if t == "DOMMAGE_STRUCTURE" or c == "Structure & paint" or (_F_STRUCT.search(x) and not _F_ELEC.search(x)):
        return "Dommage – structure"
    if t == "DOMMAGE_HABILLAGE":
        return "Dommage – identification" if _F_PLATE.search(x) else "Dommage – habillage"
    # component (E2): broken / doesn't work / not written
    if _F_RECEIVED.search(x):
        return "Composant – cause non écrite"
    if _F_DMG.search(x):
        return "Dommage – composant cassé"
    if _F_HS.search(x):
        return "Composant HS"
    return "Composant – cause non écrite"


def _wrongref_object(x, c):
    if _F_PLATE.search(x) and not _F_ELEC.search(x) or c == "Plates, labels & markers":
        return "Mauvaise réf. – identification"
    if _F_COLLAR.search(x):
        return "Mauvaise réf. – colliers / frettage"
    if _F_PLUG.search(x) or re.search(r"THERMO|GAINE\s+THERMO", x):
        return "Mauvaise réf. – obturation / thermo"
    if (_F_MECH.search(x) and not re.search(r"\bCONTACTS?\b|CONNECTEUR|\bPRISES?\b|DISJONCTEUR|RELAIS|BACKSHELL|DETROMP", x)) \
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
        if _F_COLLAR.search(x) and not _F_ELEC.search(x):
            return "Frettage / colliers – pose"
        if c == "Loose electrical connection" or (_F_ELEC.search(x) and not re.search(r"\bVIS\b|SERRE.?MODULE|ECROU|RONDELLE|ARRET\s+DE\s+MODULE", x)):
            return "Serrage électrique"
        return "Serrage mécanique"
    if t == "MEO_SERTISSAGE_SPECIFIQUE" and _F_CRIMP_SPEC.search(x) or (_F_CRIMP.search(x) and _F_CRIMP_SPEC.search(x)):
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
    if t == "MEO_SERTISSAGE_SPECIFIQUE":
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
    if t == "PROCESS_DOSSIER":
        add("Dossier")
    # 3. upstream (print room) — exceptions E3/E4 and Q12
    imp = str(tracker_imp or "")
    from_print = prov == "RECU" or imp.startswith("Salle impression")
    if cable and allow_upstream:
        if from_print and (etat == "DOMMAGE" or _F_DMG.search(x)):
            add("Amont · Câble")                                           # E3
        if (_F_MISS.search(x) or t == "MANQUANT_CABLE_ELEMENT") and (_F_NOT_SUPPLIED.search(x) or imp.startswith("Salle impression")):
            add("Amont · Câble")                                           # E4
        if from_print and etat == "LONGUEUR":
            add("Amont · Câble")                                           # Q12-003
        if _F_PRINT.search(x) and not _F_DMG.search(x):
            add("Amont · Câble")                                           # Q12-001..004
    if t == "AMONT_IMPRESSION" and (from_print or not cable):
        add("Amont · Identification / barrette VT" if (_F_PLATE.search(x) or re.search(r"\bVT\b|BARRETTE|RAIL", x)) and not cable
            else ("Cheminement – longueur / tension" if re.search(r"HARNAIS", x) and not cable else "Amont · Câble"))
    # 4. bonding (Q09 / T07) — a damaged braid is Q11-009 (code sheet)
    bond = c == "Bonding" or t == "MEO_METALLISATION" or (_F_BLEU.search(x) and re.search(r"\bBLEUS?\b|METALLI|METALISATION|BONDING|MASSE", x)
                                                         and not _F_CABLEOBJ.search(x))
    if _F_BRAID.search(x) and re.search(r"MASSE|METALLI", x) and (_F_DMG.search(x) or re.search(r"\bBRINS?\b", x)):
        add("Dommage – tresse de masse")
    if bond:
        if re.search(r"INVERSION|AU\s+LIEU", x) and _F_BRAID.search(x):
            add("Mauvaise réf. – électrique / détrompage")                 # braid wrong place = Q04-011
        elif _F_MEASURE.search(x) or re.search(r"NON\s+CONNECTE|NOT\s+CONNECTED|POINT\s+DE\s+MASSE", x):
            add("Point de masse / mesure")
        elif re.search(r"(?:MANQU\w*|OUBLI\w*|PAS)\s+(?:DE\s+|DU\s+|LE\s+|LES\s+)?BLEU|BLEU\w*\s+(?:MANQUANT|NON\s+APPLIQUE)|"
                       r"PROTECTION\s+NON\s+APPLIQUEE|MANQU\w*\s+(?:LE\s+)?BLEU", x):
            add("Bleu non appliqué")
        else:
            add("Bleu mal appliqué / débordant")
    # 5. branchement
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
    missing = (t.startswith("MANQUANT_") or bool(_F_MISS.search(x))) and not (
        re.search(r"MANQUAIT\s+LA\s+GLISSIERE", x) and _F_DMG.search(x))
    if missing and not (c in ("Damaged equipment",) and _F_DMG.search(x) and not t.startswith("MANQUANT_")):
        add(_missing_object(x, t, c, cable and t != "MEO_CHEMINEMENT"))
    damaged = t.startswith("DOMMAGE_") or c in ("Damaged equipment", "Faulty or non-conforming part", "Structure & paint") \
        or (_F_DMG.search(x) and not (cable and etat == "LONGUEUR"))
    if c == "Structure & paint" and re.search(r"PEINTURE", x) and missing:
        add("Dommage – structure")
    if damaged:
        add(_damage_object(x, t, c, cable, etat))
    # 7. wrong reference / position, identification positioning (tie-break: upside down / offset = Q06-010)
    if _F_PLATE.search(x) and _F_POSITION.search(x) and not re.search(r"INVERSION|AU\s+LIEU|MAUVAISE?\s+REF|ERREUR\s+(?:DE\s+)?(?:MANCHON|REF)|NOTEE?\s+EN\s+FAIT", x):
        add("Identification – positionnement")
    if t in ("ERREUR_REF_HABILLAGE", "ERREUR_REF_ELECTRIQUE") or c == "Wrong part or position" or _F_WRONGREF.search(x):
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


def souscat_of(text, code=None, sub_code=None, type_reporting="", categorie="", defaut_cable=False,
               etat_cable="", provenance="", tracker_imputation=None):
    """-> (sous_categorie, source). source: SOUS-CODE | CODE | CODE+TEXTE | TEXTE | AUCUN."""
    x = _cat_norm(text)
    t, c = type_reporting or "", categorie or ""
    cable = str(defaut_cable).strip().lower() in ("true", "1", "t")
    etat = etat_cable if isinstance(etat_cable, str) else ""
    sc = (sub_code or "").strip().upper() if isinstance(sub_code, str) else ""
    if sc in SUBCODE_TO_SOUSCAT:
        return SUBCODE_TO_SOUSCAT[sc], "SOUS-CODE"
    m = re.match(r"^\s*([QT]\d{2})", str(code or "").upper())
    head = m.group(1) if m and m.group(1) in HEAD_SOUSCATS else None
    cands = _text_candidates(x, t, c, cable, etat, provenance, tracker_imputation, allow_upstream=head is None)
    if head:                                                               # the written code always wins
        allowed = HEAD_SOUSCATS[head]
        for lab in cands:
            if lab in allowed:
                return lab, "CODE+TEXTE"
        if head == "Q11":
            lab = _damage_object(x, "DOMMAGE_COMPOSANT", c, cable, etat)
            return (lab if lab in allowed else _DEFAULT_OF_HEAD[head]), "CODE"
        return _DEFAULT_OF_HEAD[head], "CODE"
    if cands:
        return cands[0], "TEXTE"
    return "Non classé", "AUCUN"


def groupe_of_souscat(souscat: str) -> str:
    return SOUS_CATEGORIES.get(souscat, ("Non classé",))[0]


def rca_type_of(souscat: str) -> str:
    return SOUS_CATEGORIES.get(souscat, (None, "AUTRE"))[1]


def reference_table():
    """The 123 official sub-codes, each with its one sub-category, group and RCA type (list of dicts)."""
    return [{"sous_code": sc, "sous_categorie": lab, "groupe": g, "rca_type": t, "rca_mode": mode_of(t)}
            for lab, (g, t, scs, _) in SOUS_CATEGORIES.items() for sc in scs]
