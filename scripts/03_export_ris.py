import os
import csv

# --- PATH CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "02_interim", "openalex_records_deduped.csv")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "03_processed")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "scoping_review_dataset.ris")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Map OpenAlex work types to standard RIS reference types
TYPE_MAPPING = {
    'article': 'JOUR',
    'book': 'BOOK',
    'book-chapter': 'CHAP',
    'dissertation': 'THES',
    'preprint': 'UNPB',
    'proceedings-article': 'CPAPER'
}

def write_ris_tag(file, tag, value):
    """Helper to write a correctly formatted RIS line (TAG  - Value)"""
    if value and str(value).strip():
        file.write(f"{tag}  - {str(value).strip()}\n")

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Could not find deduplicated data at {INPUT_FILE}")
        return

    print("Loading deduplicated records...")
    records = []
    with open(INPUT_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    print(f"Converting {len(records)} records to RIS format...")
    
    with open(OUTPUT_FILE, mode='w', encoding='utf-8') as f:
        for r in records:
            # 1. Type (Must be the first tag in an RIS record)
            oa_type = r.get('type', '').lower()
            ris_type = TYPE_MAPPING.get(oa_type, 'JOUR') # Default to Journal if unknown
            write_ris_tag(f, 'TY', ris_type)
            
            # 2. Core Metadata
            write_ris_tag(f, 'TI', r.get('title', ''))
            write_ris_tag(f, 'AB', r.get('abstract', ''))
            write_ris_tag(f, 'PY', r.get('publication_year', ''))
            write_ris_tag(f, 'DO', r.get('doi', ''))
            write_ris_tag(f, 'UR', r.get('url', ''))
            
            # 3. Source Info
            write_ris_tag(f, 'JO', r.get('source', ''))
            write_ris_tag(f, 'PB', r.get('publisher', ''))
            write_ris_tag(f, 'SN', r.get('issn', ''))
            write_ris_tag(f, 'VL', r.get('volume', ''))
            write_ris_tag(f, 'IS', r.get('issue', ''))
            write_ris_tag(f, 'SP', r.get('pages', ''))
            
            # 4. Authors (RIS requires a separate AU tag for each author)
            authors_str = r.get('authors', '')
            if authors_str:
                for author in authors_str.split(', '):
                    write_ris_tag(f, 'AU', author)
                    
            # 5. Keywords (RIS requires a separate KW tag for each keyword)
            keywords_str = r.get('keywords', '')
            if keywords_str:
                for keyword in keywords_str.split('; '):
                    write_ris_tag(f, 'KW', keyword)
            
            # 6. Store the OpenAlex ID in the Notes field just in case you need to trace it back
            write_ris_tag(f, 'N1', f"OpenAlex ID: {r.get('openalex_id', '')}")
            
            # 7. End of Record (Must be the last tag, followed by a blank line)
            f.write("ER  - \n\n")

    print(f"Success! Your ASReview/Covidence ready file is saved at: \n{OUTPUT_FILE}")

if __name__ == "__main__":
    main()