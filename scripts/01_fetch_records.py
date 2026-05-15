import os
import csv
import time
import requests
import requests_cache
from dotenv import load_dotenv

# --- CACHING SETUP ---
requests_cache.install_cache('openalex_cache', backend='sqlite', expire_after=86400)

# --- CONFIGURATION & SETUP ---
load_dotenv()
API_KEY = os.getenv("OPENALEX_API_KEY")
EMAIL = os.getenv("EMAIL")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

CONFIG_FILE = os.path.join(PROJECT_ROOT, "config", "search_terms.csv")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "01_raw")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "openalex_records.csv")
BASE_URL = "https://api.openalex.org/works"
DOC_TYPES = "article|book-chapter|book|dissertation|preprint|proceedings-article"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- LOAD TERMS ---
context_terms = []
data_terms = []

print("Loading search terms from config...")
with open(CONFIG_FILE, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        if row['status'].strip().lower() in ['potential', 'active']:
            term = row['term'].strip()
            exclusions = row.get('exclusions', '').strip()
            search_field = row.get('search_field', '').strip().lower()
            
            query_string = f"({term}) NOT ({exclusions})" if exclusions else f"{term}"
            
            term_dict = {'name': term, 'query': query_string, 'search_field': search_field}
            
            category = row['list'].strip().lower()
            if category == 'context':
                context_terms.append(term_dict)
            elif category == 'data':
                data_terms.append(term_dict)

# Build context strings based on search_field constraints
c_all = " OR ".join([f"({t['query']})" for t in context_terms])
c_abs_list = [f"({t['query']})" for t in context_terms if t['search_field'] != 'title']
c_abs = " OR ".join(c_abs_list) if c_abs_list else ""

# --- HELPER FUNCTIONS ---
def reconstruct_abstract(inverted_index):
    """Reconstructs plain text from OpenAlex's abstract_inverted_index."""
    if not inverted_index:
        return ""
    try:
        max_index = max([index for positions in inverted_index.values() for index in positions])
        words = [""] * (max_index + 1)
        for word, positions in inverted_index.items():
            for pos in positions:
                words[pos] = word
        return " ".join(words)
    except Exception:
        return ""

def extract_authors(authorships):
    """Extracts a comma-separated list of author names."""
    if not authorships:
        return ""
    names = [author.get("author", {}).get("display_name", "") for author in authorships]
    return ", ".join(filter(None, names))

def fetch_paginated_records(filter_string, term_name, all_records_list):
    """Handles cursor pagination for a given filter string."""
    params = {
        "filter": filter_string,
        "select": "id,doi,title,publication_year,authorships,primary_location,biblio,abstract_inverted_index,type,keywords",
        "per-page": 100, 
        "cursor": "*",   
        "mailto": EMAIL
    }
    if API_KEY and API_KEY != "YOUR_API_KEY":
        params["api_key"] = API_KEY

    page = 1
    while params["cursor"]:
        try:
            response = requests.get(BASE_URL, params=params)
            from_cache = getattr(response, 'from_cache', False)
            cache_status = "(Cached)" if from_cache else "(Network)"
            
            response.raise_for_status()
            data = response.json()
            
            items = data.get("results", [])
            if not items:
                break
                
            print(f"  -> Page {page} {cache_status}: Fetched {len(items)} items")
                
            for item in items:
                # 1. Safely extract Primary Location data (Source, ISSN, Publisher, URL)
                source_name = ""
                issn = ""
                publisher = ""
                url = ""
                
                loc = item.get("primary_location") or {}
                if loc:
                    url = loc.get("landing_page_url", "")
                    source_obj = loc.get("source") or {}
                    if source_obj:
                        source_name = source_obj.get("display_name", "")
                        publisher = source_obj.get("host_organization_name", "")
                        issn = source_obj.get("issn_l") or (source_obj.get("issn")[0] if source_obj.get("issn") else "")

                # 2. Safely extract Biblio data (Volume, Issue, Pages)
                biblio = item.get("biblio") or {}
                vol = biblio.get("volume", "")
                iss = biblio.get("issue", "")
                f_page = biblio.get("first_page", "")
                l_page = biblio.get("last_page", "")
                pages = f"{f_page}-{l_page}" if (f_page and l_page and f_page != l_page) else str(f_page or l_page or "")

                # 3. Extract Keywords
                raw_keywords = item.get("keywords", [])
                keywords = "; ".join([kw.get("display_name", "") for kw in raw_keywords if kw.get("display_name")])

                record = {
                    "openalex_id": item.get("id", "").replace("https://openalex.org/", ""),
                    "doi": item.get("doi", ""),
                    "url": str(url),
                    "title": str(item.get("title", "") or "").replace("\n", " ").replace("\r", " "),
                    "publication_year": item.get("publication_year", ""),
                    "authors": extract_authors(item.get("authorships", [])),
                    "source": str(source_name).replace("\n", " ").replace("\r", " "),
                    "publisher": str(publisher).replace("\n", " ").replace("\r", " "),
                    "issn": str(issn),
                    "volume": str(vol) if vol else "",
                    "issue": str(iss) if iss else "",
                    "pages": pages,
                    "keywords": keywords,
                    "abstract": reconstruct_abstract(item.get("abstract_inverted_index")).replace("\n", " ").replace("\r", " "),
                    "type": item.get("type", "") 
                }
                all_records_list.append(record)
                
            params["cursor"] = data.get("meta", {}).get("next_cursor")
            page += 1
            
            if not from_cache:
                time.sleep(1.0) 
            
        except requests.exceptions.RequestException as e:
            print(f"API Error on page {page} for term '{term_name}': {e}")
            break

# --- MAIN LOGIC ---
def main():
    print("Initiating expanded dataset download from OpenAlex...")
    print("Caching is ENABLED. Reruns within 24 hours will be instantaneous.\n")
    
    all_records = []
    
    for item in data_terms:
        term_name = item['name']
        print(f"Fetching records for: [{term_name}]")
        
        q_d_all = item['query']
        q_d_abs = item['query'] if item['search_field'] != 'title' else ""
        
        filters_to_run = []
        
        if q_d_abs:
            filters_to_run.append(f"title.search:({c_all}),title_and_abstract.search:({q_d_abs}),type:{DOC_TYPES}")
        else:
            filters_to_run.append(f"title.search:({c_all}),title.search:({q_d_all}),type:{DOC_TYPES}")
            
        if c_abs:
            filters_to_run.append(f"title_and_abstract.search:({c_abs}),title.search:({q_d_all}),type:{DOC_TYPES}")

        for f_string in set(filters_to_run):
            fetch_paginated_records(f_string, term_name, all_records)

    print(f"\nSuccessfully fetched {len(all_records)} raw records (includes overlaps).")
    
    print(f"Writing dataset to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = [
            "openalex_id", "doi", "url", "title", "publication_year", "authors", 
            "source", "publisher", "issn", "volume", "issue", "pages", 
            "keywords", "abstract", "type"
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)
        
    print("Download complete! Your raw data is ready for deduplication (03_deduplicate_records.py).")

if __name__ == "__main__":
    main()