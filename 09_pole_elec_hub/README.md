# Pôle Élec Quality Hub

New home page for the Pôle Élec quality tools, to replace the current "Pole Elec Quality HUB" Slate app.

## Chosen design: template 5 (20 Oct), two rows of eight cards (21 Oct)

The page to use is `hub/pole_elec_hub.html` (previews: `screenshots/hub_final.png`, `hub_final_hover.png` with one tool hovered, `hub_final_phone.png`). It keeps the template 5 look, with the harness drawing in the header, and puts the tools on one grid of eight compact cards per row (four below 1240 px wide). All cards have the same size and line up across the page (the script sets their rows and places on the grid), so nothing is stacked on one side. A sober corporate restyle without the drawing was tried on 21 Oct and dropped (commit `b02ac35` in the history). The page is light only, so it matches the Slate app whatever the Windows theme. It is one self-contained file, HTML, CSS and JavaScript only: no other file, no external font, no library. Everything on it comes from the `HUB_CONFIG` block at the top of its `<script>`, the only part to edit:

- links, names, short descriptions, icons and colours are all there; `links:` gives a tool several buttons; a link still set to `A_COMPLETER` shows "Lien à compléter" and cannot be clicked;
- `soon: true` shows a tool as "Bientôt disponible" (not clickable); `guide:` adds a "Guide utilisateur" link;
- save, refresh the page. Links open in a new tab, as in the current app.

For Slate, `slate/` holds the same page in three parts: `hub.html` (markup), `hub.css` and `hub.js` (with `HUB_CONFIG` at the top). After changing `hub/pole_elec_hub.html`, run `python build_slate.py` to rebuild them.

Content: Mohammad's own list of 21 Oct (links, groups and the tools with several links), built on the Slate export of the current app (`06_input_data/slate_hub_export_2026-10-20.json`). Five groups, sixteen tools, in the order of the drawing (biggest groups at the top):

- **Non-conformités:** NC Writing, NC Dashboard, MFT, NC Eradication (shown as "Bientôt disponible" until it goes live; its link and user guide are already in the config).
- **Surveillance & amélioration:** Operational Surveillance (DEMAT, GDrive), Projets & Amélioration, Alert Quality, FOD.
- **Correctif:** PPS (Skywise, GDrive), SARI Events (CAPRI, GDrive), CPB (KPI, GDrive), QSR (eQSR, GDrive).
- **Assurance qualité:** MyQA, Qualif Indus (C-SAAM, GDrive), Qualif Personal.
- **Production & suivi:** Suivi de la production (SÉRIE, REC, HS).

The greeting is "Bonjour, bienvenue sur le dashboard de la qualité Pôle Élec", with no name.

At the foot of each card, every link is a short text link followed by a small ↗, underlined on hover. A tool with several `links` shows their names (DEMAT, GDrive…). A tool with a single `link` shows what it opens, found from its address: **GDrive**, **Skywise** or **Site**, and opens from anywhere on its card; on a several-link card only the names are clickable, so that card does not lift on hover.

On a wide screen the page has eight cards per row, all the same size, and groups share a row while they fit: Non-conformités and Surveillance & amélioration (4 + 4) on the first row, Correctif, Assurance qualité and Production & suivi (4 + 3 + 1) on the second. Both rows split after the fourth card, so the page gets a wider gap there and reads as a left half and a right half. Everything is visible at once on a 1440 × 900 screen. Between 1000 and 1240 px wide there are four cards per row; below 1000 px the groups go one per row with two cards per row, and on a phone the cards stack.

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

- NC Writing and NC Dashboard point to a Slate app named `test123213213` (pages `page-1` and `home`): worth checking it is the final one.

## Moving the chosen one into Slate (to check with whoever builds the Slate app)

- The page builds the cards and draws the wires with JavaScript, so it needs a Slate widget that runs JavaScript (a custom widget with HTML, CSS and JS boxes): paste `slate/hub.html`, `slate/hub.css` and `slate/hub.js` into them. A plain HTML text widget that strips scripts would show an empty page.
- Clicks: links open in a new tab. The old hub's buttons were plain HTML in a Slate text widget, so their new tabs worked. This page needs JavaScript, so it runs in a framed widget, and if that frame does not allow pop-ups a plain click opens nothing while Ctrl+click still works (reproduced in Chrome). The page then shows a short message saying to use Ctrl+click. For plain clicks to work, the widget has to allow pop-ups / new windows, if Slate offers that setting.
- No external font: the page uses Segoe UI and Consolas, which are on Windows PCs.
- No Airbus or Skywise logo is used.
