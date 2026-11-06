"""03_reports/skywise/FTO2_Skywise_installation.zip: every file the Skywise set-up needs (03_reports/skywise/README.md, steps
1 to 5), in one download. The Slate functions (step 6, optional) and the local test pages are left out.

Written again at the end of build/build_all.py, 07_scripts/mft/build_mft.py and 07_scripts/elizabeth/build_elizabeth.py, so it
always holds the latest files. The files' dates inside are fixed: the zip only changes when a file in it changes.

    python3 -I build/install_zip.py
"""
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKY = os.path.join(ROOT, "03_reports", "skywise")
OUT = os.path.join(SKY, "FTO2_Skywise_installation.zip")
TOP = "FTO2_Skywise_installation/"
L3 = "level3_datasets"
NOTE = """FTO2 NC dashboard: the files to set it up in Skywise

Follow README.md, steps 1 to 5. Every file it names is in this zip, at the same place.

  level3_datasets/   the notebook, its code (notebook_kit), the settings (config),
                     the dashboard page (fto2_level23.*, state.json) and its four queries (q_fto2_*.sql)
  mft/               the MFT page
  elizabeth/         the Tableau Elizabeth (optional)
  docs/              how to change a setting once it runs (comment_faire.md, in French)

Not in this zip: the Slate functions (step 6 of README.md, optional) and the local test pages.
"""


def files():
    """(path on disk, path in the zip) of every file of the set-up."""
    out = [(os.path.join(SKY, f), f) for f in ("README.md", "DETAILS.md")]
    for f in ("fto2_pipeline_notebook.ipynb", "q_fto2_nc.sql", "q_fto2_def.sql", "q_fto2_dis.sql", "q_fto2_ref.sql",
              "fto2_level23.css", "fto2_level23.html", "fto2_level23.js", "state.json", "columns.json"):
        out.append((os.path.join(SKY, L3, f), L3 + "/" + f))
    for sub in ("notebook_kit", "config"):
        for d, dirs, names in os.walk(os.path.join(SKY, L3, sub)):
            dirs[:] = sorted(x for x in dirs if x != "__pycache__")
            for n in sorted(names):
                if not n.endswith(".pyc"):
                    p = os.path.join(d, n)
                    out.append((p, os.path.relpath(p, SKY).replace(os.sep, "/")))
    for page in ("mft", "elizabeth"):
        for f in ("fto2_%s.css" % page, "fto2_%s.html" % page, "fto2_%s.js" % page, "state.json"):
            out.append((os.path.join(SKY, page, f), page + "/" + f))
    out.append((os.path.join(ROOT, "docs", "comment_faire.md"), "docs/comment_faire.md"))
    return out


def write(say=print):
    entries = [("READ_ME_FIRST.txt", NOTE.encode("utf-8"))]
    for path, arc in files():
        if not os.path.exists(path):
            say("installation zip: %s missing, zip not written (build that page first)" % arc)
            return None
        with open(path, "rb") as f:
            entries.append((arc, f.read()))
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, data in entries:
            info = zipfile.ZipInfo(TOP + arc, date_time=(2026, 1, 1, 0, 0, 0))   # fixed date: same files, same zip
            info.compress_type, info.external_attr = zipfile.ZIP_DEFLATED, 0o644 << 16
            z.writestr(info, data)
    say("installation zip: %d files, %d KB -> %s" % (len(entries), os.path.getsize(OUT) // 1024, os.path.relpath(OUT, ROOT)))
    return OUT


if __name__ == "__main__":
    write()
