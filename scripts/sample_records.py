import pandas as pd
import argparse
from pathlib import Path

def generate_pilot_sample(input_file: Path, output_file: Path, sample_size: int, random_seed: int):
    """
    Reads a cleaned OpenAlex dataset, extracts a reproducible random sample,
    and saves it for pilot LLM testing.
    """
    if not input_file.exists():
        print(f"CRITICAL ERROR: Input file not found at {input_file}")
        return

    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file)
    
    total_records = len(df)
    print(f"Total records loaded: {total_records}")

    # Prevent errors if the requested sample is larger than the dataset
    if sample_size > total_records:
        print(f"Warning: Requested sample size ({sample_size}) exceeds total records. Using all records.")
        sample_size = total_records

    print(f"Extracting a random sample of {sample_size} records (seed={random_seed})...")
    # random_state ensures the same random sample is drawn every time the script is run
    sample_df = df.sample(n=sample_size, random_state=random_seed)

    # Ensure output directory exists (though 02_interim should already be there)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Saving sample to {output_file}...")
    sample_df.to_csv(output_file, index=False)
    print("Sampling complete!")

if __name__ == "__main__":
    # Use argparse to allow parameter changes without hardcoding into the logic
    parser = argparse.ArgumentParser(description="Generate a reproducible random sample for pilot testing.")
    parser.add_argument("--size", type=int, default=50, help="Number of records to sample (default: 50)")
    parser.add_argument("--seed", type=int, default=34, help="Random seed for reproducibility (default: 42)")
    args = parser.parse_args()

    # Define paths relative to the script location
    project_root = Path(__file__).resolve().parent.parent
    
    # Adjust the input path name to match your actual deduplicated file name
    input_path = project_root / "data" / "02_interim" / "openalex_records_deduped.csv"
    output_path = project_root / "data" / "02_interim" / "pilot_sample.csv"
    
    generate_pilot_sample(
        input_file=input_path, 
        output_file=output_path, 
        sample_size=args.size, 
        random_seed=args.seed
    )