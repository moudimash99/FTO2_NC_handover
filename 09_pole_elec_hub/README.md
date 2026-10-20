# Pôle Élec Quality Hub: five templates

New home page for the Pôle Élec quality tools, to replace the current "Pole Elec Quality HUB" Slate app. Five designs, all with the same links. Pick one; it then gets prepared for Slate.

`screenshots/overview.png` shows the five side by side.

| # | File | Idea | Interaction |
| --- | --- | --- | --- |
| 1 | `pole_elec_hub_1_planche.html` | The hub drawn as a harness on its formboard: one connector (J1 Skywise), a trunk with braided sleeve, tie-wraps and pegs, one branch per family of tools, one wire per tool. Dark. | Hovering a tool puts its wire "under power": the other wires dim and a current runs from J1 to the tool. |
| 2 | `pole_elec_hub_2_schema.html` | The hub as a wiring diagram sheet: zone frame, revision table (= news), IEC 81346 references (=PROD, -X1), title block, notes, a spare terminal for the next tool. Paper or blueprint (button). | Hovering a tool draws its path in red from the Skywise source to the tool. |
| 3 | `pole_elec_hub_3_connecteur.html` | The hub as the front face of a circular connector: one gold contact per tool (letters skip I and O), a pinout table, a continuity tester. Dark. | Hovering a contact or a row draws a test lead between them and the tester reads "continuité OK". |
| 4 | `pole_elec_hub_4_panneau.html` | The hub as a cockpit overhead panel: one illuminated push-button per tool, two display units (news and data flow). Dark. | Buttons stay dark unless they need attention (NEW in blue, ALERT in amber); hovering lights OPEN in green. ANN LT TEST lights everything. |
| 5 | `pole_elec_hub_5_faisceau.html` | Light, corporate page: a harness in the header (one branch per family), cards with a wired terminal, news and documents. Light or dark. | Search box filters the tools; hovering a card lights its wire in the header. |

All five work on a wide screen, a laptop and a phone, can be used with the keyboard, and stop their animations when the computer asks for reduced motion.

## Changing a link or a label

1. Edit `hub_links.json` (sections, tools, URLs, news, documents).
2. Run `python build_hub.py`. The five pages are rebuilt with the same content.

`python shoot.py` retakes the screenshots (needs Playwright with Chromium).

## Still needed

- The real Skywise URL of each tool (all links are `#` for now).
- The two tiles cut off on the third row of the current hub (name and URL), if they should stay.
- Short descriptions for **QCM** and **QA Management** (now "NC Eradication" and "Gestion QA").
- Whether new tools should come in (for example the cable defects follow-up); the diagram template already shows a spare terminal for one.

## Moving the chosen one into Slate (to check with whoever builds the Slate app)

- These pages build the tiles and draw the wires with JavaScript. For Slate, the chosen design can be turned into plain HTML and CSS with the links written in, or rebuilt with Slate's own widgets and the app stylesheet. Which one depends on what the Slate app accepts (HTML widget, custom CSS, inline SVG): to confirm in Skywise.
- Fonts come from Google Fonts. If Skywise blocks them, the pages fall back to Bahnschrift / Segoe UI / Consolas, which are on Windows PCs.
- No Airbus or Skywise logo is used.
