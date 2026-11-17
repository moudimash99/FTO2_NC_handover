# Test: MFT actions kept in one object of the NC writer

The MFT actions are kept in one object of the object type "a30 Nc Writer Dataset": the object whose Msn is `MFT-ACTIONS`,
its Texte Sap holding all the actions as JSON text. This box checks the two ways: writing it, and reading it back.

## Writing (same route as the NC writer)

1. On a test page, add a Code Sandbox named `w_store`. Paste `store_test.html` and `store_test.js`. State: `{}`.
   Interaction tab, Events: `["save"]`.
2. Variables panel: add `v_store`, value `{}`.
3. Events panel: when `w_store.save` happens, `v_store.set`, code `return ` + the binding of `slEventValue` + `;`.
4. Add an Action widget with the action of the object type, default parameters: Detection, Produit, Msn, Texte Sap
   from `v_store.detection`, `v_store.produit`, `v_store.msn`, `v_store.texte_sap` (text, between quotes), Total Defauts
   from `v_store.total_defauts` (no quotes) — the same as for the NC writer, with `v_store` instead of `v_submission`.
5. Type a title, press **1**, then **2**: the action's form shows Msn `MFT-ACTIONS`. Press Submit. A new object exists.

If the object type has a "modify" action, it can update the same object instead; without one, each save adds an object and
the page reads the one saved last.

## Reading

The box reads the state key `rows`. Give it the objects in one of two ways, whichever exists:

- **A query**, if the objects have a dataset that is synced to Postgres (the object type's "Datasources" tab): a query
  `q_mft_store` on that table, and in the box's State `{"rows": "` + binding of `q_mft_store` + `"}`.
- **An object set** in Slate on the object type, and its properties bound the same way to `rows`.

Reload the page: the line "Read:" says how many rows arrived and whether the store was found, and the grey box lists the
column names as Slate gives them. Send a photo of the box.
