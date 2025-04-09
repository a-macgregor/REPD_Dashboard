# data_utils.py
import pandas as pd

def load_data(csv_url: str) -> pd.DataFrame:
    """
    Loads and cleans the REPD data from a specified CSV URL.
    
    Parameters:
        csv_url (str): The URL to the CSV file.
    
    Returns:
        pd.DataFrame: The cleaned DataFrame.
    """
    try:
        # Load the CSV with the proper encoding
        df = pd.read_csv(csv_url, encoding='ISO-8859-1')
    except Exception as e:
        raise RuntimeError(f"Failed to load CSV from {csv_url}: {e}")
    
    # Normalize column names: trim, remove quotes, and convert to lowercase
    df.columns = df.columns.str.strip().str.replace('"', '').str.replace("'", "").str.lower()
    
    # Standardize key text fields
    if 'technology type' in df.columns:
        df['technology type'] = df['technology type'].astype(str).str.strip().str.title()
    else:
        df['technology type'] = pd.NA

    if 'region' in df.columns:
        df['region'] = df['region'].astype(str).str.strip().str.title()
    else:
        df['region'] = pd.NA

    # Clean Installed Capacity column
    if 'installed capacity (mwelec)' in df.columns:
        df['installed capacity (mwelec)'] = (
            df['installed capacity (mwelec)']
            .astype(str)
            .str.replace(',', '', regex=False)
            .str.replace('MW', '', case=False, regex=False)
            .str.strip()
            .replace('', '0')
        )
        df['installed capacity (mwelec)'] = pd.to_numeric(df['installed capacity (mwelec)'], errors='coerce')
    else:
        df['installed capacity (mwelec)'] = pd.NA

    # Handle planning dates and calculate application year and consent time
    if 'planning application submitted' in df.columns:
        # Derive application year from the submitted date
        df['application year'] = df['planning application submitted'].dt.year
        # Optionally, drop rows with NaN application years if they're not useful:
        # df = df[df['application year'].notna()]  
    else:
        df['application year'] = pd.NA


    if 'planning permission granted' in df.columns:
        df['planning permission granted'] = pd.to_datetime(df['planning permission granted'], errors='coerce')
    else:
        df['planning permission granted'] = pd.NaT

    if ('planning application submitted' in df.columns) and ('planning permission granted' in df.columns):
        df['time to consent (days)'] = (
            df['planning permission granted'] - df['planning application submitted']
        ).dt.days
    else:
        df['time to consent (days)'] = pd.NA

    return df