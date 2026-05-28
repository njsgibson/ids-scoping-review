# SYSTEM CONTEXT & PROJECT OVERVIEW
* **Project:** Scoping Review of Interdisciplinary Data Stewardship (IDS) Literature
* **Ultimate Goal:** To inform the creation of a FAIR-compliant data commons for the scientific study of religion (bringing together social, behavioral, health, and economic sciences) by learning about prior efforts to create interdisciplinary data standards, ontologies, and infrastructure.

## 1. Project Scope & Guidelines
* **Frameworks:** Following PRISMA-ScR for the review and PRISMA-S for the search strategy.
* **Primary Objective:** Understand the practical challenges, solutions, and models for developing consensus metadata schemas and data stewardship across disciplinary boundaries.
* **Disciplinary Scope:** General domain literature, but with a special interest in disciplines known to handle data on religion (e.g., psychology, sociology, economics, political science, health, nursing, anthropology, history, medicine) and metascience/STS (Science and Technology Studies).
* **Data Level:** Interested in both dataset-level metadata and variable/item-level metadata (e.g., construct harmonization, codebooks).

## 2. Search Strategy (The Two-Bucket Approach)
The search string is built dynamically by combining two conceptual buckets using an (ANY Bucket 1) AND (ANY Bucket 2) matrix.
* **Bucket 1 (Context):** Boundaries (e.g., interdisciplinarity), metascience (e.g., research on research), collaborative dynamics (e.g., boundary spanning), and STS (e.g., sociotechnical).
* **Bucket 2 (Data Stewardship):** Infrastructure (e.g., data commons, repositories), governance (e.g., data stewardship, FAIR principles), and semantic interoperability (e.g., ontologies, metadata schemas).
* **Logic:** At least one term from either bucket must be present in the title; at least one term from the other bucket must be present in the title or abstract. OpenAlex keywords are ignored.

## 3. Technical Stack & Architecture
* **Primary Data Source:** OpenAlex API (polite pool via email authentication).
* **Language/Environment:** Python, VS Code, `.venv` using `pandas`, `seaborn`, and `matplotlib` for data manipulation and visualization, `google-genai` for LLM screening.
* **Configuration Principle:** Strict separation of logic and data. Scripts must read parameters from configuration files.

**Repository Structure:**
* `/config/search_terms.csv`: The master boolean strategy. 
* `/config/dict_search_terms.csv`: The machine-readable data dictionary for the search terms config.
* `/data/`: Contains `01_raw`, `02_interim`, and `03_processed`. (All data files ignored by Git.)
* `/scripts/`: Sequentially numbered Python scripts (`01_pilot_hit_counts.py`, `02_fetch_records.py`, etc.).
* `/results/`: Final outputs. Contains `/sandbox/` for ephemeral hit-count testing (ignored by Git).
* `/manuscript/`: For PRISMA flowcharts, and preprint drafts.
* `/prompts/`: For tracking LLM context and generation prompts.

* **Completed:** OpenAlex API search string optimized and fetched (~6,300 records). Data deduplicated based on strict title/author overlap and publication hierarchy (~5,700 records). LLM screening prompts meticulously piloted and validated against human raters.
* **Current Phase:** Running the full ~5,700 record dataset through the `05_classify_abstracts.py` LLM screening script, utilizing a cache/resume loop.
* **Next Steps:** 1. Filter the resulting CSV for `q4_narrative == True` to identify the core scoping review targets.
  2. Import the final refined target list into a tool (e.g., Covidence) for full-text retrieval and extraction.

## 4. Current State & Next Steps
* **Completed:** 
  * Repository architecture is set up. 
* **Data Flow:**
  * `data/01_raw/`: Raw CSVs from the OpenAlex API (`scripts/01_fetch_records.py`).
  * `data/02_interim/`: Cleaned/deduplicated datasets (`scripts/02_deduplicate_records.py`) and progressive LLM screening outputs (`scripts/03_classify_abstracts.py`).
  * `data/03_processed/`: Final, filtered datasets ready for full-text review (potentially in Covidence if < 500 records).
* **LLM Screening Logic:** Abstracts are passed to Gemini 2.5 Flash and evaluated against a 4-part information extraction schema:
  1. **Q1 Scope:** Is it about interdisciplinary research data stewardship?
  2. **Q2 Overview:** Is it a definitive overview of a specific initiative?
  3. **Q3 Diagnostics & Recommendations:** Does it propose macroscopic frameworks or diagnose structural challenges?
  4. **Q4 Narratives (Primary Target):** Does it retrospectively evaluate the implementation and lessons learned of an initiative?
* **Current Phase:** Running the full ~5,700 record dataset through the `03_classify_abstracts.py` LLM screening script, using a cache/resume loop.
* **Next Steps:** 
  1. Filter the resulting CSV for `q4_narrative == True` to identify the core scoping review targets.
  2. Import the final refined target list into a tool (e.g., Covidence) for full-text retrieval and extraction.

## 5. Instructions for the AI
When assisting me, adhere to the following rules:
1. **Maintain the Architecture:** Do not suggest hardcoding variables into Python scripts. Always use the existing `config/` CSVs or `.env` files.
2. **Be Modular:** Write scripts that do one thing well (following the numbering convention in the `scripts/` folder).
3. **Use Pandas Wisely:** I am working with large tabular data; default to using `pandas` for data manipulation.
4. **Stay FAIR:** Keep data management principles in mind. Emphasize reproducibility, idempotency (e.g., caching/resume loops), and clear documentation.
5. **Ask Questions:** If my intentions are unclear or appear to conflict with earlier instructions, ask for clarity or offer suggestions.
6. **Help me follow best practice:** Do not suggest code band-aids; guide me toward good data science conventions.
7. **Make the best use of OpenAlex:** Use the OpenAlex API Documentation at [https://developers.openalex.org/](https://developers.openalex.org/). Work quickly and efficiently with the OpenAlex API.
8. **Use the Gemini API efficiently and cost-effectively:** For tasks that use the Gemini API (e.g., for classification), help me meet my data quality goals while also working cost-effectively and efficiently.

Acknowledge that you have read this context, and ask me what specific file or script we are working on today.