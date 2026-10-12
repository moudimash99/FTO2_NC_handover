/* q03_rca_par_categorie: FTO2, RCA inside the category picked in w_groupe (bar chart)
   Returns: rca, defects, pct_du_groupe (all RCA of the category, biggest first).
   With no category picked, it shows every RCA.
   Widgets: w_mineurs (dropdown or radio buttons with the two values "Avec mineurs" and
   "Sans mineurs", default "Avec mineurs").
   Also needs: w_groupe (dropdown filled by q07_liste_categories, value = categorie).
   Reads: foundry_sync.fto2_defects (the Postgres sync of the fto2_defects dataset).
   If your sync has another name, change it on the FROM lines. Nothing else to edit. */
SELECT rca_nom                                              AS rca,
       COUNT(*)                                             AS defects,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)   AS pct_du_groupe
FROM foundry_sync.fto2_defects
WHERE perimetre = 'FTO2'
  AND COALESCE(dans_periode::text, '') IN ('true', 't', '1')
  AND ('{{w_mineurs.selectedValue}}' NOT IN ('Sans mineurs', 'false')
       OR COALESCE(mineur::text, '') NOT IN ('true', 't', '1'))
  AND ('{{w_groupe.selectedValue}}' = '' OR groupe = '{{w_groupe.selectedValue}}')
GROUP BY rca_nom
ORDER BY defects DESC, rca;
