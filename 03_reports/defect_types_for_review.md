# Defect types — proposal for review

Working document. Write in it, cross things out, rename whatever doesn't work.
4 September 2026.

---

## The idea in three sentences

We keep the official retouching codes (Q01, Q03… T04…) for **writing** NCs. Nothing changes there.

What we're adding is a layer on top, for **reading** the numbers: 26 defect types, grouped into 6 families. Nobody types this in by hand — it's calculated from the official code.

Why: right now we can't answer "what's our main problem?". The SAP code puts 43% of NCs into a single bucket ("Electrical Assembly Installation"), and the cause is "People" half the time. You can't decide anything from that.

---

## The 6 families

The grouping came from one simple question: **what would have prevented this defect?** Two defects that get fixed the same way belong together.

| Family | What it means | What fixes it | Volume |
|---|---|---|---|
| **Selection** | Right part, wrong place. Someone picked between two things that look alike. | Keying, marking, clearer instruction. Not training. | 891 (38%) |
| **Execution** | The gesture was done, but not to standard. | Tooling, calibration, work instruction, hands-on training. | 560 (24%) |
| **Omission** | A step or a part got skipped. | A cue that forces the check at the station. | 417 (18%) |
| **Handling** | Damaged while being handled. | Protection, packaging, environment. | 273 (12%) |
| **Upstream** | It arrived wrong. | Harness shop, supplier, supply chain. | 77 (3%) |
| **Process** | Paperwork, traceability. | Documentation discipline. | 4 (0%) |

The number to remember: **38% of our defects are selection errors**. And when you look at the inversions in detail, 99% happen between two adjacent or twin terminals — never between two distant ones. That means the problem is in the task (two things that look too much alike), not in people's attention. Which is why it doesn't move despite the reminders.

---

## The 26 types

The prefix tells you the family, so there's nothing to memorise.

**Selection**
- INVERSION_BRANCHEMENT (wires swapped) — 372
- ERREUR_BRANCHEMENT (wire on wrong terminal) — 299
- ERREUR_REF_HABILLAGE (wrong ref, non-electrical) — 153
- ERREUR_REF_ELECTRIQUE (wrong ref, electrical) — 67

**Execution** (MEO = mise en œuvre)
- MEO_FRETTAGE_COLLIER — 144
- MEO_SERRAGE (tightening) — 97
- MEO_GAINAGE (sheathing) — 90
- MEO_CHEMINEMENT (routing) — 86
- MEO_SERTISSAGE_STANDARD (crimping) — 56
- MEO_METALLISATION (bonding) — 42
- MEO_SERTISSAGE_SPECIFIQUE (quadrax, coax, fibre) — 32
- MEO_FINITION — 8
- MESURE_NON_CONFORME — 5

**Omission**
- MANQUANT_HABILLAGE — 140
- OUBLI_VERROUILLAGE (contact not locked) — 110
- MANQUANT_CABLE_ELEMENT — 89
- MANQUANT_OBTURATION — 32
- FOD — 20
- MANQUANT_IDENTIFICATION — 15
- NON_CONNECTE — 11

**Handling**
- DOMMAGE_COMPOSANT — 144
- DOMMAGE_STRUCTURE — 61
- DOMMAGE_CABLE — 53
- DOMMAGE_HABILLAGE — 15

**Upstream**
- AMONT_IMPRESSION (length, gauge, marking errors) — 77

**Process**
- PROCESS_DOSSIER — 4

Plus an "Other" bucket for anything that doesn't fit: 124 defects, about 5%.

---

## The choices we made, and why

**A type always belongs to exactly one family.**
This is what forces us to separate things that look similar. A missing frettage and a loose frettage are two different types: the first is an omission, the second is a gesture. We don't fix them the same way, so we don't count them together. The official grid already makes this distinction (Q03-005 vs Q05-004) — we're just following it.

**We started from the official codes, not from an invented list.**
All 123 sub-codes in the grid land in one of the 26 types. No gaps. That was the condition for this to be usable: if an official code has nowhere to go, the system is wrong.

**We're not asking anything extra from whoever writes the NC.**
The type is calculated from the code. If tomorrow someone writes Q03-006, we know it's a missing collar, therefore an omission. Zero extra clicks.

**We avoided catch-all categories.**
The biggest type is 16% of volume — compare that to 43% for the current SAP code. A Pareto where one bar crushes everything else is useless.

**There's an "Other" bucket, deliberately.**
The official grid doesn't have one, and that's probably part of why a lot of people don't code at all: when you can't find your case, you give up and write free text. We suggest reviewing the "Other" bucket once a week; if the same case comes up ten times, it becomes a real type.

---

## What we're not sure about

Worth discussing.

- **DOMMAGE_STRUCTURE and PROCESS_DOSSIER are nearly empty** (61 and 4). Do these defects not happen here, or are they declared somewhere else?
- **Standard vs specific crimping** — we split them because the tooling and the qualification aren't the same (Q07 vs Q08). Worth confirming that makes sense from the shop floor's point of view.
- **The habillage / electrical split** on reference errors: does it mean anything to people on the ground, or would one single type be better?
- **The names.** They're provisional. If "MEO_" doesn't speak to anyone, we rename.

---

## One limitation to know about

Out of the 2,346 defects analysed in the history, we're confident about the classification for roughly half — the ones where the test team wrote their code. For the other half (final inspection, MIP inspection) there's no code in the text, so we're inferring from the words. We know it, and every defect carries a confidence level so we don't tell stories on a chart.

This fixes itself as soon as NCs are written with a code. It's not an analysis problem, it's a data entry problem.

---
---

# Annex — real examples per type

All examples are genuine extracts from NCs, January to July 2026.

### Selection

**INVERSION_BRANCHEMENT** — two wires swapped
> 115VMB INVERSION DE BRANCHEMENT ENTRE LES BORNES R ET S
> 115VMB INVERSION DE BRANCHEMENT ENTRE LES BORNES AA ET CC (QUADRAX)

**ERREUR_BRANCHEMENT** — wire on the wrong terminal
> 7XCA CABLE EN B3 AU LIEU DE B2
> 11XCA CABLE EN D1 AU LIEU DE X2

**ERREUR_REF_ELECTRIQUE** — wrong reference on an electrical item
> 10REA ET 23XEA RELAIS INVERSES
> 1033VC MAUVAIS DETROMPAGE

**ERREUR_REF_HABILLAGE** — wrong reference on non-electrical hardware
> INVERSION DE PLAQUETTE ENTRE 2WTA ET 2WTB

### Execution

**MEO_SERRAGE**
> route 2M, FIN 1GG B, backshell desserré

**MEO_GAINAGE**
> ROUTE ESS 2M : liseré apparent et gaine vrillée, reprendre le gainage
> Gaine ouverte, finition non terminée sur la prise 20TC1-A

**MEO_CHEMINEMENT**
> route 1M, reprendre cheminement, clash entre support lacote et structure
> ROUTE ESS 1M 1MD 1MG : liseré apparent

**MEO_FRETTAGE_COLLIER**
> ROUTE ESS 2S 2SF et ROUTE ESS 2M 2MF : frète à reprendre

**MEO_SERTISSAGE_STANDARD**
> 1608VC019 BORNE 40 MAUVAIS SERTISSAGE
> 300VT200 BORNE 3G MAUVAIS SERTISSAGE

**MEO_METALLISATION**
> Bleu de métallisation à reprendre sur 100VN121, 100VN123, 110VN145
> 100VN131 : bleu sous rondelle à reprendre

**MEO_FINITION**
> sur platine, reprendre finition du FIN 11CP1 C
> 10FC1 A, finition du connecteur à effectuer

### Omission

**OUBLI_VERROUILLAGE**
> 12KS1 BORNE 3 DEVERROUILLE
> 100VT400 BORNE 6H DEVERROUILLEE

**MANQUANT_OBTURATION**
> FIN 411VC007 A : manque 4 obturateurs
> route 1M, FIN 411VC001 A, il manque 8 obturateurs noirs

**MANQUANT_HABILLAGE**
> FIN 1608VC064 A : Mq obturateur
> FIN 1608VC097 A : manque une frète sur reprise de blindage panneau arrière

**MANQUANT_CABLE_ELEMENT**
> route 2M, FIN 1608VC058 A, il manque la gaine thermo sur le câble

**MANQUANT_IDENTIFICATION**
> au déballage nous constatons qu'il manque l'étiquette d'identification SATO

**NON_CONNECTE**
> 3RN2A CABLE EN < P NON CONNECTE
> 115VMA DR24 N°3119-0344 NON CONNECTE AU GND

**FOD**
> FIN 11CP1 A. FOD, brin métallique entre les câbles
> FOD poussière : sur table, platine aspiration PYLONE

### Handling

**DOMMAGE_CABLE**
> CABLE COUPE ENTRE 1608VC062A BORNE 19 ET 100VT400 5D

**DOMMAGE_COMPOSANT**
> Endommagement fibre : fibre 3161-0582 cassée

**DOMMAGE_HABILLAGE**
> Étiquette collante endommagée sur la prise 1608VC006-A
> Sur platine relais, étiquette FIN 721VN abîmée

**DOMMAGE_STRUCTURE**
> Contact entre la route P et la structure au niveau de la dérivation de 6PB2

### Upstream

**AMONT_IMPRESSION**
> FIN 4DB2 A : surlongueur de câble
> route 2M, avant FIN 300VD002 A, un câble en sur-longueur sur le harnais

### Process

**PROCESS_DOSSIER**
> 1027709295 - GR non rempli
