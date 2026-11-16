import os, sys, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # the repository: the parser is fto2/parser
from fto2.parser import fto2_logic as L
pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
d=sys.argv[1]
D=pd.read_csv(f'{d}/dash.csv',dtype=str,low_memory=False)
M=pd.read_csv(f'{d}/missing_ids.csv',dtype=str,low_memory=False)
A=pd.concat([D,M],ignore_index=True).drop_duplicates('notification_no_leading_zeros')
df=L.build_defects(A)
df.to_pickle(f'{sys.argv[2]}/defects_v48.pkl')
print(df.shape); print(list(df.columns))
