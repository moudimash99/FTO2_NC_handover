# Test: does the notebook read the Fusion settings spreadsheet? Paste this whole cell into a new cell of the notebook
# (after the first cell) and run it. It only reads and prints; it writes nothing.
from foundry.transforms import Dataset

EXPECTED = {
    "fto2_set_targets": ["nom", "valeur", "description"],
    "fto2_set_cost": ["nom", "valeur", "unite", "description"],
    "fto2_set_blackout": ["debut", "fin", "poids", "motif"],
    "fto2_set_deliveries": ["produit_livraison", "produit_eqmsn", "ligne"],
    "fto2_set_eqmsn": ["produit", "version"],
    "fto2_set_plant": ["nom", "valeur", "description"],
    "fto2_set_part_prices": ["materiel", "designation", "prix_unitaire_eur"],
    "fto2_set_cables": ["Année", "Semaine", "NC"],
    "fto2_set_gps": [],
    "fto2_set_test": [],
}

for name, cols in EXPECTED.items():
    try:
        t = Dataset.get(name).read_table(format="pandas")
    except Exception as e:
        print("%-28s NOT READ: %s" % (name, str(e).splitlines()[0][:160]))
        continue
    missing = [c for c in cols if c not in t.columns]
    print("%-28s %4d rows, %2d columns%s" % (name, len(t), len(t.columns), "" if not missing else "  MISSING COLUMNS: %s" % missing))
    print("%28s columns as read: %s" % ("", list(t.columns)[:8]))
    if len(t):
        print("%28s first row: %s" % ("", [str(v)[:25] for v in t.iloc[0].tolist()[:6]]))
