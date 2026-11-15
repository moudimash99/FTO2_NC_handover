# Testing the NC writer's action, one small step at a time

The NC writer hands each NC over as six values. The action stores them as one object (Timestamp, Msn, Produit, Detection,
Total Defauts, Texte Sap). These files check that path with test values, before the real NC writer is plugged in.

The value to give to each field of the action in step 1 (the widget is named `w_nc_writer`):

| Field of the action | Value |
|---|---|
| Timestamp | `{{w_nc_writer.state.submission.timestamp}}` |
| Msn | `{{w_nc_writer.state.submission.msn}}` |
| Produit | `{{w_nc_writer.state.submission.produit}}` |
| Detection | `{{w_nc_writer.state.submission.detection}}` |
| Total Defauts | `{{w_nc_writer.state.submission.total_defauts}}` |
| Texte Sap | `{{w_nc_writer.state.submission.texte_sap}}` |

## Step 1: a state typed by hand, the action's own button

Checks the action and its six fields. No code.

1. On a test page, add a Code Sandbox and name it `w_nc_writer`. Leave its HTML, CSS and JavaScript empty.
2. Paste the content of `step1_state.json` into its State box.
3. Add the action. Give each field its value from the table above.
4. The six fields of the action show the test values. Press the action's submit button.
5. One new object exists, with Msn `TEST`.

The Timestamp is the object's key: to try again, change the seconds of `timestamp` in the State box first.

## Step 2: the state filled by code

Checks that a value set by code reaches the action. The values the code writes all say CODE and change at every click,
so they cannot be mistaken for those typed in the State box.

1. Paste `step2_dummy.html` into the HTML tab and `step2_dummy.js` into the JavaScript tab.
2. Press **1. Remplir avec les valeurs du code**. The box says which values it sent (Msn `CODE-` and the time).
3. Look at the action's form: does it show `CODE-...`? Press the action's submit button.
4. Open the new object. Msn `CODE-...`: the action takes what the code writes. The values of the State box: it does not.

The State box of the editor only holds the starting values: it never shows what the code writes while the page runs.

## Step 3: the event fills a variable, the action reads the variable

What the code writes with `setState` stays inside the box: the other widgets only see the values typed in the State box.
The row leaves the box with the event. Button 2 sends the event `submit` with the row as its value; the event sets a Slate
variable; the action reads that variable.

**A. The box sends an event named `submit`**

1. Click the widget `w_nc_writer`, then its tab **Interaction**.
2. In **Events**, replace `["event1"]` by `["submit"]`.

**B. A variable to hold the row**

1. Open the **Variables** panel of the editor.
2. Add a variable. Name: `v_submission`. Value: `{}`.

**C. An event that fills the variable**

1. Open the **Events** panel of the editor.
2. Add an event.
3. Trigger (the event to listen to): `w_nc_writer.submit`. It is in the list once A is done.
4. Action: `v_submission.set`.
5. Code: `return {{slEventValue}};`

**D. The action reads the variable**

Click the action widget. In its default parameters, give each field its value:

| Field | Value |
|---|---|
| Detection | `"{{v_submission.detection}}"` |
| Produit | `"{{v_submission.produit}}"` |
| Msn | `"{{v_submission.msn}}"` |
| Texte Sap | `"{{v_submission.texte_sap}}"` |
| Total Defauts | `{{v_submission.total_defauts}}` |

**E. Test**

1. Press **1. Remplir avec les valeurs du code**, then **2. Envoyer l'evenement submit**.
2. The action's form shows `CODE-...`. Press its submit button.
3. The new object has Msn `CODE-...`.

If the form stays empty after button 2, replace the code of C by `return {{w_nc_writer.state.submission}};` and try again.

## Step 4: the same event sends the action

Checks that nobody has to press the action's button.

1. In the **Events** panel, add a second event. Trigger: `v_submission.changed` (or `w_nc_writer.submit`). Action: the
   submit of the action widget.
2. Press 1, then 2. One more object, with no other click.

## Then: the real NC writer

Replace the HTML, CSS and JavaScript of the widget by `nc_writer.html`, `nc_writer.css` and `nc_writer.js` (the folder
above). Same widget name, same event, same six fields: nothing else changes.

Afterwards, delete the test objects (Msn `TEST`).
