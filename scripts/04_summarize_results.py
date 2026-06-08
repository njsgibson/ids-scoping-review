# This script produces a summary report of the LLM classification work.

import pandas as pd
import argparse
from pathlib import Path

def summarize_classification(input_file: Path):
    """
    Reads the classified CSV and prints a summary of the results.
    """
    if not input_file.exists():
        print(f"CRITICAL ERROR: Input file not found at {input_file}")
        return

    print(f"Loading data from {input_file}...\n")
    df = pd.read_csv(input_file)
    
    # 1. Overall Processing Stats
    total_records = len(df)
    
    # Count rows that failed processing (usually marked in an error log or have nulls for booleans)
    # Adjust this logic if your script flags errors differently
    if 'error_log' in df.columns:
        errors = df['error_log'].notna().sum()
    else:
        errors = 0
        
    # Count auto-excluded abstracts (from the 'rationale' column)
    auto_excluded = df['rationale'].str.contains('Auto-excluded', na=False).sum()

    successfully_processed = total_records - errors - auto_excluded

    # 2. Scope Stats (Q1)
    in_scope_df = df[df['q1_scope'] == True]
    out_of_scope_count = len(df[df['q1_scope'] == False]) - auto_excluded
    in_scope_count = len(in_scope_df)

    # 3. Category Stats (Q2, Q3, Q4) - Only calculated for in-scope papers
    q2_count = in_scope_df['q2_overview'].sum()
    q3_count = in_scope_df['q3_diagnostics_frameworks'].sum()
    q4_count = in_scope_df['q4_narratives'].sum()

    # Print the Summary Report
    print("="*50)
    print("CLASSIFICATION SUMMARY REPORT")
    print("="*50)
    print(f"Total Records in File:        {total_records}")
    print(f"  - Auto-Excluded (No abstract): {auto_excluded}")
    print(f"  - API Errors/Failed Rows:      {errors}")
    print(f"  - Successfully Classified:     {successfully_processed}")
    print("-" * 50)
    print("Q1 GATEKEEPER (Out of successfully classified)")
    print(f"  - Out of Scope (Q1=False):     {out_of_scope_count}")
    print(f"  - IN SCOPE (Q1=True):          {in_scope_count}")
    print("-" * 50)
    
    if in_scope_count > 0:
        print("CATEGORIZATIONS (For IN SCOPE papers only)")
        print(f"  - Q2 (Overviews):              {q2_count} ({q2_count/in_scope_count:.1%})")
        print(f"  - Q3 (Diagnostics/Frameworks): {q3_count} ({q3_count/in_scope_count:.1%})")
        print(f"  - Q4 (Narratives/Histories):   {q4_count} ({q4_count/in_scope_count:.1%})")
        print("="*50)
        print("* Note: A single paper can belong to multiple categories.")
    else:
        print("No papers were marked as In Scope.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize LLM classification results.")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/02_interim/classified_all.csv", 
        help="Path to the classified CSV file."
    )
    args = parser.parse_args()

    # Resolve paths relative to where the script is executed
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / args.input
    
    # Fallback if running from the root directory instead of the scripts directory
    if not input_path.exists():
        input_path = Path(args.input)

    summarize_classification(input_path)