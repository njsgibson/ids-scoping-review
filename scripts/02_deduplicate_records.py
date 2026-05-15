import os
import csv
import re

# --- PATH CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "01_raw", "openalex_records.csv")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "02_interim")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "openalex_records_deduped.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define hierarchy: Lower number = higher priority to keep
TYPE_PRIORITY = {
    'article': 1,
    'book-chapter': 2,
    'proceedings-article': 3,
    'book': 4,
    'dissertation': 5,
    'preprint': 6
}

def normalize_title(title):
    """Strips all punctuation, spaces, and casing for aggressive matching."""
    return re.sub(r'[^a-z0-9]', '', str(title).lower())

def extract_author_words(authors_str):
    """Extracts all names/words (3+ letters) from the author string into a set."""
    if not authors_str:
        return set()
    words = re.findall(r'[a-z]{3,}', str(authors_str).lower())
    return set(words)

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Could not find raw data at {INPUT_FILE}")
        return

    print("Loading raw records...")
    records = []
    with open(INPUT_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    initial_count = len(records)
    print(f"Loaded {initial_count} records.")

    # --- STEP 1: SORTING ---
    # We sort so the BEST version of a duplicate is seen first and kept.
    def sort_key(record):
        t_score = TYPE_PRIORITY.get(record.get('type', '').lower(), 99)
        # Prioritize records that actually have an abstract (0 comes before 1 in sort)
        has_abstract = 0 if record.get('abstract', '').strip() else 1
        return (t_score, has_abstract)

    records.sort(key=sort_key)

    # --- STEP 2: DEDUPLICATION ---
    deduped_records = []
    
    seen_ids = set()
    seen_dois = set()
    seen_titles = {} 

    for r in records:
        oa_id = r.get('openalex_id', '').strip()
        doi = r.get('doi', '').strip().lower()
        norm_title = normalize_title(r.get('title', ''))
        authors_str = r.get('authors', '')
        
        current_author_set = extract_author_words(authors_str)

        # Pass 1: Exact OpenAlex ID Match (Catches overlapping loop queries instantly)
        if oa_id and oa_id in seen_ids:
            continue
            
        # Pass 2: Exact DOI Match (Catches preprints/articles that share a DOI)
        if doi and doi in seen_dois:
            continue
            
        # Pass 3: Normalized Title + Author Intersection (Catches preprints/articles with different years/DOIs)
        is_duplicate = False
        if norm_title and norm_title in seen_titles:
            for existing_author_set in seen_titles[norm_title]:
                # It's a duplicate if authors overlap, OR if metadata is so bad we can't tell
                if not current_author_set or not existing_author_set or current_author_set.intersection(existing_author_set):
                    is_duplicate = True
                    break
            
        if is_duplicate:
            continue

        # If it survives all checks, log its signatures and keep it
        if oa_id: seen_ids.add(oa_id)
        if doi: seen_dois.add(doi)
        if norm_title:
            if norm_title not in seen_titles:
                seen_titles[norm_title] = []
            seen_titles[norm_title].append(current_author_set)
            
        deduped_records.append(r)

    final_count = len(deduped_records)
    duplicates_removed = initial_count - final_count

    # --- STEP 3: SAVE ---
    print(f"Removed {duplicates_removed} duplicates.")
    print(f"Saving {final_count} clean records to {OUTPUT_FILE}...")
    
    if deduped_records:
        with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as f:
            # Dynamically grab the new RIS fieldnames
            writer = csv.DictWriter(f, fieldnames=deduped_records[0].keys())
            writer.writeheader()
            writer.writerows(deduped_records)

    print("Deduplication complete! Data is ready for ASReview/Covidence export.")

if __name__ == "__main__":
    main()