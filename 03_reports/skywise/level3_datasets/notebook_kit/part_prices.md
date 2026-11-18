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

The update reads the material of every NC. It is filled on rejections and most exchanges, and almost never on plain
reworks, which replace no part.

## 2. The price list: the sheet *Part prices*

The prices are in the sheet *Part prices* of the Fusion spreadsheet *FTO2 NC Dashboard - Settings*, filled in by hand by the
configuration manager. One row per material:

| materiel | designation | prix_unitaire_eur |
|---|---|---|
| E0062D1S4BA0A | SWITCH-OVERS,SUBMINIATURE | 38,40 |
| 6325018500 | 334VZ01Y00#SLV FIRE P/B SW | 212,00 |

| Column | What to write |
|---|---|
| `materiel` | the material number, as in the NC (leading zeros, spaces and upper/lower case don't matter) |
| `designation` | its name, for people; not read |
| `prix_unitaire_eur` | the price of one part, in euros, with a dot or a comma; empty = no price yet |

Keep the first row (the column names) as it is: a sheet with one of these columns missing is not used, and the update says
so in its first lines. Keep the material column as text: a material number typed as a number loses its leading zeros (the
update matches the numbers without their leading zeros, but the sheet should still show them).

At each run the sheet replaces the table `1_prix_pieces.csv` kept with the code (`src/fto2/settings/`). That table stays as
the fallback, used when the sheet cannot be read. It has the same three columns, separated by `;`, and it also takes a price
list from another tool as it is: the columns are recognised by their names (for the material: `materiel`, `material`,
`article`, `reference`, `part_number`...; for the price: `prix_unitaire_eur`, `prix`, `price`, `unit_price`, `cout`...), in
any order; other columns are ignored; the separator may be `;`, `,` or a tab.

**Which materials still need a price?** Each run writes the dataset `fto2_parts_to_price`, beside the dashboard's tables:
one row per material with no price yet, with its description, the number of NCs and the date of the last one, the most
frequent first. Copy its rows into the sheet and fill in the prices.

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

| Setting | Where | Value |
|---|---|---|
| `minutes_logistique` | The sheet *Cost rates and times* (`1_cout_parametres.csv`) | 15 minutes |
| `logistique_seulement_avec_materiel` | `3_cout_avance.csv` | `oui`: only when the NC names a material (a part has to be supplied). `non`: for every NC costed from its rework order |

NCs costed by the model (no usable rework order) are not concerned: their preparation time already includes fetching what
the job needs.

## 5. Where it shows

- **The cost of each NC** (levels 2 and 3) includes the part's value; the preparation step includes the logistics minutes.
- **Dashboard, cost tab, "Expliquer le calcul":** the NC's material and its description, a line "Valeur de la pièce" with the
  price used (or why it is 0 €), and the logistics minutes in the note of the preparation step. The summary of the selection
  shows the total value of the parts.
- **Dashboard, cost by component:** a "Pièces" component appears once some parts are priced.
- **The last lines of the update's log:** how many NCs have a material, how many are priced, and how many materials still
  need a price.

## 6. In the code

In the Code Repository, folder `src/fto2/`:

| What | Where |
|---|---|
| The sheet *Part prices* replacing the table for the run | `fusion.py` |
| Reading the price list, valuing each NC, listing what is left to price | `cost/parts.py` |
| Reading the material of each NC, passing its value to the cost model | `skywise.py` (the columns read), `core.py` (`prepare`) |
| Adding the part and the logistics minutes to the cost | `cost/model.py` (`cnq_cost_part`, `cnq_min_logistics`) |
| The NC table's columns | `material`, `material_label`, `cost_part`, `min_logistics` (`core.py`, `NC_COLUMNS`) |

## 7. If a price doesn't show

| You see | Why |
|---|---|
| The run stops: "1_prix_pieces.csv: '…' is not a price (line N)" | A price holds text. The message names the table the sheet replaces: fix that line in the sheet *Part prices* |
| The first lines of the run say the sheet *Part prices* is not used, a column missing | The sheet's first row was changed: put back `materiel`, `designation`, `prix_unitaire_eur` |
| The run stops: "it needs a column for the material number…" | The fallback table's column names are not recognised: name them `materiel` and `prix_unitaire_eur` |
| An NC still at 0 € for its part | It has no material, its material has no price, its decision doesn't charge the part, or FTO2 isn't liable |
| Nothing priced at all | Every price is empty, in the sheet and in the table |
