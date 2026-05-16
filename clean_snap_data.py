import pandas as pd
import os
import re

# ─── File mapping ─────────────────────────────────────────────────────────────
files = {
    '2024-01': 'snap-cases-eligable-ind-county-jan-2024.xls',
    '2024-02': 'snap-cases-eligable-ind-by-county-feb-2024.xls',
    '2024-03': 'snap-cases-eligible-ind-by-county-march-2024.xls',
    '2024-04': 'snap-cases-eligible-ind-by-county-april-2024.xls',
    '2024-05': 'snap-cases-eligible-ind-by-county-may-2024.xls',
    '2024-06': 'snap-cases-eligible-ind-by-county-june-2024.xls',
    '2024-07': 'snap-cases-eligible-ind-by-county-july-2024.xls',
    '2024-08': 'snap-cases-eligible-ind-by-county-aug-2024.xls',
    '2024-09': 'snap-cases-eligible-ind-by-county-sept-2024.xls',
    '2024-10': 'snap-cases-eligible-ind-by-county-oct-2024.xls',
    '2024-11': 'snap-cases-eligible-ind-by-county-nov-2024.xls',
    '2024-12': 'snap-cases-eligible-ind-by-county-dec-2024.xls',
}

INPUT_DIR  = '/mnt/user-data/uploads/'
OUTPUT_DIR = '/mnt/user-data/outputs/'

# ─── Clean each file ─────────────────────────────────────────────────────────
all_months = []

for month, filename in files.items():
    filepath = os.path.join(INPUT_DIR, filename)
    
    # Read with header on row 1
    df = pd.read_excel(filepath, engine='xlrd', header=1)
    
    # Rename columns to clean names
    df.columns = [
        'county_name',
        'num_cases',
        'num_eligible_individuals',
        'ind_age_under_5',
        'ind_age_5_17',
        'ind_age_18_59',
        'ind_age_60_64',
        'ind_age_65_plus',
        'total_snap_payments',
        'avg_payment_per_case'
    ]
    
    # Remove footer rows (notes, blank rows, revision dates)
    df = df[df['county_name'].notna()]
    df = df[~df['county_name'].str.contains('Eligible|Average|Revised|Note|SNAP', 
                                             na=False, case=False)]
    df = df[df['num_cases'].notna()]
    
    # Add month column
    df['benefit_month'] = month
    
    # Convert numeric columns
    numeric_cols = ['num_cases', 'num_eligible_individuals',
                    'ind_age_under_5', 'ind_age_5_17', 'ind_age_18_59',
                    'ind_age_60_64', 'ind_age_65_plus',
                    'total_snap_payments', 'avg_payment_per_case']
    
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Clean county name
    df['county_name'] = df['county_name'].str.strip().str.title()
    
    all_months.append(df)
    print(f"✅ {month}: {len(df)} counties loaded")

# ─── Combine all months ───────────────────────────────────────────────────────
final_df = pd.concat(all_months, ignore_index=True)

# Reorder columns
final_df = final_df[[
    'benefit_month',
    'county_name',
    'num_cases',
    'num_eligible_individuals',
    'ind_age_under_5',
    'ind_age_5_17',
    'ind_age_18_59',
    'ind_age_60_64',
    'ind_age_65_plus',
    'total_snap_payments',
    'avg_payment_per_case'
]]

# ─── Save to CSV ──────────────────────────────────────────────────────────────
output_path = os.path.join(OUTPUT_DIR, 'texas_snap_enrollment_2024.csv')
final_df.to_csv(output_path, index=False)

print(f"\n✅ Done!")
print(f"Total rows: {len(final_df)}")
print(f"Months: {final_df['benefit_month'].nunique()}")
print(f"Counties per month: {final_df.groupby('benefit_month')['county_name'].count().mean():.0f}")
print(f"\nSaved to: {output_path}")
print(f"\nSample data:")
print(final_df.head(3).to_string())
print(f"\nColumn dtypes:")
print(final_df.dtypes)
