# Scoping Review Protocol: Interdisciplinary Data Stewardship

## 1. Rationale and Objectives
The objective of this scoping review is to identify and map existing precedents for interdisciplinary data stewardship in any academic domain. By analyzing how cross-disciplinary teams successfully negotiate and govern shared data infrastructure (e.g., data commons, metadata schemas, ontologies), this review aims to extract operational models that can be adapted for the development of a FAIR-compliant data commons for the scientific study of religion.

## 2. Information Sources and Search Strategy
The OpenAlex database was used as the sole information source, accessed programmatically via the OpenAlex API on May 27, 2026. The search targeted works classified as articles, preprints, book chapters, books, and dissertations.

The search strategy was constructed around two primary conceptual buckets:
1.  **Context (Bucket 1):** Terms related to cross-disciplinary collaboration (e.g., interdisciplinary, multidisciplinary).
2.  **Data Stewardship (Bucket 2):** Terms related to data infrastructure and governance (e.g., data commons, ontology, metadata, interoperability).

**Methodological Decision Log: Search Term Refinement**
Initial lists of potential search terms were generated manually and expanded with the assistance of a Large Language Model (Gemini). To refine this list, the research team conducted an exploratory hit-count analysis in OpenAlex, generating a heatmap to identify and exclude overly noisy terms (e.g., `taxonom*`, `ontolog*`). Due to limitations in OpenAlex's ElasticSearch syntax regarding wildcards in compound phrases, specific search terms were exploded to explicitly query various spelling and morphological variations (e.g., "knowledge organization system" OR "knowledge organization systems" OR "knowledge organisation system" OR "knowledge organisation systems").

To balance sensitivity and precision, the API queries used a strict field-search logic. OpenAlex keywords were ignored. A paper was included in the initial pull if it met one of the following conditions:
* At least one term from Bucket 1 in the **Title** AND at least one term from Bucket 2 in the **Title or Abstract**
* At least one term from Bucket 2 in the **Title** AND at least one term from Bucket 1 in the **Title or Abstract**

This search yielded 7,763 raw records. Metadata for the resulting records (including OpenAlex ID, DOI, Title, Publication Year, Authors, Source, and Abstract) were downloaded using a custom Python pipeline (`/data/01_raw/openalex_records.csv`). 

## 3. Data Management and Deduplication
Following the initial API fetch, the dataset underwent a programmatic deduplication process using a custom Python script. The script identified duplicates by checking for exact OpenAlex ID matches, shared DOIs, and overlapping combinations of normalized titles (stripped of punctuation and casing) and author sets. When duplicates were identified, the script prioritized retention based on publication hierarchy, keeping peer-reviewed articles over book chapters, proceedings, books, dissertations, and preprints, respectively. This process removed 1,975 duplicate records, yielding a dataset of 5,788 unique records (`data/02_interim/openalex_records_deduped.csv`).

## 4. Selection Process: Transition to LLM Screening
Title and abstract screening was initially attempted using ASReview, an active learning tool utilizing a SVM classifier. However, pilot testing revealed that the model struggled significantly to accurately screen the literature. Because ASReview relies on a "bag-of-words" approach (even when utilizing bigrams), it could not adequately distinguish between the *narrative intent* of the abstracts. Specifically, it failed to differentiate between (a) announcements of new data commons, (b) diagnoses of a need for a commons, and (c) retrospective evaluations of implementing a commons.

To address this limitation, the screening protocol was pivoted to use a Large Language Model (Gemini 2.5 Flash) via API to conduct semantic reasoning on the titles and abstracts. 

**Iterative Prompt Engineering**
The LLM screening prompt was developed through an iterative piloting process on random samples of records, compared against a human expert rater:
* **Pilot 1:** The initial prompt correctly excluded irrelevant records but over-included borderline works, capturing 29 out of 50 records compared to the human rater's 13.
* **Pilot 2:** A refined prompt was tested on the same 50 records. It successfully narrowed the inclusion to 11 records, catching two relevant papers missed by the human reviewer. It additionally excluded 4 papers the human had included; upon review, these 4 were deemed out of scope for the *primary* purpose of the scoping review, but contained valuable macroscopic recommendations.
* **Final Configuration:** Based on Pilot 2, the prompt was restructured away from a binary "Include/Exclude" decision into a four-part information extraction decision tree. 

Each abstract is now evaluated sequentially by the LLM for four independent categorizations:
1. **Scope:** Is the paper focused on backend research data stewardship across interdisciplinary boundaries (rejecting end-user apps, epistemically homogeneous data, and disciplinary mimicry)?
2. **Overview:** Does the paper provide a definitive announcement or descriptive overview of a specific interdisciplinary data commons?
3. **Diagnostics & Recommendations:** Does the paper provide a macroscopic framework for how interdisciplinary data commons *should* be built, or a diagnosis of systemic structural challenges?
4. **Narratives (Primary Inclusion):** Does the paper provide an experience report, retrospective evaluation, or lessons learned regarding the sociotechnical challenges of implementing an interdisciplinary data commons or achieving metadata consensus?

Papers flagged as True for Question 4 (Narratives) will be pushed forward for full-text review. If the final yield is manageable (e.g., < 500 records), full-text screening and data extraction will be managed using Covidence.