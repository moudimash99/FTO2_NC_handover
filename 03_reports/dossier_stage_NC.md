# Dossier de stage — Réduction des non-conformités par la donnée
### Centre électrique (FTO2) · Équipe Qualité · Airbus Atlantic, Toulouse · 2026

*Document de référence complet : contexte, méthode, pipeline, résultats, science de la réduction, standard d'écriture, feuille de route. Rédigé comme mémoire de projet et base de passation.*

---

## Table des matières

1. [Contexte et mission](#1-contexte-et-mission)
2. [La décision d'outillage : Skywise vs Sheets/Qlik](#2-la-décision-doutillage)
3. [Le constat fondateur : le facteur ×3](#3-le-constat-fondateur)
4. [Le pipeline de parsing : `nc_defect_parser.py`](#4-le-pipeline-de-parsing)
5. [La taxonomie des défauts](#5-la-taxonomie-des-défauts)
6. [Le vrai Pareto et les résultats d'investigation](#6-le-vrai-pareto-et-les-résultats)
7. [Le signal actionnable : les connecteurs récurrents](#7-le-signal-actionnable)
8. [Les trois équipes et l'écriture des défauts](#8-les-trois-équipes)
9. [Attribution fournisseur et imputation](#9-attribution-fournisseur-et-imputation)
10. [Audit des colonnes : automatisable, vérifiable, mort](#10-audit-des-colonnes)
11. [Qualité des données : auto vs GPS vs Ext](#11-qualité-des-données)
12. [La science de la réduction des NC](#12-la-science-de-la-réduction)
13. [Le standard d'écriture « DEFAUTS v1 »](#13-le-standard-décriture)
14. [Le tableau de bord proactif](#14-le-tableau-de-bord-proactif)
15. [Feuille de route et prochaines étapes](#15-feuille-de-route)
16. [Inventaire des livrables](#16-inventaire-des-livrables)
17. [Annexe : chiffres clés](#17-annexe-chiffres-clés)

---

## 1. Contexte et mission

Stage sur l'équipe Qualité du centre électrique (FTO2) d'Airbus Atlantic à Toulouse, sous la responsabilité d'Emmanuelle. L'audience de restitution inclut son N+3. Le périmètre couvre la production série : programmes A350, A330, A320 et MT.

La mission centrale est la **réduction des non-conformités (NC)** et du **coût de non-qualité (CONQ)**. L'équipe compte une dizaine de personnes et reçoit des NC en flux continu ; elle est déjà solide et mobilisée sur le terrain. La valeur ajoutée d'un stagiaire data n'est donc pas de « dire quoi corriger » — ce que l'équipe sait déjà — mais de **rendre le problème visible à une résolution où il devient trouvable et prouvable** : passer d'un brouillard de comptages agrégés à une donnée défaut par défaut, structurée, localisée, sur laquelle une action bornée peut être décidée puis mesurée.

Contrainte structurante : la donnée NC est **générée automatiquement** et arrive en continu. L'objectif à terme n'est pas un rapport ponctuel mais un dispositif **proactif** : à mesure que la donnée entre, elle est parsée, structurée, et déclenche des alertes — le tableau de bord signale un problème avant que quelqu'un n'ait à le remarquer.

Point d'attention personnel : la conversion du stage en poste dépend en partie de la démonstration d'une contribution difficilement remplaçable. Le plumbing (migration de plateforme) est remplaçable ; **l'appropriation du problème de non-qualité lui-même** ne l'est pas.

---

## 2. La décision d'outillage

Le choix initial opposait deux chaînes :

- **Rester sur Sheets + Qlik Sense** : la donnée en drives partagés et Google Sheets, visualisée dans Qlik (qui s'intègre à Sheets, pas à Skywise). Rapide, familier, mais non pérenne et hors direction d'entreprise.
- **Migrer vers Skywise** : la plateforme officielle Airbus, où la donnée est **déjà ingérée**. C'est la direction voulue par l'équipe data et l'entreprise.

Deux autres outils internes (Zaccio, Draco) ont été évoqués puis dépriorisés.

**Analyse de la décision.** L'ingestion — la partie réellement lente — étant déjà faite, un tableau de bord Skywise *fonctionnel* sur donnée ingérée est de l'ordre de quelques semaines de travail réel, pas six mois. Le risque n'est pas « ça prend six mois » mais « je passe deux mois à le rendre joli et c'est tout ce que j'ai à montrer ». Le front-end étant un point faible assumé, la victoire ne doit pas se jouer sur le polish visuel mais sur la **couche analytique**.

**Séquencement retenu.** D'abord un hand-merge rapide pour produire un Pareto CONQ et une analyse de récurrence — un livrable qui existe même si rien d'autre n'est fini en novembre. Ensuite, utiliser ce résultat démontré pour justifier la construction du pipeline Skywise. Chaque étape justifie la suivante. La décision d'outillage elle-même est présentée à Emmanuelle comme un **choix d'options à arbitrer**, pas comme une recommandation personnelle — pour réduire le risque politique.

**Ce que la donnée structurée débloque** (impossible en sheets éparses) : Pareto sur le coût et non le compte ; clustering de récurrence et de cause racine ; tendance dans le temps ; et surtout la répétabilité — une capacité appropriable par l'équipe après le départ, versus un rapport ponctuel.

---

## 3. Le constat fondateur

**Le tableau de bord comptait des notifications. Or une notification cache souvent une liste entière de défauts individuels, écrite en texte libre dans la description longue — invisible au comptage.**

Beaucoup de NC sont des **« bundles »** : une seule NC « RETOUCHES TEST MSN xxxx » ou « Inspection finale MIP MSN xxx » contient une liste numérotée de défauts (`DEF 1-T04 : ...`, `DEF 2-T02 : ...`).

En parsant chaque description longue et en comptant les défauts individuels :

| Métrique | Valeur |
|---|---|
| NC analysées (extract courant) | 807 |
| **Défauts individuels extraits** | **2 346** |
| Multiplicateur | ×2,9 environ |
| NC « bundles » (≥5 défauts) | ~15% des NC portant ~70% du volume de défauts |
| Où se concentrent les bundles | Contrôle final et test |

Conséquence : **toute tendance, tout objectif, toute discussion CONQ basée sur le compteur NC est amortie d'un facteur ~3** — et l'amortissement est maximal exactement là où ça fait mal : contrôle final et test, c'est-à-dire les échappées coûteuses.

Mensuellement, les comptes NC paraissent plats (~110–150/mois) tandis que la charge réelle de défauts tourne à 310–430/mois.

Le comptage parsé a été calibré contre la colonne de comptage manuel `Ext_Nb_Defauts` : après itérations, **95% de correspondance exacte, 99% à ±1 près** (n=314). Autrement dit, l'activité de comptage manuel réalisée aujourd'hui est **automatisable dès maintenant, par regex, sans IA**.

---

## 4. Le pipeline de parsing

`nc_defect_parser.py` — cœur en Python pur (regex + unicodedata), afin que `parse_nc()` soit transposable tel quel en UDF PySpark dans un Code Repository Foundry. pandas n'est requis que pour l'aide DataFrame.

### 4.1 Ce qu'il fait, en quatre étapes

1. **Découper** — séparer chaque NC en défauts individuels.
2. **Compter** — nombre exact de défauts par NC (`nb_defauts`), avec repli sur le comptage manuel pour les textes caviardés.
3. **Classer** — chaque défaut rangé en famille / sous-catégorie.
4. **Localiser** — extraire le connecteur (FIN), le câble, la quantité, la sévérité.

Sortie : deux tables. `nc_df` (entrée + `nb_defauts`, `is_redacted`, `nb_defauts_final`, `flags`) et `defects_df` (une ligne par défaut : `notification_number, seq, code, fin, loc, qty, text, source_format, famille, sous_categorie, severite`).

Usage :
```python
from nc_defect_parser import explode_dataframe
nc_df, defects_df = explode_dataframe(df, manual_count_col="Ext_Nb_Defauts")
```

### 4.2 Les neuf formats d'écriture décodés

Le parsing route par **format**, pas par équipe — plus robuste, car un changement de style ou une nouvelle équipe utilisant un format connu ne casse rien.

1. `DEF 1-T04 : ...` — listes DEF strictes (équipe test)
2. `Def1 : ...` — DEF sans tiret (contrôle final)
3. `Déf. 1 : ...` / `Défaut 1 : ...` — accentué ou mot complet
4. `1 - FIN xxx : ...` — listes numérotées (inspection finale MIP)
5. `1 ) ... ` — listes numérotées à parenthèse
6. `DEF1. ROUTE 1S ...` — point après le numéro
7. `N° 2424-0135 - Type : ...` — listes de câbles
8. Puces tiret après « défauts suivants : » — `dash_list`
9. Narratif libre — `NonConformity 0001 :` ou texte sans en-tête

Formats effectivement rencontrés dans l'extract : `def_list` 1 741 · `narrative` 506 · `numbered_list` 81 · `dash_list` 9 · `fal_single` 9.

### 4.3 Robustesse : le comptage ne dépend pas de la validité du code

**Leçon de conception majeure.** La première version couplait le comptage à la bonne forme du code : le marqueur exigeait `DEF n` puis un code syntaxiquement valide puis deux-points. Résultat : la moindre faute de frappe dans cette zone (`TO4` avec un O au lieu du zéro, `QQ01` doublé, deux-points oublié, code tronqué `TO`) **faisait disparaître le défaut entier du comptage**. Un caractère faux = un défaut invisible. Dans une NC, trois lignes en `TO` avaient réduit un défaut-3 à un défaut-1.

Correctif : le comptage s'ancre sur le seul marqueur `DEF n` ; l'extraction du code est best-effort avec une étape de rescousse (`_norm_code()` : O→0, collapse des lettres doublées, validation). Un code irrécupérable devient `None` — mais **la ligne compte quand même**, et la classification bascule sur les mots-clés (« au lieu de » dit encore MAUVAISE_BORNE même quand le code lit « TO »).

Autres garde-fous : `QTE k` et `( quantité 3 )` parsés pour le comptage ; dédoublonnage des mentions répétées d'un même `DEF n` ; stripping des réponses citées `> X*` qui dupliquent du contenu ; détection des NC « Decision Tree » FAL dont les lignes numérotées sont des *instructions de réparation*, pas des défauts (sinon sur-comptage) ; extraction de sévérité MAJEURE/MINEURE quand les en-têtes de section existent (habitude QRTE).

### 4.4 Historique de calibration

La calibration contre `Ext_Nb_Defauts` a progressé par itérations successives : 88% exact au départ, puis 91% après la tolérance aux fautes de frappe, puis 93–94% après ajout des formats `Déf.`/parenthèses/FAL, puis **95% exact / 99% à ±1** après les listes à puces et le dédoublonnage par préfixe.

Le résidu (~16 NC en écart) est **majoritairement non imputable au parseur** : vérification texte à l'appui, certaines NC énumèrent visiblement plus de défauts que la liste manuelle (ex. le texte liste Déf.1 à 8 quand le manuel dit 3), ou l'inverse. Au-delà de ~95%, « coller au comptage manuel » cesse d'être la bonne cible, car le parseur se met à **corriger** la liste manuelle plutôt qu'à échouer contre elle. D'où le livrable `count_disagreements.csv` : cette liste passe sous un œil humain, le parseur ne court pas après une référence bruitée jusqu'à 100%.

Résidu intrinsèque connu : les lignes décrivant deux défauts d'un souffle (« PRISES 115VMB **ET** 135VMB », « bornes 45 et 60 **PUIS** 46 et 61 ») comptent pour 1. C'est de l'ambiguïté de prose, pas un bug — et c'est exactement ce que le standard d'écriture (§13) élimine à la source.

---

## 5. La taxonomie des défauts

Remplace la liste plate actuelle par **deux niveaux : 8 familles / 23 sous-catégories**, conçus pour que **chaque famille pointe vers un responsable d'action différent** — précisément ce que `defect_code` et `cause_code` échouent à faire aujourd'hui.

### 5.1 Répartition mesurée (2 346 défauts)

| Famille | Défauts | Sous-catégories (compte) |
|---|---|---|
| **BRANCHEMENT** | 879 | inversion bornes (373), mauvaise borne (291), erreur plaquette/réf (204), non connecté (11) |
| **CONNEXION** | 530 | freinage/frettes (136), gaine/backshell (132), déverrouillage (110), serrage/couple (95), sertissage (36), blindage/tresse (21) |
| **INTEGRITE** | 221 | câble endommagé (156), composant HS (36), composant cassé (29) |
| **INSTALLATION** | 217 | cheminement/contrainte (91), fixation/visserie (72), métallisation/bonding (35), orientation (12), FOD/propreté (7) |
| **MANQUANT** | 197 | pièce manquante (134), câble manquant (63) |
| **AUTRE** | 191 | non classé (8,1%) |
| **AMONT_FABRICATION** | 88 | longueur NC (88) |
| **IDENTIFICATION** | 23 | étiquette/marquage (23) |

### 5.2 Logique d'affectation par responsable

- **BRANCHEMENT** — bonnes pièces, mauvaise logique de câblage → instruction / détrompage au poste
- **CONNEXION** — bon point, geste non conforme → formation / outillage
- **INTEGRITE** — dommage physique → manipulation / protection
- **MANQUANT** — appro / kitting
- **AMONT_FABRICATION** — le défaut est arrivé avec la pièce → atelier câbles / fournisseur
- **INSTALLATION** — intégration mécanique → gamme / outillage
- **IDENTIFICATION** — étiquettes / marquage

### 5.3 Trois niveaux de classification

`classify()` fonctionne en cascade : (1) NC au format template → le code fait foi via `TEMPLATE_CODE_MAP` ; (2) NC legacy avec code de confiance (T04, T02, T01, T03, T05, Q01, Q03, Q04) → le code l'emporte sur les mots-clés ; (3) sinon ~25 règles regex ordonnées sur le texte accent-insensible, première correspondance gagnante. Rien ne correspond → AUTRE/AUTRE, volontairement visible.

### 5.4 Réduction de l'AUTRE : 16% → 8%

Le minage du bucket AUTRE a révélé plus que du bruit :

- **Une vraie famille de défauts invisible : GAINE_BACKSHELL, 132 défauts** — « gaine non maintenue dans le backshell », rétreint, amalgamant. Aucune règle ne la couvrait ; c'est désormais la 8ᵉ catégorie. Un AUTRE gros n'est pas du bruit, c'est du signal non étiqueté (le détecteur de symptômes nouveaux, en mode manuel).
- **Réalité orthographique** : « déver**ou**illé » (un R) écrit aussi souvent que la forme correcte — un caractère de regex a fait passer DEVERROUILLAGE de 96 à 110.
- **NC en anglais** (FAL / cabine : missing, damaged, loose, inverted) désormais classées.
- **ORIENTATION** sortie en sous-catégorie propre, plus correction : « mauvais ampérage 10 au lieu de 15 » atterrissait à tort dans MAUVAISE_BORNE via « au lieu de » — désormais ERREUR_PLAQUETTE_REF.

Le résidu 8% est majoritairement du légitime : lignes administratives (« GR non rempli »), discussions d'incohérence plan en anglais, narratifs multi-sujets, instructions vagues (« reprendre finition »). Plancher réaliste pour des règles par mots-clés : ~6–8%. Descendre plus bas force du texte vague dans de mauvaises cases — pire qu'un AUTRE honnête. Ce résidu est le périmètre exact de l'IA à venir (§15).

Note de conception : l'ordre des règles est un choix de priorité. « Manque tyrap sur le backshell » va à GAINE_BACKSHELL plutôt que PIECE_MANQUANTE — première correspondance gagnante, règles ordonnées du spécifique au générique. Réorganisable en deux lignes si l'équipe préfère l'inverse.

---

## 6. Le vrai Pareto et les résultats

### 6.1 Pourquoi les codes officiels ne pilotent rien

`defect_code` vaut « [Electrical Assembly Installation] » pour 43–45% des NC ; `cause_code` vaut « [People] » pour ~49–52%. Quand la moitié de tout atterrit dans un seul bucket, le champ est décoratif. Au niveau défaut, le Pareto est net (§5.1) : **BRANCHEMENT domine avec 879 défauts** — les pièces sont bonnes, elles sont connectées au mauvais endroit, et c'est attrapé au test, l'endroit coûteux.

### 6.2 Résultats d'investigation (périmètre FTO2 SERIE, H1 2026)

Sur le périmètre GPS de référence (686 NC série, jan–juin 2026, 124 jours ouvrés), cinq tours d'investigation ont établi :

- **82% des défauts découverts en fin de chaîne** : contrôle final 43%, test 39%.
- Le flux de retouche après test a une **station nommée permanente, V42RA1**, présente sur 12% des NC.
- **~10% des défauts sont des répétitions exactes cross-MSN**, sur des connecteurs série nommés : 10FC1A, 3RN1A, 115VMA, 3SEA — chacun sur 5–6 MSN.
- **90% des erreurs de mauvaise borne diffèrent d'un seul caractère** (mécanisme off-by-one sur le repère de broche).
- **52% des NC root-caussées « [People] »** — un système qui blâme les gens six mois sans que le chiffre bouge s'est mal diagnostiqué.
- Le **code défaut SAP officiel couvre 45% des NC sous un seul libellé générique**.
- **Une équipe code 99% de ses défauts, l'équipe adjacente 0%.**
- **Les routes 1M et 2M portent 59% des défauts localisés** (échecs de frettes/sécurisation, pas des inversions).
- Le **pic NC de mars trace à un outil unique** : pince M22520/2-01, s/n DSM 39391135970, sur cinq MSN A320. Quick win : calibration/remplacement.
- **Le KPI est gonflé de 11,5% par des suppressions** (dont la moitié sont des doublons prouvables) ; la série corrigée par jour ouvré est plate sur H1. Le taux par jour ouvré est passé de 6,1 en mars à 5,0 en juin (−18%).

### 6.3 Le waterfall mensuel

Bridge mois-sur-mois (périmètre FTO2 SERIE) : **112 → +7 → +15 → −7 → −37 → +14 → 104**, pic en mars à 134. La baisse de mai est partiellement calendaire (19 jours ouvrés) mais le taux par jour ouvré baisse réellement (−18% mars→juin). Juillet exclu (données partielles).

---

## 7. Le signal actionnable

**Les inversions ne sont pas aléatoires : elles se concentrent sur une poignée de connecteurs, récurrents sur plusieurs avions.** C'est le résultat le plus fort et le plus directement actionnable.

### 7.1 Concentration

Dans les inversions et mauvaises bornes, les mêmes FIN reviennent sur des NC et des MSN distincts : familles **3RN** (3RN1A/1B/2A/3A/3B), **1WK** (1WK11A/21A/22A/53A), **300VT** (300VT101/200/400/402), **3SEA**, **9KS**, plus 1608VCxxx. Environ **120 inversions concentrées sur une dizaine de références**, chacune récurrente sur 10+ NC distinctes (donc plusieurs MSN). Chronique, pas un mauvais avion.

### 7.2 La preuve de causalité : 99,3% de confusabilité

Sur 269 inversions où la paire de bornes échangées est extractible, **267 (99,3%) se font entre bornes similaires ou adjacentes** : 164 jumelles/pair-mates (45↔60 puis 46↔61 — les deux fils d'une paire fonctionnelle, même aspect, insérables l'une pour l'autre), 55 numéros adjacents (8A↔9A, 10D↔9D), 47 lettres adjacentes (A↔B, J↔H). Quasi zéro inversion entre bornes dissemblables et éloignées. Cas extrême : bornes `W` et `<W`, distinguées par un symbole, sur 3RN1B, sur plusieurs MSN.

**Toute l'histoire causale tient dans ce nombre : le taux d'inversion est fonction de la confusabilité, pas de la compétence.**

### 7.3 Pas de décrue avec l'expérience

Six mois, mêmes équipes, MSN récurrents : 49, 53, 63, 81, 65, 51 inversions/mois. Plat à croissant, aucune courbe d'apprentissage. C'est la signature de **ripages d'experts sur des pièges structurels** (§12), qui ne répondent pas à la formation — ce qui explique la persistance malgré une équipe solide.

### 7.4 L'action proposée

Une action bornée — détrompage, aide au pinning, marquage d'une borne de chaque paire chaude pour briser la symétrie, ou vérification de continuité (buzz-test) au poste sur les FIN identifiés — attaque le sommet du Pareto réel, avec un KPI avant/après mesurable. « Si on ne fait qu'une chose suite à cette analyse, c'est celle-là. » Le 99,3% est aussi la meilleure diapositive : preuve que la cause est la tâche, pas les gens.

---

## 8. Les trois équipes

Trois équipes écrivent les listes de défauts, chacune avec son style, et **les codes Q/T viennent d'une seule d'entre elles** :

| Équipe (dept/société) | Rôle | Bundles | Défauts | Format | Codes Q/T |
|---|---|---|---|---|---|
| **OLMEP14** (Airbus Operations) | Test | 160 | 882 | `DEF n-CODE :` strict | **100%** (882 des 883 lignes codées) |
| **QRT** (Derichebourg) | Contrôle final | 36 | 569 (~16/NC, les plus gros bundles) | `Def1 :` | 0% |
| **QRTE** (Airbus Operations) | Inspection finale MIP | 9 | 194 | `1 - FIN xxx` numéroté | ~0% |

Sur « le nombre final vient surtout d'une équipe » : les **codes** viennent d'une équipe (test), mais le **volume** est réparti — test en tête à 882, Derichebourg fort second à 569 malgré bien moins de NC.

**Conséquences.** Le classifieur ne dépend pas des codes (les mots-clés couvrent les deux équipes sans code). `user_department` ne correspond à l'auteur réel de la liste que 55% du temps — il faut parser la signature dans le texte (`OLMEP14/AIRBUS...`), pas se fier à la colonne. Enfin, une harmonisation possible pour la feuille de route : faire adopter au contrôle final la convention `DEF n-CODE :` du test — c'est une habitude d'écriture, pas un changement d'outil, et cela rendrait deux tiers des lignes restantes lisibles machine au plus haut niveau de confiance.

---

## 9. Attribution fournisseur et imputation

### 9.1 L'imputation n'est PAS déductible du texte

Un détecteur de langage fournisseur (« reçu coupé », « à réception », « non livré », « fournisseur ») n'attrape que ~13% des NC marquées [SUPPLIER] par SAP. Les ratés le montrent : « Étiquettes décollées », « Modules VG défectueux » décrivent *le défaut*, pas *le responsable*. Un module cassé se lit pareil qu'il ait été livré cassé ou tombé à l'atelier ; la responsabilité dépend du contrat, de la garantie, de l'enquête — hors texte. La décision d'imputation n'est donc pas automatisable, et prétendre le contraire mal-assignerait silencieusement des coûts. `GPS_Imputation` ne peut pas servir de cible d'apprentissage : 318 valeurs sur 319 disent « Airbus TLS » — constant, donc sans information.

### 9.2 Mais la réponse est déjà dans la donnée, structurellement

Trois colonnes non profilées au départ contiennent la réponse de façon déterministe :

- **`responsible_defect_level1`** — mapping 1:1 avec la responsabilité : **Y4 = fournisseur** (exactement les 94 lignes [SUPPLIER]), **Y5 = plant** (687), Y7 = plant-autre (23). *C'est* le flag fournisseur.
- **`responsible_defect_level1_name`** — le nom du fournisseur (Mecachrome Toulouse, Safran Electronics & Defense, Daher Aerospace, Composite Industrie, Groupe Rossi Aero...). 15 fournisseurs distincts.
- **`workflow_list`** — les workflows EXT (REW-EXT-M, MECA-REF-EXT) sont 100% fournisseur ; signal corroborant.

Donc `Type_NC_auto = FOURNISSEUR` devrait simplement **lire** `responsible_defect_level1 == 'Y4'` au lieu de deviner par texte — ce qui corrige son taux actuel de 29/49 à quasi parfait.

### 9.3 Le classifieur `fournisseur_classifier.py`

Développé et validé à **97,3–98,7%** d'exactitude. Trois trouvailles :
- **Un Pareto fournisseur que personne n'a** — nouvelle tuile, zéro travail pipeline.
- **Le #1 « fournisseur » est `DUMMY TEST ONE SHOT PO` (14 NC)** — des NC fournisseur où le vendeur n'a jamais été identifié sur un PO one-shot ; le plus gros bucket de responsabilité fournisseur est « inconnu ». Chargebacks potentiellement irrécupérables.
- **File d'exceptions imputation** : 12 NC disputées identifiées en quatre catégories — 6 labels GPS à corriger en INTERNE, 3 champs liability SAP à corriger en SUPPLIER, 1 réellement provisoire, 2 dépendant du bon de commande (`fiche_arbitrage_12_NC.csv`).

### 9.4 Les retours client (`is_retour_client`)

Règle basée sur le champ `plant`. Elle trouve **54 NC downstream** contre 11 labellisées GPS — dont ~20 findings A330 FFF1 plausiblement traités sur site et jamais formellement retournés. ~35 échappées côté client (traitées au FAL, invisibles à ce KPI) : à garder dans la poche d'Emmanuelle comme carte « on connaît nos angles morts », pas sur la diapo principale.

---

## 10. Audit des colonnes

Passage en revue systématique, par verdict :

**Déjà automatisé (par le parseur) :** `Ext_Nb_Defauts` → `nb_defauts` (95% exact) ; `Ext_Defaut_Constate` → famille/code ; statut décision → 94% depuis les lignes « Decision Taken: ». Le travail de saisie manuelle que ces colonnes représentent est fait.

**Automatisable, décision d'équipe requise :** `GPS_Retouches_majeures/mineures` — maj+min ne matche le comptage parsé que 63% (petit n) ; « majeure vs mineure » n'a aucun critère écrit. Si l'équipe énonce la règle (majeure = ces codes / rebut / >X heures), ça devient un classifieur trivial (majeures ~22% du volume). Atelier de 30 min, pas une tâche de code. La sévérité est partiellement gratuite pour les équipes qui écrivent des en-têtes RETOUCHES MAJEURES/MINEURES (extraite dans `severite`).

**Dérivation cassée à corriger :** `Produit_auto` vs `Ext_Produit` : 66% d'accord seulement. Un champ produit devrait être quasi déterministe (station/work_ctr/préfixe FIN → produit). Table d'alias + mapping station→produit devrait dépasser 95%. Après Type_NC, c'est le prochain fix de règles.

**Colonnes mortes — à retirer du tableau de bord :** `origin` = « Q3 » pour les 807 lignes (zéro info) ; `defect_quantity` ≈ 1 partout (remplacé par `nb_defauts`) ; `defect_code`/`cause_code` (43%/49% dans un bucket) ; `GPS_Imputation` (constant « Airbus TLS », remplacé par `liability_description`).

**Saines telles quelles :** `msn` (100% rempli, 98% d'accord avec les MSN mentionnés en texte — le 2% d'écart est un détecteur de coquille gratuit) ; `aircraft_type` 99% ; `station` 100% ; `work_ctr` 90%.

Net : après le parseur, les seules choses réellement manuelles restantes sont le jugement majeure/mineure et la décision d'imputation. Tout le reste est dérivable, vérifiable ou du bruit.

---

## 11. Qualité des données

Batterie auto vs GPS vs Ext :

- **Statut décision — sain.** `Statut_decision_auto` vs `GPS_Statut_decision` : 94% d'accord (n=449). Deux artefacts corrigeables : auto « Request for Design Change » → GPS « DQN » (5 cas) ; confusion DQN↔Echange (6 cas).
- **Type NC — à travailler.** Accord 74% seulement (n=408). Points chauds : auto INTERNE là où GPS dit CONTROLE FINAL (46) ou FOURNISSEUR (17) ; auto CONTROLE FINAL vs GPS INTERNE (26). Cause partielle identifiée : QRT écrit avec accents (« CONTRÔLE ») ; si les règles matchent « CONTROLE » sans accent, chaque titre accentué tombe dans le bucket par défaut. **Fix d'une ligne : stripper les accents avant match.** Cause structurelle plus profonde : le champ mélange trois dimensions orthogonales — *quoi* (défaut), *où détecté*, *qui responsable*. Personne ne peut être d'accord quand il faut choisir entre trois vérités. Proposition : trois champs séparés (`famille`, `detection_stage`, `responsabilité`).
- **Backlog Unknown.** 163 NC (20%) en `Type_NC_auto = Unknown` ; GPS n'en couvre que 43, dont 11 CLIENT (catégorie que les règles auto ne produisent pas). Ces 43 sont un jeu de test/validation gratuit.
- **Autres drapeaux.** `Ext_Nb_Defauts = 0` sur 38 NC closes (convention non documentée à expliciter) ; 99 NC (12%) en statut *deleted* qui gonflent encore l'extract (à exclure par défaut, montrer en tuile séparée) ; 76 textes (9%) « Removed for classification » — angle mort permanent du text mining, d'où la nécessité d'une voie manuelle dans le pipeline.

---

## 12. La science de la réduction

**L'idée centrale, en une phrase : toute tâche manuelle a un taux d'erreur intrinsèque, mesurable, qui dépend des *conditions* de la tâche et non de la volonté de l'opérateur — donc réduire les NC, c'est ingénierer les conditions.**

### 12.1 La taxonomie de Reason

James Reason (*Human Error*) distingue :
- **Erreurs (mistakes)** — mauvaise intention, connaissance incomplète : mauvais ampérage, mauvaise réf, plan mal lu. **La formation les corrige ; décroissent nettement avec l'expérience (×~3 tôt).**
- **Ripages (slips)** — bonne intention, mauvaise exécution : la main attrape la borne habituelle ou voisine pendant que l'esprit est à l'étape suivante. **Ne répondent PAS à la formation ; certains ripages de capture *augmentent* avec l'automaticité**, car l'expert surveille moins ses mains.
- **Lapses** — omissions d'une étape sans signal saillant (ex. vérifier le verrouillage). Le travail maintenance de Reason & Hobbs trouve les **omissions comme première catégorie d'erreur en maintenance aéronautique, ~50%** — le déverrouillage (Q01) y est.

Les inversions T04/T02, plates sur six mois, mêmes connecteurs, plusieurs équipes : **signature de ripages d'experts sur pièges structurels**, pas d'une main-d'œuvre débutante. Plus de formation ciblerait le type d'erreur qu'on n'a pas.

### 12.2 Les taux de référence (THERP / HEART)

Chiffres de planification, ordre de grandeur, pas décimales :

| Geste | Taux d'erreur par action |
|---|---|
| Action routinière très pratiquée, bonnes conditions | ~5×10⁻⁴ (1 sur 2 000) |
| Sélection fil-vers-borne, bornes distinctes | ~1×10⁻³ (1 sur 1 000) |
| Idem, **bornes similaires/adjacentes, sans feedback immédiat** | 3×10⁻³ – 10⁻² (1 sur 300–100) |
| Omission d'un check non forcé | ~3×10⁻³ |
| Soudure main, opérateur formé | ~10⁻³ |
| Sertissage à l'outil calibré | ~10⁻⁴ — l'outil absorbe le geste ; l'erreur migre vers la *sélection* (mauvaise taille de contact) et l'*insertion* (Q01), à ~10⁻³ |

Multiplicateurs HEART qui s'empilent : layout confusable ×5–8, pression temporelle ×~10, interruptions ×~3, inexpérience ×~3.

### 12.3 Le calcul « attendu vs observé »

Défauts attendus = Σ (nombre de gestes × taux par geste). Exemple travaillé : un MIP à ~3 000 terminaisons × (1–3)×10⁻³ ≈ **3 à 9 ripages de câblage par MSN, attendus, d'une main-d'œuvre pleinement compétente**. La donnée parsée montre ~10–15 défauts branchement par MIP au test.

Deux conclusions : (1) **le centre est *normal*** — l'observé est au bord haut de la bande prédite, pas dix fois au-dessus ; personne n'est négligent, la tâche produit sa sortie statistique. (2) L'excès au-dessus du bord bas est exactement ce que prédisent les multiplicateurs pour les points confusables — la concentration 3RN/1WK. **On ne peut pas exhorter de 10⁻³ à zéro, mais on peut ingénierer des points chauds de 10⁻² à 10⁻³ — un gain local ×10 — en retirant le multiplicateur (marquage, détrompage, buzz-test au poste).** Brancher les vrais comptes de terminaisons par produit dans cette formule donne un graphe attendu-vs-observé défendable pour le tableau de bord.

### 12.4 MEDA, Shingo, HPI

- **MEDA (Boeing)** — méthode standard d'investigation d'erreur maintenance. Prémisse validée sur des milliers de cas : l'erreur n'est jamais la cause, elle est le résultat de facteurs contributifs, dont **80–90% sont contrôlables par le management/système** (présentation des pièces, éclairage, ambiguïté documentaire, interruptions). Investiguer les inversions 3RN comme des *événements*, pas des statistiques.
- **Shingo / poka-yoke** — l'inspection découvre les défauts, seul l'error-proofing à la source les prévient ; la vigilance humaine n'est pas un contrôle. Les études d'inspection visuelle en aéro trouvent ~80% de détection et un *déclin de vigilance* dans la première demi-heure.
- **HPI nucléaire (DOE)** — outils opérationnels : identification des *situations à risque d'erreur* (le parseur *est* un détecteur de situations à risque), self-check STAR aux seules étapes signalées, peer-check aux terminaisons à haut risque, place-keeping pour les séquences interruptibles.

### 12.5 La hiérarchie des parades

Du plus au moins efficace : **rendre l'erreur impossible (détrompage, géométrie) › détecter à la source en secondes (buzz-test au poste) › check-lists aux points clés › formation › affiches « attention » ≈ effet nul.**

Appliqué : inversions (T04/T02) = mis-sélection entre similaires → discrimination (marquage/couleur/géométrie sur les FIN chauds) + vérification de proximité immédiate, *pas* la formation. Déverrouillage (Q01) = omission → indice forçant (tug-test obligatoire, confirmation tactile/audible du verrou) à la frontière naturelle de tâche. La concentration sur 10 connecteurs = ce que Reason appelle un *piège à erreur* (mêmes conditions, même erreur, tout opérateur) — preuve la plus forte d'un facteur de conception local, argument le plus fort contre « People » comme cause.

### 12.6 Experts vs novices — la nuance

Novices et experts ne font pas moins/plus des *mêmes* erreurs ; ils font des *espèces différentes*. Novices → mistakes (formation les corrige, décrue avec l'expérience). Experts → slips (précisément *parce que* la performance est automatique). La donnée dit quelle espèce domine : inversions stables = ripages d'experts.

**Caveat RH/CNIL** : le suivi défaut par opérateur est sensible en France (comité social, CNIL). Agréger au niveau équipe/poste, ou utiliser des proxys temporels : plat dans le temps = piège ; décroissant = courbe d'apprentissage ; pic après changement d'effectif = manque de formation. Le pipeline répond en un groupby, et ce seul graphe dit s'il faut dépenser en formation ou en détrompage.

---

## 13. Le standard d'écriture « DEFAUTS v1 »

**Choix à plus fort levier : standardiser l'écriture des défauts convertit le nettoyage de données en données qui ne se salissent jamais.** Aucune liste fermée ne couvrira tout ; le standard couvre tout par construction — champs à position fixe pour la machine, queue en texte libre pour l'humain, soupapes explicites (code `AUT`, localisation `ZONE`/`-`) pour que personne ne soit bloqué.

### 13.1 Le gabarit

```
### DEFAUTS v1 | MSN: 2160 | PRODUIT: 740VU | DETECTION: TEST
DEF 1 - T04 - 3RN3B : inversion bornes J <-> H
DEF 2 - Q01 - 115VMB : contact broche 12 non verrouillé
DEF 3 - M01 - 411VC007A - QTE 4 : obturateurs manquants
DEF 4 - C02 - 1608VC070A - CABLE 2424-0135 : câble coupé côté connecteur
DEF 5 - AUT - ZONE PLANCHE SUP : trace de colle non identifiée
DEF 6 - L01 - - : câble 3161-0582 reçu trop court de 40 mm
### TOTAL: 9
```

### 13.2 La grammaire

`DEF <n> - <CODE> - <LOC> [- CABLE <réf>] [- QTE <k>] : <texte libre>`

En-tête `### DEFAUTS v1 | MSN | PRODUIT | DETECTION` (DETECTION ∈ POSTE, TEST, CONTROLE FINAL, RECEPTION, CLIENT). Pied `### TOTAL: <somme, QTE comprises>` — **somme de contrôle** vérifiée par la machine ; toute incohérence part en file d'exceptions.

### 13.3 Les règles (tous les cas limites couverts)

1. Une ligne = un défaut ; un défaut = une ligne. Pas de sous-listes.
2. Défauts identiques multiples → une ligne avec `QTE k`.
3. Références individuelles (câbles à réfs différentes) → une ligne par câble.
4. Pas de FIN → `ZONE <nom>` ou `-`, jamais vide.
5. Type inconnu → `AUT` + texte libre ; les AUT sont analysés chaque semaine et deviennent des codes si récurrents.
6. Défauts trouvés après création → lignes ajoutées, numéros suivants, TOTAL mis à jour ; numérotation append-only.
7. Une NC = un MSN + un produit.
8. Inversion → toujours nommer les deux bornes (`J <-> H`) : permet la détection des paires récurrentes.
9. Défaut fournisseur → `R01`/`L01` + DETECTION: RECEPTION ; imputation formelle reste dans SAP (Y4).
10. Programme classifié → n'écrire que ce qui est déjà autorisé.

### 13.4 La table des codes

Codes existants conservés (le terrain les connaît) : T01/T03 câble manquant, T02 mauvaise borne, T04 inversion, Q01 déverrouillage, Q03 pièce manquante, Q04 plaquette/réf, Q05/Q07 sertissage, Q08 blindage, Q11 prise cassée, T05 non connecté. Extensions proposées (placeholders à réconcilier en atelier) : M01 pièce manquante, L01 longueur, R01 défaut réception, C01 composant cassé, C02 câble endommagé, H01 composant HS, F01 fixation, F02 cheminement, F03 métallisation, FOD, E01 étiquette, N01 non connecté, FRE freinage, TOR serrage, AUT autre.

**Règle d'or : ne jamais renuméroter les codes existants — on étend, on ne remplace pas.** Option : associer à chaque code une sévérité par défaut (majeure/mineure) pour automatiser aussi ce comptage.

### 13.5 Contrat machine et déploiement

Toute NC portant `### DEFAUTS v1` est parsée en mode strict (`template_v1`) : comptage exact QTE comprises, classification par code prioritaire, FIN extrait de LOC, vérification de la somme de contrôle. Ligne malformée ou TOTAL incohérent → drapeau, jamais de comptage silencieusement faux. Les neuf formats legacy restent parsés à l'identique — migration progressive, équipe par équipe.

Déploiement : piloter avec le contrôle final d'abord (gros bundles, zéro code aujourd'hui = plus gros gain d'information). Insérer le gabarit comme texte standard SAP pour un coût d'écriture quasi nul. Mesurer l'adoption sur la tuile santé-données (% de NC au format v1 par équipe, par semaine). Atelier de 30 min avec les trois équipes pour réconcilier les codes et fixer le critère majeure/mineure — les deux seules décisions humaines restantes.

---

## 14. Le tableau de bord proactif

**Principe : changer l'unité d'analyse — du NC au défaut — et pousser des alertes au lieu d'attendre qu'on ouvre un rapport. Quatre couches.**

**Couche 1 — Parser (déterministe, existe aujourd'hui).** Transform planifié (Pipeline Builder ou job PySpark sur le dataset alimentant Slate) qui produit le dataset défaut à côté du dataset NC. Regex + mots-clés, validé à 95% — la preuve que ça marche sans IA.

**Couche 2 — Réconcilier.** Jointure parsé × listes GPS/Ext. Accord → confiance haute, auto. Désaccord → *file d'exceptions* humaine. Texte caviardé → liste manuelle fait foi. Les gens passent du comptage à la vérification ; la classe d'erreur de comptage disparaît.

**Couche 3 — Détecter (le proactif).** Alertes calculées à chaque refresh, poussées (notifications Foundry, digest email) :
1. *Veille récurrence* — même FIN, ou même code × produit, dans ≥N NC distinctes en fenêtre glissante. « 3RN3B : 3ᵉ MSN ce mois-ci. »
2. *Dérive de taux* — défauts/MSN et /semaine par produit vs sa propre référence (c-chart / EWMA — SPC standard, pas de ML).
3. *Détecteur de symptômes nouveaux* — lignes ne matchant aucune famille connue (l'AUTRE) au-dessus d'un seuil → mode de défaillance novel en semaine 1, pas au mois 3.
4. *Tuile santé-données* — écarts auto/GPS, taux Unknown, fuite de NC deleted, écarts de comptage.

**Couche 4 — L'IA (dans ~2 mois, à sa juste place).** *Dans* le pipeline, pas à sa place : classer le résidu AUTRE (8%), normaliser le texte libre vers la taxonomie Q/T, clustering sémantique (même défaut, mots différents) que la regex ne peut pas attraper. Comme les couches 1–3 produisent déjà des lignes structurées, l'IA ne traite que le résidu dur : moins cher, auditable, mesurable contre la baseline déterministe. **On n'attend pas deux mois** : l'IA arrive dans un système qui tourne, avec une baseline mesurée.

Ce que devient le tableau de bord : les charts Slate existants re-pointés sur le dataset défaut avec un toggle NC/défaut ; un panneau « ce qui a changé cette semaine » en haut ; drill-down alerte → lignes de défaut → NC source. Il cesse d'être un rapport qu'on consulte pour devenir un système qui interrompt — avant que quelqu'un au contrôle final n'ait à le remarquer.

---

## 15. Feuille de route

Séquençage proposé (à arbitrer par Emmanuelle) :

1. **Industrialiser le pipeline dans Skywise** et rebrancher le tableau de bord sur le niveau défaut. Même dataset, un transform planifié, aucune source nouvelle. Semaines 1–2 : porter le parseur en Code Repository Foundry et le planifier. Semaine 3 : jointure de réconciliation et file d'exceptions. Semaine 4 : re-pointer le dashboard, activer les deux premières alertes (récurrence, santé-données), puis tuner les seuils avec l'équipe.
2. **Piloter le standard d'écriture** avec une équipe — contrôle final, plus gros gain.
3. **Action bornée sur les ~10 connecteurs** (détrompage / marquage / buzz-test), avec KPI avant/après pour prouver l'effet. Valider avec la prod, définir le KPI.
4. **Dans ~2 mois : l'IA sur le résidu** (8% non classés), au-dessus d'une baseline mesurée.

Décisions de convention à trancher (ne peuvent l'être seul) : le sort des NC *deleted* dans les requêtes ; la signification de `Nb_Defauts = 0` ; le critère majeure/mineure ; 30 min avec les propriétaires des listes GPS pour valider le workflow d'exceptions (ça change leur routine, ils doivent le façonner).

**Quick wins déjà actionnables :** l'outil non conforme (pince M22520/2-01) — calibration/remplacement immédiat ; les doublons prouvables dans les 11,5% de suppressions ; la lecture de `responsible_defect_level1 = Y4` pour fiabiliser instantanément l'attribution fournisseur.

**La contribution, en une phrase :** transformer un brouillard de ~800 NC en un problème borné, mesurable et appropriable — et fournir l'instrument avant/après qui prouvera, en semaines, si les actions choisies par l'équipe marchent. Pas le correctif : la résolution à laquelle le correctif devient trouvable et prouvable.

---

## 16. Inventaire des livrables

| Fichier | Contenu |
|---|---|
| `nc_defect_parser.py` | Le parseur : découpe, comptage, classification, localisation. 9 formats, tolérance aux fautes, mode template. Cœur stdlib portable en PySpark. |
| `defects_split.csv` | 2 346 défauts individuels, une ligne par défaut, avec famille/sous-catégorie/FIN/qty/sévérité. Prototype de la sortie Couche 1. |
| `nc_with_counts.csv` | Les NC enrichies : `nb_defauts`, `is_redacted`, `flags`, `nb_defauts_final`. |
| `count_disagreements.csv` | Les ~16 écarts parseur vs comptage manuel, pour revue humaine (dont des erreurs de comptage manuel). |
| `fournisseur_classifier.py` | Attribution fournisseur automatisée, 97–98,7%. |
| `fiche_arbitrage_12_NC.csv` | 12 NC d'imputation disputées, quatre catégories. |
| `waterfall_NC_series_2026H1.png` | Bridge mensuel NC, périmètre FTO2 SERIE. |
| `NC_investigation_report_H1_2026.md` | Rapport d'investigation complet H1. |
| `standard_defauts_v1.md` | Spécification du standard d'écriture. |
| `stage_presentation.pptx` | La présentation de restitution (8 diapos). |

---

## 17. Annexe : chiffres clés

- **807** NC dans l'extract courant · **2 346** défauts individuels · **×~3** facteur de volume caché
- **95%** comptage exact vs manuel, **99%** à ±1 · **9** formats d'écriture décodés
- **8,1%** de défauts en AUTRE (depuis 16%)
- **879** défauts BRANCHEMENT (la plus grosse famille) · **373** inversions · **291** mauvaises bornes
- **99,3%** des inversions entre bornes similaires/adjacentes · **~10** connecteurs concentrent l'essentiel
- **49→81→51** inversions/mois sur H1 — plat, aucune décrue
- **82%** des défauts découverts en fin de chaîne (contrôle final 43%, test 39%)
- **~10%** de défauts répétés exacts cross-MSN · **90%** des mauvaises bornes off-by-one
- **52%** de NC root-caussées « People » · **45%** sous un code défaut générique unique
- **11,5%** d'inflation KPI par suppressions · **−18%** taux/jour ouvré mars→juin
- **94%** accord statut décision auto/GPS · **74%** accord Type NC (le champ à scinder)
- **97–98,7%** exactitude classifieur fournisseur · **Y4/Y5** = flag fournisseur/plant déterministe
- Équipes : **OLMEP14** (test, 100% codé), **QRT** Derichebourg (contrôle final, gros bundles), **QRTE** (inspection MIP)
- Taux d'erreur de référence : **~10⁻³** par geste de câblage · **×10** de gain local possible sur les points chauds

---

*Fin du dossier. Document vivant — à mettre à jour à chaque nouvel extract et à chaque décision d'équipe.*
