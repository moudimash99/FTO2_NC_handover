import runpy, sys, pandas as pd
sys.path.insert(0, sys.argv[1])                 # mock foundry package
import foundry.transforms as ft
ft.DATA = pd.read_pickle(sys.argv[2])
runpy.run_path(sys.argv[3], run_name="__main__")
print("dataset queries:", ft.Dataset.calls)
