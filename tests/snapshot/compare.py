"""Compare two snapshots (made by snapshot_data.py and snapshot_pages.js) and say what differs.

    python3 -I tests/snapshot/compare.py <reference folder> <new folder> [data dashboard mft elizabeth]

Compares the four snapshots, or only the ones named after the folders.

Exits 0 when everything matches, 1 otherwise. Text must match exactly. Numbers inside the data tables may differ
by a rounding of 1e-9 at most. Prints at most a few differences per item, with the text around each one.
"""
import gzip
import json
import os
import sys

MAX_SHOWN = 5


def load(folder, name):
    path = os.path.join(folder, name)
    if not os.path.exists(path):
        return None
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def same_value(a, b):
    if a == b:
        return True
    try:
        x, y = float(a), float(b)
    except (TypeError, ValueError):
        return False
    return abs(x - y) <= 1e-9 * max(1.0, abs(x), abs(y))


def around(text, i, width=70):
    return "..." + text[max(0, i - width):i + width] + "..."


def first_difference(a, b):
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n if len(a) != len(b) else -1


def walk(ref, new, where, out):
    """Collect the differences between two JSON values; `where` says where we are, in words."""
    if len(out) >= 200:
        return
    if isinstance(ref, dict) and isinstance(new, dict):
        for k in ref:
            if k not in new:
                out.append("%s: '%s' is missing in the new snapshot" % (where, k))
            else:
                walk(ref[k], new[k], "%s > %s" % (where, k), out)
        for k in new:
            if k not in ref:
                out.append("%s: '%s' is new (not in the reference)" % (where, k))
    elif isinstance(ref, list) and isinstance(new, list):
        if len(ref) != len(new):
            out.append("%s: %d items before, %d now" % (where, len(ref), len(new)))
        for i, (a, b) in enumerate(zip(ref, new)):
            walk(a, b, "%s [%d]" % (where, i), out)
    elif isinstance(ref, str) and isinstance(new, str):
        if ref != new and not same_value(ref, new):
            i = first_difference(ref, new)
            out.append("%s:\n      before: %s\n      now:    %s" % (where, around(ref, i), around(new, i)))
    elif not same_value(ref, new):
        out.append("%s: %r before, %r now" % (where, ref, new))


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    ref_dir, new_dir = sys.argv[1], sys.argv[2]
    ok = True
    only = sys.argv[3:] or ["data", "dashboard", "mft", "elizabeth"]
    for name in [x + ".json.gz" for x in only]:
        ref, new = load(ref_dir, name), load(new_dir, name)
        if ref is None:
            continue
        label = name.replace(".json.gz", "")
        if new is None:
            print("%s: no new snapshot to compare" % label)
            ok = False
            continue
        diffs = []
        walk(ref, new, label, diffs)
        if diffs:
            ok = False
            # group by the first two levels (page and view) so the report stays short
            groups = {}
            for d in diffs:
                key = " > ".join(d.split(" > ")[:2]).split(":")[0]
                groups.setdefault(key, []).append(d)
            print("%s: %d difference(s) in %d place(s)" % (label, len(diffs), len(groups)))
            for key, items in groups.items():
                for d in items[:MAX_SHOWN]:
                    print("  - " + d)
                if len(items) > MAX_SHOWN:
                    print("  ... and %d more in %s" % (len(items) - MAX_SHOWN, key))
        else:
            print("%s: identical" % label)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
