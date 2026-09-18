"""Export all N26-side data for handoff to an external analysis agent.

See export_common.py for the shared logic.
"""

from export_common import run_export

if __name__ == "__main__":
    run_export("N26", "n26_trends_data.csv", "n26_data_export.md")
