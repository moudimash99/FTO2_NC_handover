"""The agents' JSONL labels -> rows of 04_reference/llm_labels_longtext.csv (same columns), snippet = the parser's text of the line,
so the build uses each label while the line's text stays the same. Appends them (replacing any older label of the same line)."""
import json, glob, os, pandas as pd
S = os.path.dirname(os.path.abspath(__file__)) + "/"
R = "/home/user/FTO2_NC_handover/"
lab_p = R + "04_reference/llm_labels_longtext.csv"
old = pd.read_csv(lab_p, dtype=str, keep_default_na=False, encoding="utf-8-sig")
want = pd.read_csv(S + "to_label.csv", dtype=str, keep_default_na=False)
o = pd.DataFrame([json.loads(l) for f in sorted(glob.glob(S + "out/n*.jsonl")) for l in open(f, encoding="utf-8") if l.strip()])
o["notification_number"] = o.notification_number.astype(str); o["seq"] = o.seq.astype(int).astype(str)
m = want.merge(o, on=["notification_number", "seq"], how="left")
print("lines", len(want), "labelled", int(m.sous_categorie.notna().sum()))
assert m.sous_categorie.notna().all(), "missing labels"
b = lambda v: "True" if str(v).lower() in ("true", "1") else "False"
new = pd.DataFrame({"notification_number": m.notification_number, "seq": m.seq, "snippet": m.text, "llm_sous_categorie": m.sous_categorie,
                    "llm_sous_code": m.sous_code.fillna(""), "llm_confiance": m.confiance, "llm_symptome": m.symptome.fillna(""),
                    "llm_raison": m.raison.fillna(""), "llm_defaut_cable": m.defaut_cable.map(b), "llm_provenance": m.provenance.fillna(""),
                    "llm_code_conflict": m.code_conflict.map(b), "llm_deux_defauts": m.deux_defauts.map(b), "llm_contexte_utile": m.contexte_utile.map(b)})
assert list(new.columns) == list(old.columns), (list(new.columns), list(old.columns))
key = lambda t: t.notification_number + "|" + t.seq
out = pd.concat([old[~key(old).isin(set(key(new)))], new], ignore_index=True)
out.to_csv(lab_p, index=False, encoding="utf-8-sig")
new.to_csv(S + "new_labels.csv", index=False, encoding="utf-8-sig")
print("labels file:", len(old), "->", len(out), "rows")
print(new.llm_sous_categorie.value_counts().head(12).to_string()); print(new.llm_confiance.value_counts().to_dict())
