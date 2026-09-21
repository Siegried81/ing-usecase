"""Export brand-notoriety data (share of search) for handoff to an
external analysis agent.

See export_common.py for the shared logic.
"""

from export_common import run_export

if __name__ == "__main__":
    run_export("brand_trends_data.csv", "brand_share_of_search.csv", "brand_notoriety_export.md")
