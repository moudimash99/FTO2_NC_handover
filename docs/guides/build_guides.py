"""Make the guides (PDF) from their sources in this folder.

    python3 -I docs/guides/build_guides.py [name ...]        (no name: every guide)

A guide is one HTML file here (user_guide.html, settings_guide.html...): a first comment with its title lines, then its
text as sections (h2, h3, tables, figures). This script adds the cover (a page of its own, not numbered), the contents with
their page numbers and the print layout (guides.css), and prints the guide to docs/guides/pdf/ with Chromium (render.js). The figures are screenshots of the
pages built on the laptop, made by screens.js into img/.

The first comment of a source:

    <!--
    title: FTO2 NC dashboard          the big title of the cover
    subtitle: User guide              under it
    kicker: FTO2 · Quality            the small line above the title
    file: FTO2_NC_Dashboard_User_Guide   the PDF's name
    for: Everyone who reads the dashboard
    version: November 2026
    contents: Contents                the title of the contents page (in the guide's language)
    depth: 2                          1: the contents list the chapters; 2: their sections too
    lang: en
    -->

Needs Node with Playwright (as the page checks) and the Python package pypdf.
"""
import html
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "pdf")
GUIDES = ["user_guide", "settings_guide", "access_guide", "technical_manual.en", "technical_manual.fr"]


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def front(text, name):
    m = re.match(r"\s*<!--(.*?)-->", text, re.S)
    if not m:
        sys.exit("%s: the first comment with the title lines is missing" % name)
    meta = {}
    for line in m.group(1).strip().splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    for k in ("title", "subtitle", "file"):
        if k not in meta:
            sys.exit("%s: the first comment has no line '%s'" % (name, k))
    return meta, text[m.end():]


def headings(body, depth):
    """The body with an id on each chapter (h2) and section (h3), and the list [(level, id, number, text)] for the contents."""
    out, n2, n3 = [], 0, 0

    def one(m):
        nonlocal n2, n3
        tag, attrs, inner = m.group(1), m.group(2) or "", m.group(3)
        plain = 'class="plain"' in attrs
        text = re.sub(r"<[^>]+>", "", inner).strip()
        if tag == "h2":
            if not plain:
                n2, n3 = n2 + 1, 0
            num = "" if plain else str(n2)
        else:
            if not plain:
                n3 += 1
            num = "" if plain else "%d.%d" % (n2, n3)
        hid = "s-" + (num.replace(".", "-") or re.sub(r"\W+", "-", text.lower()).strip("-"))
        if tag == "h2" or (depth >= 2 and not plain):
            out.append((1 if tag == "h2" else 2, hid, num, text))
        return '<%s id="%s"%s>%s</%s>' % (tag, hid, attrs, inner, tag)
    body = re.sub(r"<(h2|h3)((?:\s[^>]*)?)>(.*?)</\1>", one, body, flags=re.S)
    return body, out


def cover_html(meta):
    """The cover, a page of its own with no margin."""
    css = read(os.path.join(HERE, "guides.css"))
    rows = ['<dt>%s</dt><dd>%s</dd>' % (html.escape(k), html.escape(meta[v])) for k, v in
            ((meta.get("label_for", "For"), "for"), (meta.get("label_version", "Version"), "version")) if meta.get(v)]
    return ('<!doctype html><html lang="%s"><head><meta charset="utf-8"><style>%s @page { margin: 0; } body { margin: 0; }</style></head><body>'
            '<section class="cover"><div class="band"></div><div class="kicker">%s</div><h1>%s</h1><div class="sub">%s</div>'
            '<dl class="meta">%s</dl></section></body></html>'
            % (meta.get("lang", "en"), css, html.escape(meta.get("kicker", "")), html.escape(meta["title"]), html.escape(meta["subtitle"]), "".join(rows)))


def page_html(meta, body, toc, pages=None, with_toc=True):
    css = read(os.path.join(HERE, "guides.css"))
    contents = ""
    if with_toc:
        items = "".join('<li class="l%d"><span class="n">%s</span><a href="#%s">%s</a><span class="dots"></span><span class="pg">%s</span></li>'
                        % (lv, num, hid, html.escape(text), (pages or {}).get(hid, "0")) for lv, hid, num, text in toc)
        contents = '<section class="toc"><h2 class="plain">%s</h2><ol>%s</ol></section>' % (html.escape(meta.get("contents", "Contents")), items)
    return ('<!doctype html><html lang="%s"><head><meta charset="utf-8"><title>%s · %s</title><style>%s</style></head><body>%s<main>%s</main></body></html>'
            % (meta.get("lang", "en"), html.escape(meta["title"]), html.escape(meta["subtitle"]), css, contents, body))


def render(text, pdf, footer):
    """Print an HTML text to a PDF. The page is written beside the sources so that img/ is found."""
    fd, tmp = tempfile.mkstemp(suffix=".html", dir=HERE, prefix=".guide_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        r = subprocess.run(["node", os.path.join(HERE, "render.js"), tmp, pdf, footer], capture_output=True, text=True)
        if r.returncode:
            sys.exit("render.js failed:\n" + r.stderr[-1500:])
    finally:
        os.remove(tmp)


def page_texts(pdf):
    from pypdf import PdfReader
    return [re.sub(r"\s+", "", p.extract_text() or "") for p in PdfReader(pdf).pages]


def build(name):
    src = os.path.join(HERE, name + ".html")
    meta, body = front(read(src), name)
    missing = [m for m in re.findall(r'<img[^>]+src="([^"]+)"', body) if not os.path.exists(os.path.join(HERE, m))]
    if missing:
        sys.exit("%s: figure(s) not found: %s (run: node docs/guides/screens.js)" % (name, ", ".join(sorted(set(missing)))))
    body, toc = headings(body, int(meta.get("depth", "2")))
    footer = "%s · %s" % (meta["title"], meta["subtitle"])
    os.makedirs(OUT, exist_ok=True)
    pdf = os.path.join(OUT, meta["file"] + ".pdf")
    with tempfile.TemporaryDirectory() as tmp:
        # 1. without the contents: on which page each chapter and section starts
        a = os.path.join(tmp, "a.pdf")
        render(page_html(meta, body, toc, with_toc=False), a, footer)
        texts, at, start = page_texts(a), {}, 0
        for lv, hid, num, text in toc:
            want = re.sub(r"\s+", "", num + html.unescape(text))
            found = next((i for i in range(start, len(texts)) if want in texts[i]), None)
            if found is None:
                sys.exit("%s: the heading '%s %s' was not found in the printed pages" % (name, num, text))
            at[hid], start = found, found
        # 2. with the contents: how many pages they take
        b = os.path.join(tmp, "b.pdf")
        render(page_html(meta, body, toc), b, footer)
        shift = len(page_texts(b)) - len(texts)
        # 3. the guide, with the page numbers in its contents, behind its cover (a page of its own, not numbered)
        c, g = os.path.join(tmp, "cover.pdf"), os.path.join(tmp, "guide.pdf")
        render(page_html(meta, body, toc, {hid: str(p + 1 + shift) for hid, p in at.items()}), g, footer)
        render(cover_html(meta), c, "--cover")
        from pypdf import PdfWriter
        out = PdfWriter()
        out.append(c)
        out.append(g)
        out.add_metadata({"/Title": "%s - %s" % (meta["title"], meta["subtitle"]), "/Author": meta.get("kicker", ""), "/Creator": "", "/Producer": ""})
        with open(pdf, "wb") as f:
            out.write(f)
    from pypdf import PdfReader
    print("%-24s -> %s (%d pages, %d KB)" % (name, os.path.relpath(pdf, os.path.dirname(os.path.dirname(HERE))), len(PdfReader(pdf).pages), os.path.getsize(pdf) // 1024))


def main():
    names = sys.argv[1:] or [g for g in GUIDES if os.path.exists(os.path.join(HERE, g + ".html"))]
    for n in names:
        build(n)


if __name__ == "__main__":
    main()
