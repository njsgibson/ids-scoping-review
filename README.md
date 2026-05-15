# Interdisciplinary Data Stewardship (IDS) Scoping Review

This repository contains the search strings, data gathering scripts, and raw data outputs for a PRISMA-ScR scoping review on Interdisciplinary Data Stewardship (IDS). This review is part of planning for the development of a FAIR-compliant data commons for the scientific study of religion.

## Project Structure

* `config/`: Contains the master search strategy parameters (`search_terms.csv`) and its machine-readable data dictionary (`dict_search_terms.csv`).
* `data/`: 
  * `01_raw/`: Raw CSV outputs downloaded directly from the OpenAlex API.
  * `02_interim/`: Cleaned and deduplicated datasets.
  * `03_processed/`: Final formatted datasets (e.g., `.ris` files) ready for import into ASReview/Covidence.
* `scripts/`: Sequentially numbered Python scripts for querying, fetching, and processing literature metadata.
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
This project uses the OpenAlex API. You must create a `.env` file in the root directory to store your credentials safely. Create a `.env` file and add the following lines:
    ```plaintext
    OPENALEX_API_KEY="your_api_key_here"
    EMAIL="your_email@example.com"
    ```

## Running the Pipeline

To ensure strict reproducibility, the workflow is divided into the core data pipeline and exploratory tools.

### 1. Core Data Workflow
Run these scripts sequentially from the root directory to generate the final dataset from the OpenAlex API.

* `scripts/01_fetch_records.py` - Executes the finalized search strings against the OpenAlex API, using caching and pagination to download raw article metadata into `data/01_raw/`.
* `scripts/02_deduplicate_records.py` - Cleans the raw data by removing exact ID matches, shared DOIs, and overlapping normalized titles/authors. Outputs the clean dataset to `data/02_interim/`.
* `scripts/03_export_ris.py` - Converts the deduplicated CSV into a standardized `.ris` file in `data/03_processed/` for ingestion into active learning and screening tools like ASReview.

### 2. Exploration & Analysis
These files were used to iteratively refine the search strategy and explore the dataset. They are not required to build the final `.ris` file.

* `notebooks/01_explore_hit_counts.ipynb` - Jupyter notebook used for initial search term testing, term-frequency analysis, and keyword co-occurrence analysis.
* `scripts/explore_build_dashboard.py` - Generates an interactive HTML dashboard (`results/sandbox/explorer.html`) to visually evaluate API hits.
* `scripts/explore_generate_heatmap.py` - Creates a visual heatmap (`results/sandbox/term_heatmap_log_grid.png`) mapping search terms against disciplines and OpenAlex concepts.