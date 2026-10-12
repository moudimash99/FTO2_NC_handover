# Codes officiels de retouche — analyse structurelle et décision de taxonomie
### Centre électrique (FTO2) · Août 2026

*Analyse de la grille officielle (123 sous-codes, cotation AMDEC) confrontée à 2 346 défauts réellement parsés. Objet : décider quelle taxonomie utiliser, et rendre la grille officielle utilisable en saisie.*

---

## 1. Verdict en une phrase

**On garde la grille officielle comme vocabulaire — elle est plus cohérente que la mienne, elle est officielle, elle est déjà cotée AMDEC — et on change uniquement le *chemin d'accès* : au lieu de parcourir 123 lignes, l'agent fait 2 choix courts et le système calcule le sous-code.**

Ma taxonomie ne disparaît pas : elle devient une **vue analytique** (regroupement par responsable d'action) calculée à partir des codes officiels. Vocabulaire = le leur. Analyse = les deux.

---

## 2. La découverte structurelle : ce n'est pas une liste, c'est une matrice

La grille paraît être une liste de 123 items. Elle ne l'est pas. Elle est le produit de **deux axes** :

**Axe 1 — la nature du défaut** (le code Q/T) : verrouillage, manquant, erreur de montage, serrage, mise en œuvre, sertissage, métallisation, dommage, impression, dossier, FOD…

**Axe 2 — l'élément concerné** (le sous-code) : contact, cosse, gaine, collier, frettage, visserie, identification, obturateur, câble, composant…

Preuve mesurée : **11 des 13 éléments récurrents apparaissent sous 3 natures ou plus.**

| Élément | Sous-codes | Apparaît sous N natures | Lesquelles |
|---|---|---|---|
| Identification | 18 | **9** | Q03, Q04, Q05, Q06, Q07, Q10, Q11, Q12, Q13 |
| Contact | 20 | **7** | Q01, Q03, Q04, Q06, Q07, Q08, Q11 |
| Visserie / mécanique | 9 | **7** | Q03, Q04, Q05, Q06, Q10, Q16, T03 |
| Câble | 16 | 6 | Q03, Q06, Q11, Q12, T01, T05 |
| Collier | 10 | 5 | Q03, Q04, Q05, Q06, Q11 |
| Tresse / masse | 9 | 5 | Q04, Q09, Q11, T07, T08 |
| Composant / VG | 9 | 5 | Q03, Q04, Q05, Q06, Q11 |
| Gaine | 6 | 4 | Q03, Q06, Q11, T08 |
| Frettage | 4 | 3 | Q04, Q05, Q06 |

**Conséquence directe.** Le sentiment d'être « écrasé par les options » ne vient pas du nombre de concepts — il vient d'avoir aplati une matrice ~14 × ~15 en une liste linéaire de 123 lignes. Les concepts réels sont ~14 natures + ~15 éléments = **29 choses à connaître, pas 123**.

C'est exactement ce que la saisie doit exploiter : demander la nature, puis l'élément, et **calculer** le sous-code. Le sous-code officiel n'est plus quelque chose qu'on cherche, c'est une **coordonnée** qu'on obtient.

---

## 3. Deuxième découverte : les CDVE ne sont pas des codes, c'est une case à cocher

**19 des 123 sous-codes (15%) sont des doublons CDVE** — la même nature, le même élément, sur circuit commandes de vol. Répartis sur Q01, Q05, Q07, Q09, Q11, Q12, T07, T08.

Exemple : `Q07-001 Contact aluminium (dénudage, sertissage)` et `Q07-006 CDVE_Contact aluminium (dénudage, sertissage)` — description identique, seule la criticité du circuit change.

**Donc : un interrupteur « circuit CDVE ? », pas 19 lignes de liste.** Le système bascule automatiquement vers le sous-code CDVE quand il existe. La liste visible tombe de 123 à **104**, et l'agent n'a jamais à chercher la variante CDVE de quoi que ce soit.

C'est la note du bas de la grille qui confirme la lecture : les 31 CDVE ont été ajoutés *après* la cotation, sans re-cotation. Ce sont bien des variantes greffées sur un axe existant, pas des défauts nouveaux.

**Incohérence de cotation à signaler** (pour la session de re-cotation) : le traitement de la détectabilité CDVE n'est pas uniforme.

| Code | Détectabilité normale | Détectabilité CDVE | Lecture |
|---|---|---|---|
| Q07 | 5 | **1** | CDVE = contrôlé à 100% |
| Q01 | 5 / 8 | **1** | idem |
| Q11 | 1 à 10 | **2** | idem |
| Q09 | 1 | 1 | pas de changement |
| **Q05** | 10 | **10** | **pas de changement — anormal** |
| T07 / T08 | 2 | 2 | pas de changement |

Si CDVE implique une vérification à 100%, Q05-005 devrait voir sa détectabilité chuter comme Q07. Elle reste à 10, ce qui lui donne le RPN le plus élevé de toute la grille (600). Soit le contrôle CDVE ne couvre effectivement pas le serrage — et c'est une information importante — soit c'est une erreur de cotation. À trancher.

---

## 4. Troisième découverte : la grille contient déjà la réponse à majeure / mineure

La question laissée ouverte depuis le début (« quel critère pour majeure vs mineure ? ») n'a pas besoin d'atelier : **la colonne Severity est déjà cotée de 1 à 10 pour chaque sous-code.**

Seuil proposé : **sévérité ≥ 8 = MAJEURE**, sinon mineure. Cela classe 29% des sous-codes en majeur, ce qui est cohérent avec la part de retouches majeures observée dans les données GPS (~22%). La distribution est nettement bimodale (34 codes à sév. 3, 36 à sév. 4, puis un saut à 15 codes à sév. 8 et 19 à sév. 9), donc le seuil tombe dans un creux naturel — il n'est pas arbitraire.

**Et la colonne Priorité est entièrement dérivable.** Règle reconstituée, vérifiée à **100% sur les 121 lignes cotées** :

> Priorité HAUTE si RPN ≥ 480 **ou** sévérité = 10 · Priorité BASSE si RPN ≤ 55 · sinon MOYENNE

Cette règle n'est écrite nulle part dans la grille. La documenter évite qu'elle se perde et permet de coter automatiquement tout nouveau sous-code.

---

## 5. Quatrième découverte : la grille n'a aucune soupape

**Il n'existe aucun code « Autre ».** 123 sous-codes très spécifiques, zéro échappatoire.

Les mentions « etc… » à l'intérieur des libellés font office de rattrapage informel, mais elles obligent l'agent à *décider si son cas compte comme « etc. »* — c'est de l'ambiguïté, pas une soupape.

**C'est probablement une cause majeure de la faible adoption.** Le comportement rationnel d'un agent qui ne trouve pas son code n'est pas de forcer un code approchant — c'est de renoncer et d'écrire du texte libre. Ce qui est exactement la situation actuelle.

Mesure sur les données réelles : **8% des défauts parsés ne correspondent à aucun code de la grille** (lignes administratives, incohérences plan, instructions vagues, défauts multi-sujets). Sans code « Autre », ces 8% ne peuvent structurellement pas être codés.

**Proposition : ajouter un code `Q99 — Autre` avec description libre obligatoire**, plus une option « Autre (préciser) » en fin de chaque liste d'éléments. Avec revue hebdomadaire : ≥ 10 occurrences d'un même motif sur 4 semaines → promotion en sous-code officiel. La soupape devient un détecteur de manques dans la grille, pas un dépotoir.

---

## 6. Couverture réelle : la grille tient la route

Test : projection des 2 346 défauts parsés sur la grille officielle.

| Résultat | Valeur |
|---|---|
| Défauts correspondant à un code officiel | **92%** |
| Non couverts (nécessitent Q99) | 8% |
| **Défauts dont le code est ambigu** (ma catégorie éclate sur plusieurs codes officiels) | **26%** |

Volume réel par code officiel (top) : **Q03 497 · T04 373 · T02 291 · Q11 221 · Q04 216 · Q01 110 · Q05 95 · Q06 91 · Q12 88**.

Deux enseignements opérationnels :

1. **Les 5 premiers codes couvrent 68% des défauts.** Une rangée de raccourcis « les plus fréquents » traite les deux tiers des saisies en un clic. Et ces 5 codes diffèrent selon le contexte : au test c'est T04/T02/T01/T05/T03, en inspection c'est Q03/Q11/Q04/Q01/Q05.
2. **Q10 (dommage structure), Q13 (dossier de fabrication) et Q16 (FOD) sont quasi absents des données** — soit ces défauts ne surviennent pas au centre électrique, soit ils sont déclarés ailleurs. À vérifier : un code jamais utilisé encombre la liste sans rien apporter.

---

## 7. La comparaison honnête : leur taxonomie vs la mienne

C'était votre question centrale — familiarité contre cohérence. Après analyse, **la réponse penche nettement de leur côté, et ce n'est pas de la diplomatie.**

**Leur grille est structurellement cohérente** : un axe nature × un axe élément, appliqué systématiquement. **La mienne est un hybride** : certaines familles sont des natures (MANQUANT), d'autres des objets (IDENTIFICATION), une autre un stade amont (AMONT_FABRICATION). Sur le critère de cohérence logique que vous posiez, c'est moi qui perds.

Là où mes familles éclatent sur leurs codes — la « non-correspondance » que vous aviez sentie :

| Ma catégorie | Défauts | Éclate sur |
|---|---|---|
| FREINAGE_FRETTES | 136 | Q03 / Q04 / Q05 / Q06 |
| GAINE_BACKSHELL | 132 | Q03 / Q06 / Q11 |
| FIXATION_VISSERIE | 72 | Q03 / Q04 / Q05 / Q11 |
| LONGUEUR_NC | 88 | Q12 / Q06 |
| CABLE_MANQUANT | 63 | T01 / Q03 |
| ETIQUETTE_MARQUAGE | 23 | Q03 / Q04 / Q11 / Q12 |

Ce n'est pas un défaut de l'une ou de l'autre : c'est la signature mathématique d'un regroupement **par objet** projeté sur un regroupement **par nature**. Le frettage éclate en quatre parce qu'un frettage peut être *manquant* (Q03), *de mauvaise référence* (Q04), *mal serré* (Q05) ou *mal mis en œuvre* (Q06) — et ce sont réellement quatre problèmes différents, avec quatre corrections différentes. **Leur découpage est plus fin et plus juste que le mien.**

Trois arguments de plus, non structurels mais décisifs :
- La grille est **officielle et cotée AMDEC** — sévérité, occurrence, détectabilité, RPN. Je n'ai rien de comparable.
- Une équipe (le test) l'utilise déjà à 100%. Toute base d'adoption existante est un actif.
- **Inventer un troisième vocabulaire est le pire résultat possible** — c'est d'ailleurs la règle que j'avais écrite moi-même dans la spec : on étend, on ne remplace pas.

**Ce que je garde de ma taxonomie** : les 8 familles restent utiles comme **vue de restitution orientée responsable d'action** (branchement → instruction/détrompage ; manquant → appro ; amont → atelier câbles). Elles se calculent à partir des codes officiels par une table de correspondance. Ce n'est pas un vocabulaire concurrent, c'est un axe d'analyse supplémentaire pour le tableau de bord — et il coexiste sans friction avec l'axe nature de la grille.

---

## 8. Ce que ça donne en saisie : 123 lignes → 2 choix

L'outil (prototype livré) applique tout ce qui précède :

**Chemin 1 — raccourcis (≈68% des cas, un clic).** La détection saisie en en-tête détermine la rangée : Test → T04, T02, T01, T05, T03. Inspection → Q03, Q11, Q04, Q01, Q05.

**Chemin 2 — recherche.** Une zone de recherche qui interroge *les deux axes en même temps* : taper « contact » remonte tous les sous-codes contact toutes natures confondues ; taper « manquant » remonte Q03 ; taper « T04 » va droit au but. C'est ce qui réconcilie les deux façons de penser — l'inspecteur qui pense « objet d'abord » et le testeur qui pense « nature d'abord » trouvent tous les deux.

**Chemin 3 — matrice explicite.** Étape 1 : la nature (21 tuiles, T ou Q priorisées selon la détection). Étape 2 : l'élément, filtré à ceux qui existent réellement sous cette nature (2 à 19 options). Le sous-code officiel s'affiche, calculé.

**Puis, automatiquement :** case CDVE si une variante existe (bascule le code) · sévérité pré-remplie depuis la cotation, modifiable · RPN et priorité affichés en direct · localisation avec autocomplétion des FIN les plus fréquents · quantité · complément libre.

**Et à la fin :** le texte SAP au format DEFAUTS v1, avec les **vrais sous-codes officiels**, lisible à 100% par le parseur existant. Plus le RPN cumulé de la NC — un indicateur de gravité que personne n'a aujourd'hui.

Le choix T vs Q disparaît aussi comme charge mentale : puisque la détection est déclarée en en-tête, le système sait déjà s'il faut proposer les codes test ou les codes inspection. C'est une ambiguïté de moins (T01 « câble manquant » vs Q03-004 « élément électrique manquant » désignent le même défaut trouvé à deux stades — aujourd'hui ce choix repose sur l'agent, demain il est déduit).

---

## 9. Défauts de la grille à corriger (liste pour la session de re-cotation)

1. **Aucun code « Autre »** — la lacune la plus coûteuse en adoption. Ajouter Q99.
2. **Q12-007 et Q12-008 non cotés** (RPN 0, colonnes vides).
3. **Libellés incohérents pour un même code** : Q05 apparaît sous 4 noms différents (TIGHTENING ELEMENT / CLOSING ELEMENT / ELEMENT TIGHTENING / ELEMENT CLAMPING) ; Q06 sous 3 ; Q01, Q03, Q11, Q12 sous 2 chacun. Un code = un libellé.
4. **Détectabilité CDVE incohérente** entre Q07/Q01/Q11 (améliorée) et Q05/Q09/T07/T08 (inchangée) — cf. §3.
5. **Colonne Priorité : « Medium » et « Average » coexistent** pour le même niveau.
6. **Trous de numérotation** : Q02, Q14, Q15 n'existent pas ; Q11 saute 15, 17, 20, 21, 23, 24, 25 (héritage des 16 sous-codes supprimés à la fusion du 19/11/24). Documenter que ce sont des trous volontaires, sinon quelqu'un les comblera un jour avec autre chose.
7. **Q11-014 est listé hors séquence** (après Q11-001).
8. **La re-cotation annoncée « début 2025 » n'a pas eu lieu** — nous sommes en août 2026. Les cotations CDVE restent provisoires depuis 18 mois.
9. **Règle de priorité non documentée** — la reconstituer officiellement (§4) pour qu'elle survive et s'applique aux futurs codes.
10. **Codes possiblement morts** : Q10, Q13, Q16 quasi absents des données réelles. Vérifier avant de les garder dans la liste de saisie.

---

## 10. Ce qu'il reste à décider (humain, pas technique)

1. **Valider le seuil sévérité ≥ 8 = majeure** — ou fixer le vôtre. Un chiffre, cinq minutes.
2. **Accepter ou refuser Q99 (Autre)** — c'est le point qui conditionne le plus l'adoption.
3. **Confirmer que CDVE est bien un attribut de circuit** et non autre chose, avant de le transformer en case à cocher.
4. **Trancher Q05-005** : la détectabilité 10 en CDVE est-elle réelle ou une erreur de cotation ?
5. **Statuer sur Q10 / Q13 / Q16** : garder ou retirer de la liste de saisie.

---

*Livré avec : `nc_tool_official_codes.jsx` (prototype cliquable sur les 123 codes officiels), `official_codes.csv` (la grille structurée, exploitable en machine).*
