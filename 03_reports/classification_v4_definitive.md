# Classification des défauts — spécification définitive (v4)
### Types de reporting · règles de classification · parseur · preuves
*Centre électrique FTO2 · 4 septembre 2026*

---

## 0. Le principe qui règle tout

**Une seule cible : le sous-code officiel. Tout le reste est une table de correspondance.**

```
sous-code officiel (123)  ──plusieurs→un──►  type de reporting (26)  ──fonction──►  mode d'erreur (6)
```

Trois conséquences, chacune vérifiée sur les données :

1. **L'agent ne choisit jamais un type.** Il choisit un code officiel — dans l'outil de saisie, ou en tête de ligne comme le fait déjà l'équipe test. Type et mode en sont déduits.
2. **Les types sont purs par nature.** Chaque type vit dans exactement un mode : un frettage manquant et un frettage desserré sont deux types différents parce que ce sont deux problèmes différents (Q03-005 vs Q05-004 dans la grille). Mode → type est donc un arbre strict, pas deux axes qui se croisent. *Vérifié : 0 type sur 26 n'apparaît sous plus d'un mode.*
3. **Le préfixe du type dit le mode.** `MANQUANT_*` = omission, `MEO_*` = exécution, `DOMMAGE_*` = manipulation, `ERREUR_REF_*` = sélection. Il n'y a rien à mémoriser.

Ce qui a été abandonné, et pourquoi : la version précédente classait *objet* et *mode* par deux jeux de règles indépendants, puis recollait les paires. Deux classifieurs indépendants multiplient les erreurs, la grille 15 × 6 fabrique une cinquantaine de combinaisons qui n'existent dans aucun sous-code officiel, et le mode est un attribut *causal* (jamais posé ? posé lâche ?) que le texte libre ne porte souvent pas — ce sont les codes Q03 / Q05 qui le portent, c'est-à-dire le jugement de l'inspecteur. Classer directement vers un type de sous-code supprime les trois problèmes d'un coup.

---

## 1. Les 26 types de reporting, par mode

Volumes mesurés sur 2 346 défauts réels (807 NC, H1 2026).

### SÉLECTION — 891 défauts (38%) · *bonne pièce, mauvais choix parmi des semblables* → détrompage, marquage, layout. **Pas la formation.**

| Type | Sous-codes officiels | Défauts |
|---|---|---|
| INVERSION_BRANCHEMENT | T04 | 372 |
| ERREUR_BRANCHEMENT | T02 | 299 |
| ERREUR_REF_HABILLAGE | Q04-001/002/003/006/007/008/010/012/013/014 | 153 |
| ERREUR_REF_ELECTRIQUE | Q04-004/005/009/011 | 67 |

### EXÉCUTION — 560 défauts (24%) · *le geste est fait, pas au standard* → outillage, calibration, gamme, formation au geste

| Type | Sous-codes officiels | Défauts |
|---|---|---|
| MEO_FRETTAGE_COLLIER | Q05-004, Q06-006/011/012 | 144 |
| MEO_SERRAGE | Q05-001/002/003/005 | 97 |
| MEO_GAINAGE | Q06-002/003/007/008 | 90 |
| MEO_CHEMINEMENT | Q06-001/004/005 | 86 |
| MEO_SERTISSAGE_STANDARD | Q07-001…010 | 56 |
| MEO_METALLISATION | Q09-001…006, T07 | 42 |
| MEO_SERTISSAGE_SPECIFIQUE | Q08-001…007 | 32 |
| MEO_FINITION | Q06-009/010 | 8 |
| MESURE_NON_CONFORME | T06, T08 | 5 |

### OMISSION — 417 défauts (18%) · *une étape ou une pièce a été sautée* → signal forçant, auto-contrôle au poste, place-keeping

| Type | Sous-codes officiels | Défauts |
|---|---|---|
| MANQUANT_HABILLAGE | Q03-002/003/005/006/010 | 140 |
| OUBLI_VERROUILLAGE | Q01-001/002/003 | 110 |
| MANQUANT_CABLE_ELEMENT | Q03-004, T01, T03 | 89 |
| MANQUANT_OBTURATION | Q03-001/007/008 | 32 |
| FOD | Q16-001…006 | 20 |
| MANQUANT_IDENTIFICATION | Q03-009/011/012 | 15 |
| NON_CONNECTE | T05 | 11 |

### MANIPULATION — 273 défauts (12%) · *endommagé en manutention* → protection, conditionnement, environnement

| Type | Sous-codes officiels | Défauts |
|---|---|---|
| DOMMAGE_COMPOSANT | Q11-003/005/006/009/012/016/018/019/022 | 144 |
| DOMMAGE_STRUCTURE | Q10-001…006 | 61 |
| DOMMAGE_CABLE | Q11-001/014 | 53 |
| DOMMAGE_HABILLAGE | Q11-002/004/007/008/010/011/013/026 | 15 |

### AMONT — 77 défauts (3%) · *arrivé faux* → fournisseur, atelier câbles, appro

| AMONT_IMPRESSION | Q12-001…008 | 77 |
|---|---|---|

### PROCESS — 4 défauts (0%) · *documentation, traçabilité*

| PROCESS_DOSSIER | Q13-001…005 | 4 |
|---|---|---|

**AUTRE (soupape) — 124 défauts (5,3%).**

Qualité de l'axe : plus gros type à **15,9%** (aucun ne noie le Pareto — `defect_code` SAP en met 43% dans un seul bucket) ; top 5 = 51% ; couverture **123 / 123** sous-codes ; le mode se lit sur le code de tête sans exception (`Q03` → omission, `Q04` → sélection, `Q05`–`Q09` → exécution, `Q10`/`Q11` → manipulation, `Q12` → amont, `Q13` → process, `T02`/`T04` → sélection, `T01`/`T03`/`T05` → omission, `T06`–`T08` → exécution).

---

## 2. Les règles de classification

Pour un défaut, dans l'ordre. On s'arrête à la première règle qui répond.

| # | Condition | Résolution | Confiance | Volume réel |
|---|---|---|---|---|
| 1 | Le sous-code officiel est écrit (outil de saisie, gabarit) | table `SUBCODE_TYPE` | **HIGH** | 0 aujourd'hui, 100% demain |
| 2 | Un code de tête à type unique est écrit (16 sur 21 : Q01, Q07–Q10, Q12, Q13, Q16, T01–T08) | table `HEAD_TYPE` | **HIGH** | 748 (32%) |
| 3 | Un code de tête multi-types est écrit (Q03, Q04, Q05, Q06, Q11) | mots-clés **restreints** aux types de ce code | **MEDIUM** | 103 |
| 3b | Idem, aucun mot-clé ne répond | type par défaut du code ; le mode reste certain | LOW | 37 |
| 4 | Pas de code, mot-clé sur un type à rappel mesuré ≥ 0,90 | règles libres | **MEDIUM** | 290 |
| 5 | Pas de code, mot-clé sur un autre type | règles libres | LOW | 1 022 |
| 6 | NC narrative mono-défaut, champ SAP « Type of nonconformity » exploitable | table `SAP_PRIOR` | LOW | 22 |
| 7 | Rien | AUTRE | NONE | 124 |

**Règles à mots-clés (règles 3–5).** 26 patrons, un par type, dans l'ordre du spécifique au générique, sur texte en majuscules sans accents. Chaque patron encode *objet + symptôme ensemble* — `(OBTURATEUR|BOUCHON|…)[^.]{0,25}(MANQU|ABSENT)` — de sorte qu'un patron ne peut atterrir que sur un type qui existe. Il n'y a ni classifieur de mode séparé, ni règle de recollage. Trois points d'ordre méritent d'être connus : `ARRET DE BLINDAGE` est routé vers le sertissage standard *avant* la règle « spécifique » parce que l'équipe le code Q07 ; la technologie (quadrax, coax, fibre) est le seul indice qui distingue Q08 de Q07 dans le texte, donc « contact à refaire » sans technologie va au standard par défaut ; `NON CONNECTE` précède les règles de branchement pour ne pas être avalé par « inversion ».

**Signal SAP (règle 6).** 90% des NC portent une ligne `Type of nonconformity : …`. Elle est générique pour les bundles (« Harness ») mais discriminante pour les NC mono-défaut (« Harness length », « Electrical crimping », « Wiring damage », « Broken »…). Elle n'est utilisée qu'en dernier recours, sur les formats `narrative` et `fal_single`, et toujours en LOW. Personne ne l'exploitait.

**Niveaux de confiance — ce qu'ils signifient pour le tableau de bord.** HIGH = le code fait foi. MEDIUM = mot-clé sur un type dont le rappel a été *mesuré* fiable. LOW = inféré, à afficher comme tel. Un Pareto se trace sur HIGH + MEDIUM (49% aujourd'hui) avec le reste en hachuré ; la proportion HIGH monte mécaniquement avec l'adoption de l'outil de saisie.

---

## 3. Preuves

Toutes mesurées sur les 807 NC de l'extract, avec le fichier livré.

**Découpage et comptage — inchangés.** 95% exacts, 99% à ±1 contre le comptage manuel ; 2 346 défauts. La refonte de la classification n'a touché aucune ligne du moteur de découpage.

**Exactitude des mots-clés — mesurée, pas déclarée.** Sur les 748 défauts dont le code de tête fixe la vérité, la classification *par mots-clés seuls* (code ignoré) donne **98% de bonnes réponses**. Le chiffre honnête est en dessous : ces 748 sont dominés par les inversions et mauvaises bornes, faciles. Sur les 129 défauts des **autres types, l'exactitude est de 93%** (elle était de 80% avec la taxonomie précédente). Rappel par type : inversion 0,99 · erreur branchement 0,99 · verrouillage 0,99 · câble/élément manquant 1,00 · non connecté 1,00 · sertissage standard 0,91 · sertissage spécifique 0,70. Erreurs silencieuses (mauvais type au lieu d'AUTRE) : 2%.

**Ce que l'ancienne taxonomie ne voyait pas — retrouvé.** Cinq types affichaient zéro parce qu'aucune règle ne les cherchait. Ils ont maintenant du volume : DOMMAGE_STRUCTURE 61, MEO_FINITION 8, MESURE_NON_CONFORME 5, PROCESS_DOSSIER 4, et le shunt est fondu dans MANQUANT_CABLE_ELEMENT. AUTRE passe de 8,1% à **5,3%**.

**Arbre strict — vérifié.** 0 type sur 26 n'apparaît sous plus d'un mode dans la sortie réelle.

**Limite connue, énoncée.** 46% des défauts historiques sont en confiance LOW : ce sont les textes sans code du contrôle final et de l'inspection MIP. Cette information n'existe pas dans le texte et aucune regex ne l'inventera. Elle est **irrécupérable dans l'historique et entièrement résolue à la source** par l'outil de saisie — c'est l'argument, pas un aveu.

---

## 4. Le parseur livré — `nc_defect_parser.py`

Un fichier, Python standard (regex + unicodedata ; pandas uniquement pour l'aide DataFrame), transposable tel quel en UDF PySpark.

```python
from nc_defect_parser import explode_dataframe, parse_nc
nc_df, defects_df = explode_dataframe(df, manual_count_col="Ext_Nb_Defauts")
```

Colonnes de `defects_df` : `notification_number, seq, code, sub_code, fin, loc, qty, text, source_format, type_reporting, mode_erreur, confidence, resolved_by, severite, severite_off, cdve, sap_type`.

Structure du fichier : moteur de découpage (9 formats, tolérance aux fautes, listes, gabarit `DEFAUTS v1`) → tables (`TYPES`, `SUBCODE_TYPE`, `SUBCODE_MAJEURE`, `HEAD_TYPE`, `HEAD_CANDIDATES`, `SAP_PRIOR`) → `RULES` → `classify()` → API. Les tables sont la source unique de vérité ; `mapping_v4_codes_types.csv` en est généré, pas l'inverse.

---

*Livrés : `nc_defect_parser.py` · `mapping_v4_codes_types.csv` · `defects_split_v4.csv` (2 346 défauts classés) · `nc_with_counts_v4.csv`.*
