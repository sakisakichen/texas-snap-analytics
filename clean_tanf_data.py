import pandas as pd
import os
import sys

sys.path.append("..")  # 往上一層找 utils.py
from utils import clean_currency, clean_numeric, extract_month

# ── 設定路徑 ──────────────────────────────────────────────
DATA_DIR = "./2024 TANF Enrollment"
OUTPUT_FILE = "texas_tanf_enrollment_2024.csv"

# ── 過濾關鍵字 ────────────────────────────────────────────
EXCLUDE_KEYWORDS = [
    "state total", "state office", "unknown",
    "total", "subtotal", "tanf", "basic", "program",
    "county", "data source", "case =", "one-time",
    "grandparent", "forecasting", "recipients",
    "cases", "average", "payment"
]

# ── 縣市名稱驗證 ──────────────────────────────────────────
def is_valid_county(val):
    if pd.isna(val):
        return False
    val_str = str(val).strip().lower()
    if val_str == "":
        return False
    for kw in EXCLUDE_KEYWORDS:
        if kw in val_str:
            return False
    return True

# ── 單一檔案處理 ──────────────────────────────────────────
def process_file(filepath, month_num):
    df_raw = pd.read_excel(
        filepath,
        sheet_name="Recipients",
        header=None,
        engine="openpyxl"
    )
    

    

    results = []

    for _, row in df_raw.iterrows():
        county_val = row.iloc[1] if len(row) > 0 else None

        if not is_valid_county(county_val):
            continue

        county_name = str(county_val).strip().title()

        # ── TANF Basic（左半，Col 0~7）────────────────────
        try:
            basic = {
                "benefit_month": f"2024-{month_num:02d}-01",
                "county": county_name,
                "program_type": "TANF Basic",
                "cases": clean_numeric(row.iloc[2]),
                "recipients": clean_numeric(row.iloc[3]),
                "children": clean_numeric(row.iloc[4]),
                "adults": clean_numeric(row.iloc[5]),
                "payments": clean_currency(row.iloc[6]),
                "avg_payment_per_case": clean_currency(row.iloc[7]),
                "avg_payment_per_recipient": clean_currency(row.iloc[8]),
            }
            results.append(basic)
        except Exception:
            pass
 
        # ── TANF State Program（右半，Col 10~16）─────────
        if len(row) > 16:
            try:
                state = {
                    "benefit_month": f"2024-{month_num:02d}-01",
                    "county": county_name,
                    "program_type": "TANF State Program",
                    "cases": clean_numeric(row.iloc[10]),
                    "recipients": clean_numeric(row.iloc[11]),
                    "children": clean_numeric(row.iloc[12]),
                    "adults": clean_numeric(row.iloc[13]),
                    "payments": clean_currency(row.iloc[14]),
                    "avg_payment_per_case": clean_currency(row.iloc[15]),
                    "avg_payment_per_recipient": clean_currency(row.iloc[16]),
                }
                results.append(state)

            except Exception as e:
                print(f"  ⚠️ State error: {e}")  # 改這行
                
    return results

# ── 主流程 ────────────────────────────────────────────────
all_records = []

for filename in sorted(os.listdir(DATA_DIR)):
    if not filename.endswith(".xlsx"):
        continue

    month_num = extract_month(filename)
    if month_num is None:
        print(f"⚠️  無法判斷月份：{filename}")
        continue

    filepath = os.path.join(DATA_DIR, filename)
    records = process_file(filepath, month_num)
    all_records.extend(records)
    print(f"✅ {filename} → {len(records)} rows")

# ── 輸出 ──────────────────────────────────────────────────
df_final = pd.DataFrame(all_records)
df_final = df_final.dropna(subset=["county"])
df_final = df_final.sort_values(["benefit_month", "program_type", "county"])
df_final.to_csv(OUTPUT_FILE, index=False)

print(f"\n🎉 完成！共 {len(df_final)} rows → {OUTPUT_FILE}")
print(df_final.head(10))
