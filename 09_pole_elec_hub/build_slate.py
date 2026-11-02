# -*- coding: utf-8 -*-
"""
Split hub/pole_elec_hub.html into the three parts a Slate widget takes:

    python build_slate.py

Writes slate/hub.html (markup only), slate/hub.css and slate/hub.js (links at the top).
Edit hub/pole_elec_hub.html, then rerun: the three files are rebuilt from it.
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "hub", "pole_elec_hub.html"), encoding="utf-8").read()

css = re.search(r"<style>\n(.*?)</style>", src, re.S).group(1)
js = re.search(r"<body>.*<script>\n(.*?)</script>", src, re.S).group(1)
body = re.search(r"<body>\n(.*?)\n<script>", src, re.S).group(1)

out = os.path.join(HERE, "slate")
os.makedirs(out, exist_ok=True)
for name, text in (("hub.html", body), ("hub.css", css), ("hub.js", js)):
    with open(os.path.join(out, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text.rstrip("\n") + "\n")
    print("slate/" + name, len(text), "chars")
