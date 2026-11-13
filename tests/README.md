# Checks

Run them after any change, from the repository folder.

| What | Command | Time |
|---|---|---|
| Rules, settings, cost settings | `python3 -m unittest discover -s tests -t .` | seconds |
| The Skywise notebook, rehearsed on the laptop | `python3 -I tests/notebook_rehearsal.py` | 1 min |
| The same run and the pages in another year | see "Another year" below | 3 min |
| Every number of the pages against the reference | see below | 30 min |
| The Slate functions, run as Slate runs them | part of the first line (`tests/test_slate_functions.py`) | seconds |
| The Skywise page with the Slate functions, every number | see the end | 25 min |

## Every number of the pages: the snapshot

`tests/golden/` holds the reference: what the build wrote and what the three pages showed on 36 views of the
dashboard, 67 of the MFT page and 85 of the Tableau Elizabeth, on the laptop data.

After a change:

```
python3 -I build/build_all.py
python3 -I 07_scripts/mft/build_mft.py
python3 -I 07_scripts/elizabeth/build_elizabeth.py
python3 -I tests/snapshot/snapshot_data.py  /tmp/new
node tests/snapshot/snapshot_pages.js       /tmp/new
python3 -I tests/snapshot/compare.py tests/golden /tmp/new
```

`compare.py` prints each difference with the text around it, and says "identical" when nothing changed.

A change that is meant to change a number: check the differences are the expected ones, then make the new snapshot
the reference (copy `/tmp/new/*` into `tests/golden/`) in the same commit, and say why in the commit message.

## Another year

The year followed is one line of `config/2_parametres.csv` (`annee`). Two checks keep it so:

- `tests/test_config.py` fails if a year is typed in the backend code;
- the rehearsal below runs the notebook and opens the pages in a year the data was never in.

```
python3 -I tests/notebook_rehearsal.py  /tmp/this_year
python3 -I tests/next_year_rehearsal.py /tmp/next_year
node tests/next_year_page.js /tmp/this_year /tmp/next_year
```

`next_year_rehearsal.py` moves the laptop's data 53 weeks later (same weekdays, same week numbers), into 2027, with one
line of the settings changed, and checks that every NC comes out as in 2026, one year later, with the production volume and
the comparison year following. `next_year_page.js` opens the dashboard and the MFT page of both folders and checks that the
second names the right years everywhere, counts the same NCs, and rings the same alarms.

Run them after any change that touches dates, weeks, the production plan or the pages' texts.

## The Skywise page with the Slate functions

`tests/slate/make_pages.py` makes the Skywise page in its three set-ups (no function, three functions, two functions and the
notebook's table), with `tests/slate/fake_slate.js` standing in for Slate: it runs the function files as Slate does and plays
the event and the variable. Each set-up must show the same numbers as the laptop page:

```
python3 -I build/build_all.py
python3 -I tests/slate/make_pages.py /tmp/slate
FTO2_PAGES=/tmp/slate/3_fonctions node tests/snapshot/snapshot_pages.js /tmp/slate3 dashboard
python3 -I tests/snapshot/compare.py tests/golden /tmp/slate3 dashboard
```

and the same for `2_fonctions` and `sans_fonction`.
