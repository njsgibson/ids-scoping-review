import pandas as pd
import math
from pathlib import Path

def export_enriched_to_ris(input_file: Path, output_file: Path):
    print(f"Loading enriched data from {input_file}...")
    
    # Load with Int64 to prevent publication years turning into floats (e.g. 2020.0)
    df = pd.read_csv(input_file, dtype={'publication_year': 'Int64'})
    
    # Fill NAs with empty strings for easier string manipulation
    df = df.fillna("")
    
    print(f"Preparing {len(df)} records for Zotero import...")

    print(f"Generating RIS file at {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for _, row in df.iterrows():
            
            # 1. Reference Type (TY must be the first tag)
            # Use the new enriched source_type to catch conferences, fallback to general type
            source_type = str(row.get('source_type', '')).lower()
            oa_type = str(row.get('type', '')).lower()
            
            if 'conference' in source_type:
                ris_type = 'CPAPER'
            elif oa_type == 'book-chapter':
                ris_type = 'CHAP'
            elif oa_type == 'dissertation':
                ris_type = 'THES'
            elif oa_type == 'preprint':
                ris_type = 'UNPB'
            elif oa_type == 'book':
                ris_type = 'BOOK'
            else:
                ris_type = 'JOUR' # Default to Journal Article
                
            f.write(f"TY  - {ris_type}\n")
            
            # 2. Title
            if row.get('title'):
                f.write(f"TI  - {row['title']}\n")
                
            # 3. Authors (Scrub, split, and format as "Lastname, Firstnames")
            if row.get('authors'):
                clean_authors = str(row['authors']).replace(';', ',')
                for author in clean_authors.split(','):
                    author = author.strip()
                    if not author:
                        continue
                    
                    # Split the name by spaces to separate first/middle from last name
                    parts = author.split(' ')
                    if len(parts) > 1:
                        # Assume the very last word is the last name, the rest are first/middle
                        last_name = parts[-1]
                        first_names = " ".join(parts[:-1])
                        f.write(f"AU  - {last_name}, {first_names}\n")
                    else:
                        # Fallback for single-word names (e.g., institutions)
                        f.write(f"AU  - {author}\n")
                    
            # 4. Publication Year (Safely handle 9999 fallback)
            if row.get('publication_year'):
                try:
                    year = int(row['publication_year'])
                    f.write(f"PY  - {year}\n")
                except (ValueError, TypeError):
                    f.write(f"PY  - 9999\n")
            else:
                f.write(f"PY  - 9999\n")
                    
            # 5. Journal / Source Name
            if row.get('source'):
                f.write(f"T2  - {row['source']}\n")
                
            # 6. Volume, Issue, Pages
            if row.get('volume'):
                f.write(f"VL  - {row['volume']}\n")
            if row.get('issue'):
                f.write(f"IS  - {row['issue']}\n")
            if row.get('pages'):
                f.write(f"SP  - {row['pages']}\n")
                
            # 7. DOI (Clean the URL prefix so Zotero's PDF fetcher works perfectly)
            has_clean_doi = False
            if row.get('doi'):
                clean_doi = str(row['doi']).replace('https://doi.org/', '').strip()
                if clean_doi:
                    f.write(f"DO  - {clean_doi}\n")
                    has_clean_doi = True
            
            # 8. URL (Prioritize the direct Open Access PDF URL over the generic landing page)
            best_url = row.get('oa_url') if row.get('oa_url') else row.get('url')
            if best_url:
                 f.write(f"UR  - {best_url}\n")
                
            # 9. Abstract
            if row.get('abstract'):
                f.write(f"AB  - {row['abstract']}\n")
                
            # 10. Accession Number (Crucial for Covidence tracking)
            if row.get('openalex_id'):
                f.write(f"AN  - {row['openalex_id']}\n")
                
            # 11. Keywords (Zotero turns these into UI Tags)
            # Combine Topics, SDGs, and raw Keywords
            keywords = []
            if row.get('topics'): keywords.extend(str(row['topics']).split(';'))
            if row.get('sdgs'): keywords.extend(str(row['sdgs']).split(';'))
            if row.get('keywords'): keywords.extend(str(row['keywords']).split(';'))
            
            for kw in keywords:
                if kw.strip():
                    f.write(f"KW  - {kw.strip()}\n")
                    
            # 12. Internal Notes (Attaches a note in Zotero with your extracted metadata)
            note_content = "SCOPING REVIEW METADATA<br>"
            if row.get('rationale'): note_content += f"<b>Gemini Rationale:</b> {row['rationale']}<br>"
            if row.get('institutions'): note_content += f"<b>Institutions:</b> {row['institutions']}<br>"
            if row.get('countries'): note_content += f"<b>Countries:</b> {row['countries']}<br>"
            if row.get('funders'): note_content += f"<b>Funders:</b> {row['funders']}<br>"
            if row.get('cited_by_count'): note_content += f"<b>Citations:</b> {row['cited_by_count']}<br>"
            
            f.write(f"N1  - {note_content}\n")
                
            # End of Reference (Must be followed by a blank line)
            f.write("ER  - \n\n")

    print("RIS export complete. Ready for Zotero import!")

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / "data" / "03_processed" / "enriched_screened_records.csv"
    output_path = project_root / "data" / "03_processed" / "zotero_import.ris"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    export_enriched_to_ris(input_path, output_path)