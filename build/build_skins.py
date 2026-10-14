"""Design studies: the built dashboard with five graphic skins and a switcher, opened on the Analyses tab.
Run after build_all.py:  python3 build/build_skins.py   ->  build/artifacts/FTO2_Design_Studies.html (+ offline copy in 03_reports/)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700"
         "&family=B612:wght@400;700&family=B612+Mono:wght@400;700&family=Barlow:wght@400;500;600;700&family=Barlow+Condensed:wght@500;600;700"
         "&family=Archivo:wdth,wght@62..125,400..800&family=Manrope:wght@400..800&family=Big+Shoulders+Display:wght@600;800"
         "&family=Public+Sans:wght@400..700&display=swap")
BAR_CSS = """
/* skin switcher: its own fixed colours, outside the skins */
body { padding-bottom: 96px; }
#skinbar { position: fixed; z-index: 100; left: max(12px, env(safe-area-inset-left, 0px)); right: max(12px, env(safe-area-inset-right, 0px)); margin: 0 auto; width: fit-content; bottom: calc(14px + env(safe-area-inset-bottom, 0px));
  display: grid; gap: 6px; max-width: calc(100% - 24px); background: #16181b; color: #f2f3f4; border-radius: 14px; padding: 8px 10px 9px;
  box-shadow: 0 10px 30px rgba(0,0,0,.28); font: 13px/1.3 "Segoe UI", Roboto, Arial, sans-serif; }
#skinbar .row { display: flex; gap: 4px; overflow-x: auto; }
#skinbar button { font: inherit; font-weight: 600; white-space: nowrap; border: 0; border-radius: 9px; padding: 6px 11px; background: transparent; color: #c9ccd1; cursor: pointer; }
#skinbar button:hover { background: #2a2d32; color: #ffffff; }
#skinbar button[aria-pressed="true"] { background: #f2f3f4; color: #16181b; }
#skinbar button:focus-visible { outline: 2px solid #8ab4ff; outline-offset: 2px; }
#skinbar .desc { color: #b4b8be; font-size: 12px; padding: 0 4px; }
"""
BAR_HTML = """
<div id="skinbar" role="group" aria-label="Choix du design"><div class="row" id="skinbtns"></div><div class="desc" id="skindesc"></div></div>
<script>
(function () {
  var SK = [
    ['base', 'Actuel', 'Le design actuel, pour comparer.'],
    ['cockpit', '1 · Cockpit', 'Écran d’avionique : fond nuit, cyan, police B612 dessinée pour les cockpits.'],
    ['calque', '2 · Calque', 'Plan technique : papier quadrillé, traits encre, cartouche sur chaque graphique.'],
    ['suisse', '3 · Suisse', 'Style typographique suisse : blanc, filets noirs, très gros titres.'],
    ['calme', '4 · Calme', 'Application tablette : surfaces arrondies, ombres douces, bleu canard.'],
    ['atelier', '5 · Atelier', 'Signalétique d’atelier : plaques noires, bandeau de sécurité, titres façon pochoir.']
  ];
  var root = document.documentElement, btns = document.getElementById('skinbtns'), desc = document.getElementById('skindesc'), cur = 'cockpit';
  try { var s = localStorage.getItem('fto2-skin'); if (s && SK.some(function (k) { return k[0] === s; })) cur = s; } catch (e) {}
  btns.innerHTML = SK.map(function (k) { return '<button type="button" data-skin-btn="' + k[0] + '">' + k[1] + '</button>'; }).join('');
  function apply(k) {
    cur = k;
    if (k === 'base') { root.removeAttribute('data-skin'); root.removeAttribute('data-theme'); }
    else { root.setAttribute('data-skin', k); root.setAttribute('data-theme', k === 'cockpit' ? 'dark' : 'light'); }
    SK.forEach(function (x) { var b = btns.querySelector('[data-skin-btn="' + x[0] + '"]'); b.setAttribute('aria-pressed', String(x[0] === k)); if (x[0] === k) desc.textContent = x[2]; });
    try { localStorage.setItem('fto2-skin', k); } catch (e) {}
    var lang = document.querySelector('.seg.lang [aria-pressed="true"]'); if (lang) lang.click();   // redraw the charts in the new colours
  }
  btns.addEventListener('click', function (e) { var b = e.target.closest('[data-skin-btn]'); if (b) apply(b.getAttribute('data-skin-btn')); });
  var tab = document.getElementById('tab-ana'); if (tab) tab.click();
  apply(cur);
})();
</script>
"""


def main():
    page = open(os.path.join(ROOT, "build", "artifacts", "FTO2_NC_Dashboard.html"), encoding="utf-8").read()
    skins = open(os.path.join(ROOT, "build", "templates", "skins.css"), encoding="utf-8").read()
    head_end = page.index("</style>") + len("</style>")
    fonts_start = page.index('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?')
    fonts_end = page.index(">", fonts_start) + 1
    page = page[:fonts_start] + '<link rel="stylesheet" href="%s">' % FONTS + page[fonts_end:]
    head_end = page.index("</style>") + len("</style>")
    page = page[:head_end] + "\n<style>\n" + skins + BAR_CSS + "</style>" + page[head_end:]
    page = page.replace("<title>FTO2 NC Dashboard</title>", "<title>FTO2 Design Studies</title>", 1) + BAR_HTML
    out = os.path.join(ROOT, "build", "artifacts", "FTO2_Design_Studies.html")
    open(out, "w", encoding="utf-8").write(page)
    full = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            + page.replace('<div class="wrap">', '</head>\n<body>\n<div class="wrap">', 1) + '\n</body>\n</html>\n')
    open(os.path.join(ROOT, "03_reports", "FTO2_Design_Studies.html"), "w", encoding="utf-8").write(full)
    print("design studies:", len(full) // 1024, "KB")


if __name__ == "__main__":
    main()
