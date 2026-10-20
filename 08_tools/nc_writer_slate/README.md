# NC writing tool in Slate (Code Sandbox widget)

The Streamlit app `reference/app_streamlit.py` ("NC · Saisie Structurée") rebuilt as plain
HTML, CSS and JavaScript, so it runs inside a Slate **Code Sandbox** widget. Same screens, same
codes, same FIN suggestions, same SAP text, character for character (`tests/check_parity.py`).

```
operator fills the NC in the widget
      |
"Soumettre la NC"  ->  widget state = { submission: row }  +  event "submit"
      |
Slate event handler  ->  writes the row (Ontology action, section 3)
```

## 1. Files

| File | Where it goes |
|---|---|
| `nc_writer.html` | Code Sandbox, **HTML** tab |
| `nc_writer.css` | Code Sandbox, **CSS** tab |
| `nc_writer.js` | Code Sandbox, **JavaScript** tab |
| `nc_writer_standalone.html` | The three files in one page. Open it in a browser to try the tool outside Slate. Nothing is saved there: it shows the text and downloads the row as CSV. |
| `build_standalone.py` | Rebuilds the standalone page after a change to one of the three files |
| `reference/app_streamlit.py` | The Streamlit app it replaces |
| `tests/check_parity.py` | Checks the JS has the same codes, FINs and texts as the Streamlit app, and no `{{` that Slate would read as a template |
| `tests/test_ui.js` | Clicks through the whole tool in Chromium, inside a fake Slate, outside Slate and with a broken Slate API |

No library, no network call, no external font: the sandbox blocks network requests, so
everything is in the three files.

## 2. Put the widget in Slate

1. In the Slate app, add a widget: **Widgets > Advanced > Code Sandbox**. Name it `w_nc_writer`
   (any name works; the bindings below use this one).
2. Copy each file's content into its tab: HTML, CSS, JavaScript. Leave **Libraries** empty.
3. In the widget's **State** field, put `{}`.
4. In the widget's **Interaction** settings, declare one event named `submit`.
5. Make the widget tall enough (about 900 px), or let it fill the page: the tool scrolls inside it.

Preview the app: the "Nouvelle NC" screen should appear. If the widget stays on "Chargement…",
open the browser console (F12): the JavaScript did not run.

## 3. Save the NC

The Streamlit app appended rows to the dataset `nc_writer_dataset`. Slate cannot append to a
dataset directly. The standard way is an **Ontology action**:

1. In Ontology Manager, create an object type, for example **NC Saisie**, with one property per
   column below, primary key `submission_id`. Its writeback dataset takes the place of
   `nc_writer_dataset`.
2. Create an action type **Créer NC Saisie** that creates one NC Saisie object, with one
   parameter per property.
3. In Slate, in the **Events** panel, add a handler on `w_nc_writer.submit` that runs this
   action, each parameter bound to the widget state:

   | Action parameter | Slate binding |
   |---|---|
   | submission_id | `{{w_nc_writer.state.submission.submission_id}}` |
   | timestamp | `{{w_nc_writer.state.submission.timestamp}}` |
   | msn | `{{w_nc_writer.state.submission.msn}}` |
   | produit | `{{w_nc_writer.state.submission.produit}}` |
   | detection | `{{w_nc_writer.state.submission.detection}}` |
   | total_defauts | `{{w_nc_writer.state.submission.total_defauts}}` |
   | texte_sap | `{{w_nc_writer.state.submission.texte_sap}}` |
   | defauts_json | `{{w_nc_writer.state.submission.defauts_json}}` |

   Use Slate's autocomplete in the binding field to confirm the exact path for your widget name.

If your Skywise project cannot create object types or actions, ask the Slate / Ontology owner
which writeback they use (an action, or a Postgres writeback table). The widget does not change:
it only fills its state and fires `submit`; how the row is written is decided in Slate.

### The row

| Column | Type | Content |
|---|---|---|
| `submission_id` | string | Unique id, e.g. `NCW-20261020072124-STMEQV`. New column: an object needs a primary key. |
| `timestamp` | string | `YYYY-MM-DD HH:MM:SS`, the operator's clock, as in the Streamlit app |
| `msn` | string | as typed |
| `produit` | string | from the list, or the typed value for "Autre" |
| `detection` | string | idem |
| `total_defauts` | integer | sum of the quantities |
| `texte_sap` | string | the full text shown on the review screen, to paste in the SAP long text |
| `defauts_json` | string | New column: the defects as structured data (code, sub-code, CDVE, FIN, quantity, severity, line). Lets the pipeline read the defects without parsing the text. Can be left out of the action. |

The first six are the columns of `nc_writer_dataset`, same names and same content.

## 4. Check it works

1. In Slate preview, fill an NC with two defects and press **Soumettre la NC**.
2. The widget shows "NC transmise à Slate (NCW-…)" and the text.
3. The object appears (Object Explorer, or the writeback dataset after its build).

If the widget shows **"Envoi impossible : SlateFunctions.setState / triggerEvent introuvables"**,
your Slate version names these two functions differently. They are used in one place only,
`sendToSlate()` in `nc_writer.js`; the names of the state key and the event are in `CONFIG` at the
top of the file. The NC is not lost when this happens: the text stays on screen with a "Copier"
button.

Note from Palantir's community forum: `SlateFunctions.setState` only changes the widget's own
state; Slate reacts to the **event**. That is why the widget does both, state first, then event.

## 5. Differences from the Streamlit app

Same behaviour, except these fixes:

| Streamlit | Slate widget | Why |
|---|---|---|
| The first FIN of the list is pre-selected | Nothing pre-selected ("— choisir —") | An operator who skips the field recorded a wrong FIN without seeing it |
| "Autre" in the FIN list wrote the word "Autre" as location | "Autre" asks for the location to be typed; save is refused until it is | Same |
| After deleting a defect, the following ones kept their old number (DEF 1 deleted, the list still started at DEF 2) | Lines are renumbered | The SAP text must count from 1 |
| Search is accent-sensitive ("element" does not find "Élément") | Accents ignored | Operators type without accents |
| Ticking CDVE after changing the severity by hand reset it | A severity chosen by hand is kept; otherwise it follows CDVE (10 = MAJEURE) | Keep the operator's choice |
| Copy button of `st.code` | "Copier" button; if the browser blocks copying, the text is selected for Ctrl+C | Clipboard access can be blocked inside the sandbox |
| Quantity limited by the number widget | Same rule (whole number, 1 or more), with a message | |

What it does not do, like the Streamlit app: keep an NC in progress if the page is reloaded.

## 6. Changing something later

- **A code, a FIN list, a product**: edit the arrays at the top of `nc_writer.js` (`NATURES`,
  `FIN_MAPPING`, `PRODUITS`, `DETECTIONS`), paste the file again in the JavaScript tab.
  `tests/check_parity.py` compares them with the Streamlit app; once the Streamlit app is retired,
  the JS file is the reference.
- **The context or action templates**: `CTX_OPTIONS` and `ACT_OPTIONS` in `nc_writer.js`.
- Never type two opening curly braces in any of the three files: Slate reads them as a template.

To check outside Slate:

```
python build_standalone.py
python tests/check_parity.py
npm install playwright-core      # once
node tests/test_ui.js            # CHROMIUM=/path/to/chrome if Chromium is elsewhere
```
