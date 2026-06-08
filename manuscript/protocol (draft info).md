# Scoping Review Protocol: Interdisciplinary Data Stewardship

## 1. Rationale and Objectives
The objective of this scoping review is to identify and map precedents for interdisciplinary data stewardship in any academic domain. By analyzing how cross-disciplinary teams successfully negotiated and established shared data infrastructure (e.g., data commons, metadata schemas, ontologies) and governance, this review aims to extract lessons that could be adapted for the development of a FAIR-compliant data commons for the scientific study of religion.

## 2. Information Sources and Search Strategy
The OpenAlex database was used as the sole information source, accessed programmatically via the OpenAlex API on May 27, 2026. The search targeted works classified as articles, preprints, book chapters, books, dissertations, and conference proceedings.

The search strategy was constructed around two conceptual buckets:
1.  **1. Context:** Terms related to cross-disciplinary collaboration (e.g., interdisciplinary, multidisciplinary);
2.  **2. Data stewardship:** Terms related to data interoperability and data management (e.g., semantic binding, metadata, data standards, data repository).

**Methodological Decision Log: Search Term Refinement**
Initial lists of potential search terms were generated manually and expanded with the assistance of a Large Language Model (Gemini). To refine this list, the research team conducted an exploratory hit-count analysis by generating a heatmap to identify and remove overly noisy terms (e.g., `taxonom*`, `ontolog*`). Due to limitations in OpenAlex's ElasticSearch syntax regarding wildcards in compound phrases, specific search terms were exploded to explicitly query various spelling and morphological variations (e.g., "knowledge organization system" OR "knowledge organization systems" OR "knowledge organisation system" OR "knowledge organisation systems").

To balance sensitivity and precision, the API queries used a strict field-search logic. OpenAlex keywords were ignored. A work was included in the initial pull if it met one of the following conditions:
* At least one term from Bucket 1 in the **Title** AND at least one term from Bucket 2 in the **Title or Abstract**
* At least one term from Bucket 2 in the **Title** AND at least one term from Bucket 1 in the **Title or Abstract**

This search yielded 7,763 raw records. Metadata for the resulting records (including OpenAlex ID, DOI, Title, Publication Year, Authors, Source, and Abstract) were downloaded using a custom Python pipeline (`/data/01_raw/openalex_records.csv`). 

## 3. Data Management and Deduplication
Following the initial API fetch, the dataset underwent a programmatic deduplication process using a custom Python script. The script identified duplicates by checking for exact OpenAlex ID matches, shared DOIs, and overlapping combinations of normalized titles (stripped of punctuation and casing) and author sets. When duplicates were identified, the script prioritized retention based on publication hierarchy, keeping peer-reviewed articles over book chapters, proceedings, books, dissertations, and preprints, respectively. This process removed 1,975 duplicate records, yielding a dataset of 5,788 unique records (`data/02_interim/openalex_records_deduped.csv`). Of these, 1,206 were removed for having a duplicate OpenAlex ID--an artifact of how the records were fetched from the OpenAlex API; 13 were removed for having duplicate DOIs, and 756 were removed for having matching titles and authors, despite unique OpenAlex IDs or DOIs (e.g., in the case of a preprint that was subsequently published as an article).

## 4. Screening Process
Title and abstract screening was initially attempted using ASReview, an active learning tool utilizing an SVM classifier. However, pilot testing revealed that the model struggled significantly to accurately screen the literature. Because ASReview relies on a "bag-of-words" approach (even when utilizing bigrams), it could not adequately distinguish between the *narrative intent* of the abstracts. Specifically, it failed to differentiate between (a) announcements of new data commons, (b) diagnoses of a need for a commons, and (c) retrospective evaluations of implementing a commons.

To address this limitation, the screening protocol was pivoted to use a Large Language Model (Gemini 2.5 Flash) via API to conduct semantic reasoning on the titles and abstracts. 

**Iterative Prompt Engineering & Logic Formatting**
The LLM screening prompt was developed through an iterative piloting process on random samples of records and in comparison with a human rater. The final prompt was structured around sets of inclusionary criteria designed to avoid missing in-scope papers qualified by exclusionary criteria designed to reduce false positives. Based on piloting, each abstract was evaluated sequentially by the LLM for four independent categorizations:
1. **Scope:** Is the paper focused on backend research data stewardship across interdisciplinary boundaries (rejecting end-user apps, epistemically homogeneous data, and disciplinary mimicry)?
2. **Overview:** Does the paper provide a definitive announcement or descriptive overview of a specific interdisciplinary data commons?
3. **Diagnostics & Frameworks:** Does the paper provide a macroscopic, domain-agnostic framework for how interdisciplinary data commons *should* be built, or a structural diagnosis of systemic challenges?
4. **Narratives (Primary Inclusion):** Does the paper provide an experience report, retrospective evaluation, or lessons learned regarding the sociotechnical challenges of implementing an interdisciplinary data commons, data standard, semantic ontology, or metadata consensus effort? 

The full prompt may be found in `prompts/03_classify.md`.

**Automated Screening Results**
The full dataset of 5,788 records was processed through the LLM classification pipeline. 901 records lacking an abstract were automatically excluded. The results of the automated screening phase are as follows:

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

**Transition to Human Screening**
The 596 records successfully flagged as True for **Question 4 (Narratives)** represent the primary target literature for this scoping review. 

At this point, we made a decision to restrict full-text review to documents with a publication year of 2013 or more recently. This year was chosen both to reduce the number of articles requiring review but also to reflect several inflection points in the institutionalization of data stewardship. The US Office of Science and Technology Policy (OSTP) issued a memo in February 2013 directing federal agencies to develop plans to make the published results of federally funded research--and the underlying data--publicly available. The Research Data Alliance (RDA) was founded in March 2013. And the G8 Science Ministers meeting in June 2013 produced a consensus that publicly funded scientific research data "should be open" and "should be easily discoverable, accessible, assessible, intelligible, useable, and wherever possible interoperable to specific quality standards." These mandates in turn led to the drafting of the FAIR principles, initially at a workshop in Leiden, Netherlands, in January 2014, and ultimately in the formalized publication in March 2016 (Wilkinson et al., 2016). Going back to 2013 therefore plausibly captures reflections on progress toward contemporary data commons and interoperability in the light of these major shifts in mandates and conceptual frameworks.

This reduced the documents for full-text review from 596 down to 489. 