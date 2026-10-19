import sys, re, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70); pd.set_option("display.max_rows", 200)
D = sys.argv[1]
wo = pd.read_pickle(D+"/wo.pkl")
s3 = wo[wo.order_type=="S03"].copy()
print("S03 ops", len(s3), "orders", s3.order_number.nunique())
print(s3.operation_short_text.value_counts().head(40).to_string())
print(s3.work_center_description.value_counts().head(20).to_string())
print(s3.material_header_description.value_counts().head(15).to_string())
print(s3.control_key.value_counts().to_dict(), s3.work_center_category.value_counts().to_dict())
# does any text mention a 9-digit NC number?
txt = (s3.operation_short_text.fillna("")+" "+s3.operation_long_text.fillna("")+" "+s3.material_header_description.fillna(""))
m = txt.str.findall(r"\b(2\d{8})\b")
print("S03 ops with 9-digit 2xxxxxxxx number in text:", (m.str.len()>0).sum())
allwo = wo.operation_short_text.fillna("")+" "+wo.operation_long_text.fillna("")
print("any op with NC-like number:", allwo.str.contains(r"\b2\d{8}\b").sum())
print(allwo[allwo.str.contains(r"\b2\d{8}\b")].head(10).to_string())
# one example order
o = s3.order_number.value_counts().index[5]
print(s3[s3.order_number==o][["operation_number","operation_short_text","work_center","work_center_description","control_key","labor_standard_value","processing_time","total_activity_to_be_confirmed","actual_start_execution_date","actual_finish_execution_time"]].to_string())
