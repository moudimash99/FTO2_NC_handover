"""Design concepts: the built dashboard with five page concepts (structure, chart style, palette, fonts) and a switcher.
Run after build_all.py:  python3 build/build_concepts.py  ->  build/artifacts/FTO2_Design_Concepts.html (+ offline copy in 03_reports/)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700"
         "&family=Newsreader:ital,opsz,wght@0,6..72,400..600;1,6..72,400..600&family=Hanken+Grotesk:wght@400..700"
         "&family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=DM+Sans:opsz,wght@9..40,400..700&family=Onest:wght@400..700"
         "&family=JetBrains+Mono:wght@400..600&family=Schibsted+Grotesk:wght@400..700&family=Lexend:wght@300..600&display=swap")
BAR_CSS = """
#tip { z-index: 90 !important; }
body { padding-bottom: 104px; }
#cbar { position: fixed; z-index: 100; left: max(12px, env(safe-area-inset-left, 0px)); right: max(12px, env(safe-area-inset-right, 0px)); margin: 0 auto; width: fit-content;
  max-width: calc(100% - 24px); bottom: calc(14px + env(safe-area-inset-bottom, 0px)); display: grid; gap: 6px; background: #16181b; color: #f2f3f4; border-radius: 14px;
  padding: 8px 10px 9px; box-shadow: 0 10px 30px rgba(0,0,0,.3); font: 13px/1.3 "Segoe UI", Roboto, Arial, sans-serif; }
#cbar .row { display: flex; gap: 4px; overflow-x: auto; }
#cbar button { font: inherit; font-weight: 600; white-space: nowrap; border: 0; border-radius: 9px; padding: 6px 11px; background: transparent; color: #c9ccd1; cursor: pointer; }
#cbar button:hover { background: #2a2d32; color: #ffffff; }
#cbar button[aria-pressed="true"] { background: #f2f3f4; color: #16181b; }
#cbar button:focus-visible { outline: 2px solid #8ab4ff; outline-offset: 2px; }
#cbar .desc { color: #b4b8be; font-size: 12px; padding: 0 4px; max-width: 62ch; }
"""
BAR_HTML = """
<div id="cbar" role="group" aria-label="Choix du concept"><div class="row" id="cbtns"></div><div class="desc" id="cdesc"></div></div>
<script>
%s
</script>
<script>
(function () {
  var C = [
    ['base', 'Actuel', 'Le design actuel, pour comparer.'],
    ['story', '1 · Récit', 'Une histoire qui se lit en défilant : une conclusion par section, en grand à gauche, le graphique à droite. Tracés épurés.'],
    ['slides', '2 · Présentation', 'Un graphique par diapositive, flèches ← → pour avancer. Pour présenter en réunion. Tracés épais.'],
    ['console', '3 · Console', 'Menu latéral, chiffres clés, grille dense de tuiles ; « Agrandir » ouvre une tuile en grand.'],
    ['gallery', '4 · Galerie', 'Planche de vignettes : cliquez sur une vignette pour l’ouvrir en grand, ← → pour passer à la suivante. Tracés techniques.'],
    ['questions', '5 · Questions', 'Choisissez une question à gauche, la réponse s’affiche à droite.']
  ];
  var btns = document.getElementById('cbtns'), desc = document.getElementById('cdesc'), cur = 'story';
  try { var s = localStorage.getItem('fto2-concept'); if (s && C.some(function (k) { return k[0] === s; })) cur = s; } catch (e) {}
  btns.innerHTML = C.map(function (k) { return '<button type="button" data-c="' + k[0] + '">' + k[1] + '</button>'; }).join('');
  function pick(k) {
    C.forEach(function (x) { var b = btns.querySelector('[data-c="' + x[0] + '"]'); b.setAttribute('aria-pressed', String(x[0] === k)); if (x[0] === k) desc.textContent = x[2]; });
    try { localStorage.setItem('fto2-concept', k); } catch (e) {}
    window.FTO2_CONCEPT(k);
  }
  btns.addEventListener('click', function (e) { var b = e.target.closest('[data-c]'); if (b) pick(b.getAttribute('data-c')); });
  pick(cur);
})();
</script>
"""


def main():
    page = open(os.path.join(ROOT, "build", "artifacts", "FTO2_NC_Dashboard.html"), encoding="utf-8").read()
    css = open(os.path.join(ROOT, "build", "templates", "concepts.css"), encoding="utf-8").read()
    js = open(os.path.join(ROOT, "build", "templates", "concepts.js"), encoding="utf-8").read()
    a = page.index('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?')
    page = page[:a] + '<link rel="stylesheet" href="%s">' % FONTS + page[page.index(">", a) + 1:]
    end = page.index("</style>") + len("</style>")
    page = page[:end] + "\n<style>\n" + css + BAR_CSS + "</style>" + page[end:]
    page = page.replace("<title>FTO2 NC Dashboard</title>", "<title>FTO2 Design Concepts</title>", 1) + BAR_HTML % js
    open(os.path.join(ROOT, "build", "artifacts", "FTO2_Design_Concepts.html"), "w", encoding="utf-8").write(page)
    full = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            + page.replace('<div class="wrap">', '</head>\n<body>\n<div class="wrap">', 1) + '\n</body>\n</html>\n')
    open(os.path.join(ROOT, "03_reports", "FTO2_Design_Concepts.html"), "w", encoding="utf-8").write(full)
    print("design concepts:", len(full) // 1024, "KB")


if __name__ == "__main__":
    main()
