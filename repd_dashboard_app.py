import streamlit as st
import pandas as pd
import datetime

# --- CONFIG ---
CSV_URL = "https://assets.publishing.service.gov.uk/media/67f5282490615dd92bc90d06/repd-q4-jan-2025.csv"

# --- PAGE SETUP ---
st.set_page_config(page_title="UK REPD Dashboard", layout="wide")
st.title("\U0001F4C8 Renewable Energy Planning Dashboard")
st.markdown("Filter, explore and export data from the UK Renewable Energy Planning Database (REPD).")

# --- LOAD AND CLEAN DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL, encoding="ISO-8859-1")

    # Clean column names
    df.columns = df.columns.str.strip().str.replace('"', '').str.replace("'", '')

    # Normalize key columns
    df['Technology Type'] = df.get('Technology Type', pd.Series(dtype='str')).astype(str).str.strip().str.title()
    df['Region'] = df.get('Region', pd.Series(dtype='str')).astype(str).str.strip().str.title()

    # Installed Capacity
    if 'Installed Capacity (MWelec)' in df.columns:
        df['Installed Capacity (MWelec)'] = (
            df['Installed Capacity (MWelec)']
            .astype(str)
            .str.replace(',', '')
            .str.replace('MW', '', case=False)
            .str.strip()
            .replace('', '0')
        )
        df['Installed Capacity (MWelec)'] = pd.to_numeric(df['Installed Capacity (MWelec)'], errors='coerce')
    else:
        df['Installed Capacity (MWelec)'] = pd.NA

    # Dates and Application Year
    df['Planning Application Submitted'] = pd.to_datetime(df.get('Planning Application Submitted', pd.NaT), errors='coerce')
    df['Planning Permission Granted'] = pd.to_datetime(df.get('Planning Permission Granted', pd.NaT), errors='coerce')
    df['Time to Consent (days)'] = (df['Planning Permission Granted'] - df['Planning Application Submitted']).dt.days
    df['Application Year'] = df['Planning Application Submitted'].dt.year

    return df

df = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.header("\U0001F50D Filters")
tech_options = df['Technology Type'].dropna().unique().tolist()
region_options = df['Region'].dropna().unique().tolist()

selected_tech = st.sidebar.multiselect("Technology Type", tech_options, default=tech_options)
selected_regions = st.sidebar.multiselect("Region", region_options, default=region_options)

if df['Installed Capacity (MWelec)'].dropna().size > 0:
    min_cap = int(df['Installed Capacity (MWelec)'].min())
    max_cap = int(df['Installed Capacity (MWelec)'].max())
    selected_capacity = st.sidebar.slider("Installed Capacity (MW)", min_cap, max_cap, (min_cap, max_cap))
else:
    selected_capacity = (0, 0)

if df['Application Year'].dropna().size > 0:
    min_year = int(df['Application Year'].min())
    max_year = int(df['Application Year'].max())
    selected_years = st.sidebar.slider("Application Year", min_year, max_year, (min_year, max_year))
else:
    selected_years = (2020, 2025)

# --- DATA FILTERING ---
filtered_df = df[
    (df['Technology Type'].isin(selected_tech)) &
    (df['Region'].isin(selected_regions)) &
    (df['Installed Capacity (MWelec)'] >= selected_capacity[0]) &
    (df['Installed Capacity (MWelec)'] <= selected_capacity[1]) &
    (df['Application Year'] >= selected_years[0]) &
    (df['Application Year'] <= selected_years[1])
]

# --- SUMMARY METRICS ---
st.subheader("\U0001F4CA Summary Stats")
st.markdown(f"**{len(filtered_df)}** projects match your filters.")

col1, col2, col3 = st.columns(3)
col1.metric("Avg. Consent Time (days)", f"{filtered_df['Time to Consent (days)'].mean():.1f}")
col2.metric("Median Consent Time (days)", f"{filtered_df['Time to Consent (days)'].median():.1f}")
col3.metric("Max Consent Time (days)", f"{filtered_df['Time to Consent (days)'].max():.0f}")

# --- LINE CHART ---
st.subheader("\U0001F4C8 Consent Time Over Time")
if not filtered_df.empty:
    chart_df = filtered_df.groupby('Application Year')['Time to Consent (days)'].mean().reset_index()
    st.line_chart(chart_df.set_index('Application Year'))
else:
    st.warning("No data available for the selected filters.")

# --- OPTIONAL: RAW DATA TABLE ---
st.subheader("\U0001F5C3️ View Filtered Data")
with st.expander("Show raw filtered data"):
    st.dataframe(filtered_df)

# --- EXPORT DATA ---
st.subheader("\U0001F4E5 Export Data")
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Filtered CSV",
    data=csv,
    file_name=f"repd_filtered_{timestamp}.csv",
    mime="text/csv"
)