import pandas as pd
from pathlib import Path

def export_q4_to_ris(input_file: Path, output_file: Path):
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file)

    # 1. Filter for ONLY records where Q4 (Narratives) is True
    q4_df = df[df['q4_narratives'] == True].copy()
    if len(q4_df) == 0:
        # Fallback in case booleans were saved as strings
        q4_df = df[df['q4_narratives'].astype(str).str.strip().str.lower() == 'true'].copy()

    print(f"Found {len(q4_df)} records where Q4 is True.")

    # 2. Handle missing values
    q4_df = q4_df.fillna("")

    # 3. Map OpenAlex types to RIS reference types
    type_map = {
        'article': 'JOUR',
        'book-chapter': 'CHAP',
        'dissertation': 'THES',
        'preprint': 'UNPB',
        'book': 'BOOK'
    }

    print(f"Generating RIS file at {output_file}...")
    
    # 4. Write the RIS file
    with open(output_file, 'w', encoding='utf-8') as f:
        for _, row in q4_df.iterrows():
            # Reference Type (TY must be the first tag)
            oa_type = str(row.get('type', '')).lower()
            ris_type = type_map.get(oa_type, 'JOUR') # Default to Journal Article
            f.write(f"TY  - {ris_type}\n")
            
            # Title
            if row['title']:
                f.write(f"TI  - {row['title']}\n")
                
            # Authors (RIS requires each author on a separate AU line)
            if row['authors']:
                authors = str(row['authors']).split(',')
                for author in authors:
                    f.write(f"AU  - {author.strip()}\n")
                    
            # Publication Year
            if row['publication_year']:
                try:
                    year = int(float(row['publication_year']))
                    f.write(f"PY  - {year}\n")
                except ValueError:
                    pass
                    
            # Journal / Source Name
            if row['source']:
                f.write(f"T2  - {row['source']}\n")
                
            # Volume, Issue, Pages
            if row['volume']:
                f.write(f"VL  - {row['volume']}\n")
            if row['issue']:
                f.write(f"IS  - {row['issue']}\n")
            if row['pages']:
                f.write(f"SP  - {row['pages']}\n")
                
            # DOI
            if row['doi']:
                f.write(f"DO  - {row['doi']}\n")
                
            # Abstract
            if row['abstract']:
                f.write(f"AB  - {row['abstract']}\n")
                
            # Accession Number (Perfect place to store OpenAlex ID in Covidence)
            if row['openalex_id']:
                f.write(f"AN  - {row['openalex_id']}\n")
                
            # End of Reference (ER must be the last tag, followed by a blank line)
            f.write("ER  - \n\n")

    print("RIS export complete. Ready for Zotero import!")

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / "data" / "02_interim" / "classified_2013_present.csv"
    output_path = project_root / "data" / "03_processed" / "zotero_import.ris"
    
    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    export_q4_to_ris(input_path, output_path)