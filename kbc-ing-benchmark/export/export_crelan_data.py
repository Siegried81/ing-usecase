"""Export all Crelan-side data for handoff to an external analysis agent.

See export_common.py for the shared logic.
"""

from export_common import run_export

if __name__ == "__main__":
    run_export("CRELAN", "crelan_trends_data.csv", "crelan_data_export.md")
