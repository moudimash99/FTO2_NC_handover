"""Executes the REC test notebook cell by cell on a Jupyter kernel, with the stand-in foundry.transforms.
Usage: python3 -I runner.py <rec_test_local dir> <skywise_mock.pkl> <rec_rule_test.ipynb> <executed.ipynb> [full]"""
import os, sys, json
import nbformat
from nbclient import NotebookClient

mock, data, nb_in, nb_out = sys.argv[1:5]
os.environ["PYTHONPATH"] = os.path.abspath(mock)
os.environ["REC_MOCK_DATA"] = os.path.abspath(data)
nb = nbformat.read(nb_in, as_version=4)
if "full" in sys.argv[5:]:
    for c in nb.cells:
        c.source = c.source.replace("FULL_SCAN = False", "FULL_SCAN = True")
NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": os.getcwd()}}).execute()
nbformat.write(nb, nb_out)
for c in nb.cells:
    if c.cell_type != "code":
        continue
    for o in c.outputs:
        if o.output_type == "stream":
            print(o.text, end="")
        elif o.output_type in ("display_data", "execute_result"):
            print(o.data.get("text/plain", ""))
        elif o.output_type == "error":
            print("ERROR", o.ename, o.evalue)
    print("-" * 40)
