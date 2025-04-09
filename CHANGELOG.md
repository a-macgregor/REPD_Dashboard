# Changelog

## [v1.0] - 2025-04-09
### Added
- Live CSV import from UK Government REPD dataset
- Filters for technology, region, year, and capacity
- Metrics: average, median, max consent time
- Data quality warnings and export to CSV

## [v1.1] - 2025-04-09
### Added
- data_utils.py created to fetch, clean, and normalise CSV data. Column names are standardised by converting them to lowercase. This avoids issues with unexpected whitespace.
- repd_dashboard_app.py updated to import load_data from data_utils.py and then use it inside a caching wrapper (@st.cache_data). This file handles UI elements (like sidebar filters, metrics, charts, and the export button). Includes debug lines to verify that the CSV has loaded correctly.