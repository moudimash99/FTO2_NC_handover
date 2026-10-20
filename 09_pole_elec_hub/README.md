# Pôle Élec Quality Hub

New home page for the Pôle Élec quality tools, to replace the current "Pole Elec Quality HUB" Slate app.

## Chosen design: template 5 (20 Oct)

The page to use is `hub/pole_elec_hub.html` (preview: `screenshots/hub_final.png`). Everything on it comes from `hub/hub_config.js`, the only file to edit:

- paste each Skywise link where it says `A_COMPLETER`; until then the card shows "Lien à compléter" and cannot be clicked;
- names, short descriptions, icons and colours are in the same file;
- keep the two files in the same folder, save, refresh the page.

Content is what the current hub shows, no more: PPS, Serie Follow Up, FOD, Alert Quality, NC Dashboard, NC Writing, the two tiles of its third row, QCM with NC Eradication, and QA Management. The third-row tiles and the QA Management card carry placeholder names for now (Audits, Documentation, Habilitations QA), marked as such in the config. The two tabs of the current hub become two small groups on the right, so everything is visible at once on a 1440 × 900 screen.

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

- The Skywise link of each tool (Mohammad pastes them in `hub/hub_config.js`).
- The real names of the two tiles on the third row of the current hub (hidden behind its scroll); "Audits" and "Documentation" are placeholders.
- What the "QA Managment" tab of the current hub contains; "Habilitations QA" is a placeholder (one line per tile in the config).

## Moving the chosen one into Slate (to check with whoever builds the Slate app)

- The page builds the cards and draws the wires with JavaScript, and reads `hub_config.js` next to it. Inside Slate the links would have to live in Slate itself (for example a variable), not in a separate file. For Slate, the chosen design can be turned into plain HTML and CSS with the links written in, or rebuilt with Slate's own widgets and the app stylesheet. Which one depends on what the Slate app accepts (HTML widget, custom CSS, inline SVG): to confirm in Skywise.
- Fonts come from Google Fonts. If Skywise blocks them, the pages fall back to Bahnschrift / Segoe UI / Consolas, which are on Windows PCs.
- No Airbus or Skywise logo is used.
