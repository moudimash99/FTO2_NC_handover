# Spécification — Assistant de saisie NC (saisie structurée des défauts)
### Règles de conception et de fonctionnement · v1 · Centre électrique (FTO2)

*Objet : remplacer la rédaction libre des NC par une saisie guidée, type par type, qui produit un texte cohérent, complet et lisible machine — sans jamais bloquer l'agent QLS. Ce document est un ensemble de règles, pas un logiciel. Les taxonomies et jeux de champs sont fondés sur l'analyse de 2 346 défauts réels (807 NC, H1 2026).*

---

## 0. Principe directeur

**P0.** L'outil est une aide à l'écriture, pas une barrière. À tout moment, pour tout défaut, il existe un chemin de saisie qui aboutit — au pire par une soupape (« Autre »). Un pourcentage marginal de cas hors cadre est acceptable ; un agent bloqué ne l'est jamais.

**P1.** Chaque champ structuré doit avoir un consommateur identifié (comptage, Pareto, récurrence, imputation, alerte). On ne demande jamais une information « au cas où » : chaque clic doit acheter de l'analyse.

**P2.** Le texte libre ne disparaît pas : il est réduit à ce que la machine ne peut pas capturer (la nuance), et les champs structurés capturent ce qu'elle doit capturer (le fait).

---

## 1. Décisions d'architecture (déléguées, tranchées ici)

### D1 — Sélection du type : hiérarchique, deux niveaux
Le QLS choisit d'abord une **famille** (8 options), puis un **type** dans cette famille (2–6 options). Justification : 23 types à plat dans une seule liste, c'est précisément une « sélection entre similaires » — la classe d'erreur qu'on cherche à réduire chez les opérateurs, on ne va pas la réintroduire dans l'outil. Deux niveaux = deux gestes courts, jamais plus de 8 options à balayer. Deux accélérateurs : une rangée « **types récents** » (les 4 derniers utilisés par cet agent sur ce produit) court-circuite la hiérarchie ; et le code historique (T04, Q01…) est affiché à côté du libellé et cherchable au clavier, pour que le langage du terrain survive.

### D2 — Répartition des métadonnées : règle du « nécessairement commun »
**Un champ est au niveau NC si et seulement si sa valeur est nécessairement identique pour tous les défauts de la NC.** Tout ce qui peut varier d'un défaut à l'autre est au niveau défaut. Corollaire : une NC = **un MSN, un produit, un événement de détection**. Deux produits → deux NC. Un même contrôle qui trouve 20 défauts → une NC, 20 blocs.

### D3 — Taxonomie et jeux de champs : inclus dans cette spec, en v1
La liste des types (§4) et leurs champs sont livrés ici comme **proposition v1 fondée sur les données**, à valider en atelier de 30 min avec les trois équipes (test, contrôle final, inspection MIP). La structure de la spec (règles, soupapes, gouvernance) ne dépend pas de cette validation ; seuls les libellés et les valeurs d'énumération peuvent bouger.

---

## 2. Structure d'une NC

```
NC
├── EN-TÊTE (niveau NC — saisi une fois)
│   ├── MSN                    [texte validé, ou repris du contexte]
│   ├── Produit                [liste : MIP A350, 740VU, PTVU, 300VU, OHP, …]
│   ├── Détection              [liste : POSTE · TEST · CONTRÔLE FINAL · RÉCEPTION · CLIENT]
│   ├── Station / poste        [pré-rempli depuis le contexte de connexion ; modifiable]
│   └── Auteur, date           [automatiques]
└── BLOCS DÉFAUT ×N (niveau défaut — répétés autant que nécessaire)
    ├── Famille → Type         [hiérarchie D1]
    ├── Champs du type         [définis §4]
    ├── Sévérité               [liste : MAJEURE · MINEURE — défaut proposé par type, modifiable]
    ├── Quantité               [entier ≥1, défaut 1 — visible seulement pour les types où elle a un sens]
    ├── Photo                  [optionnelle, jamais obligatoire]
    └── Complément libre       [texte court optionnel — la nuance]
```

Le **TOTAL de défauts est calculé par l'outil** (somme des quantités). La somme de contrôle manuelle du standard texte disparaît : la classe d'erreur « TOTAL faux » est éliminée par construction.

---

## 3. Règles universelles de saisie

**R1 — Un bloc = un défaut.** Jamais deux défauts dans un bloc, jamais un défaut réparti sur deux blocs.

**R2 — Défauts identiques multiples** (même type, même localisation, même nature) → un bloc avec `Quantité = k`. Exemple réel : « manque 4 obturateurs » = un bloc, quantité 4.

**R3 — Références individuelles → blocs séparés.** Si chaque occurrence porte sa propre référence (câbles manquants à réfs différentes), un bloc par référence : chaque réf doit être traçable individuellement.

**R4 — Localisation toujours renseignée, jamais bloquante.** Trois voies : **FIN** (champ à autocomplétion, cf. R10) ; **ZONE** (liste : planche sup., planche inf., face avant, face arrière, route 1M/2M/1S/2S/1R/2R, autre) ; **Non applicable**. Les données montrent 21% de défauts sans FIN : la voie ZONE/NA est un cas nominal, pas une exception.

**R5 — Le motif « constaté / requis » partout où il s'applique.** Chaque fois qu'un défaut est de la forme « X au lieu de Y », la saisie est **deux champs** (valeur constatée, valeur requise), jamais une phrase. C'est ce qui rend détectables les paires récurrentes, les off-by-one et les erreurs systématiques. S'applique à : mauvaise borne, erreur de référence, longueur, orientation, ampérage.

**R6 — L'inversion exige ses deux bornes.** Le type INVERSION a deux champs Borne A / Borne B obligatoires, avec validation A ≠ B. Justification mesurée : 99,3% des inversions se font entre bornes voisines ou jumelles — la paire est l'information ; sans elle, pas de détection de piège.

**R7 — Soupape à chaque niveau.** Type « AUTRE » dans chaque famille + famille « AUTRE » au sommet ; option « Autre (préciser) » dans chaque liste déroulante, ouvrant un champ texte. Rien ne bloque jamais. Contrepartie : tout ce qui passe par une soupape est revu chaque semaine (§6).

**R8 — Le complément libre est court et optionnel** (≤ 200 caractères conseillés). Il ne doit jamais contenir ce qu'un champ structuré du bloc capture déjà — l'outil affiche les champs remplis au-dessus pour décourager la redite.

**R9 — Append-only après création.** Les défauts découverts ensuite (en retouche) s'ajoutent en fin de liste avec les numéros suivants. On ne renumérote jamais, on ne supprime pas un bloc validé : on le marque « annulé » avec motif (traçabilité). Modification d'un bloc possible jusqu'à la décision (REWORK…), journalisée.

**R10 — L'autocomplétion FIN est triée par fréquence produit.** La liste des FIN proposés vient de la nomenclature du produit sélectionné, ordonnée par fréquence historique de défauts (3RN3B, 300VT101, 9KS… en tête pour le MIP A350). Saisie libre acceptée si le FIN n'est pas en liste — avec validation de format (`^\d{1,4}[A-Z]{2,4}\d{0,4}[A-Z]{0,2}$`) en avertissement, pas en blocage.

**R11 — « Dupliquer le bloc précédent ».** Un bouton copie le dernier bloc (type + localisation pré-remplis, valeurs spécifiques vidées). Justification mesurée : 232 NC contiennent des séries de ≥3 défauts du même type — les listes de test alignent couramment 8 à 20 inversions/mauvaises bornes d'affilée.

**R12 — Budget de saisie.** Cible : **≤ 20 secondes par bloc** pour les cinq types les plus fréquents (inversion, mauvaise borne, erreur réf, déverrouillage, pièce manquante), mesuré en nombre de gestes (sélections + frappes). Tout champ qui fait dépasser ce budget sur ces types doit justifier son consommateur (P1) ou devenir optionnel.

**R13 — Sévérité proposée, pas imposée.** Chaque type porte une sévérité par défaut (table §4) ; l'agent peut la modifier. Le critère officiel majeure/mineure reste à fixer en atelier ; en attendant, la valeur par défaut encode l'usage observé.

---

## 4. Taxonomie v1 et jeux de champs par type

Notation : `[L]` liste déroulante · `[T]` texte libre · `[Tv]` texte à validation de format · `[N]` numérique · `[C/R]` paire constaté/requis · **gras** = obligatoire. Tous les blocs ont en plus : sévérité, quantité (si listée), photo, complément libre (§2). Couverture historique indiquée par type (part des 2 346 défauts).

### Famille 1 — BRANCHEMENT (879 défauts · 37%) — *bonnes pièces, mauvaise logique*

**1.1 Inversion de bornes** (T04 · 373 · sévérité déf. MINEURE)
— **FIN** [Tv+autocomplétion] · — **Borne A** [T court] · — **Borne B** [T court] (validation A≠B) · — Module/repère [T, optionnel]

**1.2 Câble en mauvaise borne** (T02 · 291 · MINEURE)
— **FIN** [Tv] · — **Borne** [C/R] (constatée / requise) · — Réf câble [Tv, optionnel]

**1.3 Erreur de référence / plaquette** (Q04 · 204 · MAJEURE)
— **Emplacement** [FIN ou ZONE] · — **Élément** [L : prise, plaquette, disjoncteur, composant, autre] · — **Référence** [C/R] · — Nature [L : mauvaise réf montée, inversion de plaquettes, ampérage/calibre erroné]

**1.4 Non connecté** (T05 · 11 · MINEURE)
— **FIN** [Tv] · — Borne/repère [T, optionnel]

### Famille 2 — CONNEXION (530 · 23%) — *bon point, geste non conforme*

**2.1 Borne / contact déverrouillé** (Q01 · 110 · MINEURE)
— **FIN** [Tv] · — Borne(s) [T] · — **Quantité**

**2.2 Gaine / backshell** (132 · MINEURE)
— **FIN** [Tv] · — **Élément** [L : gaine, backshell, manchon, amalgamant, rétreint] · — **Nature** [L : non maintenu(e), mal rétreint(e), absent(e), mal positionné(e), autre]

**2.3 Freinage / frettes** (136 · MINEURE)
— **Localisation** [FIN ou ZONE/route] · — **Élément** [L : frette, frein, tyrap, collier] · — **Nature** [L : manquant, desserré, mal posé, non conforme] · — **Quantité**

**2.4 Serrage / couple** (95 · MAJEURE)
— **Élément** [L : vis, écrou, backshell, connecteur, autre] · — **Localisation** [FIN/ZONE] · — **Constat** [L : desserré, couple non atteint, non torqué, torqueseal absent] · — Couple mesuré [N, optionnel]

**2.5 Sertissage** (Q05/Q07 · 36 · MAJEURE)
— **FIN ou réf câble** [Tv] · — **Nature** [L : mal serti, desserti, non serti, brins coupés, autre]

**2.6 Blindage / tresse** (Q08 · 21 · MAJEURE)
— **FIN/câble** [Tv] · — **Nature** [L : tresse endommagée, reprise de masse NC, raccord NC, autre]

### Famille 3 — INTEGRITE (221 · 9%) — *dommage physique / panne*

**3.1 Câble endommagé** (156 · MAJEURE)
— **Réf câble** [Tv] · — Localisation [FIN/ZONE] · — **Nature** [L : coupé, abîmé, dénudé, pincé, écrasé, rayé, percé, autre]

**3.2 Composant cassé** (Q11 · 29 · MAJEURE)
— **FIN/composant** [Tv] · — **Nature** [L : cassé, fissuré, arraché, tordu/déformé, autre]

**3.3 Composant HS** (36 · MAJEURE)
— **FIN/composant** [Tv] · — **Symptôme** [L : pas de continuité, ne fonctionne pas, défectueux, autre]

### Famille 4 — MANQUANT (197 · 8%)

**4.1 Pièce manquante** (Q03 · 134 · MINEURE)
— **Pièce** [L : tyrap, obturateur, vis, étiquette, bouchon, rondelle, écrou, switch guard, capuchon, autre (préciser)] · — **Localisation** [FIN/ZONE] · — **Quantité**

**4.2 Câble manquant** (T01/T03 · 63 · MAJEURE)
— **Réf câble** [Tv] · — Type/longueur [T, optionnel] · — Statut appro [L : non reçu, non livré, introuvable, inconnu]
*(Règle R3 : une réf = un bloc.)*

### Famille 5 — AMONT_FABRICATION (88 · 4%) — *le défaut est arrivé avec la pièce*

**5.1 Longueur non conforme** (88 · MAJEURE)
— **Réf câble** [Tv] · — **Longueur** [C/R, numérique + unité] · — Sens [L : trop court, trop long/surlongueur]

**5.2 Défaut à réception** (MAJEURE)
— **Réf pièce/câble** [Tv] · — **Nature** [L : reçu coupé, reçu abîmé, erreur d'impression, non conforme plan, autre]
*(Détection = RÉCEPTION en en-tête ; l'imputation formelle reste dans SAP — champ Y4.)*

### Famille 6 — INSTALLATION (217 · 9%)

**6.1 Cheminement / contrainte** (91 · MINEURE) — **Zone/route** [L : 1M, 2M, 1S, 2S, 1R, 2R, autre] · — **Nature** [L : en contrainte, clash/en contact, frotte, en tension, vrillé, cheminement NC]
**6.2 Fixation / visserie** (72 · MINEURE) — **Élément** [L : clamp, support, vis, rivet, collier, autre] · — **Localisation** · — **Nature** [L : manquant, desserré, cassé, mal monté] · — **Quantité**
**6.3 Métallisation / bonding** (35 · MAJEURE) — **Localisation** · — **Nature** [L : bleu à reprendre, absent, non conforme]
**6.4 Orientation** (12 · MINEURE) — **FIN/élément** [Tv] · — Orientation [C/R, optionnel]
**6.5 FOD / propreté** (7 · MAJEURE) — **Zone** · — **Nature** [L : corps étranger, copeau, brin métallique, poussière, autre]

### Famille 7 — IDENTIFICATION (23 · 1%)

**7.1 Étiquette / marquage** (23 · MINEURE)
— **Élément/FIN** [T] · — **Nature** [L : manquante, décollée, erronée, illisible] · — Réf correcte si erronée [T, optionnel]

### Famille 8 — AUTRE (soupape · historiquement 8%)

**8.1 Autre défaut** — **Description** [T, obligatoire, le seul cas où le texte libre est requis] · — Localisation [FIN/ZONE/NA]

---

## 5. Types de champs et validations

**V1 — FIN** : autocomplétion (R10) ; format `chiffres+lettres(+chiffres)` vérifié en avertissement.
**V2 — Réf câble** : format `\d{4}-\d{4}` proposé, saisie libre tolérée (avertissement).
**V3 — Numériques** : quantité entier ≥1 ; longueurs avec unité (mm/cm) obligatoire.
**V4 — Paires C/R** : les deux valeurs obligatoires quand le motif s'applique ; validation constaté ≠ requis.
**V5 — Listes** : toujours ≤ 9 options visibles + « Autre (préciser) » ; les valeurs sont stockées comme codes (langue-indépendants), les libellés affichés en français avec info-bulle anglaise — les NC en anglais existent (FAL/cabine).
**V6 — Aucune validation ne bloque la soumission** : les avertissements se contournent d'un clic « confirmer quand même », et ce contournement est journalisé (il alimente la tuile santé-données).

---

## 6. Soupapes, couverture, promotion

**S1.** Couverture native mesurée de la taxonomie v1 : **~92%** des 2 346 défauts historiques tombent dans un type précis ; les ~8% restants passent par AUTRE. Avec la soupape, la couverture d'écriture est de 100% — le « pourcentage marginal qui ne rentre pas » se loge dans AUTRE, pas dans un blocage.

**S2.** Tout passage par une soupape (type AUTRE, ou « Autre (préciser) » d'une liste) est agrégé chaque semaine. **Règle de promotion : ≥ 10 occurrences d'un même motif sur 4 semaines → le motif devient une option de première classe** (nouvelle valeur de liste ou nouveau type). C'est ainsi que GAINE_BACKSHELL (132 défauts) a été découvert dans l'AUTRE historique : la soupape est un détecteur de symptômes nouveaux, pas un dépotoir.

**S3.** Symétriquement, une option de liste à zéro usage sur 6 mois est candidate à la rétrogradation (retirée de l'affichage, conservée en donnée).

---

## 7. Sortie générée — compatibilité avec l'existant

**G1.** L'outil **génère automatiquement** le bloc texte au format « DEFAUTS v1 » dans la description longue SAP :

```
### DEFAUTS v1 | MSN: 2160 | PRODUIT: 740VU | DETECTION: TEST
DEF 1 - T04 - 3RN3B : inversion bornes J <-> H
DEF 2 - Q03 - 411VC007A - QTE 4 : obturateurs manquants [tyrap]
### TOTAL: 5
```

SAP reste le système de référence ; le texte reste lisible par un humain ; le parseur existant le lit à 100% (mode `template_v1`). L'outil est donc **déployable sans toucher au SI** : il écrit là où les agents écrivaient, juste sans fautes de structure.

**G2.** La donnée structurée (blocs + champs) est aussi émise telle quelle (table/JSON) vers le pipeline — le parsing devient une simple vérification pour les NC issues de l'outil, et reste le filet pour les NC legacy.

**G3.** Mapping de codes maintenu : chaque type ↔ son code historique (T04, Q01…) et les extensions (M01, L01…). On n'invente pas un troisième vocabulaire.

---

## 8. Ergonomie — règles de vitesse

**E1.** MSN, produit, station, détection pré-remplis depuis le contexte (dernière NC de l'agent sur le poste) ; deux gestes pour confirmer l'en-tête.
**E2.** Rangée « types récents » (D1) en tête de sélection.
**E3.** « Dupliquer le bloc précédent » (R11) toujours visible pendant la saisie d'une liste.
**E4.** Tri des FIN par fréquence produit (R10).
**E5.** Navigation 100% clavier possible (les agents de test saisissent en série).
**E6.** Le bloc affiche en permanence sa phrase générée (« DEF 3 - T02 - 1WK22A : câble en 9A au lieu de 8A ») — l'agent voit ce qu'il écrit, la confiance dans l'outil se construit là.

---

## 9. Cas limites (règles explicites)

**C1 — Défaut couvrant plusieurs FIN** (ex. cheminement traversant) : FIN principal dans le champ, autres FIN dans le complément libre. Un seul bloc.
**C2 — Deux éléments jumeaux atteints du même défaut** (« prises 115VMB et 135VMB mauvaise réf ») : deux blocs (R1/R3) — l'outil propose la duplication pré-remplie.
**C3 — Agent anglophone** : libellés FR + info-bulles EN ; les valeurs stockées sont des codes ; le complément libre est dans la langue de l'agent.
**C4 — Programme classifié** : l'outil n'écrit dans SAP que ce que la règle de classification du programme autorise déjà ; pas de champ nouveau exigeant une info interdite. Les NC caviardées existantes restent hors périmètre outil (voie manuelle du pipeline).
**C5 — NC mono-défaut** : même chemin, un seul bloc — pas de mode séparé, pas de « petite NC » en texte libre.
**C6 — Défaut constaté pendant la retouche** : blocs ajoutés en fin (R9), l'en-tête ne change pas.
**C7 — L'agent ne connaît pas la réf** (câble, pièce) : champ laissé vide + case « réf inconnue » — le vide explicite vaut mieux qu'une réf inventée ; la case alimente la revue.
**C8 — Panne de l'outil** : repli = écrire à la main au format DEFAUTS v1 (le standard texte reste enseigné) ; le parseur absorbe.

---

## 10. Gouvernance et versionnage

**GV1.** Propriétaire de la taxonomie : ingénierie qualité, avec un référent par équipe (test, contrôle final, inspection MIP). Toute évolution (ajout de type, valeur de liste, champ) passe par eux.
**GV2.** Évolutions **additives uniquement** en v1.x : on ajoute des types/valeurs, on n'en supprime ni renomme pas (les données historiques doivent rester jointes). Suppressions/renommages = v2 avec table de correspondance.
**GV3.** Le critère majeure/mineure officiel, une fois fixé en atelier, remplace les défauts par type du §4 — un seul endroit à mettre à jour.
**GV4.** Journal des contournements d'avertissement (V6) et des soupapes (S2) revu en routine qualité hebdomadaire.

---

## 11. Déploiement et mesure

**M1 — Mode ombre d'abord** : l'outil génère le texte, l'agent peut encore corriger à la main avant validation SAP. Confiance avant contrainte.
**M2 — Pilote : contrôle final** (gros bundles, zéro code aujourd'hui = plus gros gain d'information), puis test, puis inspection MIP.
**M3 — Métriques de rollout** sur la tuile santé-données : % de NC créées via l'outil, par équipe/semaine ; temps médian par bloc (cible R12) ; taux de passage par soupape (attendu ≤ 10%, en décroissance) ; taux de contournement d'avertissements.
**M4 — Critère de succès à 3 mois** : ≥ 80% des NC du pilote via l'outil, écart de comptage parseur/outil = 0 par construction, et premier cycle de promotion de soupape effectué (preuve que la boucle d'apprentissage tourne).

---

*Fin de la spécification. Les §4 (types, champs, valeurs) sont la proposition v1 à valider en atelier ; tout le reste — principes, règles R/V/S/G/E/C, gouvernance, déploiement — constitue la définition de l'outil.*
