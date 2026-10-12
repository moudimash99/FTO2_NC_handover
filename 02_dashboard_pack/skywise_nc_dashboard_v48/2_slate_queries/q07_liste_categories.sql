/* q07_liste_categories: the values of the w_groupe dropdown (value and label = categorie).
   Nothing to edit. */
SELECT categorie
FROM (VALUES (1, 'MEO Câblage'), (2, 'Erreur Branchement'), (3, 'Élément Manquant'), (4, 'Élément Endommagé'), (5, 'Déverrouillage'), (6, 'Grounding/Bonding'), (7, 'Kitting Factory'), (8, 'FOD'), (9, 'Autre')) AS t(ord, categorie)
ORDER BY ord;
