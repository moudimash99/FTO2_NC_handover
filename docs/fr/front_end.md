# Front end : comment fonctionne le code des pages

Le front end, ce sont trois pages, chacune une application Slate à part : le **tableau de bord**, la **page MFT** et la
**Saisie structurée de NC**. Le tableau de bord et la page MFT lisent les tables que la mise à jour écrit, puis filtrent,
additionnent et dessinent. La Saisie structurée de NC aide à rédiger une NC selon le standard et l’enregistre. Ce guide
explique leur code.

Les trois guides du code : *Les réglages, table par table* (les paramètres), *La mise à jour, étape par étape* (le code de la
mise à jour) et *Les pages, en détail* (celui-ci). Le prix des pièces a son propre guide : *Le prix des pièces*.

**Sommaire**

1. [La vue d’ensemble](#1-la-vue-densemble)
2. [Comment les données arrivent dans une page](#2-comment-les-données-arrivent-dans-une-page)
3. [Le code du tableau de bord](#3-le-code-du-tableau-de-bord)
4. [Trouver et modifier un graphique](#4-trouver-et-modifier-un-graphique)
5. [Les alarmes (la cloche)](#5-les-alarmes-la-cloche)
6. [Le code de la page MFT](#6-le-code-de-la-page-mft)
7. [Le code de la Saisie structurée de NC](#7-le-code-de-la-saisie-structurée-de-nc)
8. [Modifier une page dans Slate](#8-modifier-une-page-dans-slate)
9. [Quand une page affiche un encadré](#9-quand-une-page-affiche-un-encadré)

---

## 1. La vue d’ensemble

```
 Postgres (synced from the update's tables)
        |
 Slate queries: q_fto2_nc, q_fto2_def, q_fto2_dis, q_fto2_ref
        |
 the sandbox's state box: links each query to a name the page knows
        |
 the page's code (JS): waits for the data, turns it into lists, then
     filters  ->  adds up  ->  draws (SVG charts, tables)
```

Chaque page est une application Slate avec un seul **code sandbox**, en quatre parties :

| Partie | Ce qu’elle contient |
|---|---|
| CSS | l’apparence : couleurs, tailles, espacements |
| HTML | le cadre : en-tête, barre de filtres, onglets, un emplacement vide par graphique |
| JS | le code : du JavaScript simple, sans bibliothèque extérieure |
| State | les liens vers les requêtes, par exemple `{"nc": "{{q_fto2_nc}}", ...}` |

Modifier une page, c’est modifier son JS (ou son CSS, son HTML) dans le sandbox de son application Slate (section 8). Les
fonctions et les variables nommées dans ce guide sont celles du JS de la page : cherchez-les là.

**Le partage des rôles :** la mise à jour décide et calcule (quelle NC compte, ce qu’est chaque défaut, ce qu’il coûte ; voir
*La mise à jour, étape par étape*). Les pages ne font que filtrer, additionner et dessiner. Un chiffre faux partout est une
question de mise à jour ; un chiffre faux sur un seul graphique est une question de page.

## 2. Comment les données arrivent dans une page

1. **Les requêtes** lisent les quatre tables dans Postgres (schéma `foundry_sync`). Leur SQL ne fait que lister les colonnes.
2. **Le champ State** donne un nom au résultat de chaque requête : `nc` (une ligne par NC), `def` (une ligne par ligne de
   défaut), `dis` (les aléas sans NC, tableau de bord seulement), `ref` (les données de référence).
3. **Le chargeur**, tout à la fin du JS, surveille ces quatre noms. Quand tous sont arrivés, il démarre la page. Si l’un d’eux
   manque trop longtemps, il affiche un encadré qui dit lequel (section 9).
4. **Les données de référence** arrivent en morceaux de texte (`partie`, `morceau`, `texte`). `fto2RefBlocks`, en haut du JS,
   recolle les morceaux de chaque partie et les lit comme un seul bloc : le plan de production, l’année de comparaison, les
   demandes de câbles, les actions MFT, les paramètres du coût, l’arbre des causes et les paramètres des pages (objectif,
   filtres à l’ouverture, couleurs, paramètres des alarmes, le poids de travail de chaque semaine).
5. **L’adaptateur** `fto2FromTables` (entre `ADAPTER START` et `ADAPTER END`) transforme les deux tables en données de la
   page, `D`. Les tables contiennent deux années, l’année de comparaison et l’année suivie : le tableau de bord garde l’année
   suivie (l’adaptateur laisse le reste), la page MFT garde les deux.
6. **Deux clés facultatives.** `reglages`, la requête `q_fto2_set_targets` (la feuille Fusion « Target and pages »), sur le
   tableau de bord et la page MFT : `fto2Reglages`, vers le haut du JS, écrit ses lignes dans les paramètres de la page avant
   qu’elle démarre (la baisse visée par l’objectif, les filtres à l’ouverture, l’objectif d’une action MFT), donc un
   changement dans la feuille apparaît à l’ouverture suivante, sans attendre la mise à jour. Une ligne absente ou mal écrite
   garde la valeur de la mise à jour ; la console du navigateur dit laquelle. `store`, sur la page MFT seulement : section 6.
   Sans ces clés dans le champ State, les pages marchent comme avant.

**Les données dans la page.** `D.ncs` est une liste de NC, chacune étant une liste de valeurs par position :

| | | | |
|---|---|---|---|
| `[0]` numéro de NC | `[1]` date de création | `[2]` semaine | `[3]` ligne |
| `[5]` 1 si FTO2 est responsable | `[6]` décision de coût | `[8]` lieu de détection | `[12]` coût |
| `[21]` lignes de défaut | `[22]` titre | `[23]` serie / client / autre | `[24]` phase |
| `[25]` MSN | `[26]` produit | `[27]` poste | `[29]` jours pour clôturer |
| `[30]` ouverte | `[33]` type de NC | `[39]` source des données | `[40]` étapes du coût (minutes...) |
| `[41]` origine | `[42]` usine | | |

`D.defects` est une liste de lignes de défaut : `[0]` numéro de NC, `[1]` numéro de ligne, `[11]` catégorie, `[12]` cause,
`[13]` sous-catégorie, `[14]` mineur, `[15]` câble, `[17]` part du coût, `[18]` texte, `[22]` sous-code, `[23]` FIN.

La liste complète, position par position, est dans `fto2FromTables`, à côté de la colonne de la table d’où vient chaque
valeur.

## 3. Le code du tableau de bord

### L’organisation de son JS

Cherchez ces repères pour vous y retrouver, de haut en bas :

| Repère | Ce qu’on y trouve |
|---|---|
| `fto2RefBlocks` | recolle les données de référence |
| `ADAPTER START` … `ADAPTER END` | `fto2FromTables` : les tables deviennent `D` |
| `function main()` | la page elle-même commence ici |
| `var STR = {` | tous les textes de la page, en français (`fr`) et en anglais (`en`) |
| `MODEL START` … `MODEL END` | les calculs, sans dessin (voir plus bas) |
| `the calculations: here, or in Slate` | de petites fonctions que les graphiques appellent pour les objectifs, les alarmes et l’explication du coût ; la page les calcule elle-même |
| `// ---- 1. Overview`, `2. Pareto`, `4. Cost`... | une section par onglet, avec les graphiques de cet onglet |
| `5. Insights`, `6. Chart texts`, `7. NC rates` | les graphiques que plusieurs onglets partagent : les graphiques `a:`, les textes des graphiques et les fonctions de dessin, les graphiques numérotés |
| `Drawing a chart by its key` | `rvDraw` : dessine un graphique `a:` ou un graphique numéroté à partir de sa clé |
| `ALARM ENGINE START` … `END` | les statistiques des alarmes (section 5) |
| `Dashboard v2 (main page)` | quels graphiques apparaissent sur quel onglet, et leurs fonctions de dessin (section 4) |
| `filter bar` | les filtres et ce qui se passe quand ils changent ; le téléchargement CSV (`csvOf`) |
| `language, tabs, minor switch` | le choix de la langue, les onglets, `renderAll` |
| `Simple mode` | le mode Essentiel (Synthèse et Détail) |
| la fin du fichier | le chargeur (section 2) et l’encadré d’erreur |

### Les calculs (`MODEL START` … `MODEL END`)

La partie de la page qui calcule sans dessiner, en huit sections numérotées :

1. **helpers** : lire une ligne de défaut ou une NC, regrouper les types de NC, les catégories (`CAT_ORDER`, tiré des
   paramètres) ;
2. **selection** : les filtres (`GF`) et `select()`, qui fait les listes de NC à l’écran ;
3. **production** : le plan de production associé aux NC sélectionnées : les MSN produits par produit et par mois (`pData`,
   `pAgg`) ;
4. **targets and forecast** : l’année de comparaison avec les mêmes filtres (`y25Sel`), l’objectif ligne par ligne
   (`v2Tgt`), la prévision jusqu’à décembre (`v2Series`, `v2Fc`) ;
5. **cost explanation** : les minutes et les euros de chaque étape d’une NC, pour « Expliquer le calcul » ;
6. **alarms** : ce que la cloche suit (`alCompute`) ;
7. et 8. les mêmes résultats regroupés sous forme de simples données (utilisés seulement par une configuration Slate
   facultative).

### L’année

La page ne contient aucune année à elle. Les deux années arrivent avec les paramètres (`SET.annee`, l’année suivie, et
`SET.annee_ref`, l’année avec laquelle elle est comparée), et sont gardées en haut de `main()` sous forme de deux textes,
`YEAR` et `PREV`.

- **Dans le code**, un graphique qui nomme une année utilise `YEAR` ou `PREV`.
- **Dans les textes** (`STR`, `GX`, `GSTR`), les années sont écrites `{YEAR}` et `{PREV}`, et le pourcentage de l’objectif
  `{CUT}` (tiré de `objectif_baisse`). `withYears(...)`, placé autour de chaque table de textes, y écrit une fois les vraies
  valeurs. Un nouveau texte qui nomme une année : écrivez `{YEAR}` ou `{PREV}`, dans une table que `withYears` entoure.
- **Les noms** `y25`, `r25`, `v26`... datent de la première année suivie (2026, comparée à 2025) : lisez « 25 » comme l’année
  de comparaison et « 26 » comme l’année suivie. `D.y25` est le bloc de l’année de comparaison, quelle que soit l’année.
- **Le moteur d’alarmes** lit l’année dans `window.FTO2_YEAR`, que la page renseigne juste avant lui : sa semaine 0 est la
  semaine ISO 1 de l’année suivie, et une date en dehors de cette année n’a pas de semaine (-1).
- **Le nom de la prévision** (« Prévision (oct. à déc.) ») est construit par `fcLeg` à partir des mois que la prévision
  couvre vraiment.
- **Le calendrier :** une semaine sous `semaine_faible_moins_de` d’une semaine normale est une semaine de fermeture, laissée
  de côté dans les moyennes (`calW`) ; le mois en cours compte la part de son temps de travail écoulée (`dayShare`), pas celle
  de ses jours de calendrier.

Une nouvelle année ne demande donc aucun changement dans les pages : la mise à jour envoie la nouvelle année, et tout ce qui
précède suit.

### Ce qui se passe quand quelqu’un clique

1. **Un filtre change** (la barre de filtres, ou un clic sur un graphique). Les filtres sont gardés dans `GF` : dates
   (`from`, `to`), période (`preset` : depuis le 1er janvier, les 30 derniers jours, le dernier mois complet, les 3, 6 ou 12
   derniers mois, toutes les dates, ou des dates choisies), ligne, phase, cases Responsabilité (`liab`), interrupteur de
   l’usine (`fto2`), source des données (`src` : une seule liste, « Source des données » : toutes les données, Skywise
   seulement, registre GPS, liste Test), mode de coût, et une valeur cliquée (`pick`).
2. `setGF` enregistre le changement et appelle `select()`, qui fait les listes de NC à l’écran :
   - `SEL_NC` : toutes les NC que les filtres gardent ;
   - `SER_NC` : les NC propres à FTO2, sans les retours clients ;
   - `CLI_NC` : les retours clients.
3. `renderAll()` redessine tous les onglets. Chaque graphique compte à partir de ces listes, donc chaque graphique suit les
   filtres.

**Un clic sur un graphique** passe par `data-pick="kind|value"` sur l’élément dessiné (`pk()` l’écrit). La page attrape le
clic (`pickSet`), renseigne `GF.pick`, et tous les onglets suivent. Une pastille dans la barre de filtres l’affiche ;
✕ l’enlève.

**Une infobulle** passe par `data-tip="title|line|line"` sur l’élément dessiné (`tip()` l’écrit).

**Un changement d’onglet** (`setTab`) affiche l’onglet et dessine ce dont cet onglet a besoin.

**Le panneau ⓘ** (« Comment la sélection est faite », section `the ⓘ panel`) rejoue les mêmes filtres un par un et dit ce que
chacun enlève.

### Les téléchargements : CSV et images

- **CSV :** en bas de chaque onglet, les NC de la sélection se téléchargent en fichier CSV, en extrait court ou complet
  (`csvOf` : ses deux listes de colonnes, les plus utiles d’abord).
- **Image :** chaque carte de graphique a un bouton **⤓ Image** qui enregistre le graphique en image PNG (`pngBtn`,
  `pngOf`) ; une carte sans graphique dessiné (un tableau) le cache.

### Les textes et les langues

Tous les textes sont dans `STR` : `STR.fr` et `STR.en`, par clé. Le code utilise `S('key')`, avec des valeurs insérées là où
`{n}`, `{v}`... apparaissent. Le HTML utilise `data-t="key"`, rempli par `applyText()`. Les titres des graphiques sont dans
`GSTR` (section 4). Pour changer un texte, changez-le dans les deux langues.

### Essentiel et Deep dive

`MODE` vaut `simple` (Essentiel) ou `expert` (Deep dive). Essentiel affiche deux onglets (Synthèse, Détail) faits de
graphiques repris des onglets de Deep dive (`V2L.syn`, `V2L.det`). Les graphiques de Détail vont de janvier à la fin de la
période (`ytd`).

## 4. Trouver et modifier un graphique

### Où chaque graphique est placé

Dans la section `Dashboard v2 (main page)`, **`V2L`** liste les cartes de graphiques de chaque onglet, par clé :

```
ov:     top: ['VT', 'VN', 'VB', 'a:lead', 'VX'], fold: ['a:cal']
pareto: top: ['a:bump', '78', 'a:flow', 'a:bub', '53', '76', 'VM', 'VQ', 'a:cmo'] ...
where:  top: ['VP', '61', 'a:prod', '54', 'a:msn', 'VF', 'a:station'] ...
```

`top` est affiché, `fold` est dans le repli « plus ». Déplacez une clé pour déplacer un graphique ; supprimez-la pour cacher
le graphique.

### Quel code dessine un graphique

Il y a trois sortes de clés :

| Clé | Dessiné par | Titre tiré de |
|---|---|---|
| `VT`, `VN`, `VB`... | la fonction nommée dans `V2F` (par exemple `VT: v2Target`, `VN: v2Trend`) | `GSTR.VT.fr` / `.en` : [nom court, titre, sous-titre, données utilisées] |
| un nombre (`53`, `78`...) | la fonction donnée pour ce nombre dans `PSPEC` | `GSTR['53']` |
| `a:name` (`a:lead`, `a:bump`...) | `RV_ANA.name` | `STR` : `k_name`, `t_name`, `s_name` |

Les cartes des graphiques numérotés et des graphiques `a:` sont d’abord créées dans deux zones du HTML qui ne sont jamais
affichées (`#pg2` et `#ag`) ; `v2Build` place ensuite chacune dans son onglet.

**Pour trouver le code d’un graphique à partir de la page :** prenez quelques mots de son titre et cherchez-les dans le JS :
ils mènent à son entrée dans `GSTR` ou `STR`, dont la clé mène à sa fonction.

### Trois graphiques de l’onglet Pareto

- **« Classement mensuel des causes »** (`a:bump`) : le rang de chacune des 8 premières causes, mois par mois. Un clic sur une
  courbe suit cette cause.
- **La cause suivie par MSN, mois par mois** (`78`, par exemple « Inversion par MSN »), à côté du classement : la cause
  cliquée dans le classement, sinon la première cause du dernier mois. Ses deux limites, 2σ et 3σ, sont des droites : le taux
  de la période plus deux et trois fois l’écart habituel de ses valeurs mensuelles (le mois en cours laissé de côté ; pas de
  limites avec moins de trois mois). `pTrend` le dessine.
- **« Les causes mois par mois »** (`a:cmo`, fonction `vCmo`) : une barre par mois, les causes empilées. Un interrupteur
  montre les causes ou les catégories du Pareto ; le − / + de la carte règle combien des premières sont affichées (3 au
  départ), et d’autres peuvent être ajoutées à la main : Déverrouillage et FOD sont ajoutées d’office, pour la sécurité
  (`CMO`). La mesure est celle de l’onglet (défauts ou coût), ou les NC avec l’autre interrupteur de la carte.

### Les fonctions utilitaires de dessin

Une fonction de graphique compte à partir de `SEL_NC` (ou de `D.defects` filtré de la même façon), puis dessine en SVG avec :

| Fonction | Rôle |
|---|---|
| `svg(w, h, inner, label)` | le cadre d’un graphique |
| `tx(x, y, text, class, anchor)` | un texte |
| `tip(title, lines)` | une infobulle sur un élément |
| `pk(kind, value)` | un clic qui filtre le tableau de bord |
| `gSet(key, html, legend)` | place le graphique et sa légende dans sa carte |
| `pEmpty(key)` | « pas de données » dans une carte |
| `num`, `eur`, `pct`, `f1`, `f2` | formats de nombres, dans la langue de la page |
| `lineCol(line)`, `catFill(category)` | la couleur d’une ligne, d’une catégorie (tirée des paramètres) |

**Modifier un graphique :** changez ce qu’il compte ou comment il dessine dans sa fonction ; continuez à lire `SEL_NC` pour
que les filtres s’appliquent ; mettez tout nouveau texte dans `STR` (dans les deux langues).

**Ajouter un graphique :** copiez la fonction d’un graphique semblable sous une nouvelle clé, ajoutez la clé à `V2F` et ses
titres à `GSTR`, puis ajoutez la clé à `V2L` sur l’onglet voulu. Sa carte reçoit le bouton ⤓ Image d’elle-même.

### Des valeurs encore écrites dans le code

Quelques valeurs sont écrites dans le JS du tableau de bord, pas dans un paramètre : `OPS_MSN` (les opérations de
branchement par avion du MIP A350, 5 572, pour les erreurs par million d’opérations), `CONN_LINES` (les lignes dont les
défauts de câble comptent comme des défauts de connecteur : A330, A350) et `CMO` (les causes ajoutées d’office sur « Les
causes mois par mois »). Pour en changer une, changez le JS.

### Les couleurs

Les couleurs sont des variables CSS en haut du CSS (`--ink`, `--s1`, `--up`, `--down`...). Les couleurs des lignes et des
catégories viennent des paramètres (`2_lignes.csv`, `2_categories.csv`). Chaque règle de style commence par `.fto2`, pour
que les styles du tableau de bord restent dans son sandbox : gardez cela pour les nouvelles règles.

## 5. Les alarmes (la cloche)

**Ce qu’elle fait :** ligne par ligne, elle compare les défauts des 4 dernières semaines terminées aux 12 semaines d’avant,
par MSN produit. Elle sonne quand la hausse est trop forte pour être due au hasard : alarme mineure ou majeure. Elle repère
aussi les hausses lentes sur plusieurs mois et les avions qui ont beaucoup plus de NC que d’habitude. Les paramètres
(semaines, seuils, combien sont affichées) viennent de `3_alarmes.csv`.

**Le code :**

| Partie | Où |
|---|---|
| Les statistiques | entre `ALARM ENGINE START` et `ALARM ENGINE END` : `run` (le test), `seen` (une alarme marquée comme vue), `spark` (la petite courbe) |
| Ce qui est suivi | `alCompute` (dans `MODEL`, sa partie sur les alarmes) : tous les défauts, catégories, causes, sous-codes, postes, lieux de détection, produits, demandes de câbles, avions, par ligne |
| La cloche à l’écran | `alRender` (la liste), `alGo` (un clic ouvre le problème), `alText` / `alName` (la formulation) |

**La page MFT a sa propre copie du moteur d’alarmes.** Si vous changez l’une, changez l’autre de la même façon, sinon les deux
pages sonneront différemment.

**En début d’année, la cloche est muette.** Elle compare 4 semaines aux 12 d’avant, à l’intérieur de l’année suivie : tant
que l’année n’a pas 16 semaines terminées (fin avril), elle affiche « Pas encore assez de semaines pour comparer ». C’est
voulu, ce n’est pas une panne.

## 6. Le code de la page MFT

Une ligne à la fois : le Pareto de la semaine, l’analyse et le suivi des actions MFT. Elle garde les deux années, pour qu’une
semaine, un mois ou une action soit comparé aux semaines d’avant, même au passage de la nouvelle année. Comme le tableau de
bord, elle a une liste **Responsabilité** (FTO2, Fournisseurs, Autres), et chaque compte, chaque graphique et la cloche
suivent les groupes cochés. Son JS, de haut en bas :

| Section | Ce qu’on y trouve |
|---|---|
| `the two Slate tables -> the page's data` | son propre adaptateur (plus simple que celui du tableau de bord) |
| `the store` | où sont gardées les actions tapées sur la page sans la clé `store` : **dans ce navigateur seulement** |
| `the shared store` | avec la clé d’état `store` : les actions gardées pour tous (`fto2SharedStore`, plus bas) |
| `data`, `weeks (ISO)`, `state`, `helpers` | les données, les numéros de semaine, ce que l’utilisateur a choisi (ligne, phase, période) |
| `controls` | les boutons de ligne, de phase et de période |
| `tab 1: the week's Pareto` | le Pareto de la semaine comparé aux semaines d’avant |
| `tab 2: analysis` | ce qui monte, ce qui baisse, les FIN récurrents |
| `tab 3: actions` | le suivi des actions : chaque action face à son objectif |
| `the action form` | ajouter ou modifier une action sur la page |
| `the bell` | le moteur d’alarmes (sa propre copie) et sa liste |
| `events` | les clics |
| `Slate: wait for the two queries` | le chargeur |

**D’où viennent les actions :** `1_actions_mft.csv` dans les paramètres, par `ref`. Elles remplacent la copie du navigateur à
chaque chargement. Sans action enregistrée (plus bas), la page part de celles de la table.

**Les actions gardées pour tous** (clé d’état `store`, la requête `q_fto2_mft_store`). Les actions sont gardées dans un objet
du type d’objet de la Saisie structurée de NC, *a30 Nc Writer Dataset* : son Msn vaut `MFT-ACTIONS`, son Texte Sap contient
toute la liste en JSON (`{page, saved_at, actions}`). `fto2SharedStore` a les mêmes appels que le stockage du navigateur,
donc le reste de la page ne change pas. À chaque changement, il met sa propre copie à jour tout de suite, puis met toute la
liste en une ligne dans la clé d’état `store_row` et lance l’événement `save` avec elle, comme la Saisie structurée de NC le
fait pour une NC. Un événement Slate met la ligne dans une variable, et le changement de la variable soumet le widget Action
du type d’objet : un clic sur la page enregistre la liste pour tous. Chaque enregistrement ajoute un objet ; la page prend
celui enregistré en dernier. Les marques « Vu » des alarmes restent dans le navigateur.

**Pas encore réglé : la relecture des enregistrements.** La requête `q_fto2_mft_store` lit la copie Postgres des données du
type d’objet, qui a du retard sur l’Ontologie ; la source HTTP « foundry » de Slate n’a pas atteint l’API qui lit
directement les objets. Tant qu’aucune solution n’est trouvée, une action modifiée sur la page n’est pas gardée : la table
`1_actions_mft.csv` est ce que tout le monde voit, et la cloche du tableau de bord ne connaît que les actions de la table.

**Ses seuils** (« ce qui monte », « ce qui baisse », FIN récurrents : les lignes `mft_`) viennent de `2_reglages_pages.csv`,
les objectifs des actions (les lignes `action_`) de `1_reglages_pages.csv` (la feuille *Target and pages*).

## 7. Le code de la Saisie structurée de NC

Une page à part, qui aide à rédiger une NC selon le standard : la personne choisit le produit et le lieu de détection, puis
chaque défaut dans la grille officielle des codes (nature, objet, sous-code, quantité, localisation), et la page écrit le
texte SAP. Elle ne lit aucune requête. Son JS, de haut en bas :

| Section | Ce qu’on y trouve |
|---|---|
| `CONFIG` | la clé d’état (`submission`) et l’événement (`submit`) qui transmettent la NC à Slate, et le message affiché une fois qu’elle est envoyée |
| `NATURES` | la grille officielle des codes : chaque nature (Q01, Q03... T08) avec ses objets, ses sous-codes, sa gravité et son RPN |
| `PRODUITS`, `DETECTIONS`, `FIN_MAPPING` | les produits, les lieux de détection, les FIN proposés pour chaque nature |
| `CTX_OPTIONS`, `ACT_OPTIONS` | les phrases toutes faites pour le contexte et l’action demandée |
| `buildSapText`, `buildRow` | le texte SAP, et la ligne enregistrée : date, MSN, produit, lieu de détection, nombre de défauts, texte SAP, défauts en JSON |
| `sendToSlate` | le seul endroit qui parle à Slate |

**Enregistrer une NC.** Sur « Soumettre la NC », `sendToSlate` met la NC en une ligne dans la clé d’état `submission` et lance
l’événement `submit` avec elle (l’état du sandbox n’est pas vu par les autres widgets : la NC part avec l’événement). Dans
l’application Slate, cet événement met la ligne dans la variable `v_submission` ; le widget Action du type d’objet *a30 Nc
Writer Dataset* prend ses valeurs dans cette variable (Detection, Produit, Msn, Texte Sap, Total Defauts ; la clé,
Timestamp, est remplie par l’action), et le changement de la variable le soumet. La NC est donc enregistrée en un clic. Pour
changer une liste (un produit, un FIN), changez-la en haut du JS.

## 8. Modifier une page dans Slate

1. Ouvrez l’application Slate de la page en mode édition, puis son code sandbox.
2. **Gardez une copie du JS actuel** (ou du CSS, du HTML) tel quel : c’est votre moyen de revenir en arrière.
3. Faites le changement dans le sandbox. Le JS du tableau de bord est long, et l’éditeur de Slate est lent avec lui : chercher
   le nom de la fonction est le chemin le plus court.
4. Vérifiez la page : les deux langues, Essentiel et Deep dive, quelques filtres, le graphique modifié avec ⤢ **Agrandir**.
   Notez les chiffres clés avant et après : seul ce que vous vouliez changer doit bouger. Vérifiez aussi la page MFT quand le
   changement touche la cloche ou les tables.
5. Si la page casse, recollez la version précédente.

**Trois règles pour le code dans Slate :**

- **Jamais deux `{` à la suite** dans le JS. Slate les lit comme un lien vers une requête et casse le code.
- **Chaque règle CSS commence par `.fto2`**, pour que les styles ne débordent pas sur le reste de la page Slate.
- **Pas de données dans le code.** Les données et les paramètres viennent des requêtes. Une liste ou une valeur que quelqu’un
  peut vouloir changer a sa place dans un paramètre (*Les réglages, table par table*), lu par la mise à jour et passé à la
  page par `ref`.

**Une nouvelle colonne venant de la mise à jour** (*La mise à jour, étape par étape*, section 6) : ajoutez-la au SQL de la
requête dans Slate, lisez-la dans l’adaptateur (`fto2FromTables` : ajoutez-la à la liste de la NC ou de la ligne de défaut),
puis utilisez-la dans un graphique.

## 9. Quand une page affiche un encadré

| L’encadré dit | Ce que cela veut dire | Où regarder |
|---|---|---|
| Toujours en attente d’une requête, avec son nom | La requête n’existe pas sous ce nom, ou elle échoue | Le nom et le SQL de la requête dans Slate |
| « La requête … n’a renvoyé aucune ligne » | La requête fonctionne mais la table est vide | La synchronisation, puis la dernière exécution de la mise à jour |
| « aucune NC lisible … colonnes reçues : … » | La requête renvoie des colonnes que la page n’attend pas | Comparez-les avec les colonnes de la table |
| « exactement N lignes reçues » | Slate a probablement coupé le résultat | Une limite de lignes sur la requête |
| Les actions partagées ne sont pas encore lues (page MFT) | La requête `q_fto2_mft_store` n’a pas répondu | La requête, sa table et le nom de ses colonnes (section 6) |
| Une erreur avec une ligne de code | Le JS contient une erreur | Recollez le JS précédent |
| La partie HTML manque | L’onglet HTML est vide | Collez la partie HTML |

Une page vide sans aucun encadré est en général un problème de droits : la personne peut ouvrir l’application mais pas les
quatre tables.
