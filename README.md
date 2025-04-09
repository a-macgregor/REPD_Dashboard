# UK REPD Dashboard

A Streamlit app that fetches, cleans, filters, and visualizes data from the UK Renewable Energy Planning Database (REPD).

## Overview

This dashboard loads the latest REPD CSV from the UK government website, cleans and standardizes key data fields (e.g., Technology Type, Region, Installed Capacity, Application Year), and allows users to:
- Filter data using interactive sidebar controls.
- View summary metrics and a line chart of average consent time.
- Export the filtered dataset as a timestamped CSV file.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/repd-dashboard.git
   cd repd-dashboard

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt

## Usage

To run the dashboard locally:
```bash
streamlit run repd_dashboard_app.py
```

This will open your browser at http://localhost:8501.

## Deployment

The app is deployed on Streamlit Cloud. Every push to the main branch triggers an automatic redeployment.

## Version

This is version v1.0

## Licence

This project is licenced under the MIT Licence.
