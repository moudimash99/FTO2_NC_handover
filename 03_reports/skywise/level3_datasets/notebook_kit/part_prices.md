# Part prices and logistics time

Two things complete the cost of an NC: the **value of the part** when it is rejected, scrapped or exchanged, and the
**logistics time** needed to supply it.

## 1. How the part is known: the NC's material

Each NC in Skywise names the part it is about in its column **`material`** (the SAP material number, with its description).
It is not the *article* of the NC, which is the whole assembly being built.

| | Example |
|---|---|
| Article (the assembly) | `F9251623400000` · ELEC ASSY 295VU |
| Material (the part concerned) | `E0062D1S4BA0A` · SWITCH-OVERS, SUBMINIATURE |

The notebook reads the material of every NC. It is filled on rejections and most exchanges, and almost never on plain
reworks, which replace no part.

## 2. The price list: `1_prix_pieces.csv`

One row per material, in the settings folder:

```
materiel;designation;prix_unitaire_eur
E0062D1S4BA0A;SWITCH-OVERS,SUBMINIATURE;38,40
6325018500;334VZ01Y00#SLV FIRE P/B SW;212,00
```

| Column | What to write |
|---|---|
| `materiel` | the material number, as in the NC (leading zeros, spaces and upper/lower case don't matter) |
| `designation` | its name, for people; not read |
| `prix_unitaire_eur` | the price of one part, in euros, with a dot or a comma; empty = no price yet |

An export from another tool can be used as it is: the columns are recognised by their names (for the material: `materiel`,
`material`, `article`, `reference`, `part_number`...; for the price: `prix_unitaire_eur`, `prix`, `price`, `unit_price`,
`cout`...), in any order; other columns are ignored; the separator may be `;`, `,` or a tab.

**Which materials still need a price?** Each run writes `fto2_parts_to_price.csv` next to the notebook: one row per
material with no price yet, with its description, the number of NCs and the date of the last one. Copy its rows into the
price list and fill in the prices.

## 3. What is counted

- **Value of the part** = unit price × quantity (the NC's defect quantity, 1 when empty).
- It counts only for the decisions that charge the part: `valeur_piece` = 1 in `2_cout_decisions.csv` (rejection, rejection
  with a rework order, scrap, exchange).
- As for the rest of the cost, it is FTO2's cost only where FTO2 is liable.
- A material with no price counts 0 €; the NC is then marked "Part value unknown" in the cost model's output.
- The comparison year gets the same prices, so both years stay comparable.

## 4. Logistics time

The planned time of a rework order (S03) holds the work and its checks, but nothing for supplying the part. So when an NC's
work is costed from its rework order, a logistics time is added to its preparation step, at the production rate.

| Setting | Table | Value |
|---|---|---|
| `minutes_logistique` | `2_cout_parametres.csv` | 15 minutes |
| `logistique_seulement_avec_materiel` | `3_cout_avance.csv` | `oui`: only when the NC names a material (a part has to be supplied). `non`: for every NC costed from its rework order |

NCs costed by the model (no usable rework order) are not concerned: their preparation time already includes fetching what
the job needs.

## 5. Where it shows

- **The cost of each NC** (levels 2 and 3) includes the part's value; the preparation step includes the logistics minutes.
- **Dashboard, cost tab, "Expliquer le calcul":** the NC's material and its description, a line "Valeur de la pièce" with the
  price used (or why it is 0 €), and the logistics minutes in the note of the preparation step. The summary of the selection
  shows the total value of the parts.
- **Dashboard, cost by component:** a "Pièces" component appears once some parts are priced.
- **The notebook's last lines:** how many NCs have a material, how many are priced, and how many materials still need a price.

## 6. In the code

| What | Where |
|---|---|
| Reading the price list, valuing each NC, listing what is left to price | `notebook_kit/fto2/cost/parts.py` |
| Reading the material of each NC, passing its value to the cost model | `notebook_kit/fto2/skywise.py` (the columns read), `notebook_kit/fto2/core.py` (`prepare`) |
| Adding the part and the logistics minutes to the cost | `notebook_kit/fto2/cost/model.py` (`cnq_cost_part`, `cnq_min_logistics`) |
| The NC table's columns | `material`, `material_label`, `cost_part`, `min_logistics` (`core.py`, `NC_COLUMNS`) |

## 7. If a price doesn't show

| You see | Why |
|---|---|
| The run stops: "1_prix_pieces.csv: '…' is not a price (line N)" | A price holds text: fix that line |
| The run stops: "it needs a column for the material number…" | The price list's column names are not recognised: name them `materiel` and `prix_unitaire_eur` |
| An NC still at 0 € for its part | It has no material, its material has no price, its decision doesn't charge the part, or FTO2 isn't liable |
| Nothing priced at all | The price list isn't in the settings folder, or every price is empty |
