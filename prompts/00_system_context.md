# SYSTEM CONTEXT & PROJECT OVERVIEW
* **Project:** Scoping Review of Interdisciplinary Data Stewardship (IDS) Literature
* **Ultimate Goal:** To inform the creation of a FAIR-compliant data commons for the scientific study of religion (bringing together social, behavioral, health, and economic sciences) by learning about prior efforts to create interdisciplinary data standards, ontologies, and infrastructure.

## 1. Project Scope & Guidelines
* **Frameworks:** Following PRISMA-ScR for the review and PRISMA-S for the search strategy.
* **Primary Objective:** Understand the practical challenges, solutions, and models for developing consensus metadata schemas and data stewardship across disciplinary boundaries.
* **Disciplinary Scope:** General domain literature, but with a special interest on disciplines known to handle data on religion (e.g., psychology, sociology, economics, political science, health, nursing, anthropology, history, medicine) and metascience/STS (Science and Technology Studies).
* **Data Level:** Interested in both dataset-level metadata and variable/item-level metadata (e.g., construct harmonization, codebooks).

## 2. Search Strategy (The Two-Pillar Approach)
The search string is built dynamically by combining two conceptual pillars using an (ANY Pillar 1) AND (ANY Pillar 2) matrix.
* **Pillar 1 (Context):** boundaries (e.g., interdisciplinarity), metascience (e.g., research on research), collaborative dynamics (e.g., boundary spanning), and STS (e.g., epistemic cultures).
* **Pillar 2 (Data & Standards):** infrastructure (e.g., knowledge commons), interoperability (e.g., data harmonization), knowledge organization (e.g., ontologies), data management (e.g., FAIR principles), metadata, and standards.

## 3. Technical Stack & Architecture
* **Primary Database:** OpenAlex API (polite pool via email authentication).
* **Language/Environment:** Python, VS Code, `.venv` using `pandas`, `seaborn`, and `matplotlib` for data manipulation and visualization.
* **Configuration Principle:** Strict separation of logic and data. Scripts must read parameters from configuration files.

**Repository Structure:**
* `/config/search_terms.csv`: The master boolean strategy. Columns include: `list`, `subgroup`, `term`, `exclusions`, `search_field`, `source`, `date_added`, `status`, `note`. 
* `/config/dict_search_terms.csv`: The machine-readable data dictionary for the search terms config.
* `/data/`: Contains `01_raw`, `02_interim`, and `03_processed`. (All data files ignored by Git.)
* `/scripts/`: Sequentially numbered Python scripts (`01_pilot_hit_counts.py`, `02_fetch_records.py`, etc.).
* `/results/`: Final outputs. Contains `/sandbox/` for ephemeral hit-count testing (ignored by Git).
* `/manuscript/`: For PRISMA flowcharts, and preprint drafts.
* `/prompts/`: For tracking LLM context and generation prompts.

## 4. Current State & Next Steps
* **Completed:** 
  * Repository architecture is set up. 
  * `01_pilot_hit_counts.py`: tests combinations of terms from `search_terms.csv`, outputting a matrix to the `results/sandbox/` folder.
  * `02_fetch_records.py`: downloads full OpenAlex records to `data/01_raw/`.
  * `03_deduplicate_records.py`: dedupes records, outputting to `data/03_processed/openalex_records_deduped.csv`.
  * `04_build_dashboard.py`: builds a local HTML DataTables explorer with regex highlighting, ad-hoc searching, dynamic year-range filtering, and real-time term frequency counts.
  * `05_generate_heatmap.py`: A log-scale Seaborn co-occurence matrix of Context vs. Data pillars.
* **Pending/Next Actions:** 
  1. Evaluate the current selection of search terms using the explorer and heatmap by identifying noise and refining the boolean strings in `search_terms.csv`. 
  2. Run the final fetch and write an export script to format the final dataset for import into an appropriate dual-screening tool (e.g., Rayyan, Covidence).

## 5. Instructions for the AI
When assisting me, adhere to the following rules:
1. **Maintain the Architecture:** Do not suggest hardcoding variables into Python scripts. Always use the existing `config/` CSVs or `.env` files.
2. **Be Modular:** Write scripts that do one thing well (following the numbering convention in the `scripts/` folder).
3. **Use Pandas Wisely:** I am working with potentially large tabular data (abstracts, metadata); default to using `pandas` for data manipulation in scripts 02 and 03.
4. **Stay FAIR:** Keep data management principles in mind. Emphasize reproducibility and clear documentation in all code provided.
5. **Ask Questions:** If my intentions are unclear or appear to conflict with earlier instructions or with the apparent goals of the project, ask for clarity or offer suggestions.
6. **Help me follow best practice:** Do not suggest code band-aids; guide me toward good data science conventions.
7. **Make the best use of OpenAlex:** Use the OpenAlex API Documentation at [https://developers.openalex.org/](https://developers.openalex.org/). Work quickly and efficiently with the OpenAlex API.

Acknowledge that you have read this context, and ask me what specific file or script we are working on today.