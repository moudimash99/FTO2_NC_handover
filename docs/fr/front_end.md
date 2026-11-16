# Front end : comment fonctionne le code des pages

Le front end, ce sont les trois pages de l'application Slate : le **tableau de bord**, la **page MFT** et le
**Tableau Elizabeth**. Elles lisent les tables que le notebook écrit, puis filtrent, additionnent et dessinent. Ce guide
explique leur code.

Les trois guides : `config.md` (les tables de paramètres ; dans le Code Workspace, aussi sous le nom `data/config/README.md`),
`logic.md` (le code du notebook) et `front_end.md` (le code des pages) ; ces deux derniers sont aussi dans `notebook_kit/`.

**Sommaire**

1. [La vue d'ensemble](#1-la-vue-densemble)
2. [Comment les données arrivent dans une page](#2-comment-les-données-arrivent-dans-une-page)
3. [Le code du tableau de bord](#3-le-code-du-tableau-de-bord)
4. [Trouver et modifier un graphique](#4-trouver-et-modifier-un-graphique)
5. [Les alarmes (la cloche)](#5-les-alarmes-la-cloche)
6. [Le code de la page MFT](#6-le-code-de-la-page-mft)
7. [Le code du Tableau Elizabeth](#7-le-code-du-tableau-elizabeth)
8. [Modifier une page dans Slate](#8-modifier-une-page-dans-slate)
9. [Quand une page affiche un encadré](#9-quand-une-page-affiche-un-encadré)

---

## 1. La vue d'ensemble

```
 Postgres (synced from the notebook's tables)
        |
 Slate queries: q_fto2_nc, q_fto2_def, q_fto2_dis, q_fto2_ref
        |
 the sandbox's state box: links each query to a name the page knows
        |
 the page's code (JS): waits for the data, turns it into lists, then
     filters  ->  adds up  ->  draws (SVG charts, tables)
```

Chaque page est un **code sandbox** Slate, en quatre parties :

| Partie | Ce qu'elle contient |
|---|---|
| CSS | l'apparence : couleurs, tailles, espacements |
| HTML | le cadre : en-tête, barre de filtres, onglets, un emplacement vide par graphique |
| JS | le code : du JavaScript simple, sans bibliothèque extérieure |
| State | les liens vers les queries, par exemple `{"nc": "{{q_fto2_nc}}", ...}` |

**Le partage des rôles :** le notebook décide et calcule (quelle NC compte, ce qu'est chaque défaut, ce qu'il coûte ; voir
`logic.md`). Les pages ne font que filtrer, additionner et dessiner. Un chiffre faux partout est une question de notebook ; un
chiffre faux sur un seul graphique est une question de page.

## 2. Comment les données arrivent dans une page

1. **Les queries** lisent les quatre tables dans Postgres (schéma `foundry_sync`). Leur SQL ne fait que lister les colonnes.
2. **Le champ State** donne un nom au résultat de chaque query : `nc` (une ligne par NC), `def` (une ligne par ligne de
   défaut), `dis` (les aléas sans NC, tableau de bord seulement), `ref` (les données de référence).
3. **Le chargeur**, tout à la fin du JS, surveille ces quatre noms. Quand tous sont arrivés, il démarre la page. Si l'un d'eux
   manque trop longtemps, il affiche un encadré qui dit lequel (section 9).
4. **Les données de référence** arrivent en morceaux de texte (`partie`, `morceau`, `texte`). `fto2RefBlocks`, en haut du JS,
   recolle les morceaux de chaque partie et les lit comme un seul bloc : le plan de production, 2025, les demandes de câbles,
   les actions MFT, les paramètres du coût, l'arbre des causes et les paramètres des pages (objectif, filtres à l'ouverture,
   couleurs, paramètres des alarmes).
5. **L'adaptateur** `fto2FromTables` (entre `ADAPTER START` et `ADAPTER END`) transforme les deux tables en données de la
   page, `D`.

**Les données dans la page.** `D.ncs` est une liste de NC, chacune étant une liste de valeurs par position :

| | | | |
|---|---|---|---|
| `[0]` numéro de NC | `[1]` date de création | `[2]` semaine | `[3]` ligne |
| `[5]` 1 si FTO2 est responsable | `[6]` décision de coût | `[8]` lieu de détection | `[12]` coût |
| `[21]` lignes de défaut | `[22]` titre | `[23]` serie / client / autre | `[24]` phase |
| `[25]` MSN | `[26]` produit | `[27]` poste | `[29]` jours pour clôturer |
| `[30]` ouverte | `[33]` type de NC | `[39]` source des données | `[40]` étapes du coût (minutes...) |
| `[41]` origine | `[42]` usine | | |

`D.defects` est une liste de lignes de défaut : `[0]` numéro de NC, `[1]` numéro de ligne, `[11]` catégorie, `[12]` cause,
`[13]` sous-catégorie, `[14]` mineur, `[15]` câble, `[17]` part du coût, `[18]` texte, `[22]` sous-code, `[23]` FIN.

La liste complète, position par position, est dans `fto2FromTables`, à côté de la colonne de la table d'où vient chaque
valeur.

## 3. Le code du tableau de bord

### L'organisation de son JS

Cherchez ces repères pour vous y retrouver, de haut en bas :

| Repère | Ce qu'on y trouve |
|---|---|
| `fto2RefBlocks` | recolle les données de référence |
| `ADAPTER START` … `ADAPTER END` | `fto2FromTables` : les tables deviennent `D` |
| `function main()` | la page elle-même commence ici |
| `var STR = {` | tous les textes de la page, en français (`fr`) et en anglais (`en`) |
| `MODEL START` … `MODEL END` | les calculs, sans dessin (voir plus bas) |
| `the calculations: here, or in Slate` | de petites fonctions que les graphiques appellent pour les objectifs, les alarmes et l'explication du coût ; la page les calcule elle-même |
| `// ---- 1. Overview`, `2. Pareto`, `3. Weekly Pareto`, `4. Cost`... | une section par onglet, avec les graphiques de cet onglet |
| `ALARM ENGINE START` … `END` | les statistiques des alarmes (section 5) |
| `Dashboard v2 (main page)` | quels graphiques apparaissent sur quel onglet, et leurs fonctions de dessin (section 4) |
| `filter bar` | les filtres et ce qui se passe quand ils changent |
| `language, tabs, minor switch` | le choix de la langue, les onglets, `renderAll` |
| `Simple mode` | le mode Essentiel (Synthèse et Détail) |
| la fin du fichier | le chargeur (section 2) et l'encadré d'erreur |

Les sections marquées « local page only », ainsi que Gallery, Review et Mock-up, ne sont pas affichées dans Skywise :
laissez-les.

### Les calculs (`MODEL START` … `MODEL END`)

La partie de la page qui calcule sans dessiner, en huit sections numérotées :

1. **helpers** : lire une ligne de défaut ou une NC, regrouper les types de NC, les catégories (`CAT_ORDER`, tiré des
   paramètres) ;
2. **selection** : les filtres (`GF`) et `select()`, qui fait les listes de NC à l'écran ;
3. **production** : le plan de production associé aux NC sélectionnées : les MSN produits par produit et par mois (`pData`,
   `pAgg`) ;
4. **targets and forecast** : l'année de comparaison avec les mêmes filtres (`y25Sel`), l'objectif ligne par ligne
   (`v2Tgt`), la prévision jusqu'à décembre (`v2Series`, `v2Fc`) ;
5. **cost explanation** : les minutes et les euros de chaque étape d'une NC, pour « Expliquer le calcul » ;
6. **alarms** : ce que la cloche suit (`alCompute`) ;
7. et 8. les mêmes résultats regroupés sous forme de simples données (utilisés seulement par une configuration Slate
   facultative).

### L'année

La page ne contient aucune année à elle. Les deux années arrivent avec les paramètres (`SET.annee`, l'année suivie, et
`SET.annee_ref`, l'année avec laquelle elle est comparée), et sont gardées en haut de `main()` sous forme de deux textes,
`YEAR` et `PREV`.

- **Dans le code**, un graphique qui nomme une année utilise `YEAR` ou `PREV`.
- **Dans les textes** (`STR`, `GX`, `GSTR`), les années sont écrites `{YEAR}` et `{PREV}`, et le pourcentage de l'objectif
  `{CUT}` (tiré de `objectif_baisse`). `withYears(...)`, placé autour de chaque table de textes, y écrit une fois les vraies
  valeurs. Un nouveau texte qui nomme une année : écrivez `{YEAR}` ou `{PREV}`, dans une table que `withYears` entoure.
- **Les noms** `y25`, `r25`, `v26`... datent de la première année suivie (2026, comparée à 2025) : lisez « 25 » comme l'année
  de comparaison et « 26 » comme l'année suivie. `D.y25` est le bloc de l'année de comparaison, quelle que soit l'année.
- **Le moteur d'alarmes** lit l'année dans `window.FTO2_YEAR`, que la page renseigne juste avant lui : sa semaine 0 est la
  semaine ISO 1 de l'année suivie, et une date en dehors de cette année n'a pas de semaine (-1).
- **Le nom de la prévision** (« Prévision (oct. à déc.) ») est construit par `fcLeg` à partir des mois que la prévision
  couvre vraiment.

Une nouvelle année ne demande donc aucun changement dans les pages : le notebook envoie la nouvelle année, et tout ce qui
précède suit.

### Ce qui se passe quand quelqu'un clique

1. **Un filtre change** (la barre de filtres, ou un clic sur un graphique). Les filtres sont gardés dans `GF` : dates
   (`from`, `to`), période (`preset`), ligne, phase, cases Responsabilité (`liab`), interrupteur de l'usine (`fto2`), source
   des données, mode de coût, et une valeur cliquée (`pick`).
2. `setGF` enregistre le changement et appelle `select()`, qui fait les listes de NC à l'écran :
   - `SEL_NC` : toutes les NC que les filtres gardent ;
   - `SER_NC` : les NC propres à FTO2, sans les retours clients ;
   - `CLI_NC` : les retours clients.
3. `renderAll()` redessine tous les onglets. Chaque graphique compte à partir de ces listes, donc chaque graphique suit les
   filtres.

**Un clic sur un graphique** passe par `data-pick="kind|value"` sur l'élément dessiné (`pk()` l'écrit). La page attrape le
clic (`pickSet`), renseigne `GF.pick`, et tous les onglets suivent. Une pastille dans la barre de filtres l'affiche ;
✕ l'enlève.

**Une infobulle** passe par `data-tip="title|line|line"` sur l'élément dessiné (`tip()` l'écrit).

**Un changement d'onglet** (`setTab`) affiche l'onglet et dessine ce dont cet onglet a besoin.

**Le panneau ⓘ** (« Comment la sélection est faite », section `the ⓘ panel`) rejoue les mêmes filtres un par un et dit ce que
chacun enlève.

### Les textes et les langues

Tous les textes sont dans `STR` : `STR.fr` et `STR.en`, par clé. Le code utilise `S('key')`, avec des valeurs insérées là où
`{n}`, `{v}`... apparaissent. Le HTML utilise `data-t="key"`, rempli par `applyText()`. Les titres des graphiques sont dans
`GSTR` (section 4). Pour changer un texte, changez-le dans les deux langues.

### Essentiel et Deep dive

`MODE` vaut `simple` (Essentiel) ou `expert` (Deep dive). Essentiel affiche deux onglets (Synthèse, Détail) faits de
graphiques empruntés aux onglets de Deep dive (`V2L.syn`, `V2L.det`). Les graphiques de Détail vont de janvier à la fin de la
période (`ytd`).

## 4. Trouver et modifier un graphique

### Où chaque graphique est placé

Dans la section `Dashboard v2 (main page)`, **`V2L`** liste les cartes de graphiques de chaque onglet, par clé :

```
ov:     top: ['VT', 'VN', 'VB', 'a:lead', 'VX'], fold: ['a:cal']
pareto: top: ['a:bub', 'a:bump', 'a:flow', '78', '76', 'VM', 'VQ', '53'] ...
where:  top: ['VP', '61', 'a:prod', '54', 'a:msn', 'VF', 'a:station'] ...
```

`top` est affiché, `fold` est dans le repli « plus ». Déplacez une clé pour déplacer un graphique ; supprimez-la pour cacher
le graphique.

### Quel code dessine un graphique

Il y a trois sortes de clés :

| Clé | Dessiné par | Titre tiré de |
|---|---|---|
| `VT`, `VN`, `VB`... | la fonction nommée dans `V2F` (par exemple `VT: v2Target`, `VN: v2Trend`) | `GSTR.VT.fr` / `.en` : [nom court, titre, sous-titre, données utilisées] |
| un nombre (`53`, `78`...) | la fonction donnée pour ce nombre dans `PSPEC` | `GSTR['53']` |
| `a:name` (`a:lead`, `a:bump`...) | `RV_ANA.name` | `STR` : `k_name`, `t_name`, `s_name` |

**Pour trouver le code d'un graphique à partir de la page :** prenez quelques mots de son titre et cherchez-les dans le JS :
ils mènent à son entrée dans `GSTR` ou `STR`, dont la clé mène à sa fonction.

### Les fonctions utilitaires de dessin

Une fonction de graphique compte à partir de `SEL_NC` (ou de `D.defects` filtré de la même façon), puis dessine en SVG avec :

| Fonction | Rôle |
|---|---|
| `svg(w, h, inner, label)` | le cadre d'un graphique |
| `tx(x, y, text, class, anchor)` | un texte |
| `tip(title, lines)` | une infobulle sur un élément |
| `pk(kind, value)` | un clic qui filtre le tableau de bord |
| `gSet(key, html, legend)` | place le graphique et sa légende dans sa carte |
| `pEmpty(key)` | « pas de données » dans une carte |
| `num`, `eur`, `pct`, `f1`, `f2` | formats de nombres, dans la langue de la page |
| `lineCol(line)`, `catTok(category)` | la couleur d'une ligne, d'une catégorie (tirée des paramètres) |

**Modifier un graphique :** changez ce qu'il compte ou comment il dessine dans sa fonction ; continuez à lire `SEL_NC` pour
que les filtres s'appliquent ; mettez tout nouveau texte dans `STR` (dans les deux langues).

**Ajouter un graphique :** copiez la fonction d'un graphique semblable sous une nouvelle clé, ajoutez la clé à `V2F` et ses
titres à `GSTR`, puis ajoutez la clé à `V2L` sur l'onglet voulu.

### Les couleurs

Les couleurs sont des variables CSS en haut du CSS (`--ink`, `--s1`, `--up`, `--down`...). Les couleurs des lignes et des
catégories viennent des paramètres (`2_lignes.csv`, `2_categories.csv`). Chaque règle de style commence par `.fto2`, pour
que les styles du tableau de bord restent dans son sandbox : gardez cela pour les nouvelles règles.

## 5. Les alarmes (la cloche)

**Ce qu'elle fait :** ligne par ligne, elle compare les défauts des 4 dernières semaines terminées aux 12 semaines d'avant,
par MSN produit. Elle sonne quand la hausse est trop forte pour être due au hasard : alarme mineure ou majeure. Elle repère
aussi les hausses lentes sur plusieurs mois et les avions qui ont beaucoup plus de NC que d'habitude. Les paramètres
(semaines, seuils, combien sont affichées) viennent de `3_alarmes.csv`.

**Le code :**

| Partie | Où |
|---|---|
| Les statistiques | entre `ALARM ENGINE START` et `ALARM ENGINE END` : `run` (le test), `seen` (une alarme marquée comme vue), `spark` (la petite courbe) |
| Ce qui est suivi | `alCompute` (dans `MODEL`, section 6) : tous les défauts, catégories, causes, sous-codes, postes, lieux de détection, produits, demandes de câbles, avions, par ligne |
| La cloche à l'écran | `alRender` (la liste), `alGo` (un clic ouvre le problème), `alText` / `alName` (la formulation) |

**La page MFT a sa propre copie du moteur d'alarmes.** Si vous changez l'une, changez l'autre de la même façon, sinon les deux
pages sonneront différemment.

**En début d'année, la cloche est muette.** Elle compare 4 semaines aux 12 d'avant, à l'intérieur de l'année suivie : tant
que l'année n'a pas 16 semaines terminées (fin avril), elle affiche « Pas encore assez de semaines pour comparer ». C'est
voulu, ce n'est pas une panne.

## 6. Le code de la page MFT

Une ligne à la fois : le Pareto de la semaine, l'analyse et le suivi des actions MFT. Son JS, de haut en bas :

| Section | Ce qu'on y trouve |
|---|---|
| `the two Slate tables -> the page's data` | son propre adaptateur (plus simple que celui du tableau de bord) |
| `the store` | où sont gardées les actions tapées sur la page : **dans ce navigateur seulement** |
| `data`, `weeks (ISO)`, `state`, `helpers` | les données, les numéros de semaine, ce que l'utilisateur a choisi (ligne, phase, période) |
| `controls` | les boutons de ligne, de phase et de période |
| `tab 1: the week's Pareto` | le Pareto de la semaine comparé aux semaines d'avant |
| `tab 2: analysis` | ce qui monte, ce qui baisse, les FIN récurrents |
| `tab 3: actions` | le suivi des actions : chaque action face à son objectif |
| `the action form` | ajouter ou modifier une action sur la page |
| `the bell` | le moteur d'alarmes (sa propre copie) et sa liste |
| `events` | les clics |
| `Slate: wait for the two queries` | le chargeur |

**D'où viennent les actions :** `1_actions_mft.csv` dans les paramètres, par `ref`. Elles remplacent la copie du navigateur à
chaque chargement. Une action tapée sur la page reste dans ce navigateur jusqu'à ce que quelqu'un l'ajoute à la table.

**Ses seuils** (« ce qui monte », « ce qui baisse », FIN récurrents : les lignes `mft_`) viennent de `2_reglages_pages.csv`,
les objectifs des actions (les lignes `action_`) de `1_reglages_pages.csv`.

## 7. Le code du Tableau Elizabeth

Les NC d'une ligne, trois familles de problèmes, un Pareto, et les semaines au-dessus d'un seuil (10 NC par semaine par
défaut). Son JS :

| Section | Ce qu'on y trouve |
|---|---|
| `the two tables -> the page's data` | `elzFromTables` : son propre adaptateur |
| `families` | comment une NC est mise dans une famille (les câbles d'abord, puis les autres) ; `cableWhy` dit pourquoi une NC compte comme un problème de câble |
| `weeks (ISO)` | numéros de semaine, semaines de fermeture et semaines basses |
| `state`, `helpers` | ligne, phase, période, seuil ; mémorisés dans le navigateur |
| `render` | le dessin |
| `events` | les clics |
| `start` | le chargeur |

## 8. Modifier une page dans Slate

1. **Copiez le JS actuel** (ou le CSS, le HTML) hors du sandbox et gardez-le tel quel : c'est votre moyen de revenir en
   arrière.
2. Faites le changement dans un éditeur de texte (le JS du tableau de bord est long ; l'éditeur de Slate est lent avec lui),
   puis recollez-le.
3. Vérifiez la page : les deux langues, Essentiel et Deep dive, quelques filtres. Notez les chiffres clés avant et après :
   seul ce que vous vouliez changer doit bouger.
4. Si la page casse, recollez la version précédente.

**Trois règles pour le code dans Slate :**

- **Jamais deux `{` à la suite** dans le JS. Slate les lit comme un lien vers une query et casse le code.
- **Chaque règle CSS commence par `.fto2`**, pour que les styles ne débordent pas sur le reste de la page Slate.
- **Pas de données dans le code.** Les données et les paramètres viennent des queries. Une liste ou une valeur que quelqu'un
  peut vouloir changer a sa place dans une table de paramètres (`config.md`), lue par le notebook et passée à la page par
  `ref`.

**Une nouvelle colonne venant du notebook** (`logic.md`, section 6) : ajoutez-la au SQL de la query dans Slate, lisez-la dans
l'adaptateur (`fto2FromTables` : ajoutez-la à la liste de la NC ou de la ligne de défaut), puis utilisez-la dans un
graphique.

## 9. Quand une page affiche un encadré

| L'encadré dit | Ce que cela veut dire | Où regarder |
|---|---|---|
| Toujours en attente d'une query, avec son nom | La query n'existe pas sous ce nom, ou elle échoue | Le nom et le SQL de la query dans Slate |
| « La requête … n'a renvoyé aucune ligne » | La query fonctionne mais la table est vide | La synchronisation, puis l'exécution du notebook |
| « aucune NC lisible … colonnes reçues : … » | La query renvoie des colonnes que la page n'attend pas | Comparez-les avec les colonnes de la table |
| « exactement N lignes reçues » | Slate a probablement coupé le résultat | Une limite de lignes sur la query |
| Une erreur avec une ligne de code | Le JS contient une erreur | Recollez le JS précédent |
| La partie HTML manque | L'onglet HTML est vide | Collez la partie HTML |
