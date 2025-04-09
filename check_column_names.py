import pandas as pd

# Load from your downloaded file using ISO-8859-1 (a.k.a. Latin-1) which works with Windows-generated CSVs
df = pd.read_csv("repd_jan2025.csv", encoding='ISO-8859-1')

# Print all column names to check for typos or unexpected changes
print("🧾 Column Names in REPD:")
for col in df.columns:
    print(f" - '{col}'")