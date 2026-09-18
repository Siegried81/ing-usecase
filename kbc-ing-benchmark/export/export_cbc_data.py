"""Export all CBC-side data for handoff to an external analysis agent.

See export_common.py for the shared logic.
"""

from export_common import run_export

if __name__ == "__main__":
    run_export("CBC", "cbc_trends_data.csv", "cbc_data_export.md")
