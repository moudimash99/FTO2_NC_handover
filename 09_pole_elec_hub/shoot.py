# -*- coding: utf-8 -*-
"""
Take preview screenshots of the built hub pages (needs Playwright + Chromium).

    python shoot.py [width] [height] [only]

Writes screenshots/<page>.png (full page), screenshots/<page>_hover.png (one tile hovered)
and, after a full run at 1440 px, screenshots/overview.png (the five pages side by side).
"""
import glob, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
W = int(sys.argv[1]) if len(sys.argv) > 1 else 1440
H = int(sys.argv[2]) if len(sys.argv) > 2 else 900
ONLY = sys.argv[3] if len(sys.argv) > 3 else ""
HOVER = {"1": ".tile[data-id=cnqd]", "2": "[data-id=cnqd] .comp", "3": ".row[data-id=cnqd]", "4": "[data-id=cnqd] .pb-btn", "5": ".card[data-id=cnqd]"}

os.makedirs(os.path.join(HERE, "screenshots"), exist_ok=True)
with sync_playwright() as p:
    kw = {"executable_path": CHROME} if os.path.exists(CHROME) else {}
    b = p.chromium.launch(**kw)
    for f in sorted(glob.glob(os.path.join(HERE, "pole_elec_hub_*.html"))):
        name = os.path.basename(f)[:-5]
        if ONLY and ONLY not in name:
            continue
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto("file://" + f, wait_until="networkidle")
        pg.wait_for_timeout(1900)
        suffix = "" if W == 1440 else "_%d" % W
        pg.screenshot(path=os.path.join(HERE, "screenshots", name + suffix + ".png"), full_page=True)
        sel = HOVER.get(name.split("_")[3])
        if sel and not suffix and pg.query_selector(sel):
            pg.hover(sel)
            pg.wait_for_timeout(500)
            pg.screenshot(path=os.path.join(HERE, "screenshots", name + "_hover.png"), full_page=False)
        if not suffix and name.split("_")[3] in ("2", "5"):
            dk = b.new_page(viewport={"width": W, "height": H}, color_scheme="dark")
            dk.goto("file://" + f, wait_until="networkidle")
            dk.wait_for_timeout(1200)
            dk.screenshot(path=os.path.join(HERE, "screenshots", name + "_dark.png"), full_page=False)
            dk.close()
        sw = pg.evaluate("document.documentElement.scrollWidth")
        print(name, "scrollWidth", sw, "errors", errors)
        pg.close()
    b.close()


NAMES = ["Planche · formboard, dark", "Schéma · wiring diagram, paper or blueprint", "Connecteur · connector face, dark",
         "Panneau · cockpit panel, dark", "Faisceau · light, corporate"]


def overview():
    from PIL import Image, ImageDraw, ImageFont
    shots = sorted(glob.glob(os.path.join(HERE, "screenshots", "pole_elec_hub_*_hover.png")))
    if len(shots) != 5:
        return
    tw, th, gap, cap = 720, 450, 28, 44
    W2, H2 = 2 * tw + 3 * gap, 3 * (th + cap) + 4 * gap
    sheet = Image.new("RGB", (W2, H2), (238, 240, 243))
    d = ImageDraw.Draw(sheet)
    font = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
    f1 = ImageFont.truetype(font, 22) if os.path.exists(font) else ImageFont.load_default()
    f2 = ImageFont.truetype(font.replace("SemiBold", "Regular"), 18) if os.path.exists(font) else ImageFont.load_default()
    for i, path in enumerate(shots):
        x, y = gap + (i % 2) * (tw + gap), gap + (i // 2) * (th + cap + gap)
        d.text((x, y + 8), "%d · %s" % (i + 1, NAMES[i]), fill=(20, 32, 47), font=f1)
        im = Image.open(path).convert("RGB").resize((tw, th), Image.LANCZOS)
        sheet.paste(im, (x, y + cap))
        d.rectangle([x - 1, y + cap - 1, x + tw, y + cap + th], outline=(200, 206, 214))
    x, y = gap + tw + gap, gap + 2 * (th + cap + gap) + cap
    for k, line in enumerate(["Pôle Élec hub: five templates, same links.",
                              "Links and labels come from hub_links.json;",
                              "python build_hub.py rebuilds the five pages.",
                              "Each preview shows one tool hovered."]):
        d.text((x + 10, y + 20 + 34 * k), line, fill=(70, 84, 102), font=f2)
    sheet.save(os.path.join(HERE, "screenshots", "overview.png"), optimize=True)
    print("overview written")


if W == 1440 and not ONLY:
    overview()
