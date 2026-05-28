import os
import pandas as pd

# --- PATH CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "02_interim", "openalex_records_deduped.csv")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "02_interim", "openalex_records_2016_present.csv")

def main():
    print("Loading deduplicated dataset...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"Error: Could not find {INPUT_FILE}")
        return
        
    initial_count = len(df)
    print(f"Initial record count: {initial_count}")
    
    # 1. Ensure publication_year is a number (coercing any weird data to NaN)
    df['publication_year'] = pd.to_numeric(df['publication_year'], errors='coerce')
    
    # 2. Filter for 2016 and newer
    filtered_df = df[df['publication_year'] >= 2016]
    
    final_count = len(filtered_df)
    dropped_count = initial_count - final_count
    
    print(f"Applying temporal filter (>= 2016)...")
    print(f"Dropped {dropped_count} legacy records.")
    print(f"New review record count: {final_count}")
    
    # 3. Save the new dataset
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    filtered_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    print(f"Success! Saved filtered dataset to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()