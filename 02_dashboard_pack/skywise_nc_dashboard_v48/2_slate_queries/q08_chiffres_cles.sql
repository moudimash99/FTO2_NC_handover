/* q08_chiffres_cles: the headline numbers (text tiles), one row.
   Returns: defauts_fto2, nc_fto2, defauts_client, nc_client.
   Tiles: {{q08_chiffres_cles.defauts_fto2[0]}} and so on.
   Defects follow the w_mineurs toggle; NC counts do not (an NC is counted once).
   Reads: foundry_sync.fto2_defects and foundry_sync.fto2_nc (Postgres syncs). Change the FROM lines if your syncs have other names. */
WITH d AS (
    SELECT perimetre, COUNT(*) AS defauts
    FROM foundry_sync.fto2_defects
    WHERE COALESCE(dans_periode::text, '') IN ('true', 't', '1')
      AND ('{{w_mineurs.selectedValue}}' NOT IN ('Sans mineurs', 'false')
           OR COALESCE(mineur::text, '') NOT IN ('true', 't', '1'))
    GROUP BY perimetre
),
n AS (
    SELECT perimetre, COUNT(*) AS ncs
    FROM foundry_sync.fto2_nc
    WHERE COALESCE(dans_periode::text, '') IN ('true', 't', '1')
    GROUP BY perimetre
)
SELECT COALESCE((SELECT defauts FROM d WHERE perimetre = 'FTO2'), 0)          AS defauts_fto2,
       COALESCE((SELECT ncs FROM n WHERE perimetre = 'FTO2'), 0)              AS nc_fto2,
       COALESCE((SELECT defauts FROM d WHERE perimetre = 'Retour client'), 0) AS defauts_client,
       COALESCE((SELECT ncs FROM n WHERE perimetre = 'Retour client'), 0)     AS nc_client;
