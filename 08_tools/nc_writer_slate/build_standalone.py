# -*- coding: utf-8 -*-
"""
Assemble nc_writer_standalone.html from the three Slate tabs (HTML, CSS, JS), to try the tool
outside Slate or keep an offline copy. The three source files stay the reference.

    python build_standalone.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
read = lambda name: open(os.path.join(HERE, name), encoding="utf-8").read()

page = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NC FTO2 · Saisie</title>
<style>
{css}</style>
</head>
<body>
{html}<script>
{js}</script>
</body>
</html>
""".format(css=read("nc_writer.css"), html=read("nc_writer.html"), js=read("nc_writer.js"))

with open(os.path.join(HERE, "nc_writer_standalone.html"), "w", encoding="utf-8") as f:
    f.write(page)
print("wrote nc_writer_standalone.html")
