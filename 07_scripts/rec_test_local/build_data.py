"""Union of the exported NCs with Skywise-like types (liability as array, creation_time as timestamp)."""
import glob, sys, numpy as np, pandas as pd
I, N, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
rd = lambda f: pd.read_csv(f, dtype=str, low_memory=False)
parts = [rd(f'{I}/nc-rec.csv'), rd(f'{I}/fto2_dashboard_data_12.csv'), rd(f'{I}/fto2_dashboard_data_missing_ids_3.csv')]
parts += [pd.read_csv(f, dtype=str, encoding='utf-8-sig', keep_default_na=False, na_values=['']) for f in sorted(glob.glob(f'{N}/split_part_nc_*.csv'))]
D = pd.concat(parts, ignore_index=True).drop_duplicates('notification_no_leading_zeros')
D['liability'] = D['liability'].map(lambda v: None if pd.isna(v) else [x.strip() for x in v.strip('[]').split(',') if x.strip()])
D['creation_time'] = pd.to_datetime(D['creation_time'].str[:19].str.replace('T', ' '), errors='coerce')
D['msn'] = pd.to_numeric(D['msn'], errors='coerce')
D.to_pickle(OUT); print(D.shape)
