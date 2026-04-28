import os
import sys

# Add the root directory to sys.path to allow imports from backend and shared
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if path not in sys.path:
    sys.path.insert(0, path)

from backend.main import app
