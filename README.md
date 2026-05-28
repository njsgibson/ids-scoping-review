# Interdisciplinary Data Stewardship (IDS) Scoping Review

This repository contains the search strings, data gathering scripts, and raw data outputs for a PRISMA-ScR scoping review on Interdisciplinary Data Stewardship (IDS). This review is part of planning for the development of a FAIR-compliant data commons for the scientific study of religion.

## Project Structure

* `config/`: Contains the master search strategy parameters (`search_terms.csv`) and its machine-readable data dictionary (`dict_search_terms.csv`).
* `data/`: 
  * `01_raw/`: Raw CSV outputs downloaded directly from the OpenAlex API.
  * `02_interim/`: Cleaned, deduplicated datasets, and LLM-classified outputs.
  * `03_processed/`: Final datasets ready for full-text review.
* `scripts/`: Sequentially numbered Python scripts for querying, fetching, processing, and classifying literature metadata using LLMs.
* `notebooks/`: Jupyter notebooks for exploratory data analysis, keyword co-occurrence, and hit-count visualizations.
* `results/`: Human-readable outputs, including interactive HTML data explorers.
  * `sandbox/`: Contains ephemeral API hit-count CSVs used to refine the search strategy.
* `manuscript/`: Contains protocol documents, search string documentation, methodological decision logs, and preprint drafts.

## Setup Instructions

1. **Clone the repository and set up a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up API Credentials:**
This project uses the OpenAlex and Gemini APIs. You must create a `.env` file in the root directory to store your credentials safely. Create a `.env` file and add the following lines:
    ```plaintext
    OPENALEX_API_KEY="your_openalex_key"
    GEMINI_API_KEY="your_gemini_key"
    EMAIL="your_email@example.com"
    ```

## Running the Pipeline

To ensure strict reproducibility, the workflow is divided into the core data pipeline and exploratory tools.

### 1. Core Data Workflow
Run these scripts sequentially from the root directory to generate the final dataset from the OpenAlex API.

* `scripts/01_fetch_records.py` - Executes the finalized search strings against the OpenAlex API, using caching and pagination to download raw article metadata into `data/01_raw/`.
* `scripts/02_deduplicate_records.py` - Cleans the raw data by removing exact ID matches, shared DOIs, and overlapping normalized titles/authors, keeping the highest-priority publication type (e.g., peer-reviewed articles over preprints). Outputs the deduplicated dataset to `data/02_interim/`.
* `scripts/03_classify_abstracts.py` - Passes the deduplciated titles and abstracts to the Gemini 2.5 Flash API for automated screening and multi-dimensional classification based on the review protocol.

### 2. Exploration & Analysis
These files were used to iteratively refine the search strategy and explore the dataset. 

* `notebooks/01_explore_hit_counts.ipynb` - Jupyter notebook used for initial search term testing, term-frequency analysis, and keyword co-occurrence analysis.
* `scripts/explore_02_generate_heatmap.py` - Creates a visual heatmap (`results/sandbox/term_heatmap_log_grid.png`) mapping search terms against disciplines and OpenAlex concepts.
* `scripts/explore_03_build_dashboard.py`: builds a local HTML DataTables explorer (`results/sandbox/explorer.html`) with regex highlighting, ad-hoc searching, dynamic year-range filtering, and real-time term frequency counts.
* `scripts/explore_filter_years.py` - Filters the deduplicated dataset by publication year (e.g., 2016 or newer).