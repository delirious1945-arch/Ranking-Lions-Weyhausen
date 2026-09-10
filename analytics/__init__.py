"""
Dart Analytics Engine Package
"""
__version__ = "1.0.0"

from .data_access import (
    save_full_analytics_match,
    update_analytics_match,
    delete_analytics_match,
    get_analytics_match_details,
    get_all_analytics_matches,
    import_analyzer_csv_data,
    scan_main_directory_for_spieltage,
    batch_import_spieltage,
)

__all__ = [
    "save_full_analytics_match",
    "update_analytics_match",
    "delete_analytics_match",
    "get_analytics_match_details",
    "get_all_analytics_matches",
    "import_analyzer_csv_data",
    "scan_main_directory_for_spieltage",
    "batch_import_spieltage",
]
