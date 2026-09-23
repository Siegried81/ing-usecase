"""Put src/ on the path and load .env, so the scripts run without an install step.

Without this, .env.example documents the variables but nothing READS a .env
file, so every key has to be exported by hand in each shell.

Loading goes through python-dotenv rather than a hand-rolled parser: the
dependency is already in requirements.txt and called from run_collection.py
and llm_extractor.py, and two mechanisms with subtly different parsing is one
too many.

Kept here as well as in the two call sites because this module is imported
first by EVERY script - a script that forgets load_dotenv() still gets its
environment. load_dotenv() is idempotent, so calling it in both places is free.

A real environment variable still wins over the file: python-dotenv does not
override by default, which is the behaviour the previous version had too.
Exporting a different key for one run keeps working, and CI has no .env at all.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
ENV_FILE = REPO_ROOT / ".env"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

load_dotenv(ENV_FILE)
