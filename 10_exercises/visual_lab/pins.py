"""The two pins named in a connection-error defect ("... ENTRE LES BORNES 41 ET 42"), when the text gives them.

pin_pair(text) -> (a, b) sorted, or None. Only short pin names count (1 to 3 characters: 7, 41, S, KK, B1);
plug names such as 9KSJ26 never do. Redacted pins (#PRS~) give None.
"""
import re

_PIN = r"([A-Z]{1,2}\d?|\d{1,3}[A-Z]?)"
_SEP = r"\s*(?:ET\s+(?:LA\s+)?BORNE|ET|/|&|-|AND)\s*"
_OPEN, _CLOSE = r"\s*[<«\"]?\s*", r"\s*[>»\"]?"
_BORNES = re.compile(r"(?:BORNES?|PINS?|CONTACTS?|BROCHES?)" + _OPEN + _PIN + _CLOSE + _SEP + r"[<«\"]?\s*" + _PIN + r"(?![A-Z0-9])", re.I)
_ENTRE = re.compile(r"INVERS\w*[^.]*?ENTRE" + _OPEN + _PIN + _CLOSE + r"\s+ET" + _OPEN + _PIN + r"(?![A-Z0-9])", re.I)


def _key(p):
    return (0, int(p)) if p.isdigit() else (1, len(p), p)


def pin_pair(text):
    if not isinstance(text, str):
        return None
    for pat in (_BORNES, _ENTRE):
        m = pat.search(text)
        if m:
            a, b = m.group(1).upper(), m.group(2).upper()
            if a != b:
                return tuple(sorted((a, b), key=_key))
    return None


def consecutive(a, b):
    """True when the two pins follow each other in the connector's numbering: 7 and 8, S and T, KK and LL."""
    if a.isdigit() and b.isdigit():
        return abs(int(a) - int(b)) == 1
    doubled = lambda p: p.isalpha() and p == p[0] * len(p)
    if doubled(a) and doubled(b) and len(a) == len(b):
        return abs(ord(a[0]) - ord(b[0])) == 1
    if len(a) == len(b) == 2 and a[1:] == b[1:] and a[0].isalpha() and b[0].isalpha():   # B1 and C1
        return abs(ord(a[0]) - ord(b[0])) == 1
    return False
