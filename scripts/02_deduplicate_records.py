import os
import csv
import re

# --- PATH CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "01_raw", "openalex_records.csv")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "02_interim")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "openalex_records_deduped.csv")
AUDIT_FILE = os.path.join(OUTPUT_DIR, "deduplication_audit.csv")

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
    def sort_key(record):
        # 1. Primary priority: Document type
        t_score = TYPE_PRIORITY.get(record.get('type', '').lower(), 99)
        
        # 2. Secondary priority: Must have an abstract (0 is better than 1)
        has_abstract = 0 if record.get('abstract', '').strip() else 1
        
        # 3. Tertiary priority: Has a publication year (0 is better than 1)
        has_year = 0 if record.get('publication_year', '').strip() else 1
        
        # 4. Quaternary priority: Total number of populated fields (negative so that a HIGHER number of fields sorts to the top)
        populated_fields = sum(1 for key, value in record.items() if str(value).strip() not in ['', 'None', 'null'])
        completeness_score = -populated_fields
        
        return (t_score, has_abstract, has_year, completeness_score)

    records.sort(key=sort_key)

    # --- STEP 2: DEDUPLICATION & AUDIT TRACKING ---
    deduped_records = []
    audit_records = []
    
    # State tracking maps signatures to the OpenAlex ID of the "Kept" record
    seen_ids = {}      
    seen_dois = {}     
    seen_titles = {}   

    stats = {"Kept": 0, "Exact OpenAlex ID": 0, "Exact DOI": 0, "Title + Author Intersection": 0}

    for r in records:
        oa_id = r.get('openalex_id', '').strip()
        doi = r.get('doi', '').strip().lower()
        norm_title = normalize_title(r.get('title', ''))
        authors_str = r.get('authors', '')
        
        current_author_set = extract_author_words(authors_str)

        status = "Kept"
        match_reason = ""
        matched_with_id = ""

        # Pass 1: Exact OpenAlex ID Match
        if oa_id and oa_id in seen_ids:
            status = "Removed"
            match_reason = "Exact OpenAlex ID"
            matched_with_id = seen_ids[oa_id]
            
        # Pass 2: Exact DOI Match
        elif doi and doi in seen_dois:
            status = "Removed"
            match_reason = "Exact DOI"
            matched_with_id = seen_dois[doi]
            
        # Pass 3: Normalized Title + Author Intersection
        else:
            if norm_title and norm_title in seen_titles:
                for existing_author_set, existing_oa_id in seen_titles[norm_title]:
                    if not current_author_set or not existing_author_set or current_author_set.intersection(existing_author_set):
                        status = "Removed"
                        match_reason = "Title + Author Intersection"
                        matched_with_id = existing_oa_id
                        break

        # Generate a unique ID to group duplicates with their kept counterpart
        fallback_id = oa_id if oa_id else (doi if doi else norm_title)
        cluster_id = fallback_id if status == "Kept" else matched_with_id

        # If it survived, log its signatures to the state trackers and add to deduped list
        if status == "Kept":
            stats["Kept"] += 1
            if oa_id: seen_ids[oa_id] = fallback_id
            if doi: seen_dois[doi] = fallback_id
            if norm_title:
                if norm_title not in seen_titles:
                    seen_titles[norm_title] = []
                seen_titles[norm_title].append((current_author_set, fallback_id))
            
            # Append to the clean dataset list
            deduped_records.append(r)
        else:
            stats[match_reason] += 1

        # Create a copy for the audit log to avoid mutating the clean dataset
        audit_row = r.copy()
        audit_row['Cluster_ID'] = cluster_id
        audit_row['Status'] = status
        audit_row['Match_Reason'] = match_reason
        audit_row['Matched_With_ID'] = matched_with_id
        audit_records.append(audit_row)

    # --- STEP 3: SAVE CLEAN DATA ---
    duplicates_removed = initial_count - len(deduped_records)
    print(f"Removed {duplicates_removed} duplicates.")
    print(f"Saving {len(deduped_records)} clean records to {OUTPUT_FILE}...")
    
    if deduped_records:
        with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=deduped_records[0].keys())
            writer.writeheader()
            writer.writerows(deduped_records)

    # --- STEP 4: SAVE AUDIT LOG ---
    # Sort audit records so clusters are grouped together ("Kept" record first, followed by its "Removed" duplicates)
    audit_records.sort(key=lambda x: (x['Cluster_ID'], 0 if x['Status'] == 'Kept' else 1))

    # Reorder columns to put audit data right at the front for easy viewing
    original_fields = list(records[0].keys())
    audit_fields = ['openalex_id', 'Cluster_ID', 'Status', 'Match_Reason', 'Matched_With_ID']
    fieldnames = audit_fields + [f for f in original_fields if f != 'openalex_id']

    print("\n--- DEDUPLICATION AUDIT STATS ---")
    print(f"Total Records Kept: {stats['Kept']}")
    print(f"Removed (Duplicate ID): {stats['Exact OpenAlex ID']}")
    print(f"Removed (Duplicate DOI): {stats['Exact DOI']}")
    print(f"Removed (Fuzzy Title+Author): {stats['Title + Author Intersection']}")
    
    print(f"\nSaving audit report to {AUDIT_FILE}...")
    
    if audit_records:
        with open(AUDIT_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(audit_records)

    print("Pipeline complete! Both clean data and audit logs are ready.")

if __name__ == "__main__":
    main()