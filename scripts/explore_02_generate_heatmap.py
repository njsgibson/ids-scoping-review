import os
import csv
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import re

# --- PATH CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

DATA_FILE = os.path.join(PROJECT_ROOT, "data", "02_interim", "openalex_records_deduped.csv")
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config", "search_terms.csv")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "results", "sandbox", "term_heatmap_log_grid.png")

def build_regex(query_string):
    """Simple whole-word regex builder."""
    base = query_string.split(' NOT ')[0].replace('(', '').replace(')', '')
    chunks = [c.strip().replace('"', '') for c in base.split(' OR ')]
    patterns = []
    for c in chunks:
        p = c.replace(' ', r'[\s\-]')
        p = r"\b" + (p[:-1] + r"\w*" if p.endswith('*') else p) + r"\b"
        patterns.append(p)
    return "|".join(patterns)

def main():
    print("Loading data for grid-enhanced log heatmap...")
    df = pd.read_csv(DATA_FILE)
    
    context_terms = {}
    data_terms = {}
    with open(CONFIG_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['status'].strip().lower() in ['potential', 'active']:
                label = row['term'].strip()
                reg = build_regex(row.get('query_string') or label)
                if row['list'].strip().lower() == 'context':
                    context_terms[label] = reg
                else:
                    data_terms[label] = reg

    matrix = pd.DataFrame(0, index=context_terms.keys(), columns=data_terms.keys())
    for _, row in df.iterrows():
        title = str(row['title']).lower()
        matched_contexts = [l for l, r in context_terms.items() if re.search(r, title, re.I)]
        matched_data = [l for l, r in data_terms.items() if re.search(r, title, re.I)]
        for c in matched_contexts:
            for d in matched_data:
                matrix.loc[c, d] += 1

    # Prune entirely empty rows/cols
    matrix = matrix.loc[(matrix.sum(axis=1) > 0), (matrix.sum(axis=0) > 0)]

    if matrix.empty:
        print("No co-occurrences found.")
        return

    # Log Scale setup
    max_val = matrix.values.max()
    norm = mcolors.LogNorm(vmin=1, vmax=max_val)

    print(f"Generating heatmap with grid lines...")
    plt.figure(figsize=(22, 14))
    
    # Set background color to light gray so the grid is visible in empty areas
    ax = sns.heatmap(
        matrix, 
        annot=True, 
        fmt="d", 
        cmap="YlGnBu", 
        norm=norm,
        mask=(matrix == 0), 
        cbar_kws={'label': 'Record Count (Log Scale)'},
        linewidths=0.5,        # Adds the grid lines
        linecolor='#e0e0e0',   # Light gray line color
        annot_kws={"size": 9}  # Slightly smaller numbers for readability
    )
    
    # Set the background of the plot (masked areas) to a very faint gray
    ax.set_facecolor('#f9f9f9')

    plt.title("Co-occurrence Heatmap (Log Scale): Grid-Enhanced View", fontsize=16, pad=20)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(rotation=0, fontsize=10)
    plt.tight_layout()

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    plt.savefig(OUTPUT_FILE, dpi=300)
    print(f"Grid-enhanced heatmap saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()