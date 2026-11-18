"""The Code Repository's style check refuses a transform file with a line over 120 characters: the update is then
not registered and every build says "No transforms discovered". Keep the transform file within that limit."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_transform_lines_within_120():
    path = os.path.join(ROOT, "build", "repository", "fto2_update.py")
    with open(path, encoding="utf-8") as f:
        long = [(n, len(line.rstrip("\n"))) for n, line in enumerate(f, 1) if len(line.rstrip("\n")) > 120]
    assert not long, "lines over 120 characters (line, length): %s" % long
