"""The dashboard page's template, with its calculations put in.

The page is build/templates/dashboard.html. Its calculations (selection, production, targets and forecast, cost explanation,
alarms) are in build/templates/model.js, because the Slate functions run the same code. Every script that needs the page
reads it with read(), which puts model.js in place of the line holding /*@@MODEL@@*/.
"""
import os

TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
MARK = "/*@@MODEL@@*/"


def model():
    """The calculations shared by the page and the Slate functions (build/templates/model.js)."""
    with open(os.path.join(TEMPLATES, "model.js"), encoding="utf-8") as f:
        return f.read()


def read(name="dashboard.html"):
    """A page template, with model.js in place of its /*@@MODEL@@*/ line."""
    with open(os.path.join(TEMPLATES, name), encoding="utf-8") as f:
        text = f.read()
    i = text.find(MARK)
    if i < 0:
        return text
    start, end = text.rfind("\n", 0, i) + 1, text.find("\n", i)
    return text[:start] + model().rstrip("\n") + text[end:]
