# repd_update_script.py

import pandas as pd
import requests
import io
import os
import smtplib
from datetime import datetime
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# --- CONFIG ---
REPD_PAGE_URL = "https://www.gov.uk/government/publications/renewable-energy-planning-database-monthly-extract"
RAW_FOLDER = "raw_data"
LOG_FILE = "update_log.txt"
CLEANED_FILE = "cleaned_repd.csv"
DATE_TAG = datetime.today().strftime("%Y-%m-%d")

# --- LOAD ENV VARIABLES ---
load_dotenv()
EMAIL_SENDER = os.getenv("annabel.macgregor@gmail.com")
EMAIL_PASSWORD = os.getenv("gjfk dnkq qejs wsby")
EMAIL_RECEIVER = "annabel.macgregor@gmail.com"

# --- CREATE FOLDER STRUCTURE ---
os.makedirs(RAW_FOLDER, exist_ok=True)

# --- LOGGING FUNCTION ---
def log_message(message):
    with open(LOG_FILE, "a") as log:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"[{timestamp}] {message}\n")

# --- EMAIL NOTIFICATION FUNCTION ---
def send_email_notification(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        log_message("📧 Email notification sent successfully.")
    except Exception as e:
        log_message(f"❌ Failed to send email notification: {e}")

# --- FIND LATEST REPD CSV LINK ---
def get_latest_repd_csv_url():
    page = requests.get(REPD_PAGE_URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.endswith('.csv') and 'repd' in href.lower():
            return f"https://www.gov.uk{href}" if href.startswith('/') else href
    raise ValueError("❌ Could not find latest REPD CSV link on the page.")

print("🔎 Locating latest REPD CSV...")
RAW_CSV_URL = get_latest_repd_csv_url()
filename_from_url = RAW_CSV_URL.split('/')[-1]
raw_csv_path = os.path.join(RAW_FOLDER, filename_from_url)

# --- SKIP IF FILE ALREADY DOWNLOADED ---
if os.path.exists(raw_csv_path):
    print(f"⏩ Latest file '{filename_from_url}' already downloaded. Skipping download.")
    log_message(f"Skipped download: {filename_from_url} already exists.")
else:
    print(f"📥 Downloading from: {RAW_CSV_URL}")
    response = requests.get(RAW_CSV_URL)
    with open(raw_csv_path, "wb") as f:
        f.write(response.content)
    print(f"✅ Saved to: {raw_csv_path}")
    log_message(f"Downloaded and saved: {filename_from_url}")
    send_email_notification(
        subject="📥 New REPD Data Downloaded",
        body=f"A new REPD dataset ({filename_from_url}) was downloaded and added to the archive."
    )

# --- LOAD DATA ---
def load_csv(path):
    df = pd.read_csv(path, encoding='ISO-8859-1')
    df.columns = df.columns.str.strip().str.replace('"', '').str.replace("'", '')
    log_message(f"Columns in {os.path.basename(path)}: {list(df.columns)}")
    if 'Ref ID' not in df.columns:
        raise ValueError("❌ 'Ref ID' column not found. Check column names and formatting.")
    df['Ref ID'] = df['Ref ID'].astype(str).str.strip()
    return df

new_df = load_csv(raw_csv_path)

if os.path.exists(CLEANED_FILE):
    print("Loading existing cleaned data...")
    cleaned_df = load_csv(CLEANED_FILE)
else:
    print("No cleaned data found. Creating a new cleaned dataset from scratch.")
    cleaned_df = pd.DataFrame(columns=new_df.columns)

# --- MERGE NEW DATA WITH CLEANED ---
print("Merging new data with existing cleaned data...")
merged_df = pd.merge(
    cleaned_df, new_df, on='Ref ID', how='outer', suffixes=('', '_new'), indicator=True
)

# Identify truly new records
new_rows = merged_df[merged_df['_merge'] == 'right_only']

# Concatenate with existing cleaned data
updated_cleaned = pd.concat([cleaned_df, new_rows[new_df.columns]], ignore_index=True)

# Save updated cleaned file
updated_cleaned.to_csv(CLEANED_FILE, index=False, encoding='utf-8')

print(f"✅ Updated cleaned data saved to {CLEANED_FILE} with {len(new_rows)} new rows added.")
log_message(f"Merged and updated cleaned data: {len(new_rows)} new rows added.")