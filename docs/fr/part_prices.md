# Prix des pièces et temps logistique

Deux choses complètent le coût d’une NC : la **valeur de la pièce** quand elle est rejetée, rebutée ou échangée, et le
**temps logistique** nécessaire pour l’approvisionner.

## 1. Comment la pièce est connue : le matériel de la NC

Chaque NC dans Skywise indique la pièce qu’elle concerne dans sa colonne **`material`** (le numéro de matériel SAP, avec sa
description). Ce n’est pas l’*article* de la NC, qui est l’ensemble complet en cours de fabrication.

| | Exemple |
|---|---|
| Article (l’ensemble) | `F9251623400000` · ELEC ASSY 295VU |
| Matériel (la pièce concernée) | `E0062D1S4BA0A` · SWITCH-OVERS, SUBMINIATURE |

La mise à jour lit le matériel de chaque NC. Il est rempli sur les rejets et la plupart des échanges, et presque jamais sur
les simples retouches, qui ne remplacent aucune pièce.

## 2. La liste des prix : la feuille *Part prices*

Les prix sont dans la feuille *Part prices* du classeur Fusion *FTO2 NC Dashboard - Settings*, remplie à la main par le
gestionnaire de configuration. Une ligne par matériel :

| materiel | designation | prix_unitaire_eur |
|---|---|---|
| E0062D1S4BA0A | SWITCH-OVERS,SUBMINIATURE | 38,40 |
| 6325018500 | 334VZ01Y00#SLV FIRE P/B SW | 212,00 |

| Colonne | Ce qu’il faut écrire |
|---|---|
| `materiel` | le numéro de matériel, comme dans la NC (les zéros de tête, les espaces et les majuscules / minuscules ne comptent pas) |
| `designation` | son nom, pour les personnes ; pas lu |
| `prix_unitaire_eur` | le prix d’une pièce, en euros, avec un point ou une virgule ; vide = pas encore de prix |

Gardez la première ligne (les noms des colonnes) telle quelle : une feuille à laquelle il manque l’une de ces colonnes n’est
pas utilisée, et la mise à jour le dit dans ses premières lignes. Gardez la colonne du matériel en texte : un numéro de
matériel tapé comme un nombre perd ses zéros de tête (la mise à jour compare les numéros sans leurs zéros de tête, mais la
feuille doit quand même les montrer).

À chaque exécution, la feuille remplace la table `1_prix_pieces.csv` gardée avec le code (`src/fto2/settings/`). Cette table
reste la valeur de secours, utilisée quand la feuille ne peut pas être lue. Elle a les mêmes trois colonnes, séparées par
`;`, et elle accepte aussi telle quelle une liste de prix venant d’un autre outil : les colonnes sont reconnues par leur nom
(pour le matériel : `materiel`, `material`, `article`, `reference`, `part_number`... ; pour le prix : `prix_unitaire_eur`,
`prix`, `price`, `unit_price`, `cout`...), dans n’importe quel ordre ; les autres colonnes sont ignorées ; le séparateur
peut être `;`, `,` ou une tabulation.

**Quels matériels attendent encore un prix ?** Chaque exécution écrit le dataset `fto2_parts_to_price`, à côté des tables du
tableau de bord : une ligne par matériel encore sans prix, avec sa description, le nombre de NC et la date de la dernière,
les plus fréquents d’abord. Copiez ses lignes dans la feuille et remplissez les prix.

## 3. Ce qui est compté

- **Valeur de la pièce** = prix unitaire × quantité (la quantité en défaut de la NC, 1 quand elle est vide).
- Elle ne compte que pour les décisions qui prennent en compte la pièce : `valeur_piece` = 1 dans `2_cout_decisions.csv`
  (rejet, rejet avec ordre de retouche, rebut, échange).
- Comme pour le reste du coût, c’est un coût pour FTO2 seulement quand FTO2 est responsable.
- Un matériel sans prix compte 0 € ; la NC est alors marquée « Part value unknown » dans la sortie du modèle de coût.
- L’année de comparaison reçoit les mêmes prix, pour que les deux années restent comparables.

## 4. Le temps logistique

Le temps prévu d’un ordre de retouche (S03) contient le travail et ses vérifications, mais rien pour approvisionner la pièce.
Donc, quand le travail d’une NC est chiffré à partir de son ordre de retouche, un temps logistique est ajouté à son étape de
préparation, au taux de production.

| Paramètre | Où | Valeur |
|---|---|---|
| `minutes_logistique` | La feuille *Cost rates and times* (`1_cout_parametres.csv`) | 15 minutes |
| `logistique_seulement_avec_materiel` | `3_cout_avance.csv` | `oui` : seulement quand la NC indique un matériel (une pièce doit être approvisionnée). `non` : pour chaque NC chiffrée à partir de son ordre de retouche |

Les NC chiffrées par le modèle (sans ordre de retouche utilisable) ne sont pas concernées : leur temps de préparation
comprend déjà le temps d’aller chercher ce dont le travail a besoin.

## 5. Où cela apparaît

- **Le coût de chaque NC** (niveaux 2 et 3) comprend la valeur de la pièce ; l’étape de préparation comprend les minutes de
  logistique.
- **Tableau de bord, onglet du coût, « Expliquer le calcul » :** le matériel de la NC et sa description, une ligne « Valeur de
  la pièce » avec le prix utilisé (ou la raison pour laquelle il vaut 0 €), et les minutes de logistique dans la note de
  l’étape de préparation. Le résumé de la sélection affiche la valeur totale des pièces.
- **Tableau de bord, coût par composante :** une composante « Pièces » apparaît dès que des pièces ont un prix.
- **Les dernières lignes du journal de la mise à jour :** combien de NC ont un matériel, combien ont un prix, et combien de
  matériels attendent encore un prix.

## 6. Dans le code

Dans le Code Repository, dossier `src/fto2/` :

| Quoi | Où |
|---|---|
| La feuille *Part prices* qui remplace la table pour l’exécution | `fusion.py` |
| Lire la liste des prix, donner une valeur à chaque NC, lister ce qui reste à chiffrer | `cost/parts.py` |
| Lire le matériel de chaque NC, transmettre sa valeur au modèle de coût | `skywise.py` (les colonnes lues), `core.py` (`prepare`) |
| Ajouter la pièce et les minutes de logistique au coût | `cost/model.py` (`cnq_cost_part`, `cnq_min_logistics`) |
| Les colonnes de la table des NC | `material`, `material_label`, `cost_part`, `min_logistics` (`core.py`, `NC_COLUMNS`) |

## 7. Si un prix n’apparaît pas

| Vous voyez | Pourquoi |
|---|---|
| L’exécution s’arrête : « 1_prix_pieces.csv: '…' is not a price (line N) » | Un prix contient du texte. Le message nomme la table que la feuille remplace : corrigez cette ligne dans la feuille *Part prices* |
| Les premières lignes de l’exécution disent que la feuille *Part prices* n’est pas utilisée, une colonne manquante | La première ligne de la feuille a été changée : remettez `materiel`, `designation`, `prix_unitaire_eur` |
| L’exécution s’arrête : « it needs a column for the material number… » | Les noms des colonnes de la table de secours ne sont pas reconnus : nommez-les `materiel` et `prix_unitaire_eur` |
| Une NC toujours à 0 € pour sa pièce | Elle n’a pas de matériel, son matériel n’a pas de prix, sa décision ne prend pas en compte la pièce, ou FTO2 n’est pas responsable |
| Aucune pièce n’a de prix | Tous les prix sont vides, dans la feuille et dans la table |
