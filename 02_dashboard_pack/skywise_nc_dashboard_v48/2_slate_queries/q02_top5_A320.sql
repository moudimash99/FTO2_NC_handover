/* q02_top5_A320: FTO2, top 5 RCA on the A320 line (bar chart)
   The 5 biggest RCA, plus Déverrouillage every time, even when it is not in the top 5
   (then with 0 defects if there are none).
   Returns: rca, defects, defects_top5, defects_ajoute, ajoute, rang.
   Chart: renderer stackedBar (horizontal), x = rca, two series: defects_top5 (colour) and
   defects_ajoute (grey), so an added Déverrouillage bar comes out grey.
   Widgets: w_mineurs (dropdown or radio buttons with the two values "Avec mineurs" and
   "Sans mineurs", default "Avec mineurs").
   The line comes from the programme value (see LINES in fto2_logic.py).
   Reads: foundry_sync.fto2_defects (the Postgres sync of the fto2_defects dataset).
   If your sync has another name, change it on the FROM lines. Nothing else to edit. */
WITH c AS (
    SELECT rca_type, rca_nom AS rca, COUNT(*) AS defects
    FROM foundry_sync.fto2_defects
    WHERE perimetre = 'FTO2'
      AND COALESCE(dans_periode::text, '') IN ('true', 't', '1')
      AND ('{{w_mineurs.selectedValue}}' NOT IN ('Sans mineurs', 'false')
           OR COALESCE(mineur::text, '') NOT IN ('true', 't', '1'))
      AND ligne = 'A320'
    GROUP BY rca_type, rca_nom
),
r AS (
    SELECT c.*, ROW_NUMBER() OVER (ORDER BY defects DESC, rca) AS rang
    FROM c
),
x AS (
    SELECT rca, defects, rang FROM r WHERE rang <= 5 OR rca_type = 'OUBLI_VERROUILLAGE'
    UNION ALL
    SELECT COALESCE((SELECT MAX(rca_nom) FROM foundry_sync.fto2_defects WHERE rca_type = 'OUBLI_VERROUILLAGE'), 'Déverrouillage'), 0, 99
    WHERE NOT EXISTS (SELECT 1 FROM c WHERE rca_type = 'OUBLI_VERROUILLAGE')
)
SELECT rca,
       defects,
       CASE WHEN rang <= 5 THEN defects END AS defects_top5,
       CASE WHEN rang > 5 THEN defects END  AS defects_ajoute,
       rang > 5                             AS ajoute,
       rang
FROM x
ORDER BY rang;
