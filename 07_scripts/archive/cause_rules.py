# v4.5 — ROOT CAUSE, LEVEL 1 vs LEVEL 0  (draft, pasted into the parser once settled)
import re

# label -> (groupe, niveau, what it means)
CAUSES = {
    # Ligne: the wrong operation is known
    "Inversion":                   ("Ligne", 1, "Deux câbles, prises ou repères échangés."),
    "Mauvaise borne":              ("Ligne", 1, "Un câble branché sur la mauvaise borne ou prise."),
    "Verrouillage oublié":         ("Ligne", 1, "Contact ou connecteur laissé déverrouillé."),
    "Branchement oublié":          ("Ligne", 1, "Câble, prise ou tresse laissé non branché."),
    "Pose oubliée":                ("Ligne", 1, "Élément non posé: collier, gaine, obturateur, shunt, étiquette, bleu…"),
    "Mauvaise pièce montée":       ("Ligne", 1, "Mauvaise référence, longueur de vis, calibre ou contact."),
    "Pièce mal positionnée":       ("Ligne", 1, "Orientation, détrompage, position ou fixation d'une pièce."),
    "Frettage mal fait":           ("Ligne", 1, "Frette ou collier trop serré, lâche, mal coupé, mal placé."),
    "Cheminement mal fait":        ("Ligne", 1, "Clash, tension, sur-longueur, rayon, câble sorti du toron."),
    "Gaine ou obturateur mal posé":("Ligne", 1, "Gaine, thermo, manchon ou obturateur mal posé."),
    "Serrage mal fait":            ("Ligne", 1, "Vis, cosse, backshell ou prise non serré ou desserré."),
    "Sertissage mal fait":         ("Ligne", 1, "Sertissage, contact, brin ou soudure à reprendre."),
    "Métallisation mal faite":     ("Ligne", 1, "Bleu de métallisation débordant, mesure de masse hors tolérance."),
    "Endommagé au montage":        ("Ligne", 1, "Abîmé par un outil, un serrage ou une manipulation (écrit dans la NC)."),
    "Reprise d'une autre erreur":  ("Ligne", 1, "Câble recoupé ou abîmé pendant une retouche; l'erreur d'origine n'est pas écrite."),
    "FOD laissé":                  ("Ligne", 1, "Corps étranger laissé."),
    # Amont: made wrong before it reached the line
    "Salle d'impression":          ("Amont", 1, "Câble, étiquette ou plaquette reçu court, abîmé, mal marqué ou non fourni."),
    "Pièce reçue non conforme":    ("Amont", 1, "Pièce livrée non conforme: fournisseur, réception, QSR."),
    # Méthodes & moyens
    "Définition (BE)":             ("Méthodes & moyens", 1, "Plan ou définition en cause."),
    "Outillage":                   ("Méthodes & moyens", 1, "Outil défectueux (pince à sertir…)."),
    "Process non respecté":        ("Méthodes & moyens", 1, "Dossier, instruction ou processus non appliqué."),
    # Niveau 0: only the state of the product is written
    "Câble court ou coupé":        ("Niveau 0", 0, "Câble trop court ou coupé; l'opération en cause n'est pas écrite."),
    "Câble abîmé":                 ("Niveau 0", 0, "Câble abîmé; l'opération en cause n'est pas écrite."),
    "Câble manquant":              ("Niveau 0", 0, "Câble manquant; non fourni ou perdu, pas écrit."),
    "Pièce endommagée":            ("Niveau 0", 0, "Pièce cassée, rayée, déchirée, effacée; cause pas écrite."),
    "Pièce défectueuse":           ("Niveau 0", 0, "Pièce HS ou non conforme; origine pas écrite."),
    "Non précisé":                 ("Niveau 0", 0, "Le texte ne dit pas ce qui s'est passé."),
}

_C = lambda p: re.compile(p)
# A. The NC names the earliest error ("suite à…", "par la pince…"). First match wins.
_EXPLICIT = [
    ("Définition (BE)",        _C(r"MODIFICATION\s+DU\s+DESIGN|MISE\s+A\s+JOUR\s+NON\s+FAITE|PAR\s+LE\s+BE\b|A\s+LA\s+DEF\b|"
                                  r"ERREUR\s+(?:DE|DU|SUR\s+LE)\s+PLAN|PLAN\s+(?:ERRONE|FAUX)|ERREUR\s+DE\s+DEFINITION")),
    ("Outillage",              _C(r"PINCE\s+A\s+SERTIR[^.]{0,80}DEFECTUEU|OUTILLAGE|OUTIL\s+(?:NON\s+CONFORME|DEFECTUEUX)")),
    ("Salle d'impression",     _C(r"MARQUAGE\s+DEF+ECTUEUX|MAL\s+MARQUEE?S?|NON\s+LASERISEE?S?|PAS\s+(?:ETE\s+)?LASERISEE?S?|"
                                  r"NON\s+IMPRIMEE?S?|PAS\s+(?:ETE\s+)?IMPRIMEE?S?|MAL\s+IMPRIMEE?S?|ERREUR\s+D.?IMPRESSION|"
                                  r"DE\s+L.?IMPRESSION|RAPID\s?SHARE|FIN\s+DE\s+BOBINE|ERREUR\s+D.?ETIQUETTE|NOTEE?\s+EN\s+FAIT")),
    ("Inversion",              _C(r"SUITE\s+A\s+(?:UNE?\s+|L.?\s?|DES?\s+)?INVERSION")),
    ("Sertissage mal fait",    _C(r"SUITE\s+A\s+(?:UNE?\s+)?(?:ERREUR\s+DE\s+|MAUVAIS\s+)SERTISSAGE")),
    ("Cheminement mal fait",   _C(r"SUITE\s+A\s+(?:UNE?\s+)?(?:MAUVAIS|ERREUR\s+DE)\s+CHEMINEMENT|MAL\s+CHEMINEE?S?")),
    ("Frettage mal fait",      _C(r"(?:FRETT?ES?|COLLIERS?|TYRAPS?)\s+TROP\s+SERREE?S?")),
    ("Process non respecté",   _C(r"PROCESSUS\s+NON\s+RESPECTE|INSTRUCTIONS?\s+OU\s+EXIGENCES?\s+NON\s+RESPECTEE?S?")),
    ("Mauvaise pièce montée",  _C(r"UTILISATION\s+D.?UNE?\s+\w+\s+NON\s+CONFORME")),
    ("Endommagé au montage",   _C(r"PAR\s+LA\s+PINCE|LORS\s+DU\s+(?:TORQUAGE|SERRAGE|MONTAGE\s+DU)|S.?EST\s+ABIMEE?\s+LORS|"
                                  r"NOUS\s+AVONS\s+(?:ENDOMMAGE|ABIME|CASSE)|MAUVAISE\s+MANIPULATION|"
                                  r"(?:ABIMEE?S?|ENDOMMAGEE?S?|CASSEE?S?)\s+PAR\s+(?:LA\s+PROD|L.?OPERAT|LE\s+COMPAGNON)")),
    ("Reprise d'une autre erreur", _C(r"SUITE\s+A\s+(?:UNE?\s+|LA\s+)?(?:RETOUCHE|REPRISE|REPARATION)|"
                                  r"SUITE\s+A\s+UNE?\s+ERREUR\b|LORS\s+DE\s+LA\s+(?:RETOUCHE|REPRISE)")),
]
# B. Received / supplier signals (for non-cable parts)
_RECEIVED = _C(r"RECUE?S?\s+AVEC|NOUS\s+AVONS\s+RECUE?\s+UN\s+LOT|A\s+RECEPTION|LORS\s+DE\s+LA\s+RECEPTION|\bINCOMING\b|"
               r"LIVREE?S?\s+PAR\s+LE\s+FOURNISSEUR|FOURNISSEUR|NE\s+CORRESPONDENT\s+PAS|\bQSR\b|NON\s+CONFORMES?\s+AU\s+PLAN|"
               r"\bRECUE?S?\s+(?:NE\s+SONT\s+PAS|SONT\s+NON|NON)|DATE\s+CODE")
_MISSING = _C(r"MANQU\w*|\bMANQUE\b|OUBLI\w*|ABSENTE?S?\b|PAS\s+DE\b|N.?EST\s+PLUS\s+PRESENTE?|NON\s+POSEE?S?")
_DAMAGED = _C(r"CASSEE?S?\b|\bABIMEE?S?\b|ENDOM+AGE\w*|DETERIORE\w*|\bRAYEE?S?\b|RAILLEE?S?|RAYURES?|FISSURE\w*|TORDUE?S?\b|"
              r"DEFORM\w*|ARRACHE\w*|ECRASEE?S?\b|\bIMPACTS?\b|SCRAPE|DECHIRE\w*|EFFACEE?S?|DECOLLEE?S?|BRISE\w*|FENDUE?S?\b")
_POSITION = _C(r"ORIENT\w*|DETROMP\w*|\bSENS\b|POSITION\w*|PLACEE?S?\b|PLACEMENT|A\s+L.ENVERS|MAUVAIS\s+COTE|CENTR\w*|DECALEE?S?|"
               r"MAL\s+(?:ATTACHEE?S?|FIXEE?S?|MONTEE?S?|INSEREE?S?)|A\s+FIXER|NON\s+MAINTENUE?S?|TIENT\s+PAR|INVERSION\s+DE\s+MONTAGE")
_WRONGREF = _C(r"MAUVAISE?\s+(?:REFERENCE|MODULE|CONNECTEUR|PRISE|EQUIPEMENT|PIECE|VIS|CONTACT)|ERREUR\s+(?:DE\s+)?(?:REFERENCE|MODULE|GAUGE|JAUGE)|"
               r"AU\s+LIEU\s+D|TROP\s+(?:COURTE?S?|LONGUE?S?)|REFERENCE\s+(?:DU|DE)\s+\w+\s+(?:N.EST\s+PAS|NON)\s+CONFORME|"
               r"N.EST\s+PAS\s+LA\s+BONNE|MONTEE?S?\s+AU\s+LIEU")
_SHUNT_MISSING = _C(r"SHUNTS?\b[^.]{0,60}MANQU|MANQU\w*[^.]{0,20}SHUNTS?")
_CABLE_NOT_SUPPLIED = _C(r"PAS\s+(?:ETES?\s+)?FOURNIE?S?|NON\s+FOURNIE?S?|NON\s+LIVREE?S?|PAS\s+(?:ETE\s+)?LIVREE?S?|NON\s+RECUE?S?|"
                         r"MANQUANTE?S?\s+A\s+LA\s+RECEPTION")


def _truthy(v) -> bool:
    return str(v).strip().lower() in ("true", "1", "t")


def cause_of(categorie, type_reporting, defaut_cable, provenance, etat_cable, text, tracker_imputation=None):
    """-> (cause_n1, niveau, cause_source). Level 1 = the wrong operation (or the upstream
    step) is named; level 0 = only the state of the product is written."""
    x = _cat_norm(text)
    t = type_reporting or ""
    cat = categorie or ""
    cable = _truthy(defaut_cable)
    imp = str(tracker_imputation or "")
    missing_type = t.startswith("MANQUANT_")

    def out(c, src):
        return c, CAUSES[c][1], src

    # A. the text names the earliest error
    for c, pat in _EXPLICIT:
        if pat.search(x):
            return out(c, "TEXTE")
    # B. origin known from the cable team's tracker or from "reçu / fournisseur"
    if imp.startswith("Salle impression"):
        return out("Salle d'impression", "TRACKER")
    if imp.startswith("Définition"):
        return out("Définition (BE)", "TRACKER")
    if imp.startswith("Fournisseur"):
        return out("Pièce reçue non conforme", "TRACKER")
    if provenance == "RECU":
        return out("Salle d'impression" if (cable or cat == "Plates, labels & markers") else "Pièce reçue non conforme", "PROVENANCE")
    if _RECEIVED.search(x) and not cable:
        return out("Salle d'impression" if cat == "Plates, labels & markers" else "Pièce reçue non conforme", "TEXTE")
    # C. the defect itself is the error
    if t == "PROCESS_DOSSIER":
        return out("Process non respecté", "TYPE")
    if cat == "Cable problems":
        if _SHUNT_MISSING.search(x):
            return out("Pose oubliée", "TEXTE")
        if _CABLE_NOT_SUPPLIED.search(x):
            return out("Salle d'impression", "TEXTE")
        if t == "INVERSION_BRANCHEMENT":
            return out("Inversion", "TYPE")
        if etat_cable == "LONGUEUR":
            return out("Câble court ou coupé", "TYPE")
        if etat_cable == "DOMMAGE":
            return out("Câble abîmé", "TYPE")
        if t == "MANQUANT_CABLE_ELEMENT" or _MISSING.search(x):
            return out("Câble manquant", "TYPE")
        if re.search(r"\bCOUPEE?S?\b|COURTE?S?\b", x):
            return out("Câble court ou coupé", "TYPE")
        if _DAMAGED.search(x):
            return out("Câble abîmé", "TYPE")
        return out("Non précisé", "TYPE")
    if cat == "Wiring errors":
        return out("Inversion" if (t == "INVERSION_BRANCHEMENT" or "INVERS" in x) else "Mauvaise borne", "TYPE")
    if cat == "Connectors not locked":
        return out("Verrouillage oublié", "TYPE")
    if cat == "Not connected":
        return out("Branchement oublié", "TYPE")
    if cat == "FOD":
        return out("FOD laissé", "TYPE")
    if cat == "Plates, labels & markers":
        if "INVERS" in x:
            return out("Inversion", "TYPE")
        if missing_type or _MISSING.search(x):
            return out("Pose oubliée", "TYPE")
        if _DAMAGED.search(x):
            return out("Pièce endommagée", "TYPE")
        if _POSITION.search(x):
            return out("Pièce mal positionnée", "TYPE")
        if t == "MEO_FRETTAGE_COLLIER":
            return out("Frettage mal fait", "TYPE")
        return out("Non précisé", "TYPE")
    if cat in ("Tie-wraps & clamps", "Routing & harness dressing", "Sleeves & protection", "Plugs & caps", "Bonding"):
        if missing_type or t == "NON_CONNECTE" or _MISSING.search(x):
            return out("Pose oubliée", "TYPE")
        if _DAMAGED.search(x) and cat != "Routing & harness dressing":
            return out("Pièce endommagée", "TYPE")
        return out({"Tie-wraps & clamps": "Frettage mal fait", "Routing & harness dressing": "Cheminement mal fait",
                    "Sleeves & protection": "Gaine ou obturateur mal posé", "Plugs & caps": "Gaine ou obturateur mal posé",
                    "Bonding": "Métallisation mal faite"}[cat], "TYPE")
    if cat == "Screws & mechanical fixing":
        if _WRONGREF.search(x):
            return out("Mauvaise pièce montée", "TYPE")
        if missing_type or _MISSING.search(x):
            return out("Pose oubliée", "TYPE")
        if _DAMAGED.search(x):
            return out("Pièce endommagée", "TYPE")
        return out("Serrage mal fait", "TYPE")
    if cat == "Loose electrical connection":
        return out("Serrage mal fait", "TYPE")
    if cat == "Contacts & crimping":
        if _WRONGREF.search(x):
            return out("Mauvaise pièce montée", "TYPE")
        if _MISSING.search(x) and not re.search(r"SERTI|BRIN", x):
            return out("Pose oubliée", "TYPE")
        return out("Sertissage mal fait", "TYPE")
    if cat == "Wrong part or position":
        if "INVERS" in x:
            return out("Inversion", "TYPE")
        if _POSITION.search(x) and not _WRONGREF.search(x):
            return out("Pièce mal positionnée", "TYPE")
        return out("Mauvaise pièce montée", "TYPE")
    if cat in ("Damaged equipment", "Structure & paint"):
        if cat == "Structure & paint" and _MISSING.search(x) and not _DAMAGED.search(x) and "PEINTURE" not in x:
            return out("Pose oubliée", "TYPE")
        return out("Pièce endommagée" if (_DAMAGED.search(x) or "PEINTURE" in x or cat == "Damaged equipment") else "Pièce défectueuse", "TYPE")
    if cat == "Faulty or non-conforming part":
        return out("Pièce défectueuse", "TYPE")
    # Other
    if t in ("MEO_CHEMINEMENT",) or re.search(r"REPRENDRE\s+(?:LE\s+)?CABLAGE", x):
        return out("Cheminement mal fait", "TYPE")
    if missing_type:
        return out("Pose oubliée", "TYPE")
    return out("Non précisé", "TYPE")
