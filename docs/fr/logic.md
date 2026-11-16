# Logique : comment fonctionne le code du notebook

La logique, c'est tout ce que fait le notebook : il lit les NC dans Skywise, décide lesquelles comptent, lit leurs défauts,
les étiquette, calcule leur coût et écrit les tables que les pages lisent. Ce guide explique ce code.

Les trois guides : `config.md` (les tables de paramètres ; dans le Code Workspace, aussi sous le nom `data/config/README.md`),
`logic.md` (le code du notebook) et `front_end.md` (le code des pages) ; ces deux derniers sont aussi dans `notebook_kit/`.

**Sommaire**

1. [La vue d'ensemble](#1-la-vue-densemble)
2. [Où se trouve le code](#2-où-se-trouve-le-code)
3. [L'exécution, étape par étape](#3-lexécution-étape-par-étape)
4. [Chaque fichier expliqué](#4-chaque-fichier-expliqué)
5. [Les tables qu'il écrit](#5-les-tables-quil-écrit)
6. [Modifier la logique](#6-modifier-la-logique)
7. [Quand le notebook s'arrête](#7-quand-le-notebook-sarrête)

---

## 1. La vue d'ensemble

```
 Skywise datasets                          data/config/ (the settings)
   non_conformity        (the NCs)                 |
   fto2_ai_labels        (the AI labels)           |
   work_order_operation  (rework orders)           |
   mes_disruptions       (aléas)                   |
            \                                      /
             THE NOTEBOOK  ->  notebook_kit/fto2/  (the code)
                                   |
   fto2_dash_nc           one row per NC
   fto2_dash_defects      one row per defect line
   fto2_dash_disruptions  the quality aléas that led to no NC
   fto2_dash_ref          everything else the pages need (production plan, comparison year, settings...)
                                   |
                         synced to Postgres -> read by the Slate pages
```

**Le partage des rôles :** la logique décide et calcule (quelle NC compte, ce qu'est chaque défaut, ce qu'il coûte). Les
pages ne font que filtrer, additionner et dessiner. Donc un chiffre faux sur toutes les vues du tableau de bord est une
question de logique ; un chiffre faux sur un seul graphique est une question de page.

## 2. Où se trouve le code

Dans le Code Workspace :

| Quoi | Où |
|---|---|
| Le notebook | `fto2_pipeline_notebook` : trois cellules courtes. Il ne fait qu'appeler `skywise.run(...)`. |
| Le code | `notebook_kit/fto2/` : du Python simple, un fichier par sujet. |
| Les paramètres | `data/config/` (voir `config.md`). |
| Les fichiers lus en plus des datasets | `data/` : la liste des postes, le registre GPS, la liste Test (noms dans `data/config/2_sources.csv`). |

Les fichiers de `notebook_kit/fto2/` :

| Fichier | En une phrase |
|---|---|
| `skywise.py` | L'exécution : lit les datasets, appelle tout le reste dans l'ordre, écrit les tables. **Commencez la lecture ici.** |
| `config.py` | Lit les tables de paramètres et s'arrête avec un message clair quand l'une d'elles est mal remplie. |
| `rules.py` | Le moteur de règles : applique une table de règles (`2_regle_*.csv`) aux NC. |
| `selection.py` | Quelles NC comptent, et les étiquettes que chaque NC reçoit des tables de règles. |
| `manual_lists.py` | Lit le registre GPS et la liste Test. |
| `parser/` | Le lecteur de défauts : transforme le texte long d'une NC en lignes de défaut. |
| `core.py` | Des NC aux tables du tableau de bord : défauts, étiquettes, ordres de retouche, aléas, coût, périmètre. |
| `cost/` | Le modèle de coût, avec les ordres de retouche, les aléas et les prix des pièces. |
| `reference.py` | Tout ce dont les pages ont besoin en plus des tables de NC (plan de production, année de comparaison, câbles, actions, paramètres). |
| `downloads.py` | Lit les fichiers déposés dans `data/` tels qu'ils ont été téléchargés : les exports du plan de production, le suivi de l'équipe câbles. |

## 3. L'exécution, étape par étape

`skywise.py`, fonction `run`. Le notebook affiche chaque étape pendant son exécution, donc la dernière ligne affichée dit où il
en est.

**A. La sélection standard** (`select_ncs`, puis `selection.apply_rules`)

1. Lit les NC de l'usine créées pendant l'année suivie (`2_parametres.csv` : `usine` ; `1_parametres.csv` : `annee`), plus les
   NC d'autres usines pour lesquelles l'usine est responsable. On demande à Skywise les NC créées à partir du 1er janvier
   (`config.first_day`) ; les NC créées après le 31 décembre sont retirées en Python (`skywise._until`), parce que le filtre
   de Skywise échoue sur trois conditions reliées par `&`.
2. Laisse de côté les NC exclues (`2_regle_exclusion.csv` : ERMA, NC supprimées dans une autre usine).
3. Ajoute les étiquettes tirées des tables de règles, dans cet ordre : phase (`2_regle_phase.csv`), libellé de la décision
   (`2_decisions.csv`), origine (`2_regle_origine.csv`), type (`2_regle_type_nc.csv`, qui utilise l'origine), produit
   (`2_regle_produit.csv`).

**B. Les listes manuelles** (`manual_lists.py`) : les NC du registre GPS et de la liste Test que l'étape A n'a pas trouvées
sont récupérées par leur numéro, puis passent par les mêmes règles.

**C. Les anciennes sorties** : tant que `garder_anciennes_sorties` vaut `oui`, les quatre tables de l'ancienne application
Slate sont écrites comme avant.

**D. Les tables du tableau de bord** (`core.build`, qui appelle `core.prepare` puis `core.tables`) :

1. **Défauts :** le lecteur de défauts découpe le texte long de chaque NC en lignes de défaut (`parser/`). Les NC A400M n'ont
   pas de texte long : une ligne est faite à partir du titre (`core.title_lines`, `3_a400m_titres.csv`).
2. **Ordres de retouche :** les ordres de retouche de la NC, leur état et leur temps prévu (`cost/orders.py`).
3. **Aléas :** l'aléa qualité qui a conduit à chaque NC et son temps déclaré, et les aléas qui n'ont conduit à aucune NC
   (`cost/disruptions.py`).
4. **Étiquettes :** chaque ligne de défaut prend son étiquette IA dans `fto2_ai_labels`, **seulement si le texte de la ligne
   est toujours le même qu'au moment où elle a été étiquetée**. Sinon, elle garde l'étiquette du lecteur de défauts et elle
   est listée « à étiqueter ». Ensuite, la catégorie, la cause, l'indicateur « mineur » et le sous-code officiel découlent de
   l'étiquette.
5. **Prix des pièces :** les données NC donnent la pièce concernée par chaque NC (colonne `material`) ; son prix vient de
   `1_prix_pieces.csv` (`cost/parts.py`). Les matériels encore sans prix sont écrits dans `fto2_parts_to_price.csv`.
6. **Coût :** le modèle de coût est appliqué à chaque NC (`cost/model.py`, section 4).
7. **Périmètre :** où chaque NC a été émise : `serie`, `client` (retour client), `autre` (`2_regle_perimetre.csv`).
8. **Tables :** `core.tables` met le tout dans les deux tables, colonne par colonne, et `core.dis_table` fait la table des
   aléas.
9. **Lignes à étiqueter :** `core.lines_to_label` écrit `fto2_lines_to_label.csv` à côté du notebook : les lignes sans
   étiquette IA utilisable, avec leur texte complet, prêtes pour la prochaine passe d'étiquetage.

**E. Les données de référence** (`reference.py`) : le plan de production, l'année de comparaison (l'année qui précède l'année
suivie, sauf si `annee_comparaison` en désigne une autre : ses NC sont lues dans Skywise, à partir du 1er janvier et
arrêtées à la fin de l'année comme à l'étape A ; elles passent par les mêmes règles, le même lecteur de défauts, les mêmes
prix des pièces et le même modèle de coût, puis sont additionnées par mois), les demandes de câbles, les actions MFT, les
paramètres du coût, l'arbre des causes et les paramètres des pages. Elles sont regroupées dans `fto2_dash_ref`
(section 5).

**L'année.** Toutes les dates de l'exécution viennent d'une seule ligne, `annee` dans `1_parametres.csv`, par cinq fonctions
de `config.py` : `year()`, `comparison_year()`, `first_day()` (le 1er janvier), `year_end()` (le 1er janvier de l'année
suivante) et `aleas_since()` (le 1er décembre de l'année d'avant : une NC de début janvier peut suivre un aléa de fin
décembre). Aucune année n'est écrite dans le code : `tests/test_config.py` échoue s'il y en a une. Quand l'année suivie est
terminée, les dernières lignes de l'exécution le disent et donnent la ligne à changer.

## 4. Chaque fichier expliqué

### `config.py` : la lecture des paramètres

- `table(name, columns)` : une table de paramètres sous forme de texte, après avoir vérifié qu'elle existe, que chaque ligne
  a le bon nombre de colonnes et que les colonnes attendues sont là.
- `parameter(name, table)` : une valeur d'une table nom-valeur (`2_parametres.csv` par défaut). `parameter_list` la découpe
  sur `|` ; `parameter_yes` lit `oui` / `non` ; `optional` donne `''` pour une ligne vide ou absente.
- Deux de ces tables sont en deux parties (`SPLIT`) : les lignes de la personne responsable sont dans `1_parametres.csv` et
  `1_reglages_pages.csv`, les lignes techniques dans la table `2_` du même nom. `parameter` cherche dans les deux ; `held_by`
  dit quelle partie contient une ligne, pour qu'une erreur nomme le bon fichier.
- `path(name)` : où se trouve une table. Un dossier de paramètres créé avant le regroupement des tables en contient certaines
  sous leur ancien nom : une table introuvable sous son nom est prise sous son ancien nom (`FORMER`).
- `year`, `comparison_year`, `first_day`, `year_end`, `aleas_since` : l'année suivie et les dates qui en dépendent.
- `number`, `day` : un nombre ou une date tels qu'une personne les tape dans Excel (`0,25` ; `31/01/2026`).
- `rule_table(name, columns)` : une table de règles, vérifiée par `rules.check`.
- `mapping(name, key, value)` : une table à deux colonnes utilisée comme table de correspondance, avec sa ligne `(autre)`
  comme valeur par défaut.
- `folder()` : où sont les paramètres (`data/config/` dans le Code Workspace).

### `rules.py` : le moteur de règles

Une seule fonction applique toutes les tables de règles, donc elles se comportent toutes de la même façon (cette façon est
expliquée dans `config.md`, section 4.3).

- `check(table, name, columns)` : liste chaque problème en clair (un test inconnu, une règle par défaut manquante, une
  expression régulière fausse, une colonne absente des données NC).
- `apply(df, table, name)` : pour chaque NC, essaie les règles selon `ordre` ; les lignes d'une même règle doivent toutes
  être vraies ; la première règle vérifiée donne le résultat ; `toujours` donne la valeur par défaut. Les tests eux-mêmes
  sont dans `_condition`.

### `selection.py` : quelles NC comptent, et leurs étiquettes

- `exclusions(df)` : True pour les NC à laisser de côté.
- `add_columns(df)` : ajoute `Programme_auto` (la phase), `Statut_decision_auto`, `Origin_auto`, `Type_NC_auto` (qui utilise
  l'origine) et `Produit_auto`.
- `apply_rules(raw, station_desc)` : les deux, sur un extrait brut de NC. Elle ajoute aussi la description de chaque poste
  (tirée de la liste des postes), que les règles de produit lisent.

### `manual_lists.py` : le registre GPS et la liste Test

Lit les deux fichiers (`2_sources.csv` dit où ils sont, combien de lignes sauter et quelles colonnes contiennent le numéro de
NC et la date ; `{annee}` dans un nom de fichier tient la place de l'année suivie), garde les NC datées de l'année suivie, et marque chaque NC avec la liste où elle figure (`Ext_Source` :
`GPS`, `Test`, ou aucune).

### `parser/` : le lecteur de défauts

- `nc_defect_parser.py` : lit le texte long d'une NC. Il trouve les défauts qui y sont écrits (listes numérotées, le modèle du
  standard de rédaction, une ligne qui relie deux défauts par « + »), puis donne à chaque défaut une **sous-catégorie** à
  partir des codes officiels écrits dans le texte, ou de mots-clés. Des règles d'expert, avec des priorités (câble d'abord,
  puis branchement, puis contact non verrouillé).
- `fto2_logic.py` : fait le lien entre le lecteur et le reste du code : `build_defects` (une ligne par défaut), `build_nc`
  (une ligne par NC avec ses nombres de défauts), `line_of` (la ligne avion d'un programme, `2_regle_ligne.csv`), et les noms
  des causes (`2_causes_noms.csv`).

### `core.py` : des NC aux tables du tableau de bord

- `prepare` : les étapes D1 à D7 ci-dessus.
- `official_subcode` : le sous-code officiel de chaque ligne de défaut, à partir de son étiquette.
- `title_lines` : les lignes A400M lues dans le titre de la NC.
- `nc_extras` : les champs de NC dont les graphiques ont besoin (MSN, produit, poste, heure de création, jours pour clôturer,
  ouverte ou non, âge, type de NC, responsabilité, codes SAP, source des données, les étapes du coût).
- `customer_return_extras` : les champs de l'onglet Retours clients (type de dommage, moment de la détection, symptôme
  observé).
- `tables` : les deux tables, dans l'ordre de `NC_COLUMNS` et `DEF_COLUMNS` (les listes de colonnes en haut du fichier,
  chaque colonne avec sa signification).
- `lines_to_label` : les lignes de défaut qui ont besoin d'une étiquette IA.
- `liab_cat` : les trois groupes « Responsabilité » (`2_regle_responsabilite.csv`).
- `year_baseline`, `year_causes` : l'année de comparaison passée par les mêmes règles, additionnée par mois.

### `cost/` : le modèle de coût

**En clair :** chaque NC passe par six étapes au plus : l'alerte de l'opérateur, la rédaction de la NC, le support
technique, la préparation du travail, l'intervention et le recontrôle. Chaque étape prend des minutes, payées au taux horaire
de la personne qui la fait (production, qualité ou ME). On ajoute les heures d'ingénierie (design queries), la matière, et le
prix d'une pièce rejetée, rebutée ou échangée. La décision (retouche, rebut, design query...) dit quelles étapes sont
comptées, et si la pièce compte.

`model.py`, fonction `compute_cnq`, dans cet ordre :

1. **Chaque ligne de défaut :** minutes et matière selon son type de défaut (`3_cout_temps_defauts.csv`) ; pour les erreurs
   de branchement, seule la première de la NC prend le temps complet, chacune des suivantes moins
   (`minutes_branchement_suivant`).
2. **Chaque NC, ses minutes par étape :** alerte (ou le temps déclaré de l'aléa à l'origine de la NC), rédaction (plus longue
   au contrôle final), support, intervention (la somme de ses lignes, multipliée par un facteur pour les NC internes),
   préparation (sans jamais laisser le travail descendre sous le minimum), recontrôle, heures d'ingénierie. Quand la NC a un
   ordre de retouche clos avec un temps prévu, ce temps prévu remplace les minutes de préparation et d'intervention du
   modèle, et les minutes de logistique (`minutes_logistique`) sont ajoutées à la préparation quand une pièce doit être
   approvisionnée (la NC indique un matériel).
3. **Euros :** les minutes de chaque étape à son taux, plus l'ingénierie, la matière et la valeur de la pièce (le prix de la
   pièce, tiré de `1_prix_pieces.csv`, pour les décisions qui la prennent en compte).
4. **Retours clients :** un supplément forfaitaire, ou le montant réel quand il est connu.
5. **Deux niveaux de comparaison :** « global » (des temps moyens pour toutes les NC) et « Standard Airbus » (le coût officiel
   par décision).
6. **Retour aux lignes :** chaque ligne reçoit sa part du coût de la NC (son propre travail et sa matière, plus une part égale
   du reste).

Les autres fichiers :

| Fichier | Ce qu'il fait |
|---|---|
| `params.py` | Transforme les tables de coût de `data/config/` en paramètres du modèle |
| `orders.py` | Lit les opérations des ordres de retouche et leur temps prévu ; donne un état aux ordres de chaque NC (used, open, no_time, not_found) |
| `disruptions.py` | Relie les aléas aux NC (même ordre de travail, de 2 h avant à 72 h après) et construit le bloc des aléas sans NC |
| `parts.py` | La valeur de la pièce : `part_values` donne à chaque NC le prix unitaire de son matériel (`1_prix_pieces.csv`, retrouvé par le numéro de matériel sans les zéros de tête) × sa quantité ; `to_price` liste les matériels qui attendent encore un prix. Guide : `part_prices.md` |
| `explain.py` | Écrit l'explication du coût de chaque NC sous forme de table (seulement pour une configuration Slate facultative, non utilisée) |

Le modèle est appliqué deux fois : une fois sur les étiquettes IA (les chiffres du tableau de bord) et une fois sur les étiquettes
propres au lecteur de défauts (gardées pour comparaison).

### `reference.py` : ce dont les pages ont besoin en plus des tables de NC

| Fonction | Donne aux pages |
|---|---|
| `eqmsn`, `working_day_volume`, `production_msn` | Le plan de production : les MSN produits par produit et par mois de l'année suivie (comptés sur les jours travaillés, `1_calendrier_production.csv`), et les dates de production de chaque avion |
| `weekly_volume` | Les MSN produits par ligne et par semaine de l'année : le dénominateur des alarmes |
| `comparison_year` | L'année de comparaison, additionnée par mois, ligne, produit. Les pages connaissent ce bloc sous le nom `y25`, son nom depuis la première année suivie (2026, comparée à 2025) |
| `deliveries` | Les produits livrés pendant l'année de comparaison, mois par mois : `0_livraisons_<year>.csv` quand cette table existe, sinon comptés dans le plan de production (un produit est livré le mois de son Départ OTA) |
| `cable_requests` | Les demandes de l'équipe câbles (`downloads.cables` : l'export du suivi déposé dans `data/`, sinon `0_demandes_cables.csv`) |
| `mft_actions`, `mft_actions_page` | Les actions MFT (`1_actions_mft.csv`), chacune reliée à son problème ; `_actions` vérifie d'abord la table (ids, genre de problème, dates) |
| `cnq_explain` | Les paramètres du coût, pour « Expliquer le calcul » |
| `rca_reference` | L'arbre des causes pour l'onglet Définitions, avec des exemples réels |
| `page_settings` | Les paramètres des pages : objectif, filtres à l'ouverture, catégories, couleurs, paramètres des alarmes |
| `dashboard_block`, `mft_block` | Tout ce qui précède, regroupé en paquets par page |
| `ref_table` | Les paquets, découpés en lignes de texte pour `fto2_dash_ref` |

### `downloads.py` : les fichiers déposés tels qu'ils ont été téléchargés

Deux choses arrivent à l'exécution sous forme de fichiers que l'équipe télécharge et dépose dans `data/`, sans table à
remplir (`2_sources.csv` les nomme : `exports_plan`, `suivi_cables`).

| Fonction | Ce qu'elle fait |
|---|---|
| `files`, `file_day` | Les fichiers que nomme une ligne de `2_sources.csv`, du plus ancien au plus récent. Le jour d'un téléchargement est la date à la fin de son nom, sinon le jour où il a été enregistré |
| `plan_of_export` | Un export du Tableau Avances / Retards sous forme de lignes du plan : une par avion et par produit, avec la date prévue et la date réelle de ses 8 jalons ; un MSN affiché `#N/A` est repris des exports plus anciens |
| `merge_plan`, `plan` | Le plan à partir de tous les exports, du plus ancien au plus récent : la ligne la plus récente de chaque avion l'emporte ; un avion livré avant un nouvel export garde sa dernière ligne ; une ligne qui a quitté l'export avant sa livraison est abandonnée. `0_plan_msn.csv` est lu comme un export de plus |
| `cables_of_export`, `cables` | L'export le plus récent du suivi de l'équipe câbles sous forme de lignes de demandes (origine tirée de `2_cables_origines.csv`, cause proposée tirée de `2_regle_cause_cable.csv`) ; sans export, `0_demandes_cables.csv` |
| `report` | Deux lignes pour le journal de l'exécution : quels fichiers ont été lus |

Un fichier qui n'est pas l'export attendu arrête l'exécution avec un message qui dit quel fichier et ce qui était cherché.

## 5. Les tables qu'il écrit

| Table | Une ligne par | Colonnes |
|---|---|---|
| `fto2_dash_nc` | NC | Listées avec leur signification dans `core.py`, `NC_COLUMNS` : numéro, dates, ligne, usine, responsabilité, décision de coût et niveaux, coût par étape, phase, MSN, produit, poste, type de NC, source, ordres de retouche, aléas... |
| `fto2_dash_defects` | ligne de défaut | `core.py`, `DEF_COLUMNS` : NC, numéro de ligne, catégorie, cause, sous-catégorie, mineur, câble, part du coût, quantité, texte, sous-code, FIN, d'où vient l'étiquette (`ai`, `titre`, `parser`) |
| `fto2_dash_disruptions` | aléa qualité sans NC | `core.py`, `DIS_COLUMNS` : numéro, date, ligne, poste, ordre de travail, minutes, compté ou non, motif, statut, commentaire |
| `fto2_dash_ref` | morceau de texte | `partie` (dashboard, mft, elizabeth), `morceau` (0, 1, 2... dans l'ordre), `texte`. Les pages recollent les morceaux d'une partie et les lisent comme un seul bloc de données. Découpée en morceaux parce qu'une cellule ne peut pas tout contenir. |

Sont aussi écrits : `fto2_lines_to_label.csv` (à côté du notebook) et, tant que `garder_anciennes_sorties` vaut `oui`, les
quatre tables de l'ancienne application.

## 6. Modifier la logique

**Vérifiez d'abord que ce n'est pas un paramètre.** La plupart des changements (une règle, un taux, un produit, une date) se
font dans une table de `data/config/`, pas dans le code : voir `config.md`.

**Où changer quoi :**

| Vous voulez changer... | Fichier |
|---|---|
| Quelles NC sont lues dans Skywise | `skywise.py`, `select_ncs` |
| Un nouveau genre d'étiquette sur chaque NC | une table de règles, plus une ligne dans `selection.add_columns` |
| Comment les défauts sont lus dans le texte | `parser/nc_defect_parser.py` (expert) |
| Une nouvelle colonne dans les tables du tableau de bord | `core.py` : ajoutez-la à `NC_COLUMNS` / `DEF_COLUMNS` et remplissez-la dans `tables` ; puis ajoutez-la à la query dans Slate et lisez-la dans la page (`front_end.md`) |
| Comment le coût est calculé | `cost/model.py` |
| Comment une pièce est trouvée et chiffrée | `cost/parts.py` (les prix eux-mêmes : `1_prix_pieces.csv`) |
| Ce que les pages reçoivent en plus des tables | `reference.py` |

**Tester un changement dans le Code Workspace :**

1. Notez les chiffres que le notebook affiche à la fin (nombre de NC, lignes de défaut, coût) et les chiffres clés du tableau
   de bord.
2. Modifiez le code dans `notebook_kit/fto2/` et gardez une copie du fichier tel qu'il était.
3. Redémarrez le kernel du notebook (Python garde l'ancien code en mémoire jusque-là) et lancez toutes les cellules.
4. Comparez : seul ce que vous vouliez changer doit bouger.

## 7. Quand le notebook s'arrête

| Le message | Ce qu'il veut dire | Que faire |
|---|---|---|
| Nomme un fichier de `data/config/` et une ligne | Une table de paramètres est mal remplie | Corrigez cette ligne (`config.md`, section 1) |
| « settings table … not found » | Une table a été renommée, déplacée ou supprimée | Remettez-la dans `data/config/` |
| Un nom de dataset introuvable | Le dataset n'est pas dans le panneau Data du notebook, ou il a été renommé | Ajoutez-le, ou changez son nom dans `2_sources.csv` |
| « 1_prix_pieces.csv: '…' is not a price » | Un prix de la liste des prix des pièces contient du texte | Corrigez cette ligne |
| « fto2_dash_cout not written » | Normal : cette table ne sert qu'à une configuration facultative | Rien |
| Toute autre erreur | La dernière étape affichée dit où il en était | Le fichier de cette étape (section 3) |
