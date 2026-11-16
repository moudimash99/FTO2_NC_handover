"""The handover package: one folder (and its zip) with what the team keeps, split in two.

    python3 -I handover/make_package.py [output folder]          (default: handover/dist)

    FTO2_NC_Dashboard/
      README.txt
      for_users/          the guides for the people who read the dashboard, keep its settings, give access (PDF)
      for_developers/     the technical manuals (PDF, English and French), the Skywise installation file, and the source

The source is a copy of the files of this repository listed in SOURCE below, without the work folders of the project
(history, trials, exercises). Before writing, every text file and every PDF of the package is searched for the words of
MUST_NOT_APPEAR and NAMES; one found stops the script with the file and the line.

The guides are taken as they are in docs/guides/pdf/: build them first (python3 -I docs/guides/build_guides.py).
"""
import fnmatch
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "FTO2_NC_Dashboard"
PDF = os.path.join(ROOT, "docs", "guides", "pdf")

USERS = ["FTO2_NC_Dashboard_User_Guide.pdf", "FTO2_NC_Dashboard_Settings_Guide.pdf", "FTO2_NC_Dashboard_Access_Guide.pdf"]
DEVELOPERS = ["FTO2_NC_Dashboard_Technical_Manual_EN.pdf", "FTO2_NC_Dashboard_Manuel_Technique_FR.pdf"]
INSTALL = os.path.join(ROOT, "03_reports", "skywise", "FTO2_Skywise_installation.zip")

# the source: (path in the repository, path in source/); a folder is copied whole, less SKIP
SOURCE = [
    ("README.md", "README.md"), ("requirements.txt", "requirements.txt"),
    ("fto2", "fto2"), ("config", "config"), ("build", "build"), ("tests", "tests"),
    ("07_scripts/mft", "07_scripts/mft"), ("07_scripts/elizabeth", "07_scripts/elizabeth"),
    ("08_tools/nc_writer_slate", "08_tools/nc_writer_slate"),
    ("docs/config.md", "docs/config.md"), ("docs/logic.md", "docs/logic.md"), ("docs/front_end.md", "docs/front_end.md"),
    ("docs/part_prices.md", "docs/part_prices.md"), ("docs/comment_faire.md", "docs/comment_faire.md"),
    ("docs/fr", "docs/fr"), ("docs/guides", "docs/guides"),
    ("03_reports/skywise", "03_reports/skywise"),
    ("04_reference", "04_reference"), ("05_outputs", "05_outputs"), ("06_input_data", "06_input_data"),
]
SKIP = ["__pycache__", "*.pyc", ".DS_Store", "build/artifacts", "build/build_report.json", "node_modules", "docs/guides/.guide_*",
        "05_outputs/archive", "05_outputs/CNQ_*",                                   # work notes, not read by the code
        "06_input_data/REC_findings_note_unverified.md", "06_input_data/slate_hub_export_*", "06_input_data/*.rar"]

# the tools used to write the code, and the names of the people of the project; names are not searched in the data the
# code reads (NC texts name the people who wrote them)
MUST_NOT_APPEAR = re.compile(r"claude|anthropic|sonnet|\bopus\b|co-authored", re.I)
NAMES = re.compile(r"mohammad|emmanuel|didier|karine", re.I)
DATA = ("source/04_reference/", "source/05_outputs/", "source/06_input_data/", "source/tests/golden/")
TEXT = (".py", ".js", ".html", ".css", ".md", ".txt", ".csv", ".json", ".sql", ".ipynb", ".mermaid", ".jsx", ".yml", ".yaml")


def skipped(rel):
    """True for a file of the repository that stays out of the package (SKIP)."""
    parts = rel.split("/")
    for pat in SKIP:
        if "/" in pat:
            if rel == pat or rel.startswith(pat + "/") or fnmatch.fnmatch(rel, pat):
                return True
        elif any(fnmatch.fnmatch(p, pat) for p in parts):
            return True
    return False


def copy_source(dest):
    n = 0
    for src, to in SOURCE:
        path = os.path.join(ROOT, src)
        if not os.path.exists(path):
            sys.exit("not found in the repository: " + src)
        if os.path.isfile(path):
            items = [(path, to)]
        else:
            items = []
            for d, dirs, files in os.walk(path):
                for f in files:
                    full = os.path.join(d, f)
                    rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
                    if not skipped(rel):
                        items.append((full, to + rel[len(src):]))
        for full, rel in items:
            out = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copy2(full, out)
            n += 1
    return n


def text_of(path):
    if path.endswith(".pdf"):
        r = subprocess.run(["pdftotext", "-q", path, "-"], capture_output=True, text=True)
        return r.stdout
    if path.endswith(".zip"):
        out = []
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if n.endswith(TEXT):
                    out.append("== %s\n%s" % (n, z.read(n).decode("utf-8", "replace")))
        return "\n".join(out)
    if path.endswith(TEXT):
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    return ""


def scan(top):
    """Every place where a word of MUST_NOT_APPEAR is found: [(file, line number, line)]."""
    found = []
    for d, dirs, files in os.walk(top):
        for f in files:
            path = os.path.join(d, f)
            rel = os.path.relpath(path, top).replace(os.sep, "/")
            data = any(("/" + rel).find("/" + x) >= 0 for x in DATA)
            for i, line in enumerate(text_of(path).splitlines(), 1):
                if MUST_NOT_APPEAR.search(line) or (not data and NAMES.search(line)):
                    found.append((rel, i, line.strip()[:160]))
    return found


README = """FTO2 NC dashboard
=================

for_users/
  FTO2_NC_Dashboard_User_Guide.pdf       Reading the dashboard and the MFT page. For everyone.
  FTO2_NC_Dashboard_Settings_Guide.pdf   What to keep up to date (tables, downloads, the yearly change) and how
                                         to run the update. For the person in charge of the dashboard.
  FTO2_NC_Dashboard_Access_Guide.pdf     Who needs which rights in Skywise, and the checks before the dashboard
                                         changes hands. For the owner of the dashboard in Skywise.

for_developers/
  FTO2_NC_Dashboard_Technical_Manual_EN.pdf   How it works, how to keep it working, how to change it.
  FTO2_NC_Dashboard_Manuel_Technique_FR.pdf   The same, in French.
  FTO2_Skywise_installation.zip               Every file the Skywise set-up needs (technical manual, chapter 7).
  source/                                     The code, the settings as first installed, the checks and their
                                              reference data (technical manual, chapter 8).

The dashboard itself is a Skywise (Slate) application: open it from its link.
"""


def main():
    out = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "handover", "dist"))
    top = os.path.join(out, NAME)
    if os.path.exists(top):
        shutil.rmtree(top)
    users, devs = os.path.join(top, "for_users"), os.path.join(top, "for_developers")
    os.makedirs(users)
    os.makedirs(devs)
    missing = [f for f in USERS + DEVELOPERS if not os.path.exists(os.path.join(PDF, f))]
    if missing:
        sys.exit("guide(s) not built: %s (python3 -I docs/guides/build_guides.py)" % ", ".join(missing))
    for f in USERS:
        shutil.copy2(os.path.join(PDF, f), users)
    for f in DEVELOPERS:
        shutil.copy2(os.path.join(PDF, f), devs)
    shutil.copy2(INSTALL, devs)
    n = copy_source(os.path.join(devs, "source"))
    with open(os.path.join(top, "README.txt"), "w", encoding="utf-8") as f:
        f.write(README)
    found = scan(top)
    if found:
        for path, i, line in found[:200]:
            print("  %s:%d: %s" % (path, i, line))
        sys.exit("%d line(s) to correct before the package can be handed over (above)" % len(found))
    z = os.path.join(out, NAME + ".zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for d, dirs, files in os.walk(top):
            dirs.sort()
            for f in sorted(files):
                full = os.path.join(d, f)
                zf.write(full, os.path.relpath(full, out))
    print("package: %s (%d source files), %s (%d MB)" % (top, n, z, os.path.getsize(z) // (1024 * 1024)))


if __name__ == "__main__":
    main()
