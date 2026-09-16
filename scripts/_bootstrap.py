"""Put src/ on the path and load .env, so the scripts run without an install step.

steph 16/09: added the .env loading. Sieg's .env.example documented the
variables from day one, but nothing in the repo ever READ a .env file - every
script used os.getenv() only, so the file was inert and a key had to be
exported by hand in every shell. That is the kind of gap where someone
concludes "the LLM step is broken" when it is only unconfigured.

Deliberately a dozen lines rather than a python-dotenv dependency: we have just
added playwright plus a browser download to everyone's setup, and this does not
need a package.

A real environment variable always wins over the file. Exporting a different
key for one run has to keep working, and CI has no .env at all.
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
ENV_FILE = REPO_ROOT / ".env"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def load_env(path: Path = ENV_FILE) -> int:
    """Read KEY=value lines into os.environ. Returns how many were set."""
    if not path.is_file():
        return 0

    loaded = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip().removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        if not key or key in os.environ:  # the real environment wins
            continue
        os.environ[key] = value
        loaded += 1
    return loaded


load_env()
