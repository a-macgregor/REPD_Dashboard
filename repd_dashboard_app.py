# repd_dashboard_app.py

import streamlit as st
import pandas as pd
import datetime
from data_utils import load_data  # Import our helper function

# --- CONFIG ---
CSV_URL = "https://assets.publishing.service.gov.uk/media/67f5282490615dd92bc90d06/repd-q4-jan-2025.csv"

# --- PAGE SETUP ---
st.set_page_config(page_title="UK REPD Dashboard", layout="wide")
st.title("📈 Renewable Energy Planning Dashboard")
st.markdown("Filter, explore and export data from the UK Renewable Energy Planning Database (REPD).")

# --- LOAD DATA ---
@st.cache_data
def get_data():
    return load_data(CSV_URL)

df = get_data()

# For debugging purposes, you might display the raw loaded data:
st.write("✅ Fetched CSV from:", CSV_URL)
# st.write("📋 Loaded columns:", df.columns.tolist())
# st.write("🔢 Data preview:", df.head())

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filters")
tech_options = sorted(df['technology type'].dropna().unique().tolist())
default_tech = ['Solar Photovoltaics'] if 'Solar Photovoltaics' in tech_options else []
selected_tech = st.sidebar.multiselect("Technology Type", tech_options, default=default_tech)
region_options = sorted(df['region'].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect("Region", region_options, default=region_options)

if df['installed capacity (mwelec)'].dropna().size > 0:
    min_cap = int(df['installed capacity (mwelec)'].min())
    max_cap = int(df['installed capacity (mwelec)'].max())
    selected_capacity = st.sidebar.slider("Installed Capacity (MW)", min_cap, max_cap, (min_cap, max_cap))
else:
    selected_capacity = (0, 0)

if df['application year'].dropna().size > 0:
    min_year = int(df['application year'].min())
    max_year = int(df['application year'].max())
    selected_years = st.sidebar.slider("Application Year", min_year, max_year, (min_year, max_year))
else:
    selected_years = (2020, 2025)

# --- DATA FILTERING ---
filtered_df = df[
    (df['technology type'].isin(selected_tech)) &
    (df['region'].isin(selected_regions)) &
    (df['installed capacity (mwelec)'] >= selected_capacity[0]) &
    (df['installed capacity (mwelec)'] <= selected_capacity[1]) &
    (df['application year'] >= selected_years[0]) &
    (df['application year'] <= selected_years[1])
]

# --- SUMMARY METRICS ---
st.subheader("📊 Summary Stats")
st.markdown(f"**{len(filtered_df)}** projects match your filters.")

col1, col2, col3 = st.columns(3)
col1.metric("Avg. Consent Time (days)", f"{filtered_df['time to consent (days)'].mean():.1f}")
col2.metric("Median Consent Time (days)", f"{filtered_df['time to consent (days)'].median():.1f}")
col3.metric("Max Consent Time (days)", f"{filtered_df['time to consent (days)'].max():.0f}")

# --- LINE CHART ---
st.subheader("📈 Consent Time Over Time")
if not filtered_df.empty:
    # Filter out rows with missing application year
    df_year = filtered_df[filtered_df['application year'].notna()].copy()
    # Force conversion of 'application year' to integer (this avoids decimal labels)
    df_year['application year'] = df_year['application year'].astype(int)
    # Group by application year and calculate the mean consent time
    chart_df = df_year.groupby('application year', as_index=False)['time to consent (days)'].mean()
    chart_df = chart_df.sort_values('application year')
    # Convert the year column to strings before plotting
    chart_df['application year'] = chart_df['application year'].astype(int).astype(str)
    st.line_chart(chart_df.set_index('application year'))
else:
    st.warning("No data available for the selected filters.")

# After grouping and sorting:
# chart_df['application year'] = chart_df['application year'].astype(int).astype(str)
# st.line_chart(chart_df.set_index('application year'))

# --- EXPANDABLE RAW DATA VIEW ---
st.subheader("📂 View Filtered Data")
with st.expander("Show raw filtered data"):
    st.dataframe(filtered_df)

# --- CSV EXPORT ---
st.subheader("📥 Export Filtered Data")
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
csv_data = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Filtered CSV",
    data=csv_data,
    file_name=f"repd_filtered_{timestamp}.csv",
    mime="text/csv"
)