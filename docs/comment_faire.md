# Comment faire

Tous les réglages sont dans `config/` (dans Skywise : `data/config/` à côté du notebook). Chaque table s'ouvre dans Excel ;
la liste complète, avec ce que chaque table change, est dans `config/lisez_moi.csv`.

Le premier chiffre du nom dit à quel groupe la table appartient :

- **0** : des données, remplies par les fichiers téléchargés ou historiques. On ne les modifie pas à la main ;
- **1** : les réglages du responsable du tableau de bord (l'année, l'objectif, les taux, les fermetures, les prix des
  pièces, les actions MFT). Six petites tables ;
- **2** : les règles et les noms (une personne attentive, avec le guide du développeur) ;
- **3** : les tables d'expert (une personne technique).

Deux choses ne se tapent dans aucune table : **le plan de production** et **les demandes de câbles**. On télécharge le
fichier et on le dépose tel quel dans `data/` ; le notebook le lit au lancement suivant (voir plus bas).

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

**Un taux horaire** : `config/1_cout_parametres.csv`, colonne `valeur` de `taux_production`, `taux_qualite` ou `taux_me`.

**L'objectif** (−25 % par rapport à l'année de comparaison) : `config/1_reglages_pages.csv`, ligne `objectif_baisse`
(0.25, 0,25 ou 25 % = −25 %). Les textes des pages affichent le pourcentage écrit ici.

**Commencer une nouvelle année** (chaque mois de janvier) : l'année suivie change toute seule (la ligne `annee` de
`config/1_parametres.csv` reste vide). Puis :
- déposer un export récent du Tableau Avances / Retards dans `data/`, **sans supprimer les anciens** : ils donnent les
  livraisons de l'année d'avant, donc les objectifs ;
- ajouter les fermetures de la nouvelle année dans `config/1_calendrier_production.csv` ;
- déposer le registre GPS de la nouvelle année dans `data/`, nommé comme celui de 2026 avec la nouvelle année
  (`GPS NC INT_SERIE ELEC 2027 - NC REGISTRE.csv`) : dans `config/2_sources.csv`, son nom est écrit avec `{annee}` à la
  place de l'année. La liste Test garde son nom.

Rien d'autre à changer : les NC affichées, l'année de comparaison, les objectifs, la cloche et tous les textes des pages
suivent. La cloche reste muette tant que l'année n'a pas 16 semaines terminées (fin avril). Si une année est écrite sur la
ligne `annee`, les pages gardent cette année, complète, et le notebook le rappelle à la fin de chaque lancement.

**Un nouveau produit** : la règle qui le reconnaît dans `config/2_regle_produit.csv` ; son nom dans le plan de production
dans `config/2_produits_plan.csv`.

**Mettre à jour le plan de production** : télécharger le Tableau Avances / Retards en CSV et déposer le fichier dans
`data/`, à côté des exports précédents (son nom commence par `Avances_Retards`). Tous les exports sont lus : le plus récent
l'emporte pour chaque avion, et un avion livré que le nouvel export ne liste plus garde sa dernière ligne. Les dernières
lignes du notebook disent quels fichiers ont été lus.

**Ajouter une action MFT** : une ligne dans `config/1_actions_mft.csv`, avec un `id` à elle. Le problème visé :
`niveau` (`cat` = une catégorie, `rca` = une cause, `sub` = une sous-catégorie, `code` = un sous-code, `where` = un lieu de
détection ; les mots français sont lus aussi) et `valeurs` (séparées par `|`), écrites comme sur le tableau de bord.
Elle apparaît sur la page MFT, pour tout le monde, au prochain lancement du notebook, avec son résultat.
Une action tapée directement sur la page MFT reste dans ce navigateur seulement : pour la partager, l'ajouter à la table.

**Les demandes de câbles** : télécharger le suivi de l'équipe câbles en CSV et déposer le fichier dans `data/` (son nom
contient `cables`). Le plus récent remplace la liste. La cause proposée vient des mots-clés de
`config/2_regle_cause_cable.csv`.

## Vérifier que rien d'autre n'a bougé (personne technique)

`python3 -m unittest discover -s tests -t .` puis la comparaison complète des pages : voir `tests/README.md`.
