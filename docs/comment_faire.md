# Comment faire

Tous les réglages sont dans `config/` (dans Skywise : `data/config/` à côté du notebook). Chaque table s'ouvre dans Excel ;
la liste complète, avec ce que chaque table change, est dans `config/lisez_moi.csv`.

Le premier chiffre du nom dit qui peut la modifier : **1** tout le monde, **2** une personne attentive, **3** une personne
technique.

Après un changement : relancer le notebook dans Skywise (ou, sur le portable, `python3 -I build/build_all.py`). Si un réglage
est mal écrit, le lancement s'arrête avec un message qui donne le fichier, la ligne et quoi corriger.

## Les règles : comment elles se lisent

Les tables `2_regle_*.csv` se lisent toutes pareil : une ligne = une condition.

| ordre | resultat | colonne | test | valeur |
|---|---|---|---|---|
| 1 | FTI | constituent_assembly | commence_par | WY\|WA |
| 2 | REC | workflow_list | mot | REC |
| 3 | REC | workflow_list | contient | -CRE\|-PNC\|A30-REJ-PVU2 |
| 99 | SERIE | | toujours | |

- Les règles sont essayées par `ordre` croissant ; **la première qui marche donne le résultat**.
- Plusieurs lignes avec le **même ordre** = toutes leurs conditions doivent être vraies.
- `valeur` : plusieurs valeurs séparées par `|` (une seule suffit).
- Tests : `contient`, `ne_contient_pas`, `mot` (mot entier), `commence_par`, `ne_commence_pas_par`, `egal`, `different`,
  `vide`, `non_vide`, `toujours` (la règle par défaut, en dernier). Pour les personnes techniques : `regex`, `pas_regex`,
  `extraire`. Majuscules et minuscules sont traitées pareil.

## Exemples

**Un nouveau cas de REC** (par exemple un workflow qui contient `-RCX`) : dans `config/2_regle_phase.csv`, ajouter `-RCX` à
la valeur de la ligne 3 (`-CRE|-PNC|A30-REJ-PVU2|-RCX`), ou ajouter une ligne `4;REC;workflow_list;contient;-RCX;`.

**Un taux horaire** : `config/2_cout_parametres.csv`, colonne `valeur` de `taux_production`, `taux_qualite` ou `taux_me`.

**L'objectif** (−25 % par rapport à 2025) : `config/2_reglages_pages.csv`, ligne `objectif_baisse` (0.25 = −25 %).

**Un nouveau produit** : la règle qui le reconnaît dans `config/2_regle_produit.csv` ; son nom dans le plan de production
dans `config/2_produits_plan.csv`.

**Mettre à jour le plan de production** :
- automatiquement : `python3 -I scripts/plan_depuis_avances_retards.py "06_input_data/Avances_Retards_AAAA-MM-JJ.csv"` ;
- à la main : corriger les dates d'un avion dans `config/1_plan_msn.csv` et mettre sa colonne `source` à `manuel`
  (le script ne la remplacera plus).

**Ajouter une action MFT** : une ligne dans `config/1_actions_mft.csv` avec `source` = `manuel`. Le problème visé :
`niveau` (`cat` = une catégorie, `rca` = une cause, `sub` = une sous-catégorie, `code` = un sous-code, `where` = un lieu de
détection) et `valeurs` (séparées par `|`), écrites comme sur le tableau de bord.
Elle apparaît sur la page MFT, pour tout le monde, au prochain lancement du notebook, avec son résultat.
Une action tapée directement sur la page MFT reste dans ce navigateur seulement : pour la partager, l'ajouter à la table.

**Les demandes de câbles** : `python3 -I scripts/cables_depuis_suivi.py "06_input_data/cable_team_tracker_A30_NC_cables.csv"`.
La cause proposée vient des mots-clés de `config/2_regle_cause_cable.csv`.

## Vérifier que rien d'autre n'a bougé (personne technique)

`python3 -m unittest discover -s tests -t .` puis la comparaison complète des pages : voir `tests/README.md`.
