#!/usr/bin/env python3
"""Build the real Java tools and execute the focused correctness tests."""
import os
from pathlib import Path
import sys
import unittest

os.environ.setdefault('LOKY_MAX_CPU_COUNT', '1')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evolution.toolchain import build_java

if __name__ == '__main__':
    build_java()
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
