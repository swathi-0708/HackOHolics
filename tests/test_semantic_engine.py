"""
test_semantic_engine.py
------------------------
Proxy test runner pointing to resume_matcher/tests/test_semantic_engine.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from resume_matcher.tests.test_semantic_engine import *
