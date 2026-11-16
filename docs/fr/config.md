# Paramètres (config) : comment ils fonctionnent et comment les remplir

Tout ce que l'on peut vouloir changer dans le tableau de bord sans toucher au code est une petite table du dossier
`data/config/`, à côté du notebook dans le Code Workspace. Il y a 45 tables, en quatre groupes. Ce guide explique ce
qu'elles contiennent, comment elles sont construites, comment les remplir et comment le code les lit.

Les trois guides : `config.md` (les tables de paramètres ; dans le Code Workspace, aussi sous le nom `data/config/README.md`),
`logic.md` (le code du notebook) et `front_end.md` (le code des pages) ; ces deux derniers sont aussi dans `notebook_kit/`.

**Sommaire**

1. [Les bases : à quoi ressemble une table](#1-les-bases--à-quoi-ressemble-une-table)
2. [Les quatre groupes : qui doit modifier quoi](#2-les-quatre-groupes--qui-doit-modifier-quoi)
3. [Après un changement](#3-après-un-changement)
4. [Les cinq sortes de tables](#4-les-cinq-sortes-de-tables)
5. [Chaque table, une par une](#5-chaque-table-une-par-une)
6. [Les tâches courantes](#6-les-tâches-courantes)
7. [Comment le code lit les tables](#7-comment-le-code-lit-les-tables)

---

## 1. Les bases : à quoi ressemble une table

Chaque table est un fichier texte qui finit par `.csv`. Elle s'ouvre dans Excel comme un tableur : la première ligne contient
les noms des colonnes, et chaque ligne en dessous est une entrée. Dans le fichier, les colonnes sont séparées par un
point-virgule (`;`).

**Règles pour les remplir**

- **Gardez la première ligne** (les noms des colonnes) exactement comme elle est. Le code trouve les colonnes par leur nom.
- **Ne tapez pas de `;` dans une cellule.** Le point-virgule sépare les colonnes : s'il est tapé dans un texte, il décale tout
  ce qui suit. Si l'exécution s'arrête avec « line N has X columns, the header has Y », c'est la cause.
- **Dates :** année-mois-jour, par exemple `2026-01-01`. Un mois seul : `2026-01`.
- **Décimales :** écrivez-les avec un point, par exemple `0.25`. (Les tables de coût acceptent aussi une virgule.)
- **Plusieurs valeurs dans une cellule :** séparez-les par `|`, par exemple `FTO2|FT02`. Une seule suffit.
- **Paramètres oui / non :** écrivez `oui` ou `non`.
- **Enregistrer depuis Excel :** « CSV UTF-8 (séparé par des points-virgules) », pour que les accents et le `;` restent
  justes. Si Excel propose de conserver ce format, répondez oui.
- Une colonne nommée `commentaire`, `description`, `note` ou `exemple` est destinée aux personnes. Le code l'ignore :
  écrivez-y tout ce qui peut aider la personne suivante.

Le fichier `lisez_moi.csv` (en français) liste chaque table, son groupe, ce qu'elle change, qui doit la modifier et quelle
partie du code la lit.

## 2. Les quatre groupes : qui doit modifier quoi

Le chiffre au début de chaque nom de fichier dit dans quel groupe se trouve la table.

| Groupe | Qui modifie | Ce que contiennent ces tables |
|---|---|---|
| **0** données | Personne : jamais à la main | Ce qui vient des fichiers que l'équipe télécharge (le plan de production, les demandes de câbles) et l'historique (les livraisons 2025, la feuille EqMSN 2026). Pour les mettre à jour, déposez un nouveau téléchargement dans `data/` (voir « Les fichiers déposés tels que téléchargés » plus bas). |
| **1** les paramètres de la personne responsable | La personne responsable du tableau de bord | Les quelques éléments qui se décident et ne se calculent pas : l'année suivie, l'objectif, ce que les pages affichent à l'ouverture, les taux horaires et les minutes du coût, les jours de fermeture, les prix des pièces, les actions MFT. Six petites tables. |
| **2** règles et noms | Le développeur (ou une personne attentive, avec ce guide) | Comment les choses sont comptées et nommées : ce qui compte comme REC, à quel produit appartient une NC, les catégories, les couleurs, d'où viennent les données. Les chiffres changent : vérifiez le tableau de bord avant et après. |
| **3** expert | Le développeur | Les minutes par type de défaut du modèle de coût, les statistiques des alarmes, la liste officielle des sous-codes. À ne changer qu'en ayant en tête le modèle qui est derrière. |

**Deux tables nom / valeur sont en deux parties.** `1_parametres.csv` et `1_reglages_pages.csv` contiennent les lignes que
la personne responsable modifie ; `2_parametres.csv` et `2_reglages_pages.csv` contiennent les lignes techniques du même
genre. Le code demande une ligne par son nom et la trouve dans l'une ou l'autre partie ; une ligne écrite dans les deux arrête
l'exécution avec un message.

### Les fichiers déposés tels que téléchargés

Deux choses ne se tapent dans aucune table. L'équipe télécharge un fichier et le dépose dans `data/`, à côté du fichier des
postes, du registre GPS et de la liste Test ; l'exécution suivante le lit (`notebook_kit/fto2/downloads.py`).

| Quoi | Le fichier à déposer dans `data/` | Comment il est lu |
|---|---|---|
| Le plan de production | Chaque export du **Tableau Avances / Retards**, en CSV, nommé `Avances_Retards...csv` | **Tous** les exports du dossier sont lus, du plus ancien au plus récent : gardez les précédents. Un avion prend sa ligne dans l'export le plus récent qui le liste ; un avion livré avant un nouvel export, et qui n'y figure plus, garde sa dernière ligne (c'est ainsi que le plan se souvient de l'année d'avant, dont les livraisons sont le point de départ des objectifs) ; une ligne qui a quitté l'export avant sa livraison a quitté le plan. |
| Les demandes de câbles | L'export du **suivi de l'équipe câbles**, en CSV, avec `cables` dans son nom | L'export le plus récent remplace la liste. |

Le jour d'un téléchargement est la date à la fin de son nom quand il en a une (`Avances_Retards_2026-11-03.csv`), sinon le
jour où le fichier a été enregistré. Les noms que l'exécution cherche sont deux lignes de `2_sources.csv` (`exports_plan`,
`suivi_cables`), avec `*` pour n'importe quel texte. Les tables `0_plan_msn.csv` et `0_demandes_cables.csv` contiennent le
plan et les demandes tels qu'ils étaient quand on a commencé à déposer les téléchargements dans `data/` : la table du plan
est lue comme un export de plus, à sa propre date ; la table des câbles n'est utilisée que s'il n'y a aucun export du suivi.
Les dernières lignes de chaque exécution disent quels fichiers ont été lus.

## 3. Après un changement

1. Enregistrez la table.
2. Lancez le notebook.
3. Si une table est mal remplie, l'exécution s'arrête et dit **quel fichier, quelle ligne et quoi corriger**. Par exemple :
   « 2_regle_phase.csv line 4: test 'contien' is not one of contient, mot, commence_par... ».
4. Regardez le tableau de bord : le changement doit apparaître là où vous l'attendez, et nulle part ailleurs.

Pour un changement de niveau 2 ou 3, notez les chiffres clés du tableau de bord avant le changement, et comparez après : seul
ce que vous attendiez doit bouger.

## 4. Les cinq sortes de tables

Presque toutes les tables sont de l'une de ces cinq sortes. Une fois que vous les connaissez, toutes les tables se lisent de
la même façon.

### 4.1 Les listes : une ligne par élément

Exemple : `1_calendrier_production.csv`, une ligne par fermeture, avec ses dates et son poids. Ajoutez une ligne pour ajouter
un élément, supprimez une ligne pour l'enlever. Chaque colonne contient une information sur cet élément.

### 4.2 Nom et valeur : un paramètre par ligne

Exemple : `1_cout_parametres.csv`.

| nom | valeur | unite | description |
|---|---|---|---|
| taux_production | 123 | EUR/h | Production : alerte de l'opérateur, préparation, travail... |

Le code cherche chaque paramètre par son **nom** (`nom`) : ne changez jamais un nom, ne supprimez jamais une ligne. Changez
seulement la **valeur** (`valeur`). La description dit ce que la valeur veut dire.

### 4.3 Les règles : comment le code décide quelque chose sur chaque NC

Exemple : `2_regle_phase.csv`, qui décide si une NC est SERIE, REC ou FTI.

| ordre | resultat | colonne | test | valeur | commentaire |
|---|---|---|---|---|---|
| 1 | FTI | constituent_assembly | commence_par | WY\|WA | Assemblage FTI, ex. WA999 |
| 2 | REC | workflow_list | mot | REC | Le mot REC dans le workflow |
| 3 | REC | workflow_list | contient | -CRE\|-PNC\|A30-REJ-PVU2 | Workflows REC connus |
| 99 | SERIE | | toujours | | Tout le reste |

**Comment la lire, en clair :** « Si l'assemblage commence par WY ou WA, c'est FTI. Sinon, si le workflow contient le mot
REC, c'est REC. Sinon, si le workflow contient -CRE, -PNC ou A30-REJ-PVU2, c'est REC. Sinon, c'est SERIE. »

Les colonnes :

- **ordre** : l'ordre dans lequel les règles sont essayées, de la plus petite valeur à la plus grande. **La première règle qui
  correspond donne le résultat** ; les autres ne sont pas regardées.
- **resultat** : ce que la NC reçoit quand la règle correspond.
- **colonne** : quelle donnée de la NC la règle regarde (une colonne des données NC de Skywise). Deux colonnes reliées par
  ` + ` sont lues comme un seul texte, par exemple `description_short + article_version_description`.
- **test** : comment elle regarde (liste ci-dessous).
- **valeur** : ce qu'elle cherche. Plusieurs valeurs séparées par `|` : une seule suffit.
- **commentaire** : une note pour les personnes.

**Plusieurs lignes avec le même `ordre` forment une seule règle : toutes doivent être vraies.** Dans `2_regle_perimetre.csv`,
deux lignes ont l'ordre 1 : la NC est un retour client seulement si son type est « NC Retour client » **et** si FTO2 figure
dans sa responsabilité.

**La dernière règle** a le test `toujours` et pas de colonne : c'est la règle par défaut, pour toutes les NC qu'aucune autre
règle n'a attrapées. Chaque table de règles doit en avoir une.

**Les tests** (majuscules et minuscules sont traitées pareil) :

| Test | Veut dire | Exemple |
|---|---|---|
| `contient` | le texte contient l'une des valeurs | `-CRE` correspond à « REW-CRE-01 » |
| `ne_contient_pas` | le texte n'en contient aucune | |
| `mot` | contient l'une d'elles comme mot entier | `REC` correspond à « REW-REC » mais pas à « RECEPTION » |
| `commence_par` | commence par l'une d'elles | `WY\|WA` correspond à « WA999 » |
| `ne_commence_pas_par` | ne commence par aucune d'elles | |
| `egal` | est exactement l'une d'elles (espaces aux extrémités ignorés) | |
| `different` | n'est aucune d'elles | |
| `vide` / `non_vide` | la cellule est vide / n'est pas vide | |
| `toujours` | toujours vrai : la règle par défaut, en dernier | |
| `regex` / `pas_regex` | expert : une « expression régulière » (un motif de recherche) est trouvée / n'est pas trouvée | `32\d` = « 32 » puis un chiffre |
| `extraire` | expert : prend un morceau du texte, qui devient le résultat quand `resultat` vaut `{extrait}` | trouve « 740VU » dans l'article |

### 4.4 Les correspondances : une valeur en devient une autre

Exemple : `2_produits_plan.csv`, qui fait correspondre le nom du produit sur une NC à son nom dans le plan de production
(`MIP A350` → `MIP`). La colonne de gauche est ce qui est trouvé, la colonne de droite ce que cela devient. Une ligne par
valeur.

### 4.5 Les tables de données (groupe 0)

Les tables dont le nom commence par `0_` ne sont pas des paramètres : elles contiennent des données. Deux sont le point de
départ de ce que l'exécution lit maintenant dans les téléchargements déposés dans `data/` (le plan de production, les demandes
de câbles : section 2) ; les autres sont de l'historique (les livraisons 2025, la feuille EqMSN 2026). Personne ne les
modifie. Une erreur dans le plan ou dans les demandes de câbles se corrige là où elle a été faite, dans le Tableau Avances /
Retards ou dans le suivi câbles, puis un nouveau téléchargement est déposé.

---

## 5. Chaque table, une par une

Les tables sont regroupées par sujet. Pour chacune : ce qu'elle fait, ce qu'est une ligne, et comment la remplir.

### Quelles NC comptent, et comment chacune est étiquetée (tables de règles, groupe 2)

Ce sont toutes des **tables de règles** (section 4.3). Elles regardent les colonnes des données NC de Skywise.

| Table | Décide | Résultats |
|---|---|---|
| `2_regle_exclusion.csv` | Quelles NC sont entièrement laissées de côté (les NC d'ERMA, les NC supprimées dans une autre usine) | `exclure` ou `garder` |
| `2_regle_phase.csv` | Le type de production | `SERIE`, `REC`, `FTI` |
| `2_regle_ligne.csv` | La ligne avion, d'après le programme | `A350`, `A330`, `A400M`, `A320`, sinon le nom du programme lui-même, sinon `Autre` |
| `2_regle_perimetre.csv` | Où la NC a été émise | `serie` (chez FTO2), `client` (retour client, FTO2 responsable), `autre` |
| `2_regle_origine.csv` | Qui l'a ouverte | `Test` ou `Qualite` |
| `2_regle_type_nc.csv` | Le type de NC (où elle a été trouvée), par ordre de priorité | `CONTROLE FINAL`, `CABLES`, `TEST`, `NC Interne`, `NC Fournisseur`, `NC Retour client`... |
| `2_regle_produit.csv` | Le produit, d'après l'article puis le poste | `MIP A350`, `PTVU`, `300VU`... ou le numéro d'armoire trouvé (`{extrait}`), sinon `Other` |
| `2_regle_responsabilite.csv` | Les trois cases « Responsabilité » du tableau de bord | `f` (FTO2), `s` (un fournisseur), `o` (autres) |

Deux règles simples : mettez les cas particuliers **avant** les cas généraux (un `ordre` plus petit), et gardez la règle
`toujours` en dernier.

### Les produits et le plan de production

| Table | Groupe | Ce qu'est une ligne | Comment la remplir |
|---|---|---|---|
| `0_plan_msn.csv` | 0 | Un avion (MSN) et un produit : ligne, produit, MSN, rang, puis la date **prévue** (`prevu_`) et la date **réelle** (`reel_`) des 8 jalons (impression, enclenchement, SE, méca, inté, test, qualité, départ OTA), la date de l'export d'où elle vient | Ne se modifie pas. Le plan tel qu'il était le 3 novembre 2026 ; l'exécution ajoute chaque export du Tableau Avances / Retards déposé dans `data/` (section 2). |
| `0_eqmsn_mois.csv` | 0 | Un produit et une version (`std` = feuille Standard, `adj` = feuille Adjusted) : son EqMSN pour chaque mois de 2026, la date de l'export, le premier mois de prévision | Ne se modifie pas. Les pages comptent le volume à partir du plan de production (chaque avion réparti sur les jours où l'usine travaille) ; cette table ajoute seulement les deux versions de la feuille EqMSN tant que ses mois sont ceux de l'année suivie. Pour une autre année, elle est ignorée. |
| `1_calendrier_production.csv` | 1 | Une période de fermeture ou de production ralentie : début, fin, **poids** (0 = fermé, 0,5 = la moitié d'une semaine normale), motif | Ajoutez une ligne pour chaque nouvelle fermeture ou chaque nouveau pont, chaque année. Cela change le volume MSN des mois et des semaines concernés. Dates sous la forme `2026-12-24` ou `24/12/2026`. |
| `0_livraisons_2025.csv` | 0 | Un produit livré en 2025 : son nom, son nom dans le plan, sa ligne, le nombre par mois de 2025, le total | Ne se modifie pas. La base des objectifs 2026. Pour une année de comparaison plus récente, aucune table de ce genre n'est nécessaire : les livraisons sont comptées dans le plan de production (voir « L'année » plus bas). Une table `0_livraisons_<year>.csv` de même forme est utilisée à la place quand elle existe. |
| `0_livraisons_2025_lignes.csv` | 0 | Une ligne avion : les MSN entiers livrés en 2025 | Ne se modifie pas. |
| `2_produits_plan.csv` | 2 | Nom du produit sur les NC → nom du produit dans le plan (`produit_eqmsn`) ; `a_confirmer` = oui s'il n'est pas encore confirmé | Un nouveau produit : ajoutez sa ligne. |
| `2_produits_noms_plan.csv` | 2 | Nom dans le plan → nom affiché (`MIP` → `MIP A350`) | |
| `2_produits_alias.csv` | 2 | Les NC dont le produit n'est pas dans le plan, renvoyées vers le produit du plan dont elles font partie : ligne, motif du produit, motif du poste (facultatif), produit cible | Les motifs sont des expressions régulières (expert) : `^\d{3}VU$` = trois chiffres puis VU. |

### Le coût de non-qualité

Comment le coût fonctionne, en simple : chaque NC passe par six **étapes** au plus (alerte, rédaction, support technique,
préparation, intervention, recontrôle). Chaque étape prend un certain nombre de **minutes**, payées au **taux horaire** de
la personne qui la fait. On ajoute les heures d'ingénierie (design queries), la matière, et le prix d'une pièce rejetée,
rebutée ou échangée.

| Table | Groupe | Ce qu'elle contient | Comment la remplir |
|---|---|---|---|
| `1_cout_parametres.csv` | 1 | Nom / valeur : les **taux horaires** (production 123, qualité 107, ME 76, ingénierie 78,16) et les **minutes de chaque étape** (alerte 41, rédaction 30, au contrôle final 60, support 60, préparation 50, travail minimum 60, recontrôle 30...), les **minutes de logistique** ajoutées quand le travail vient de l'ordre de retouche (15), le facteur des NC internes, le montant forfaitaire d'un retour client | Changez seulement la valeur, avec un point ou une virgule. Une valeur inférieure à zéro arrête l'exécution. |
| `2_cout_decisions.csv` | 2 | Une décision (RWK retouche, REJ rejet, SCR rebut, EXC échange, DQN design query...) : `1` ou `0` pour chaque étape qu'elle compte (alerte, redaction, support, travail, recontrole), ses heures d'ingénierie, `valeur_piece` (1 = la valeur de la pièce compte), son libellé, et `base` (d'où vient la règle) | Un nouveau code de décision : ajoutez une ligne. |
| `2_cout_qui_fait_quoi.csv` | 2 | Chaque étape → qui la fait (`production`, `qualite`, `me`), donc à quel taux elle est payée | |
| `3_cout_temps_defauts.csv` | 3 | Un **type de défaut** : minutes de travail, matière en euros, nom anglais, sous-code de référence, et `base` (d'où vient le temps). Un type peut aussi être **calculé à partir d'un autre** (`calcule_depuis`) × un facteur (`facteur`) : « mauvaise référence » = 2 × « manquant » | Expert : ces minutes font l'essentiel du coût. |
| `1_prix_pieces.csv` | 1 | **Le prix de chaque pièce** : une ligne par matériel (le numéro de matériel que la NC indique), sa description et son prix unitaire. La valeur d'une pièce rejetée, rebutée ou échangée = prix × quantité | Ajoutez une ligne par matériel, ou collez un export (les colonnes du matériel et du prix sont reconnues par leur nom). Prix vide = pas encore de prix. Les matériels encore sans prix sont listés à chaque exécution dans `fto2_parts_to_price.csv`. Guide : `part_prices.md`. |
| `3_cout_airbus.csv` | 3 | Le coût standard Airbus par décision (niveau 1 du coût) | Seulement si le standard officiel change. |
| `3_cout_avance.csv` | 3 | Nom / valeur : la version du modèle, quels types de NC sont « contrôle final » ou « interne », les préfixes d'un ordre de retouche, les classes d'erreur de branchement, si le temps prévu des ordres de retouche et le temps déclaré des aléas remplacent les temps du modèle (`oui`/`non`), la fenêtre de temps qui relie un aléa à une NC | Expert. |
| `3_cout_ordres_operations.csv` | 3 | Comment lire les opérations d'un ordre de retouche : un motif dans le texte de l'opération → à quelle étape elle compte (préparation ou travail) | Expert. |

### Catégories, causes et sous-codes (comment s'appellent les défauts)

Les défauts sont classés sur trois niveaux : **catégorie** (par exemple Erreur Branchement) → **cause** (par exemple
Inversion) → **sous-code** (le code officiel, par exemple T04).

| Table | Groupe | Ce qu'est une ligne | Comment la remplir |
|---|---|---|---|
| `2_categories.csv` | 2 | Une catégorie : son ordre sur les graphiques, sa couleur (1 à 9), `a_part` = oui pour la montrer à part, sans couleur | Changez l'ordre ou la couleur. |
| `2_causes_noms.csv` | 2 | Un code de cause (venant du lecteur de texte) → le nom affiché | **Ne changez pas le code** (colonne de gauche) ; le nom peut changer. |
| `2_causes_definitions.csv` | 2 | Une cause : sa catégorie, sa définition en français et en anglais (l'onglet Définitions) | Améliorez une définition librement. |
| `3_sous_categories.csv` | 3 | Une sous-catégorie : sa catégorie, sa cause, mineure ou non, ses sous-codes officiels | Expert. |
| `3_souscodes.csv` | 3 | Les sous-codes officiels : sous-catégorie, groupe, cause, description, gravité... | Seulement quand la liste officielle change. |
| `3_souscodes_fr.csv` | 3 | La description en français de chaque sous-code | |
| `3_a400m_titres.csv` | 3 | Les NC A400M n'ont pas de texte long, donc leur sous-code est lu dans le titre : un motif dans le titre → sous-code, câble ou non, un exemple. Le premier motif trouvé l'emporte ; un sous-code vide veut dire « pas un défaut » | Expert : les motifs sont des expressions régulières. |
| `2_decisions.csv` | 2 | Un code de décision → son libellé | |
| `2_libelles_lieu_detection.csv` | 2 | Une valeur de « lieu de détection » → son libellé anglais | |

### Les pages

| Table | Groupe | Ce qu'elle contient |
|---|---|---|
| `1_reglages_pages.csv` | 1 | Nom / valeur, la partie de la personne responsable. L'**objectif** (`objectif_baisse` : 0.25, 0,25 ou 25 % veulent tous dire le taux de l'année de comparaison moins 25 % ; les textes des pages affichent le pourcentage écrit ici), le poids de juillet et d'août dans l'objectif mensuel (`poids_mois` : numéro du mois = poids), les **filtres à l'ouverture** (`defaut_phase` : SERIE, REC, FTI ou vide ; `defaut_responsabilite` : des lettres parmi f, s, o ; `defaut_periode` : ytd, m1, m3, m6, m12 ou all), l'**objectif des actions MFT** (moins 30 %, tenu 4 semaines). Chaque valeur est vérifiée : une erreur arrête l'exécution et dit quoi écrire. |
| `2_reglages_pages.csv` | 2 | Nom / valeur, la partie technique : ce qui compte comme semaine de fermeture, le volume MSN minimum pour un taux, les sous-codes qui veulent dire « non précisé », les seuils de la page MFT (« ce qui monte / baisse », FIN récurrents, fenêtres de référence). |
| `2_lignes.csv` | 2 | La couleur de chaque ligne (1 à 4). |
| `3_alarmes.csv` | 3 | Nom / valeur : les statistiques de la cloche. Combien de semaines récentes sont comparées (4) avec combien de semaines d'avant (12), les seuils d'une alarme mineure ou majeure, les hausses lentes, les avions hors norme, combien d'alarmes sont affichées (5). |

### Les actions MFT et les câbles

| Table | Groupe | Ce qu'est une ligne | Comment la remplir |
|---|---|---|---|
| `1_actions_mft.csv` | 1 | Une action MFT : `id` (le sien, jamais réutilisé), ligne, titre (français et anglais), **le problème visé** (`niveau` + `valeurs`), porteurs de l'analyse et de l'action, dates, statut, bénéfice attendu, d'où elle vient | Pour ajouter une action : une ligne. `niveau` dit de quel genre de problème il s'agit : `cat` une catégorie, `rca` une cause, `sub` une sous-catégorie, `code` un sous-code, `where` un lieu de détection (les mots français sont lus aussi : `catégorie`, `cause`, `sous-catégorie`, `sous-code`, `lieu`). `valeurs` : les noms exactement comme sur le tableau de bord, plusieurs séparés par `\|`. Dates sous la forme `2026-07-01` ou `01/07/2026`. Une action sans `niveau` apparaît sur la page MFT sans résultat suivi. L'exécution vérifie les ids, le `niveau` et les dates. |
| `0_demandes_cables.csv` | 0 | Une demande de câble de l'équipe câbles : semaine, date, NC, programme, MSN, motif, imputation, origine, cause proposée, câbles, commentaire | Ne se modifie pas. Les demandes telles qu'elles étaient en novembre 2026 ; l'exécution lit à la place l'export le plus récent du suivi câbles déposé dans `data/` (section 2). |
| `2_cables_origines.csv` | 2 | Une imputation du suivi câbles → l'origine affichée (`(autre)` = tout le reste) | Lue chaque fois que l'export du suivi est lu. Une nouvelle imputation dans le suivi : ajoutez sa ligne. |
| `2_regle_cause_cable.csv` | 2 | Table de règles (section 4.3) : la cause proposée d'une demande de câble, d'après des mots-clés de son commentaire d'analyse | Lue chaque fois que l'export du suivi est lu. |

### Les paramètres généraux et les sources de données

| Table | Groupe | Ce qu'elle contient |
|---|---|---|
| `1_parametres.csv` | 1 | Nom / valeur, la partie de la personne responsable : **l'année suivie** (`annee`) et l'année de comparaison (`annee_comparaison`, vide = l'année d'avant). Voir « L'année » plus bas. |
| `2_parametres.csv` | 2 | Nom / valeur, la partie technique : l'usine suivie (`FTO2`) et ses codes (`FTO2\|FT02`), si les anciennes sorties Slate sont encore écrites (`oui` tant que l'ancienne application est utilisée), une limite au nombre de NC (vide = toutes). |
| `2_sources.csv` | 2 | Nom / valeur : les noms des datasets Skywise (comme dans le panneau Data du notebook) et des fichiers de `data/` (postes, registre GPS, liste Test, exports du plan de production, suivi câbles), avec les lignes à sauter et les noms des colonnes de ces fichiers. Changez-la quand un dataset ou un fichier est renommé. Dans le nom d'une liste, `{annee}` tient la place de l'année suivie ; dans le nom d'un téléchargement, `*` tient la place de n'importe quel texte. |

### L'année

Les pages suivent **une année civile** : les NC créées cette année-là, son plan de production, ses objectifs. L'année est
une ligne de `1_parametres.csv` :

```
annee;2026
```

Tout ce qui dépend de l'année découle de cette ligne, sans rien d'autre à changer :

| Quoi | Comment cela suit l'année |
|---|---|
| Les NC affichées | Créées du 1er janvier au 31 décembre de l'année (plus les NC du registre GPS et de la liste Test datées de cette année) |
| Le volume de production | Les avions du plan de production (les exports déposés dans `data/`), comptés dans les mois et les semaines de l'année |
| L'année de comparaison | L'année d'avant (ou celle écrite dans `annee_comparaison`) : ses NC sont lues dans Skywise à chaque exécution |
| Les livraisons de l'année de comparaison | `0_livraisons_<year>.csv` quand cette table existe (2025), sinon comptées dans le plan de production : un produit est livré le mois de son Départ OTA |
| Les objectifs | Le taux de l'année de comparaison, moins le pourcentage de `objectif_baisse`, multiplié par la production de l'année |
| La cloche | Ses semaines sont les semaines de l'année ; il lui faut 16 semaines de l'année avant de pouvoir comparer |
| Chaque texte des pages | Les deux années et le pourcentage de l'objectif y sont écrits à partir des paramètres |

**Pour commencer une nouvelle année** (chaque mois de janvier) :

1. Dans `1_parametres.csv`, écrivez la nouvelle année sur la ligne `annee`.
2. Déposez un export récent du Tableau Avances / Retards dans `data/`, **à côté des précédents** (ils donnent les livraisons
   de l'année dernière : ne les supprimez jamais).
3. Ajoutez les fermetures de la nouvelle année dans `1_calendrier_production.csv`.
4. Déposez le registre GPS de la nouvelle année dans `data/`. Son nom est écrit dans `2_sources.csv` avec `{annee}` à la
   place de l'année (`GPS NC INT_SERIE ELEC {annee} - NC REGISTRE.csv`), donc le fichier 2027 est trouvé tout seul s'il est
   nommé comme celui de 2026. La liste Test garde son nom.
5. Lancez le notebook. Si une liste manque, ses dernières lignes disent quel fichier il a cherché.

Tant que la ligne n'est pas changée, les pages continuent d'afficher l'année qui y est écrite, complète, et le notebook le
signale à la fin de chaque exécution une fois cette année terminée.

---

## 6. Les tâches courantes

| Je veux... | Table | Ce qu'il faut faire |
|---|---|---|
| Compter un nouveau genre de REC | `2_regle_phase.csv` | Ajoutez le texte du workflow à la `valeur` d'une ligne REC (`-CRE\|-PNC\|-RCX`), ou ajoutez une ligne avant la règle `99`. |
| Chiffrer les pièces rejetées | `1_prix_pieces.csv` | Une ligne par matériel : `materiel;designation;prix_unitaire_eur`. Ce qui reste à chiffrer : `fto2_parts_to_price.csv`, écrit à chaque exécution. |
| Changer un taux horaire | `1_cout_parametres.csv` | Changez la `valeur` de `taux_production`, `taux_qualite` ou `taux_me`. |
| Changer l'objectif | `1_reglages_pages.csv` | `objectif_baisse` : 0.30 pour −30 %. |
| Commencer une nouvelle année | `1_parametres.csv` | `annee` : la nouvelle année ; puis le plan de production, les fermetures et le registre GPS (voir « L'année »). |
| Ajouter un produit | `2_regle_produit.csv`, puis `2_produits_plan.csv` | Une règle qui le reconnaît, puis son nom dans le plan. |
| Mettre à jour le plan de production | un fichier dans `data/` | Téléchargez le Tableau Avances / Retards en CSV et déposez-le dans `data/` à côté des exports précédents. |
| Mettre à jour les demandes de câbles | un fichier dans `data/` | Téléchargez le suivi de l'équipe câbles en CSV et déposez-le dans `data/`. |
| Ajouter une fermeture | `1_calendrier_production.csv` | Début, fin, poids 0 (fermé) ou 0,5 (moitié), motif. |
| Ajouter une action MFT | `1_actions_mft.csv` | Une ligne avec son propre `id` (voir plus haut). Elle apparaît sur la page MFT pour tout le monde à la prochaine exécution du notebook. |
| Changer ce que le tableau de bord affiche à l'ouverture | `1_reglages_pages.csv` | `defaut_phase`, `defaut_responsabilite`, `defaut_periode`. |
| Changer la couleur ou l'ordre d'une catégorie | `2_categories.csv` | `couleur` (1 à 9), `ordre`. |
| Renommer un dataset que Skywise nous fournit | `2_sources.csv` | Le nouveau nom dans `valeur`. |

---

## 7. Comment le code lit les tables

Rien n'est recopié d'une table dans le code : le notebook lit toutes les tables **à chaque exécution**. C'est pourquoi un
changement ne demande qu'une nouvelle exécution.

**Qui lit quoi.** `lisez_moi.csv`, colonne `lu_par`, donne le fichier de code qui lit chaque table. En bref :

| Tables | Lues par (dans `notebook_kit/fto2/`) | Ce qu'elles deviennent |
|---|---|---|
| `2_regle_*.csv` (les règles) | `selection.py`, `core.py`, `parser/fto2_logic.py`, via `rules.py` | Appliquées à chaque NC pour lui donner une étiquette (phase, ligne, produit, type, périmètre...) |
| `1_cout_parametres.csv`, `2_cout_*.csv`, `3_cout_*.csv` (le coût) | `cost/params.py` | Transformées en paramètres du modèle de coût, utilisés par `cost/model.py` |
| `1_parametres.csv`, `2_parametres.csv`, `2_sources.csv` | `skywise.py`, `config.py`, `manual_lists.py`, `downloads.py` | Quelle usine, quelle année (`config.year`, `config.comparison_year`), quels datasets et quels fichiers lire |
| `1_prix_pieces.csv` (prix des pièces) | `cost/parts.py` | Le matériel de chaque NC (lu dans les données NC) reçoit son prix unitaire ; le modèle de coût ajoute prix × quantité pour les décisions qui prennent en compte la pièce |
| les téléchargements déposés dans `data/` (exports du plan de production, suivi câbles) avec `0_plan_msn.csv`, `0_demandes_cables.csv`, `2_cables_origines.csv`, `2_regle_cause_cable.csv` | `downloads.py` | Transformés en plan de production et en demandes de câbles |
| les autres tables `0_` et `1_` (livraisons, fermetures, actions MFT) et les paramètres des pages (`1_reglages_pages.csv`, `2_reglages_pages.csv`, `2_categories.csv`, `2_lignes.csv`, `3_alarmes.csv`) | `reference.py` | Regroupés avec le plan et les demandes dans la table `fto2_dash_ref`, que les pages lisent |
| catégories, causes, sous-codes | `reference.py`, `core.py`, `parser/fto2_logic.py` | Noms et définitions affichés sur les pages, sous-codes officiels des lignes de défaut |

Les pages ne lisent donc jamais `data/config/` elles-mêmes : elles reçoivent les paramètres dont elles ont besoin par
`fto2_dash_ref`, réécrite à chaque exécution.

**Les vérifications avant tout calcul** (`notebook_kit/fto2/config.py`) :

- la table existe et n'est pas vide ;
- chaque ligne a autant de colonnes séparées par `;` que la première ligne (« line N has X columns, the header has Y ») ;
- les colonnes qu'une table doit avoir sont toutes là (« the column(s) X are missing ») ;
- un paramètre nom-valeur que le code demande existe (« the line 'X' is missing »), et ne se trouve que dans une seule partie ;
- les paramètres `oui` / `non` contiennent `oui` ou `non` ;
- les valeurs de la personne responsable sont du bon type : une année a quatre chiffres, une part est entre 0 et 1 (ou un
  pourcentage), un filtre à l'ouverture est l'un de ses choix, un taux n'est pas négatif, une action MFT a son propre id, un
  `niveau` connu et des dates lisibles. Chaque message nomme la table, la ligne et ce qu'il faut écrire.

**Un dossier de paramètres créé avant novembre 2026** contient certaines tables sous leur ancien nom (`1_plan_msn.csv`,
`2_cout_parametres.csv`...) et les lignes de la personne responsable dans `2_parametres.csv` et `2_reglages_pages.csv`. Il
fonctionne toujours : une table qui n'est pas trouvée sous son nom est prise sous son ancien nom (`config.path`).

**Les vérifications d'une table de règles** (`notebook_kit/fto2/rules.py`, fonction `check`) : `ordre` est un nombre, le test
fait partie de la liste et a une valeur quand il en a besoin, la colonne existe dans les données NC, une expression régulière
est valide, `resultat` n'est pas vide, et il y a une règle par défaut (`toujours`). Chaque problème
est signalé avec le fichier et la ligne, en clair.

**Comment une table de règles est appliquée** (`rules.py`, fonction `apply`) : pour chaque NC, les règles sont essayées selon
`ordre` ; les lignes d'une même règle sont combinées (toutes doivent être vraies) ; la première règle vérifiée donne le
résultat ; la règle `toujours` donne la valeur par défaut. La même fonction sert pour toutes les tables de règles, donc elles
se comportent toutes de la même façon.

**Les paramètres à plusieurs valeurs** (`FTO2|FT02`, `7=0.6|8=0.6`) sont découpés sur `|` par `config.parameter_list` ; les
tables de coût et `1_prix_pieces.csv` acceptent une virgule ou un point pour les décimales (`cost/params.py`, `cost/parts.py`).

**Les prix des pièces** (`cost/parts.py`) sont vérifiés aussi : un prix qui n'est pas un nombre arrête l'exécution avec
« 1_prix_pieces.csv: '…' is not a price (line N) », et une liste sans colonne de matériel ou de prix reconnaissable dit
quelles colonnes elle a trouvées. Sans la table, aucune pièce n'a de prix. Le guide complet de cette table : `part_prices.md`.
