import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome"); pg = b.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto("file://" + sys.argv[1]); pg.wait_for_timeout(800)
    print("hero:", pg.inner_text("#hero")[:80].replace("\n", " | "))
    h = pg.inner_html("#matrix"); print("matrix rows:", h.count("<tr>") - 1, "| REJ_RW row:", "Rejet avec ordre de retouche" in h, "| WO tag:", "Ordres de retouche SAP" in h)
    for nc in ["216052773", "16995857"]:
        pg.fill("#ncpick", nc); pg.keyboard.press("Enter"); pg.wait_for_timeout(300)
        print(nc, " | ".join(l for l in pg.inner_text("#ncout").split("\n") if l.strip())[:420])
    print("JS errors:", errs or "none"); b.close()
