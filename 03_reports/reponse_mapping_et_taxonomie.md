# Codes officiels → types de défaut : cardinalité du mapping et refonte de la taxonomie de reporting

*Réponse aux deux questions, mesurée sur les 123 sous-codes officiels et 2 346 défauts réels.*

---

## Question 1 — Le mapping est-il bien « plusieurs vers un » ?

**Oui, mais uniquement au niveau du SOUS-CODE. Pas au niveau du code de tête.** C'est la distinction qui décide de toute l'architecture.

### Au niveau du code de tête (Q03, Q04…) : ce n'est PAS une fonction

**6 codes sur 21 pointent vers plusieurs types de reporting.** Q04 et Q06 en touchent 7 chacun, Q03 et Q11 en touchent 6.

Exemple : `Q03 (élément manquant)` se disperse sur 6 types différents — un obturateur manquant, un câble manquant, une étiquette manquante, un frettage manquant, une gaine manquante et un collier manquant n'ont ni la même cause ni le même responsable. Coder au niveau Q03 perd toute l'information utile.

C'est la conséquence directe de la structure matricielle : le code de tête porte la **nature**, pas l'objet. Ce n'est pas un défaut de la grille — c'est simplement le mauvais niveau de granularité pour du reporting.

### Au niveau du sous-code (Q03-004, Q04-011…) : oui, c'est une fonction propre

**120 des 123 sous-codes se projettent sur exactement un type. Le mapping est déterministe, calculable, sans jugement.**

Il reste **exactement 3 sous-codes intrinsèquement ambigus**, parce que leur libellé mélange des objets hétérogènes :

| Sous-code | Libellé officiel | Pourquoi c'est ambigu | Résolution |
|---|---|---|---|
| **Q03-004** | Élément électrique manquant (câble, contact, diode, résistance, connecteur, module VG, connecteur arrière) | Un câble manquant ≠ un composant manquant : appro vs assemblage | L'outil demande déjà l'élément → on lit sa réponse |
| **Q04-011** | Élément électrique (tresse de masse, terminal, voyant) | La tresse de masse relève du bonding, pas de l'erreur de référence | Idem |
| **Q06-001** | Faisceau (cheminement, sous/surlongueur, mauvaise destination, pincé) | Le cheminement est un geste au poste ; la longueur vient de l'amont | Idem |

**Ces 3 cas se résolvent gratuitement** : l'outil de saisie demande de toute façon l'élément concerné à l'étape 2. Il suffit d'enregistrer cette réponse et le mapping redevient une fonction totale — 123/123, zéro ambiguïté.

### Conclusion Q1

> **Sous-code officiel → type de reporting = fonction plusieurs-vers-un, 123 → 26.** Le type se calcule, il ne se saisit pas. Le QLS ne choisit jamais un type de reporting : il choisit un code officiel, le système en déduit tout le reste.

Corollaire à retenir : **il faut stocker le sous-code complet, jamais le code de tête seul.** Aujourd'hui les équipes écrivent souvent « Q01 » ou « T04 » sans le suffixe — au niveau code de tête, l'information de reporting est déjà perdue à l'écriture.

---

## Question 2 — La taxonomie actuelle est-elle suffisante ?

**Non. Trois défauts mesurés, dont un rédhibitoire.**

### Défaut 1 — Des trous : 20 sous-codes officiels (16%) sans domicile

| Code officiel | Sous-codes orphelins | Ce que ça couvre |
|---|---|---|
| **Q10** | 6 | Dommages structure : plaque, structure, main courante, colonne, tuyauterie, mécanisme |
| **Q13** | 5 | Dossier de fabrication : opération non badgée, tampon, traçabilité, doc, saisie outillage |
| **Q12** | 4 | Erreurs d'impression : jauge câble, type câble, identification |
| **T03** | 1 | Shunt manquant |
| **T06 / T08** | 3 | Mesures non conformes : perte optique, résistance linéique |
| **Q06-009** | 1 | Route non reprise après test |

Ma taxonomie était construite par induction sur ce que le parseur trouvait dans le texte libre. Elle ne pouvait donc pas contenir ce que personne n'écrit — ce qui ne veut pas dire que ça n'arrive pas. Q13 et Q10 en particulier sont des familles entières absentes.

### Défaut 2 — Des regroupements incohérents pour la réduction

`ETIQUETTE_MARQUAGE` réunissait quatre problèmes sans rapport : étiquette **manquante** (oubli), **erronée** (erreur de sélection), **abîmée** (manipulation), **mal imprimée** (amont). Quatre causes, quatre correctifs, un seul type : inutilisable pour piloter une action.

Symétriquement, `PIECE_MANQUANTE` mélangeait obturateurs, visserie et colliers — trois responsables différents (appro, poste, méthodes).

### Défaut 3 — Aucun axe orienté réduction

L'ancienne taxonomie répond à « qu'est-ce que c'est ? ». Elle ne répond pas à « qu'est-ce qui l'empêcherait ? ». Or c'est exactement la question de la réduction des NC.

---

## La refonte proposée : deux axes, tous deux calculés

L'agent QLS ne saisit **qu'une chose** : le sous-code officiel. Les deux axes analytiques en découlent automatiquement.

### Axe 1 — Type de défaut (reporting) : 26 types

Couverture **123/123 sous-codes**, fonction totale, zéro jugement. Équilibre mesuré sur 2 346 défauts réels :

| Type | Défauts | Part |
|---|---|---|
| INVERSION_BRANCHEMENT | 373 | 15,9% |
| ERREUR_BRANCHEMENT | 291 | 12,4% |
| ERREUR_REFERENCE | 216 | 9,2% |
| *(Autre / non classé)* | 191 | 8,1% |
| DOMMAGE_CABLE | 156 | 6,6% |
| FREINAGE_FRETTAGE | 136 | 5,8% |
| OBTURATION_PROTECTION | 134 | 5,7% |
| GAINAGE | 132 | 5,6% |
| VERROUILLAGE_CONTACT | 110 | 4,7% |
| SERRAGE | 95 | 4,0% |
| CHEMINEMENT_CLASH | 91 | 3,9% |
| IMPRESSION_CABLE | 88 | 3,8% |
| COLLIER_FIXATION | 72 | 3,1% |
| DOMMAGE_COMPOSANT_ELEC | 65 | 2,8% |
| CABLE_MANQUANT | 63 | 2,7% |
| SERTISSAGE_STANDARD | 36 | 1,5% |
| METALLISATION_BONDING | 35 | 1,5% |
| IDENTIFICATION | 23 | 1,0% |
| SERTISSAGE_SPECIFIQUE | 21 | 0,9% |
| CABLE_NON_CONNECTE | 11 | 0,5% |
| FOD | 7 | 0,3% |
| *+ 5 types à volume nul aujourd'hui* | 0 | — |

**Critères de qualité d'un axe de reporting, vérifiés :** plus gros type à **15,9%** (aucun type ne noie le Pareto — à comparer aux 43% du `defect_code` SAP et aux 49% de `cause_code`) · top 5 = **52%**, top 10 = **78%** (Pareto lisible, pas plat) · seulement 3 types sous 1% · granularité stable (les 5 types à volume nul correspondent à Q10/Q13 : soit ces défauts ne surviennent pas ici, soit ils sont déclarés ailleurs — c'est en soi une question à poser).

### Axe 2 — Mode d'erreur (réduction) : 6 modes

C'est l'axe qui manquait. Il ne décrit pas le défaut, il **désigne la parade**.

| Mode | Défauts | Part | Parade impliquée |
|---|---|---|---|
| **SÉLECTION** | 880 | **37,5%** | Détrompage, marquage, layout — **pas la formation** |
| **EXÉCUTION** | 618 | 26,3% | Outillage, calibration, gamme, formation au geste |
| **OMISSION** | 348 | 14,8% | Signal forçant, auto-contrôle au poste, place-keeping |
| **MANIPULATION** | 221 | 9,4% | Protection, conditionnement, environnement |
| *(non classé)* | 191 | 8,1% | → périmètre du code « Autre » |
| **AMONT** | 88 | 3,8% | Fournisseur / atelier câbles / appro |
| **PROCESS** | 0 | 0% | Discipline documentaire (Q13 — jamais codé à ce jour) |

**C'est le chiffre qui pilote la réduction : 37,5% des défauts sont des erreurs de sélection.** Combiné au constat des 99,3% d'inversions entre bornes voisines, ça donne une conclusion directement présentable : *plus d'un tiers du volume relève de parades de conception (détrompage, marquage), et par nature ne répondra pas à la formation.* Aucun axe existant ne permettait de dire cela.

Le mode se déduit du code de tête à deux exceptions près (Q06-009 et les mesures T06/T08), donc il est calculable sans effort supplémentaire.

---

## Réponse directe aux deux questions

**1. Many-to-one ?** Oui — 123 sous-codes → 26 types, fonction propre, à condition de (a) stocker le sous-code complet et non le code de tête, et (b) enregistrer l'élément choisi pour lever les 3 sous-codes ambigus. Au niveau code de tête, non : 6 codes sur 21 sont multi-types.

**2. Taxonomie actuelle suffisante ?** Non — 16% des codes officiels sans domicile, des regroupements qui mélangent des causes distinctes, et aucun axe de réduction. La version révisée corrige les trois : couverture 123/123, Pareto équilibré à 15,9% max, et un axe mode d'erreur qui traduit chaque défaut en famille de parade.

---

## Anomalies relevées dans la grille officielle (bonus)

- **Q06-007 vs Q06-008** — quasi-doublons : les deux couvrent « gaine trop courte » et « gaine non maintenue sur connecteur arrière ». Deux codes pour le même défaut = donnée dispersée. À fusionner ou à délimiter explicitement.
- **Q06-001 vs Q12-003** — la sous/surlongueur de câble apparaît dans les deux. Mais elles ne relèvent **pas du même mode** : Q06-001 = exécution (poste), Q12-003 = amont (atelier câbles). Le choix du code change le responsable désigné — il faut trancher lequel s'applique quand.
- **Q11-001 (câble coupé, RPN 48) vs Q11-014 (câble éraflé, RPN 480)** — même sévérité, même occurrence, détectabilité 1 vs 10, soit un facteur 10 sur le RPN. C'est défendable (une coupure se voit, une éraflure non) mais mérite d'être explicité, sinon le codeur choisira au hasard et fera varier le RPN d'un facteur 10.
- **Q03-002 (gaine thermorétractable) vs Q03-010 (gainage)** — recouvrement possible, même RPN. À délimiter.

---

*Livré : `mapping_codes_vers_types.csv` — les 123 sous-codes avec leur type de reporting, leur mode d'erreur, leur sévérité dérivée (≥8 = majeure) et un drapeau sur les 3 nécessitant une désambiguïsation à la saisie.*
