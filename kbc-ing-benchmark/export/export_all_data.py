"""Export combined data for every bank of the benchmark in one document.

See export_common.py for the shared logic.
"""

from export_common import run_export_all

if __name__ == "__main__":
    run_export_all("all_trends_data.csv", "all_data_export.md")
