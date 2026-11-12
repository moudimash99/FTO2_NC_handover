# Part prices: the value of rejected, scrapped and exchanged parts

When an NC is a rejection, a scrap or an exchange, the part itself is part of the cost of non-quality. Its price comes from
one settings table, `data/config/1_prix_pieces.csv`. Without a price, the part counts 0 €.

## 1. Set it up in the Code Workspace (once)

**a. Add the new code file** `notebook_kit/fto2/cost/parts.py`.

**b. In `notebook_kit/fto2/core.py`, add two things.**

Near the top, under `from .cost.orders import nc_order_times`:

```python
from .cost.parts import part_values
```

In the function `prepare`, right after the line that ends with `"aleas", "alea_minutes"]].copy()`:

```python
    nc_in["part_value"] = part_values(nc["notification_number"], nc["description_short"], nc["notification_number"].map(lt))
    report["parts_priced"] = int(pd.notna(nc_in["part_value"]).sum())
```

**c. Add the table** `data/config/1_prix_pieces.csv`. It comes already listing the parts and NCs found so far, with the prices
empty.

**d. Restart the notebook's kernel and run all cells.**

**e. Optional, for the dashboard:** paste the new dashboard JS into its Slate sandbox, so that "Expliquer le calcul" shows the
price on its own line, "Valeur de la pièce". Without it the totals are right, but the NC's page shows the price on the
customer-return line.

## 2. The table `1_prix_pieces.csv`

```
reference;prix_unitaire_eur;nc;quantite;note
```

| Column | What to write |
|---|---|
| `reference` | the part number (or the name used for it) |
| `prix_unitaire_eur` | the price of one part, in euros; a dot or a comma |
| `nc` | empty, or an NC number to tie this part to that NC |
| `quantite` | how many parts that NC used; empty = 1 |
| `note` | anything, for people |

There are two kinds of rows.

**A price row: a reference and its price, no NC.**

```
NSA932844CN;12.50;;;socle de raccordement
```

Every NC whose title or long text contains `NSA932844CN` gets 12.50 € (spaces and upper/lower case don't matter). This is where
your price list goes: one row per part.

**An NC row: an NC number and a reference.**

```
NSA932844CN;;216060124;2;
```

NC 216060124 used 2 of that part. Its price is the row's own `prix_unitaire_eur`, or, when empty, the price row of the same
reference. Use it when the NC's text doesn't name the part (only a FIN, or a description), or to give the quantity.

**The rules:**

- an NC tied by hand (an NC row) is not searched in the text: its NC rows decide;
- the value of an NC = the sum of price × quantity of its parts;
- references shorter than 5 characters are not searched in the text, to avoid false matches;
- only the decisions that count the part get the value: `valeur_piece` = 1 in `2_cout_decisions.csv` (rejection, rejection
  with a rework order, scrap, exchange);
- the cost is FTO2's only where FTO2 is liable, as for the rest of the cost;
- the 2025 comparison year gets the same prices, so 2025 and 2026 stay comparable.

## 3. What it changes

- **The cost of each NC** (level 3, and level 2) includes the part's value.
- **The NC's completeness** (`cnq_complete`) no longer says "Part value unknown" once its part is priced.
- **The notebook's report** gives `parts_priced`: how many NCs got a part value.
- **The dashboard:** every cost figure follows. In "Expliquer le calcul", the part has its own line (with the new dashboard JS).

## 4. Where it is in the code

| Part | File |
|---|---|
| Reading the table and finding each NC's parts | `notebook_kit/fto2/cost/parts.py`, function `part_values` |
| Giving the value to the cost model | `notebook_kit/fto2/core.py`, function `prepare` (column `part_value`) |
| Adding it to the cost, only for the decisions that count it | `notebook_kit/fto2/cost/model.py` (`cnq_cost_part`) |
| Which decisions count it | `data/config/2_cout_decisions.csv`, column `valeur_piece` |

## 5. If a price doesn't show

| You see | Why |
|---|---|
| The run stops: "1_prix_pieces.csv: '…' is not a number" | A price or quantity has text in it: fix that line |
| An NC still at 0 € for its part | Its text doesn't contain the reference (add an NC row), or its decision doesn't count the part, or FTO2 isn't liable |
| An NC priced that shouldn't be | Its text mentions a reference by chance: add an NC row for it with the right part (it then stops being searched) |
| Nothing priced at all | The table isn't in `data/config/`, or the code of section 1 isn't in place: restart the kernel after adding it |
