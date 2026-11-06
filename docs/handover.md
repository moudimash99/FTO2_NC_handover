# Handover: the FTO2 NC dashboard

Mohammad built this during his internship in the Quality team of the FTO2 electrical centre, and leaves in November 2026.
This note is for whoever looks after the dashboard next. Read it first. It points to the other documents when you need detail.

## 1. What it is

A set of pages on the non-conformities (NCs) of FTO2. They answer simple questions: how many NCs, which defects, where they were
found, what they cost, how we compare with last year and with the target, and which problems are getting worse.

- **The dashboard**, in two modes:
  - **Essentiel**: a few charts for the monthly review (Synthèse, Détail).
  - **Deep dive**: everything (Vue d'ensemble, Pareto, Localisation, Coût de non-qualité, Retours clients, Câbles,
    Définitions, Production).
  - A **bell** at the top flags problems that are rising, line by line (a cause, a station, a product...).
- **The MFT page**: the weekly Pareto of each line, the analysis, and the follow-up of the MFT actions.
- **The Tableau Elizabeth**: optional.

The pages are in French, with an English switch. The target is last year's level minus 25 %.

**Where it runs.** In Skywise. A notebook reads the NCs (plus work orders and aléas) and writes four tables. The Slate app
reads those tables and shows the pages. The same pages can also be built on a laptop from exported files: that is how changes
are checked before they go into Skywise.

## 2. Keeping it running

| When | What to do | How |
|---|---|---|
| Every week, or whenever you want fresh numbers | Run the notebook in Skywise. The pages update once the tables are synced. | `03_reports/skywise/README.md`, "Keep it up to date" |
| When the production plan changes | Update the plan from the Avances / Retards file, or correct an aircraft by hand | `docs/comment_faire.md` |
| When an MFT action is decided | Add one row to the MFT actions table | `docs/comment_faire.md` |
| Every few weeks | Label the new defect lines with the AI pass (see below) | `03_reports/skywise/DETAILS.md` |

**New defect lines.** The causes shown on the dashboard come from labels given by an AI pass on each defect line. A new line
gets a simpler label (from the text-reading rules) until the next AI pass. The dashboard stays complete; only the causes of the
newest lines are a little less precise. **The AI pass needs IT's approval first** (see section 7).

## 3. Changing something

**Most changes are settings, not code.** Every setting is a small table in `config/` (in Skywise: `data/config/`, next to the
notebook). One table per subject, and each one opens in Excel. The number at the start of its name says who should edit it:
**1** anyone, **2** someone careful, **3** someone technical. `config/lisez_moi.csv` lists them all and says what each one
changes.

Examples: what counts as REC, an hourly rate, the target, a new product, the production plan, an MFT action. **`config/README.md`**
explains every table and how to fill it in; the same tasks in French are in `docs/comment_faire.md`.

After a change, run the notebook. If a table is badly filled, the run stops and says which file, which line and what to fix.

**Some tables are made from a raw file** by a script: the production plan, the cable requests, the MFT trackers. Run the script
on the new file (`docs/comment_faire.md`). A row you corrected by hand (column `source` = `manuel`) is kept when the script
runs again.

**Changing how a page looks, or adding a chart**, needs someone at ease with JavaScript: `docs/front_end.md`.

**Changing how NCs are read or costed** (the backend, in Python): `fto2/`, one file per subject. The notebook and the laptop
build use the same code.

## 4. Where things are

| You want to... | Look in |
|---|---|
| Understand the folders | `README.md` |
| Change a setting | `config/` and `docs/comment_faire.md` |
| Set up or update Skywise | `03_reports/skywise/README.md` |
| Change a page | `docs/front_end.md` |
| Check that nothing broke | `tests/README.md` |
| Know why something was done a certain way | `HANDOVER.md` (the detailed log of the work, with dates) |

## 5. Checking that nothing broke

There are two levels of checks.

- **Quick (seconds):** the settings tables are complete and readable, the rules work, and no setting is hidden in the code.
- **Full (about 30 minutes, on the laptop):** every number the three pages show, on 188 different views, is compared with a
  saved reference. A change that should move nothing must come out "identical".

Both are explained in `tests/README.md`. Run them before you paste anything new into Skywise.

## 6. Open points

**Calculations in Slate functions: ready, not yet tried in Skywise.** The targets and forecast, the alarms and the cost
explanation can run as Slate functions instead of inside the page. Two ways are ready: three functions, or two functions plus a
table written by the notebook. Both give the same figures as the page on the laptop. What can only be seen in Skywise is
whether the round trip works and how fast it is. Try them with `03_reports/skywise/level3_datasets/fonctions/README.md`, then
keep one way, or none: the page works on its own.

**Running the notebook automatically (a Foundry data pipeline).** Today someone runs the notebook. A pipeline would run the
same steps on a schedule and keep a history of each table. The code is ready for it: it is plain Python. But the settings
tables would have to move into Foundry datasets or into the pipeline's repository, and it needs access to Code Repositories.
Not started.

**Points from the work log that were open at some point.** Check with Mohammad which ones still are, before he leaves:

- cable defects: the choice between the proposed options, and the definition of a "cable problem";
- the REC rule to give to the pipeline team;
- the cost-model checks in `05_outputs/CNQ_investigation_checklist.html`;
- the review of the defect lines where the text-reading rules and the AI labels disagree (`05_outputs/FTO2_llm_longtext_review.xlsx`);
- comparing the cost model with the official Airbus method (not started).

**The old Slate app.** Keep it until the new one has run well for a few weeks. Then set `garder_anciennes_sorties` to `non`
in `config/2_parametres.csv`, so the notebook stops writing the old tables.

## 7. Rules to keep

- **NC texts must not be sent to an outside AI tool** without the agreement of Emmanuelle and IT. This includes the AI
  labelling pass.
- **Don't edit the generated files** (`03_reports/`, `05_outputs/`, the Skywise files). The next build writes them again.
  Edit the settings, the templates or the code instead.
- **Keep the old Slate app** until the new one is trusted.
- **Run the checks** before you change anything in Skywise.

## 8. Who to ask

- **Emmanuelle** (Mohammad's manager): priorities, and approvals such as the use of AI on NC texts.
- **Mohammad**, until he leaves.
- For the history of a choice: `HANDOVER.md`, the detailed log of the work. It is long and technical, and some folder
  names in it are older than the current layout.
