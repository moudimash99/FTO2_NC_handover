import sys
from playwright.sync_api import sync_playwright
path = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    ctx = b.new_context(accept_downloads=True); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto("file://" + path); pg.wait_for_timeout(500)
    cards = lambda: [c.inner_text().replace("\n", " | ") for c in pg.query_selector_all(".card")]
    print("cards:"); [print("  ", c) for c in cards()]
    print("checks rows:", pg.locator("#checks tbody tr").count(), "|", pg.locator("#checks tbody tr").first.inner_text().replace("\t", " | ")[:120])
    # open H3, enter repair hours on first row
    pg.locator("#checks tbody tr", has_text="Customer returns").click(); pg.wait_for_timeout(300)
    print("dialog:", pg.inner_text("#dlgTitle"), "| H3 totals:", pg.inner_text("#tot-H3"))
    first = pg.locator("#tb-H3 tbody tr").first
    first.locator('[data-f="rep"]').fill("3"); first.locator('[data-f="rep"]').dispatch_event("change")
    print("H3 row1 after 3 h:", first.locator('[data-comp="cwf"]').inner_text(), "| totals:", pg.inner_text("#tot-H3"))
    pg.locator('#dlg [data-close]').click()
    # M4 opens D pre-filtered on possible ERMA
    pg.locator("#checks tbody tr", has_text="ERMA aléas").click(); pg.wait_for_timeout(300)
    print("M4:", pg.inner_text("#cnt-D"), "| totals:", pg.inner_text("#tot-D"))
    r = pg.locator("#tb-D tbody tr:visible").first; r.locator('[data-f="keep"]').select_option("Y"); r.locator('[data-f="keep"]').dispatch_event("change")
    print("after Keep=Y on one ERMA aléa:", pg.inner_text("#tot-D")); pg.locator('#dlg [data-close]').click()
    # M1 group yes
    pg.locator("#checks tbody tr", has_text="Other aléas").click(); pg.wait_for_timeout(300)
    g = pg.locator("#tb-M1g tbody tr").first; g.locator('[data-f="yes"]').select_option("Y"); g.locator('[data-f="yes"]').dispatch_event("change")
    pg.fill('#dlg textarea[data-note="f"]', "Checked with line leader"); pg.dispatch_event('#dlg textarea[data-note="f"]', "change")
    pg.locator('#dlg [data-close]').click()
    pg.locator("#checks tbody tr").nth(7).locator("select").select_option("Done")
    print("cards after answers:"); [print("  ", c) for c in cards() if "live" in c]
    pg.reload(); pg.wait_for_timeout(500)
    print("after reload, status of M1:", pg.locator("#checks tbody tr").nth(7).locator("select").input_value(), "| block card:", [c for c in cards() if "Disruption" in c][0][:90])
    with pg.expect_download() as d: pg.click("#btnExport")
    f = d.value.path(); print("export:", d.value.suggested_filename, open(f, encoding="utf-8-sig").read().splitlines()[:1], "lines:", len(open(f, encoding="utf-8-sig").read().splitlines()))
    pg.click("#btnChanges"); pg.wait_for_timeout(200); print("changes sections:", pg.locator("#chgBody h4").count())
    print("JS errors:", errs or "none"); b.close()
