"""Export all Argenta-side data for handoff to an external analysis agent.

See export_common.py for the shared logic.
"""

from export_common import run_export

if __name__ == "__main__":
    run_export("ARGENTA", "argenta_trends_data.csv", "argenta_data_export.md")
