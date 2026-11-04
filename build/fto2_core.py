"""Moved to fto2/core.py. This name stays so that older scripts importing fto2_core keep working."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fto2 import core as _core  # noqa: E402

sys.modules[__name__] = _core
