# NC writing tool in Slate (Code Sandbox widget)

The Streamlit app `reference/app_streamlit.py` ("NC · Saisie Structurée") rebuilt as plain
HTML, CSS and JavaScript, so it runs inside a Slate **Code Sandbox** widget. Same screens, same
codes, same FIN suggestions, same SAP text, character for character (`tests/check_parity.py`).

```
operator fills the NC in the widget
      |
"Soumettre la NC"  ->  widget state = { submission: row }  +  event "submit"
      |
your Slate JS function, run on that event  ->  appends the row to nc_writer_dataset
```

The widget does not write anything itself: it hands the row over and fires the event. How the
row reaches the dataset is decided in Slate.

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
5. Size: the layout is drawn for a widget **1316 px wide** (steps on the left, the SAP text on
   the right). Below 1000 px the SAP text goes under the steps. Height: about 900 px; longer
   screens scroll inside the widget.

Preview the app: the "Nouvelle NC" screen should appear. If the widget stays on "Chargement…",
open the browser console (F12): the JavaScript did not run.

## 3. Save the NC

On "Soumettre la NC" the widget calls, in this order:

```js
SlateFunctions.setState({ submission: row });
SlateFunctions.triggerEvent("submit");
```

In Slate, add a handler on the event `w_nc_writer.submit` that runs your JS function. The row is in
the widget state, `w_nc_writer.state.submission` (with the usual double curly braces in a Slate
binding). It has the six columns of `nc_writer_dataset`, same names and same content as the
Streamlit app, plus two:

| Column | Type | Content |
|---|---|---|
| `submission_id` | string | **New.** Unique id, e.g. `NCW-20261020072124-STMEQV`. Lets you spot a row written twice. Drop it if the dataset should keep exactly its six columns. |
| `timestamp` | string | `YYYY-MM-DD HH:MM:SS`, the operator's clock, as in the Streamlit app |
| `msn` | string | as typed |
| `produit` | string | from the list, or the typed value for "Autre" |
| `detection` | string | idem |
| `total_defauts` | integer | sum of the quantities |
| `texte_sap` | string | the full text shown on the review screen, with its line breaks |
| `defauts_json` | string | **New.** The defects as structured data (code, sub-code, CDVE, FIN, quantity, severity, line), as JSON text. Lets the pipeline read the defects without parsing the text. Drop it if not wanted. |

The names of the state key and the event are in `CONFIG` at the top of `nc_writer.js`.

## 4. Check it works

1. In Slate preview, fill an NC with two defects and press **Soumettre la NC**.
2. The widget shows "NC transmise à Slate (NCW-…)" and the text.
3. The row appears in `nc_writer_dataset`.

If the widget shows **"Envoi impossible : SlateFunctions.setState / triggerEvent introuvables"**,
your Slate version names these two functions differently. They are used in one place only,
`sendToSlate()` in `nc_writer.js`. The NC is not lost when this happens: the text stays on screen with a "Copier"
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
| Templates of context and action in a drop-down, cut when long | Clickable chips showing the whole sentence; click again to remove | Readable, one click |
| Text SAP only visible at the end | Built live on the right of every screen, with the counts of defects and majors | The operator sees what will be sent |

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
