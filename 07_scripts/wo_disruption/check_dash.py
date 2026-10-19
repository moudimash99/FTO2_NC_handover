import sys
from playwright.sync_api import sync_playwright
path = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    pg = b.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto("file://" + path); pg.wait_for_timeout(800)
    print("hero:", pg.inner_text("#hero")[:120].replace("\n", " | "))
    print("formula:", pg.inner_text("#chformula"))
    for nc in ["216135746", "216224176", "16995857"]:
        pg.fill("#ncpick", nc); pg.keyboard.press("Enter"); pg.wait_for_timeout(300)
        t = pg.inner_text("#ncout")
        print(f"\nNC {nc}:", " | ".join(l for l in t.split("\n") if l.strip())[:700])
    pg.evaluate("document.querySelector('#nclines') && (document.querySelector('#nclines').open = true)")
    pg.fill("#ncpick", "216224176"); pg.keyboard.press("Enter"); pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('#nclines').open = true")
    print("\nlines:", pg.inner_text("#nclines")[:600].replace("\n", " | "))
    print("\nparams has connNext:", pg.locator('[data-path="connNext"]').count(), "internalFactor:", pg.locator('[data-path="internalFactor"]').count())
    pg.fill('[data-path="internalFactor"]', "1"); pg.dispatch_event('[data-path="internalFactor"]', "change"); pg.wait_for_timeout(600)
    print("hero with factor 1:", pg.inner_text("#hero")[:60].replace("\n", " | "))
    btn = pg.locator('.lang button[data-lang="fr"]')
    if btn.count(): btn.first.click(); pg.wait_for_timeout(400); print("FR formula:", pg.inner_text("#chformula"))
    print("\nJS errors:", errs or "none")
    b.close()
