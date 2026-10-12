# FTO2 NC defect labelling — instructions

You label individual **defects** found in Airbus FTO2 (electrical harness / electrical furniture shop, Toulouse) non-conformity reports (NCs). Texts are mostly French shop-floor language.

## Input

A JSON batch file: a list of NCs. Each NC has context fields and a list of `defects`.

- `long_text`: the **full NC long text** (cleaned): header, the description written by the inspector, the "Type of nonconformity" header, then the later workflow entries (Decision Taken / Justification / Task Description / what was actually done to fix it, e.g. "Collier changé et contrôle OK", "câble refait", "pièce remplacée").
- `description_short`: the NC title.
- `sap_defect_code`, `sap_cause`: SAP header codes, chosen by the writer for the whole NC. Generic and often wrong — weak hint only.
- `station`, `user_department`: where it was found / who wrote it (OLMEP14 = test bench, QRT DERICHEBOURG = final control, QRTE/QLOT = MIP / reception inspection, FAL stations F10xx/V10xx = on the aircraft line).
- `defects`: the defects a rule-based parser split out of the long text. Each has `seq`, `written_code` (official code written by the author for that defect, may be empty), `fin` (equipment ID), `snippet` (the parser's extract for that defect — may be truncated, cut badly or missing context).

## The job

For **every defect** (every `seq` of every NC — never skip one, never merge two), choose the **one** Pareto sub-category from the taxonomy below that describes **that defect**.

**Use the full long text to understand the defect**, not just the snippet:
- The snippet is the target. The long text gives context: section headers (e.g. "Pylône :", "Route 2M"), the sentence before/after that the parser cut, the "Type of nonconformity", and above all the **fix actually done** and the decision justification (they often reveal what really was wrong: a cable remade, a collar replaced, a part swapped, a contact re-locked).
- **NCs with several defects (lists "Def1 :", "DEF 3-T04 :", "1 - FIN xxx :"):** label each defect on its own content. Use the rest of the text only as context. Do **not** copy a cause, origin or fix that belongs to another item of the list onto this one. A sentence that clearly applies to the whole NC (e.g. "tous les câbles ci-dessus ont été reçus abîmés de la salle d'impression") does apply to the items it covers.
- If the snippet is empty, "*", or garbage but the long text makes the defect clear, label from the long text. If nothing anywhere says what the defect is, use "Non classé" with confidence low.


## ROOT CAUSE FIRST (most important rule — added by the quality owner)

The Pareto is used for **root cause analysis**. Label the **root cause of the defect, on the exact element at fault**, not the symptom, not the consequence, not where it was detected.

- **Name the element that is actually wrong.** If the gaine (sheath / sleeve / thermo / chaussette) is damaged, it is "Dommage – habillage", not "Dommage – câble" nor a component. If the plate/label is damaged, "Dommage – identification". If the structure/thread/insert is damaged, "Dommage – structure". Be specific: pick the sub-category whose object matches the element at fault.
- **Cause over consequence.** If something is wrong *because* it was not secured / not held / not fixed (non maintenu, non tenu, non frettée, pas dans le collier, collier manquant, pas fixé), the defect is the lack of securing (e.g. "Frettage / colliers – pose", or "Manquant – colliers" if the collar/tyrap is absent, "Serrage …" if not tightened), not the damage or the clash it produced.
  - "câble abîmé car il frotte sur la structure, non maintenu" → securing problem (Frettage / colliers – pose), not Dommage – câble.
  - "gaine pincée / écrasée / déchirée dans (ou par) le collier", "plaquette déchirée par les frettes" → the collar/frette placement is the root cause → Frettage / colliers – pose (symptome = the pinched/torn element).
  - "harnais / câbles non attachés / non maintenus sur le support" → Frettage / colliers – pose (or Manquant – colliers if the text says the tyrap/collier is missing).
  - "test KO / pas de continuité, fil inversé" → Inversion. "connecteur HS car contact reculé" → Déverrouillage. "câble trop court suite à une inversion" → Inversion.
  - "câble pincé lors du montage du capot" → Dommage – câble (the damage is the root; the cable itself is at fault) unless the text says a routing/securing error made it happen.
- Only apply a cause that is **written** (in the snippet or clearly in the long text for this defect: e.g. "suite à", "car", "à cause de", "dû à", "lors de", or the fix done: "collier ajouté", "câble refretté", "contact reverrouillé"). Do not invent a cause.
- **A written code still wins** (rule 1 below): if the code points at the symptom but the text gives a different root cause, keep the label inside the code's head if a sub-category there fits the cause; if none fits, follow the code and set `code_conflict` = true, naming the root cause in `raison`.
- Add the key `symptome` to every output line: the observed consequence in ≤ 8 words when it differs from the root cause you labelled (e.g. "câble endommagé", "test continuité KO"), else "".

## Decision rules (approved by the quality team — follow them strictly)

1. **A written code wins.** If `written_code` is a full sub-code (e.g. Q06-001, Q11-014) take its sub-category. If it is a head code (Q03, Q04, Q05, Q06, Q11, T02, T04…), the sub-category must be one listed under that head (use the text to pick which). Typos are common: TO4 = T04, QQ01 = Q01, Q6 = Q06. If the text plainly contradicts the code, still follow the code but set `code_conflict` = true and say why in `raison`.
2. **Without a code, the text decides.** When one text gives a cause and its consequence ("câble trop court suite à une inversion"), label the **cause**.
3. **Detection is not cause.** "Sur la ligne A350, nous constatons…" / "lors du contrôle…" says where it was found, not who caused it.
4. **Exceptions:**
   - **E1 "Câble à refaire (ligne)"**: a cable cut too short / too short to be connected, so it must be remade, and the text does NOT say it was received that way. (Rest of Q06-001 — overlength, tension, re-routing, wrong path — stays "Cheminement – longueur / tension".)
   - **E2 Q11 components**: "Dommage – composant cassé" (broken / cracked / bent / pin pushed), "Composant HS" (does not work, faulty, failed test, no continuity) or "Composant – cause non écrite" (replaced/to replace, no damage or failure stated).
   - **E3** a cable **explicitly received** damaged (from the print room / salle d'impression / machine à débiter / supplier) → "Amont · Câble" (only when no code is written).
   - **E4** a cable **never supplied** (non fourni, pas livré, manquant au kit) → "Amont · Câble" (only when no code is written).
   - Length / gauge / type / marking error of a cable that came that way from the print room → "Amont · Câble" (Q12).
5. **Decisions of 7 Oct:** "S/N illisible" (printed illegible) → "Amont · Identification / barrette VT" (Défaut d'Impression); "plaquette desserrée, reprendre le frettage" → "Frettage / colliers – pose"; Mesure hors tolérance (insertion loss / linear resistance) → its own sub-category under Grounding/Bonding.
6. **Wording cues:** inversion / inversé / croisé between two pins or wires → Inversion; wire on wrong pin ("branché en 27 au lieu de 17") → Erreur de branchement; contact not locked / reculé / non verrouillé / sorti → Déverrouillage; contact / wire not connected → Non connecté; missing tyrap / frette / ficelle → Manquant – colliers; missing cap / cerise / bouchon / obturateur / plug → Manquant – obturateurs / bouchons; blue paint (bleu, vernis de protection) on bonding points → Bleu …; ground braid / metallisation measurement → Point de masse / mesure.
7. If an item really holds two different defects ("gaine non maintenue + plaquette à l'envers"), label the main/first one and put `deux_defauts` = true.

## Cable fields (separate from the sub-category)

- `defaut_cable`: true only if **a cable itself must be remade or resupplied** (cut too short, cable damaged/cut/scratched needing replacement, cable missing / never supplied, wrong gauge/type/marking from the print room). A wire just on the wrong pin, not locked, badly routed, or a tension/overlength rework is **false**.
- `provenance` (only meaningful when `defaut_cable` = true, else ""): `RECU` if the text explicitly says received/supplied that way (reçu, livré, à réception, salle d'impression, fournisseur, déballage); `LIGNE` if it explicitly says the line/operator caused it (coupé trop court, coupé par erreur, par l'opérateur, lors du montage, pincé au montage, à cause des pions de cheminement); `NON_PRECISE` otherwise. Only explicit wording counts — do not guess.

## Output

Write **one JSON object per line** (JSONL) to the output path you are given, one line per defect, in input order, with exactly these keys:

```
{"notification_number": "218129758", "seq": 1, "sous_categorie": "Frettage / colliers – pose", "sous_code": "Q05-004", "confiance": "high", "defaut_cable": false, "provenance": "", "code_conflict": false, "deux_defauts": false, "contexte_utile": true, "symptome": "gaine annelée pincée", "raison": "gaine pincée par le collier = pose du collier; fix = collier changé"}
```

- `sous_categorie`: exactly one label from the taxonomy (copy the spelling exactly, including the en dash "–" and "·"), or "Non classé".
- `sous_code`: the best-fitting official sub-code from the taxonomy list, or "" for exception sub-categories / when unsure.
- `confiance`: `high` (clear), `medium` (reasonable but another sub-category is plausible), `low` (guess).
- `contexte_utile`: true if information outside the snippet (long text, fix, title) changed or was needed for your choice.
- `raison`: ≤ 25 words, French or English, saying what decided it.

Work through every defect yourself by reading — do **not** write a keyword/regex script to classify. You may use a script only to read the input or to check that your output has one valid line per defect. At the end, verify the line count equals the number of defects in the batch and that every `sous_categorie` is a valid label.

## Taxonomy (9 categories → sub-categories → official sub-codes)

### MEO Câblage

- **Sertissage spécifique** (RCA: Défaut de Sertissage sur câble spécifique)
    - Q08-001: QUADRAX contact (Stripping, Crimping)
    - Q08-002: TWINAX contact (Stripping, Crimping)
    - Q08-003: TRIAXIAL contact (Stripping, Crimping)
    - Q08-004: BUSCAN contact (Stripping, Crimping)
    - Q08-005: Coax contact (Stripping, Crimping)
    - Q08-006: Optical fiber contact (Stripping, gluing)
    - Q08-007: Brazing (Non-compliant weld)
- **Sertissage** (RCA: Défaut de Sertissage sur câble standard)
    - Q07-001: Aluminum contact (Stripping, Crimping)
    - Q07-002: Copper contact (Stripping, Crimping)
    - Q07-003: Self-welding sleeve (Deformation, overheating)
    - Q07-004: Copper lug (Stripping, Crimping)
    - Q07-005: Aluminum lug (Stripping, Crimping)
    - Q07-006: CDVE Aluminum contact (Stripping, Crimping)
    - Q07-007: CDVE Copper contact (Stripping, Crimping)
    - Q07-008: CDVE Self-welding sleeve (Deformation, overheating)
    - Q07-009: CDVE Copper lug (Stripping, Crimping)
    - Q07-010: CDVE Aluminum lug (Stripping, Crimping)
- **Mauvaise réf. – électrique / détrompage** (RCA: Erreur Composant Électrique)
    - Q04-004: Contact (Reference, copper, aluminum)
    - Q04-005: Resistor, connector, circuit breaker, relay, switch, rear connection (Ref, mounting, orientation)
    - Q04-009: Error correction/detrompage (Coding key, ARINC plug pin, polarization key)
    - Q04-011: Electrical element (Ground braid, terminal, indicator light - ref/orientation/charging)
- **Mauvaise réf. – colliers / frettage** (RCA: Erreur Fixation ou Protection)
    - Q04-007: Plastic routing collar (Reference, size, orientation)
    - Q04-008: Metal routing collar (Reference, size, orientation)
    - Q04-014: Frettage (Reference plastic fret collar, reference string fret)
- **Mauvaise réf. – identification** (RCA: Erreur Fixation ou Protection)
    - Q04-013: Identification plate (plate, function label, adhesive END, flame, sleeve - ref/identification/reversal)
- **Mauvaise réf. – mécanique** (RCA: Erreur Fixation ou Protection)
    - Q04-003: Mechanical (Screw, washer, nut, spacer, V-bracket, structure, VT bar - ref/size/orientation)
    - Q04-006: Lock wire (Reference)
- **Mauvaise réf. – obturation / thermo** (RCA: Erreur Fixation ou Protection)
    - Q04-001: Shutter (Reference, mounting direction)
    - Q04-002: Heat shrink tubing (Reference, size)
    - Q04-010: Ventilation hole protective caps (Reference)
    - Q04-012: Socket protective cap (Reference, size)
- **Câblage non terminé** (RCA: Finition Inachevée)
    - Q06-009: Route not resumed after test (Cabling not completed)
- **Identification – positionnement** (RCA: Finition Inachevée)
    - Q06-010: Identification (Positioning flame, plate, sleeve - offset, not specified, too short/long, illegible)
- **Frettage / colliers – pose** (RCA: Frettage Incorrect)
    - Q05-004: Frettage (Plastic collar, string fret)
    - Q06-006: Incorrect positioning of shrink ring (Plastic collar, string)
    - Q06-011: Frettage implementation (double capstan knot, fret length cut, ferrule clamp)
    - Q06-012: Implementation of connections in Band-it collar
- **Gainage / protection** (RCA: MEO Gainage)
    - Q06-002: Poor sheathing installation (Visible line, incorrect twist, branch, sock)
    - Q06-003: Combining tape/amalgamant (Overlap, permitted overlap)
    - Q06-007: Fringing on rear connection (Sheath not secured, sheath too short)
    - Q06-008: Sheathing (Too short, in contact with grommet, not secured to rear connector)
- **Cheminement – clash** (RCA: Mauvais Cheminement)
    - Q06-004: Cable in contact with structural element (Clash with plate, ramp, pipe, screw, connecting rod)
    - Q06-005: Cable in contact with electrical component (Clash with VG, connector)
- **Cheminement – longueur / tension** (RCA: Mauvais Cheminement)
    - Q06-001: Harness (Routing, cable management, under/overlength, wrong destination, not in collar, V-support, pinched)
- **Câble à refaire (ligne)** (RCA: Mauvais Cheminement) — E1: part of Q06-001
    - (exception): E1: part of Q06-001
- **Serrage mécanique** (RCA: Serrage Incorrect)
    - Q05-002: Mechanical (screws, safety wire, frangible paint, clamp, diode block, BAND-IT, VT bar, standoff, sleeve, light, switch, relay)
    - Q05-003: Rope collar (Over/under/loose screws)
- **Serrage électrique** (RCA: Serrage Incorrect)
    - Q05-001: Electrical element (Rear connection, connector, VG module, terminal, circuit breaker - over/under/loose)
    - Q05-005: CDVE Electrical components (rear connection, connector, VG module, terminal, circuit breaker)

### Erreur Branchement

- **Inversion** (RCA: Inversion)
    - T04: Connection reversal (Copper, Aluminum, Fiber optic)
- **Erreur de branchement** (RCA: Mauvaise Borne)
    - T02: Connection error (Copper, aluminum, fiber optic)
- **Non connecté** (RCA: Non Connecté)
    - T05: Unconnected cable (Copper, aluminum, fiber optic)

### Élément Manquant

- **Manquant – câble / shunt / élément** (RCA: Câble ou Élément Manquant)
    - Q03-004: Electrical element (Cable, contact, diode, resistor, connector, VG module, rear connector)
    - T01: Missing cable (Copper, aluminum, fiber optic)
    - T03: Missing shunt (Electrical, Mechanical)
- **Manquant – colliers** (RCA: Fixation ou Protection Manquante)
    - Q03-006: Collar/collier (routing, plastic shrink, string shrink, V-support, plastic, metal)
- **Manquant – gaine / thermo** (RCA: Fixation ou Protection Manquante)
    - Q03-002: Heat shrink tubing (Low temp, high temp)
    - Q03-010: Sheathing/gaine (Textile, corrugated, EMI, spare)
- **Manquant – mécanique / freinage** (RCA: Fixation ou Protection Manquante)
    - Q03-003: Mechanical element (Screw, washer, nut, spacer)
    - Q03-005: Braking/freinage (Brake wire, glue, frangible paint line)
- **Manquant – identification** (RCA: Identification Manquante)
    - Q03-009: Tamper-evident label (Furniture door lock, cut-off socket)
    - Q03-011: Identification plate/sleeve/flag (END, route, cable number, clamp, ramp)
    - Q03-012: Identification label (FIN, MSN)
- **Manquant – obturateurs / bouchons** (RCA: Obturateur Manquant)
    - Q03-001: Shutter/obturateur (Circular, rectangular, VT module, ventilation hole)
    - Q03-007: Protective caps (Ventilation hole, open hole)
    - Q03-008: End protection (Socket plug, plastic bag)

### Élément Endommagé

- **Composant HS** (RCA: Composant Endommagé) — E2: part of Q11 component codes
    - (exception): E2: part of Q11 component codes
- **Composant – cause non écrite** (RCA: Composant Endommagé) — E2: part of Q11 component codes
    - (exception): E2: part of Q11 component codes
- **Dommage – composant cassé** (RCA: Composant Endommagé)
    - Q11-003: Component (VG module, circuit breaker, VT strip module, connector, rear fitting, lighting plate)
    - Q11-005: Lug (copper, aluminum)
    - Q11-006: Contact (Copper, aluminum)
    - Q11-012: VT strip (Damaged module, deformed rail)
    - Q11-016: CDVE Component
    - Q11-018: CDVE Lug
    - Q11-019: CDVE Contact
- **Dommage – tresse de masse** (RCA: Composant Endommagé)
    - Q11-009: Ground braid metallization (Broken strands)
    - Q11-022: CDVE Ground braid metallization
- **Dommage – câble** (RCA: Câble Endommagé)
    - Q11-001: Cable cut
    - Q11-014: Scratched, damaged cable
- **Dommage – habillage** (RCA: Protection Endommagée)
    - Q11-004: Protective sheath (Textile, corrugated, EMI)
    - Q11-007: Amalgamating tape (Torn, soiled)
    - Q11-008: Heat shrink tubing (Torn, soiled)
    - Q11-010: Cable collar (Plastic, metal, V-bracket)
    - Q11-011: BAND-IT clamp (Metal clamp, PTFE tape)
    - Q11-013: Damaged sealing sleeves
    - Q11-026: CDVE Damaged sealing sleeves
- **Dommage – identification** (RCA: Protection Endommagée)
    - Q11-002: Identification (Wave, label, sleeve - torn, soiled)
- **Dommage – structure** (RCA: Structure Endommagée)
    - Q10-001: Damaged plate (Impact, scratch, bent, soiling)
    - Q10-002: Damaged structure (Impact, scratch, soiling)
    - Q10-003: Damaged handrail (Impact, scratch, bent, soiled)
    - Q10-004: Column (Impact, scratch, soiling)
    - Q10-005: Damaged piping (Impact, scratch, soiling)
    - Q10-006: Mechanism (Insert, screws - damaged threads, broken screws inside)

### Déverrouillage

- **Déverrouillage** (RCA: Déverrouillage)
    - Q01-001: Contact (Copper, aluminum, fiber optic)
    - Q01-002: False contact (Not locked)
    - Q01-003: CDVE Contact (Copper, aluminum, fiber optic)

### Grounding/Bonding

- **Bleu mal appliqué / débordant** (RCA: Défaut de Métallisation)
    - Q09-002: Application of protection (Partially applied, metallization visible)
    - Q09-005: CDVE Application of protection
- **Bleu non appliqué** (RCA: Défaut de Métallisation)
    - Q09-001: Protection not applied (Petroleum jelly, protective paint)
    - Q09-004: CDVE Protection not applied
- **Mesure hors tolérance** (RCA: Défaut de Métallisation)
    - T06: Insertion loss measurement on non-compliant optical links
    - T08: Non-compliant linear resistance measurement (EMI sheath, overbraiding)
    - T08-CDVE: CDVE Non-compliant linear resistance measurement
- **Point de masse / mesure** (RCA: Défaut de Métallisation)
    - Q09-003: Ground point (Oxidation, non-compliant brush diameter, non-compliant measurement)
    - Q09-006: CDVE Ground point
    - T07: Resistance measurement on non-conforming metallization (VN, VG, VH)
    - T07-CDVE: CDVE Resistance measurement on non-conforming metallization

### Kitting Factory

- **Amont · Câble** (RCA: Défaut d'Impression) — E3 (received damaged) and E4 (never supplied) also land here
    - Q12-001: Cable gauge error (G20, G18)
    - Q12-002: Cable type error (DR, AD)
    - Q12-003: Cable length error (Too short, too long)
    - Q12-004: Cable identification (Readability, ID number error, marking characteristics)
    - Q12-007: CDVE Cable gauge error
    - Q12-008: CDVE Cable type error
- **Amont · Identification / barrette VT** (RCA: Défaut d'Impression)
    - Q12-005: Identification (Sleeve, plate, label - legibility, incorrect reference, color)
    - Q12-006: VT bar (Module identification error, module reference, rail size)

### FOD

- **FOD** (RCA: FOD)
    - Q16-001: Tools (Flashlight, mirror, wrench, screwdriver, Allen key)
    - Q16-002: Fasteners and aircraft parts (Bolts, washers, nuts)
    - Q16-003: Personal effects (ID badge, glasses, phone, laptop, tablet)
    - Q16-004: Industrial debris (Silver filings, dust, insulation, metal chips)
    - Q16-005: Additional items (Consumables, caps, plugs, work order)
    - Q16-006: Maintenance (Item left in work area, workshop, workstation, corridor)

### Autre

- **Dossier** (RCA: Erreur Dossier)
    - Q13-001: Operation (Not badged, order of operations not respected)
    - Q13-002: Stamp (Not affixed to tracking sheet, partially visible)
    - Q13-003: Traceability label (CT176 not completed, CT129D not completed)
    - Q13-004: Documentation (Missing, non-compliant)
    - Q13-005: Tool entry (Not performed, tool kit error)

- **Non classé** — nothing in the snippet or long text says what the defect is.
