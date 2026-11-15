# Testing the NC writer's action, one small step at a time

The NC writer hands each NC over as six values. The action stores them as one object (Timestamp, Msn, Produit, Detection,
Total Defauts, Texte Sap). These files check that path with test values, before the real NC writer is plugged in.

The value to give to each field of the action (the widget is named `w_nc_writer`):

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

## Step 3: the event sends the action

Checks that nobody has to press the action's button.

1. In the widget's Interaction tab, put `["submit"]` in Events.
2. In the Events panel: when `w_nc_writer.submit` happens, submit the action.
3. Press 1, then **2. Envoyer l'evenement submit**. One more object, with no other click.

## Then: the real NC writer

Replace the HTML, CSS and JavaScript of the widget by `nc_writer.html`, `nc_writer.css` and `nc_writer.js` (the folder
above). Same widget name, same event, same six fields: nothing else changes.

Afterwards, delete the test objects (Msn `TEST`).
