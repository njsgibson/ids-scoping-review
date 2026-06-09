import os
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
API_KEY = os.getenv("OPENALEX_API_KEY")
EMAIL = os.getenv("EMAIL")

def fetch_enriched_openalex_data(openalex_ids):
    """Fetches full, enriched metadata from OpenAlex API in batches of 50."""
    base_url = "https://api.openalex.org/works"
    enriched_data = []
    
    # Batch IDs into chunks of 50
    batch_size = 50
    for i in range(0, len(openalex_ids), batch_size):
        batch = openalex_ids[i:i + batch_size]
        
        id_filter = "|".join(batch)
        params = {
            "filter": f"openalex_id:{id_filter}",
            "per-page": batch_size,
        }
        
        # Inject credentials safely
        if EMAIL:
            params["mailto"] = EMAIL
        if API_KEY and API_KEY != "YOUR_API_KEY":
            params["api_key"] = API_KEY
        
        print(f"Fetching batch {i//batch_size + 1} of {(len(openalex_ids)//batch_size) + 1}...")
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for work in data.get('results', []):
                # 1. Primary Location / OA Data
                loc = work.get('primary_location') or {}
                source = loc.get('source') or {}
                
                # 2. Extract Geographic & Institutional Data
                countries = set()
                institutions = set()
                for authorship in work.get('authorships', []):
                    for inst in authorship.get('institutions', []):
                        if inst.get('country_code'):
                            countries.add(inst.get('country_code'))
                        if inst.get('display_name'):
                            institutions.add(inst.get('display_name'))
                            
                # 3. Extract OpenAlex Topics
                topics = [t.get('display_name') for t in work.get('topics', [])[:3]]
                
                # 4. Extract UN Sustainable Development Goals
                sdgs = [sdg.get('display_name') for sdg in work.get('sustainable_development_goals', [])]
                
                # 5. Extract Funders (Checking both modern 'awards' and legacy 'grants')
                raw_funding = work.get('awards', []) if work.get('awards') else work.get('grants', [])
                funders = [f.get('funder_display_name') for f in raw_funding if f.get('funder_display_name')]
                
                # Build the enriched dictionary for this paper
                enriched_data.append({
                    "openalex_id": work.get('id'),
                    "source_type": source.get('type', ''),  # 'journal' or 'conference'
                    "is_oa": work.get('open_access', {}).get('is_oa', False),
                    "oa_url": work.get('open_access', {}).get('oa_url', ''),
                    "cited_by_count": work.get('cited_by_count', 0),
                    "countries": "; ".join(list(countries)),
                    "institutions": "; ".join(list(institutions)),
                    "topics": "; ".join(topics),
                    "sdgs": "; ".join(sdgs),
                    "funders": "; ".join(list(set(funders)))
                })
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching batch {i//batch_size + 1}: {e}")
            
        time.sleep(0.1) # Safe pause, even with API key
        
    return pd.DataFrame(enriched_data)

def main():
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / "data" / "02_interim" / "classified_2013_present.csv"
    output_path = project_root / "data" / "03_processed" / "enriched_screened_records.csv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading classified data from {input_path}...")
    # Force pandas to keep IDs and years clean
    df = pd.read_csv(input_path, dtype={'publication_year': 'Int64'})
    
    # Filter for the included records (Q4 == True)
    included_df = df[
        (df['q4_narratives'] == True) | 
        (df['q4_narratives'].astype(str).str.strip().str.lower() == 'true')
    ].copy()
    
    print(f"Found {len(included_df)} included records. Extracting IDs...")
    
    # Clean the OpenAlex IDs to just the 'W...' string
    included_df['clean_id'] = included_df['openalex_id'].astype(str).apply(
        lambda x: x.split('/')[-1] if 'http' in x else x
    )
    
    ids_to_fetch = included_df['clean_id'].tolist()
    
    # Fetch the new enriched data
    enriched_df = fetch_enriched_openalex_data(ids_to_fetch)
    
    print(f"Successfully fetched enriched metadata for {len(enriched_df)} records.")
    
    # Clean IDs on the enriched dataframe for a perfect merge
    enriched_df['clean_id'] = enriched_df['openalex_id'].astype(str).apply(
        lambda x: x.split('/')[-1] if 'http' in x else x
    )
    enriched_df.drop(columns=['openalex_id'], inplace=True)
    
    # Merge the new data onto your existing dataframe
    final_df = pd.merge(included_df, enriched_df, on='clean_id', how='left')
    final_df.drop(columns=['clean_id'], inplace=True)
    
    print(f"Saving enriched dataset to {output_path}...")
    final_df.to_csv(output_path, index=False)
    print("Done! Your extraction dataset is ready.")

if __name__ == "__main__":
    main()