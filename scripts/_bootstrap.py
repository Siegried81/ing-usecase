"""Put src/ on the path and load .env, so the scripts run without an install step.

steph 15/09: added .env loading - Sieg's .env.example documented the variables
from day one, but nothing in the repo READ a .env file, so it was inert and a
key had to be exported by hand in every shell.

steph 16/09, CONSOLIDATED. That first version was a hand-rolled parser, written
to avoid adding a dependency. Sieg has since added python-dotenv to
requirements.txt and calls load_dotenv() in run_collection.py and
llm_extractor.py, so the dependency exists either way and the repo had two
mechanisms doing the same job with subtly different parsing. One is enough, and
it should be the maintained library rather than my twelve lines.

Kept here as well as in Sieg's two call sites because this module is imported
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
