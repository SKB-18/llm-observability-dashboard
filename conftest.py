# Root conftest.py – ensures the project root is on sys.path so
# "from backend.xxx import yyy" works regardless of how pytest is invoked.
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
