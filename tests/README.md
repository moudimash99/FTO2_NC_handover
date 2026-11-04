# Checks

Run them after any change, from the repository folder.

| What | Command | Time |
|---|---|---|
| Rules, settings, cost settings | `python3 -m unittest discover -s tests -t .` | seconds |
| The Skywise notebook, rehearsed on the laptop | `python3 -I tests/notebook_rehearsal.py` | 1 min |
| Every number of the pages against the reference | see below | 30 min |

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
