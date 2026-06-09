# Scoping Review Protocol: Interdisciplinary Data Stewardship

## 1. Rationale and Objectives
The objective of this scoping review is to identify and map precedents for interdisciplinary data stewardship in any academic domain. By analyzing how cross-disciplinary teams successfully negotiated and established shared data infrastructure (e.g., data commons, metadata schemas, ontologies) and governance, this review aims to extract lessons that could be adapted for the development of a FAIR-compliant data commons for the scientific study of religion.

## 2. Information Sources and Search Strategy
The OpenAlex database was used as the sole information source, accessed programmatically via the OpenAlex API on May 27, 2026. The script used was `scripts/01_fetch_records.py`, calling on the search terms at `config/search_terms.csv`. The search targeted works classified as articles, preprints, book chapters, books, dissertations, and conference proceedings.

The search strategy was constructed around two conceptual buckets:
1.  **Context:** Terms related to cross-disciplinary collaboration (e.g., interdisciplinary, multidisciplinary);
2.  **Data stewardship:** Terms related to data interoperability and data management (e.g., semantic binding, metadata, data standards, data repository).

Initial lists of potential search terms were generated manually and expanded with the assistance of a Large Language Model (Gemini). To refine this list, the research team conducted an exploratory hit-count analysis by generating a heatmap to identify and remove overly noisy terms (e.g., `taxonom*`, `ontolog*`). Due to limitations in OpenAlex's ElasticSearch syntax regarding wildcards in compound phrases, specific search terms were exploded to explicitly query various spelling and morphological variations (e.g., "knowledge organization system" OR "knowledge organization systems" OR "knowledge organisation system" OR "knowledge organisation systems").

To balance sensitivity and precision, the API queries used a strict field-search logic. OpenAlex keywords were ignored. A work was included in the initial pull if it met one of the following conditions:
* At least one term from Bucket 1 in the **Title** AND at least one term from Bucket 2 in the **Title or Abstract**
* At least one term from Bucket 2 in the **Title** AND at least one term from Bucket 1 in the **Title or Abstract**

This search yielded 7,763 raw records. Metadata for the resulting records (including OpenAlex ID, DOI, Title, Publication Year, Authors, Source, and Abstract) were downloaded using a custom Python pipeline (`data/01_raw/openalex_records.csv`). 

## 3. Data Management and Deduplication
Following the initial API fetch, the dataset underwent a programmatic deduplication process using a custom Python script (`scripts/02_deduplicate_records.py`). The script identified duplicates by checking for exact OpenAlex ID matches, shared DOIs, and overlapping combinations of normalized titles (stripped of punctuation and casing) and author sets. When duplicates were identified, the script prioritized retention based on publication hierarchy, keeping peer-reviewed articles over book chapters, proceedings, books, dissertations, and preprints, respectively. This process removed 1,975 duplicate records, yielding a dataset of 5,788 unique records (`data/02_interim/openalex_records_deduped.csv`). Of these, 1,206 were removed for having a duplicate OpenAlex ID--an artifact of how the records were fetched from the OpenAlex API; 13 were removed for having duplicate DOIs, and 756 were removed for having matching titles and authors, despite unique OpenAlex IDs or DOIs (e.g., in the case of a preprint that was subsequently published as an article).

## 4. Automated Screening Process
Title and abstract screening was initially attempted using ASReview, an active learning tool using an SVM classifier. However, pilot testing revealed that the model struggled to accurately screen the literature. Because ASReview relies on a "bag-of-words" approach (even when using bigrams), it could not adequately distinguish among the potential *narrative intents* of the abstracts. Specifically, it failed to differentiate among (a) announcements of new data commons, (b) diagnoses of a need for a commons, and (c) retrospective evaluations of implementing a commons.

To address this limitation, the screening protocol was pivoted to use a Large Language Model (Gemini 2.5 Flash) via API to conduct semantic reasoning on the titles and abstracts. 

**Iterative Prompt Engineering & Logic Formatting**
The LLM screening prompt was developed through an iterative piloting process on random samples of records and in comparison with a human rater. The final prompt was structured around sets of inclusionary criteria designed to avoid missing in-scope papers and qualified by exclusionary criteria designed to reduce false positives. Based on piloting, each abstract was evaluated sequentially by the LLM for four independent categorizations:
1. **Scope:** Is the paper focused on backend research data stewardship across interdisciplinary boundaries (rejecting end-user apps, epistemically homogeneous data, and disciplinary mimicry)?
2. **Overview:** Does the paper provide a definitive announcement or descriptive overview of a specific interdisciplinary data commons?
3. **Diagnostics & Frameworks:** Does the paper provide a macroscopic, domain-agnostic framework for how interdisciplinary data commons *should* be built, or a structural diagnosis of systemic challenges?
4. **Narratives (Primary Inclusion):** Does the paper provide an experience report, retrospective evaluation, or lessons learned regarding the sociotechnical challenges of implementing an interdisciplinary data commons, data standard, semantic ontology, or metadata consensus effort? 

The full prompt may be found in `prompts/03_classify.md`.

**Automated Screening Results**
The full dataset of 5,788 records was processed through the LLM classification pipeline (`scripts/03_classify_abstracts.py`). 901 records lacking an abstract were automatically excluded. The results of the automated screening phase (`data/02_interim/classified_all.csv`) are as follows:

* **Total Records Processed:** 4,559
  * Auto-Excluded (No abstract): 901
  * Successfully Classified: 4,887
* **Q1 Gatekeeper (Scope Filter):**
  * Out of Scope (Q1 = False): 3,455
  * In Scope (Q1 = True): 1,432
* **Categorizations (Of the 1,432 In-Scope papers):**
  * Q2 (Overviews): 758 (52.9%)
  * Q3 (Diagnostics/Frameworks): 920 (64.2%)
  * Q4 (Narratives/Histories): 596 (41.6%)

*(Note: Papers could be assigned to multiple categories for Q2, Q3, and Q4).*

**Temporal Filtering**
The 596 records successfully flagged as True for **Question 4 (Narratives)** represent the primary target literature for this scoping review. 

At this point, we made the decision to restrict full-text review to documents with a publication year of 2013 or more recently. This temporal filter was chosen both to reduce the number of articles requiring review and to reflect several inflection points in the institutionalization of data stewardship. The US Office of Science and Technology Policy (OSTP) issued a memo in February 2013 directing federal agencies to develop plans to make the published results of federally funded research--and the underlying data--publicly available. The Research Data Alliance (RDA) was founded in March 2013. Furthermore, the G8 Science Ministers meeting in June 2013 produced a consensus that publicly funded scientific research data "should be open" and "should be easily discoverable, accessible, assessible, intelligible, useable, and wherever possible interoperable to specific quality standards." These mandates led to the drafting of the FAIR principles, initially at a workshop in Leiden, The Netherlands, in January 2014, and ultimately in the formalized publication in March 2016 (Wilkinson et al., 2016). Going back to 2013 therefore plausibly captures reflections on progress toward contemporary data commons and interoperability in the light of these major shifts in mandates and conceptual frameworks. This step was executed programmatically (`scripts/05_filter_years.py`), reducing the target pool from 596 down to 489 documents (`data/02_interim/classified_2013_present.csv`).

## 5. Data Enrichment and Full-Text Retrieval
To facilitate human screening and subsequent data extraction, the 489 target records underwent an automated metadata enrichment process. Because initial API queries were kept lightweight for the title and abstract screening phase, a custom Python script (`scripts/06_enrich_metadata.py`) was used to query the OpenAlex API for additional metadata for the target records, including citation counts, OpenAlex Topics, institutional geography, UN Sustainable Development Goals (SDGs), funding agencies, and direct Open Access PDF URLs (`data/03_processed/enriched_screened_records.csv`).

This enriched dataset was then programmatically formatted into a Research Information Systems (.ris) file using `scripts/07_export_to_ris.py` (`data/03_processed/zotero_import_final.ris`). During this export, the OpenAlex ID was embedded into the Accession Number (`AN`) tag to ensure traceability across platforms, and the LLM rationales and enriched metadata were embedded into internal notes (`N1`). 

The `.ris` file was imported into a shared Zotero Group Library. Full-text PDFs were retrieved in bulk utilizing Zotero's IP-authenticated PDF fetcher (via university VPN) combined with open-access repository data. Remaining missing PDFs were retrieved manually via institutional OpenURL resolvers.

## 6. Human Screening and Reconciliation Procedure
The retrieved PDFs and corresponding metadata will be imported into Covidence for full-text review. Covidence will map the PDFs to the bibliographic metadata via the embedded OpenAlex Accession Numbers.

Due to time and resource constraints, full-text screening will utilize a calibration exercise followed by single-reviewer screening. To ensure reliability and a shared understanding of the eligibility criteria, two reviewers will initially conduct dual, independent screening on a random pilot sample of 30 articles (approximately 6% of the full-text subset). Screener agreement for this pilot phase will be assessed using simple percentage agreement. 

During this calibration phase, any divergent screener decisions will be resolved through direct discussion between the two primary reviewers until a consensus is reached to refine the eligibility criteria. If consensus cannot be reached on a specific article, a third independent reviewer will be consulted to make the final determination. If the overall agreement threshold of ≥ 90% is not met, the reviewers will conduct a second independent pilot screening on a new random batch of 15 to 20 articles. This calibration loop will repeat until the 90% agreement threshold is achieved. 

Once consensus is firmly established, the remaining full-text articles will be divided evenly between the two reviewers for independent, single-reviewer screening. To maintain rigor during this phase, if a reviewer encounters an article with high ambiguity regarding its eligibility, they will flag the article and withhold a final vote until it can be jointly reviewed and reconciled through discussion with the second reviewer.