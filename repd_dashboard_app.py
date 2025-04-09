# repd_dashboard_app.py

import streamlit as st
import pandas as pd
import os
import urllib.request
from datetime import datetime

# --- CONFIG ---
LOCAL_CSV_PATH = "cleaned_repd.csv"
ONLINE_CSV_URL = "https://assets.publishing.service.gov.uk/media/67f5282490615dd92bc90d06/repd-q4-jan-2025.csv"

# --- PAGE SETUP ---
st.set_page_config(page_title="UK REPD Dashboard", layout="wide")
st.title("📈 Renewable Energy Planning Dashboard")
st.markdown("Filter, explore and export data from the UK Renewable Energy Planning Database (REPD).")

# --- DATA FETCH & CLEAN ---
@st.cache_data
def load_data():
    # Attempt to use online CSV first
    try:
        df = pd.read_csv(ONLINE_CSV_URL, encoding='ISO-8859-1')
        source = "🟢 Loaded from online source"
        # Cache the download locally
        df.to_csv(LOCAL_CSV_PATH, index=False, encoding='utf-8')
    except Exception as e:
        st.warning("⚠️ Failed to load online CSV. Trying local fallback...")
        if os.path.exists(LOCAL_CSV_PATH):
            df = pd.read_csv(LOCAL_CSV_PATH, encoding='utf-8')
            source = "🟡 Loaded from local fallback"
        else:
            st.error("❌ No CSV file found to load.")
            return pd.DataFrame()

    # Clean up weird formatting in column names
    df.columns = df.columns.str.strip().str.replace('"', '').str.replace("'", '')

    # Standardize key text fields
    if 'Technology Type' in df.columns:
        df['Technology Type'] = df['Technology Type'].astype(str).str.strip().str.title()
    else:
        df['Technology Type'] = pd.NA

    if 'Region' in df.columns:
        df['Region'] = df['Region'].astype(str).str.strip().str.title()
    else:
        df['Region'] = pd.NA

    if 'Development Status' in df.columns:
        df['Development Status'] = df['Development Status'].astype(str).str.strip().str.title()
    else:
        df['Development Status'] = pd.NA

    # Clean Installed Capacity column
    if 'Installed Capacity (MWelec)' in df.columns:
        df['Installed Capacity (MWelec)'] = (
            df['Installed Capacity (MWelec)']
            .astype(str)
            .str.replace(',', '', regex=False)
            .str.replace('MW', '', case=False, regex=False)
            .str.strip()
            .replace('', '0')
            .astype(float)
        )
        df['Installed Capacity (MWelec)'] = pd.to_numeric(df['Installed Capacity (MWelec)'], errors='coerce')
    else:
        df['Installed Capacity (MWelec)'] = pd.NA

    # Handle planning dates
    if 'Planning Application Submitted' in df.columns:
        df['Planning Application Submitted'] = pd.to_datetime(df['Planning Application Submitted'], errors='coerce')
    if 'Planning Permission Granted' in df.columns:
        df['Planning Permission Granted'] = pd.to_datetime(df['Planning Permission Granted'], errors='coerce')
    if 'Planning Application Submitted' in df.columns and 'Planning Permission Granted' in df.columns:
        df['Time to Consent (days)'] = (df['Planning Permission Granted'] - df['Planning Application Submitted']).dt.days
    else:
        df['Time to Consent (days)'] = pd.NA

    # Create or clean Application Year
    if 'Application Year' in df.columns:
        df['Application Year'] = pd.to_numeric(df['Application Year'], errors='coerce')
    elif 'Planning Application Submitted' in df.columns and df['Planning Application Submitted'].notna().any():
        df['Application Year'] = df['Planning Application Submitted'].dt.year
    else:
        df['Application Year'] = pd.NA

    # Log file metadata
    st.caption(f"{source} | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Rows: {len(df):,} | Columns: {df.shape[1]}")

    return df


df = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filters")
tech_options = sorted(df['Technology Type'].dropna().unique().tolist())
default_tech = ['Solar Photovoltaics'] if 'Solar Photovoltaics' in tech_options else []

technologies = st.sidebar.multiselect("Technology Type", options=tech_options, default=default_tech)
regions = st.sidebar.multiselect("Region", sorted(df['Region'].dropna().unique()), default=sorted(df['Region'].dropna().unique()))

# --- SAFELY HANDLE PROJECT SIZE SLIDER ---
if df['Installed Capacity (MWelec)'].dropna().size > 0:
    min_size = int(df['Installed Capacity (MWelec)'].min())
    max_size = int(df['Installed Capacity (MWelec)'].max())
    size_range = st.sidebar.slider("Project Size (MW)", min_size, max_size, (min_size, max_size))
else:
    size_range = (0, 0)

# --- SAFELY HANDLE APPLICATION YEAR SLIDER ---
if 'Application Year' in df.columns and df['Application Year'].dropna().size > 0:
    min_year = int(df['Application Year'].min())
    max_year = int(df['Application Year'].max())
    years = st.sidebar.slider("Application Year", min_year, max_year, (min_year, max_year))
else:
    st.warning("⚠️ Application Year data not available.")
    years = (2020, 2025)

# --- DATA FILTERING ---
filterable = all(col in df.columns for col in ['Technology Type', 'Region', 'Installed Capacity (MWelec)', 'Application Year'])

if filterable:
    filtered_df = df[
        (df['Technology Type'].isin(technologies)) &
        (df['Region'].isin(regions)) &
        (df['Installed Capacity (MWelec)'] >= size_range[0]) &
        (df['Installed Capacity (MWelec)'] <= size_range[1]) &
        (df['Application Year'] >= years[0]) &
        (df['Application Year'] <= years[1])
    ]
else:
    st.warning("⚠️ Some required columns are missing. Showing full dataset instead.")
    filtered_df = df

# --- MAIN DASHBOARD ---
st.subheader("📊 Summary Stats")
st.markdown(f"**{len(filtered_df)}** projects match your filters.")

col1, col2, col3 = st.columns(3)
col1.metric("Average Consent Time (days)", f"{filtered_df['Time to Consent (days)'].mean():.1f}" if not filtered_df['Time to Consent (days)'].isna().all() else "N/A")
col2.metric("Median Consent Time (days)", f"{filtered_df['Time to Consent (days)'].median():.1f}" if not filtered_df['Time to Consent (days)'].isna().all() else "N/A")
col3.metric("Max Consent Time (days)", f"{filtered_df['Time to Consent (days)'].max():.0f}" if not filtered_df['Time to Consent (days)'].isna().all() else "N/A")

# --- CHARTS ---
st.subheader("📈 Consent Time Over Time")
if not filtered_df.empty:
    chart_df = filtered_df.groupby('Application Year')['Time to Consent (days)'].mean().reset_index()
    st.line_chart(chart_df.set_index('Application Year'))
else:
    st.warning("No data available for the selected filters.")

# --- DATA QUALITY WARNINGS ---
st.subheader("🚨 Data Quality Warnings")

blanks = df[
    df['Planning Application Submitted'].isna() |
    df['Planning Permission Granted'].isna() |
    df['Installed Capacity (MWelec)'].isna() |
    df['Technology Type'].isna() |
    df['Region'].isna() |
    df['Ref ID'].isna()
]

outliers = df[
    (df['Time to Consent (days)'] < 0) |
    (df['Installed Capacity (MWelec)'] <= 0) |
    (df['Installed Capacity (MWelec)'] > 300)
]

if blanks.empty and outliers.empty:
    st.success("No major data quality issues found. 🎉")
else:
    if not blanks.empty:
        st.warning(f"⚠️ {len(blanks)} projects have missing critical fields.")
        st.dataframe(blanks[['Ref ID', 'Site Name', 'Planning Application Submitted', 'Planning Permission Granted', 'Installed Capacity (MWelec)', 'Region']])
    if not outliers.empty:
        st.warning(f"⚠️ {len(outliers)} projects have suspicious values.")
        st.dataframe(outliers[['Ref ID', 'Site Name', 'Installed Capacity (MWelec)', 'Time to Consent (days)', 'Region']])

# --- EXPORT ---
st.subheader("📥 Export Data")
export_csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button("Download CSV", export_csv, "filtered_repd.csv", "text/csv")