# MFT page in Slate: everything to copy

In the MFT Slate app, in this order. On GitHub, each grey box has a copy button at its top right.

## 1. A test query, to find the ontology's name (delete it afterwards)

Queries panel, **+**. Source: **foundry**. Paste in the editor, then press **Test**:

```json
{
  "path": "api/v2/ontologies",
  "method": "GET",
  "extractors": { "result": "$" }
}
```

In the answer, note the **apiName** of your ontology. If there are several, take the one whose **displayName** is the name
shown at the top left of Ontology Manager.

If the answer is "not found": change the path to `v2/ontologies` (without `api/`), and do the same in step 2.

## 2. The query `q_fto2_mft_store`

It replaces the earlier one of that name (the Postgres one). Name: `q_fto2_mft_store`. Source: **foundry**.

In the text below, replace:
- `ONTOLOGY` with the apiName of step 1;
- `OBJECT_TYPE` with the API name of the object type "a30 Nc Writer Dataset" (Ontology Manager, its overview page);
- `msn`, only if the API name of its property Msn is something else (Ontology Manager, its Properties).

```json
{
  "path": "api/v2/ontologies/ONTOLOGY/objects/OBJECT_TYPE/search",
  "method": "POST",
  "bodyJson": {
    "where": { "type": "eq", "field": "msn", "value": "MFT-ACTIONS" },
    "pageSize": 100
  },
  "extractors": { "result": "$" }
}
```

Press **Test**: an empty list (`"data": []`) is right while nothing is saved yet. Then **Update**.

## 3. The page

In the sandbox `w_fto2_mft`, paste the three files of this folder into its three tabs: `fto2_mft.css`, `fto2_mft.html`,
`fto2_mft.js` (1,453 lines).

Its state box:

```json
{
  "nc": "{{q_fto2_nc}}",
  "def": "{{q_fto2_def}}",
  "ref": "{{q_fto2_ref}}",
  "reglages": "{{q_fto2_set_targets}}",
  "store": "{{q_fto2_mft_store}}"
}
```

Its **Interaction** tab, **Events**:

```json
["save"]
```

## 4. The variable

Variables panel, **+**. Name: `v_mft_store`. Value:

```json
{}
```

## 5. Event 1: the page's save fills the variable

Events panel, **+**. Trigger: `w_fto2_mft.save`. Action: `v_mft_store.set`. Code:

```
return {{slEventValue}};
```

## 6. The Action widget

Under the page, add an **Action widget**. Action: **Create or Modify a30 Nc Writer Dataset**. Its default parameters (leave
the key, Timestamp, empty: the action fills it):

Detection:
```
"{{v_mft_store.detection}}"
```
Produit:
```
"{{v_mft_store.produit}}"
```
Msn:
```
"{{v_mft_store.msn}}"
```
Texte Sap:
```
"{{v_mft_store.texte_sap}}"
```
Total Defauts (no quotes: a number):
```
{{v_mft_store.total_defauts}}
```

## 7. Event 2: each change of the variable saves

Events panel, **+**. Trigger: the variable `v_mft_store` **changed**. Action: the Action widget, **Submit**. No code.

## 8. Event 3: once saved, read it back

Events panel, **+**. Trigger: the Action widget, **submit succeeded**. Action: **run** the query `q_fto2_mft_store`. No code.

## 9. Test

1. Reload the page: no message "Le navigateur bloque…".
2. Tab *Suivi des actions*: change one action's weekly point. A grey note "Enregistrement…" shows, then goes within a few
   seconds.
3. Ontology Manager: one object with Msn `MFT-ACTIONS`.
4. Reload the page: the change is still there.

If the page says "Enregistrement impossible : la requête q_fto2_mft_store n'a pas répondu", the query does not answer:
check step 2 (press Test there).
