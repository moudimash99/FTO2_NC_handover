# Pôle Élec Quality Hub

New home page for the Pôle Élec quality tools, to replace the current "Pole Elec Quality HUB" Slate app.

## Chosen design: template 5 (20 Oct)

The page to use is `hub/pole_elec_hub.html` (preview: `screenshots/hub_final.png`). It is one self-contained file, HTML, CSS and JavaScript only: no other file, no external font, no library. Everything on it comes from the `HUB_CONFIG` block at the top of its `<script>`, the only part to edit:

- links, names, short descriptions, icons and colours are all there; a link still set to `A_COMPLETER` shows "Lien à compléter" and cannot be clicked;
- `soon: true` shows a tool as "Bientôt disponible" (not clickable); `guide:` adds a "Guide utilisateur" link;
- save, refresh the page. Links open in a new tab, as in the current app.

For Slate, `slate/` holds the same page in three parts: `hub.html` (markup), `hub.css` and `hub.js` (with `HUB_CONFIG` at the top). After changing `hub/pole_elec_hub.html`, run `python build_slate.py` to rebuild them.

Content (from the Slate export of the current app, `06_input_data/slate_hub_export_2026-10-20.json`, with Mohammad's changes of 20 and 21 Oct):

- **Outils qualité:** PPS, Serie Follow Up, FOD, Alert Quality, NC Dashboard, NC Writing, CPB, Projets & Amélioration, plus **QSR** and **Operational Surveillance** (new, links to fill in). With ten tools the block shows four cards per row.
- **QCM:** NC Eradication, shown as "Bientôt disponible" until it goes live; its link and user guide are already in the config.
- **QA Management:** MyQA. **Form (DEMAT)** removed: it was the "capri" to remove (21 Oct); it is kept as a commented line in the config.

The current app's tabs become two small groups on the right, so everything is visible at once on a 1440 × 900 screen.

## The five templates (design round of 20 Oct)

Kept as the record of the choice. They still carry the earlier content (with the CNQ tools and news) and are not the page to install.

`screenshots/overview.png` shows the five side by side.

| # | File | Idea | Interaction |
| --- | --- | --- | --- |
| 1 | `pole_elec_hub_1_planche.html` | The hub drawn as a harness on its formboard: one connector (J1 Skywise), a trunk with braided sleeve, tie-wraps and pegs, one branch per family of tools, one wire per tool. Dark. | Hovering a tool puts its wire "under power": the other wires dim and a current runs from J1 to the tool. |
| 2 | `pole_elec_hub_2_schema.html` | The hub as a wiring diagram sheet: zone frame, revision table (= news), IEC 81346 references (=PROD, -X1), title block, notes, a spare terminal for the next tool. Paper or blueprint (button). | Hovering a tool draws its path in red from the Skywise source to the tool. |
| 3 | `pole_elec_hub_3_connecteur.html` | The hub as the front face of a circular connector: one gold contact per tool (letters skip I and O), a pinout table, a continuity tester. Dark. | Hovering a contact or a row draws a test lead between them and the tester reads "continuité OK". |
| 4 | `pole_elec_hub_4_panneau.html` | The hub as a cockpit overhead panel: one illuminated push-button per tool, two display units (news and data flow). Dark. | Buttons stay dark unless they need attention (NEW in blue, ALERT in amber); hovering lights OPEN in green. ANN LT TEST lights everything. |
| 5 | `pole_elec_hub_5_faisceau.html` | Light, corporate page: a harness in the header (one branch per family), cards with a wired terminal, news and documents. Light or dark. | Search box filters the tools; hovering a card lights its wire in the header. |

All five work on a wide screen, a laptop and a phone, can be used with the keyboard, and stop their animations when the computer asks for reduced motion.

## Changing a link or a label in the five templates

1. Edit `hub_links.json` (sections, tools, URLs, news, documents).
2. Run `python build_hub.py`. The five pages are rebuilt with the same content.

`python shoot.py` retakes the screenshots (needs Playwright with Chromium).

## Still needed

- Links for QSR and Operational Surveillance (and a short description for QSR).
- The NC Dashboard link in the current app points to a Slate app named `ttttteqwffadsdasadsad`: worth checking it is the right one.

## Moving the chosen one into Slate (to check with whoever builds the Slate app)

- The page builds the cards and draws the wires with JavaScript, so it needs a Slate widget that runs JavaScript (a custom widget with HTML, CSS and JS boxes): paste `slate/hub.html`, `slate/hub.css` and `slate/hub.js` into them. A plain HTML text widget that strips scripts would show an empty page.
- If the widget runs in a sandboxed frame, it must allow popups, or the links (which open a new tab) will not open.
- The welcome line has the name written in; in Slate it can come from `{{user.firstName}}`.
- No external font: the page uses Segoe UI and Consolas, which are on Windows PCs.
- No Airbus or Skywise logo is used.
