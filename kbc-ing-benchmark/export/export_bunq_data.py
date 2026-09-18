"""Export all bunq-side data for handoff to an external analysis agent.

See export_common.py for the shared logic.
"""

from export_common import run_export

if __name__ == "__main__":
    run_export("BUNQ", "bunq_trends_data.csv", "bunq_data_export.md")
