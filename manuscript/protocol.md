# Scoping Review Protocol: Interdisciplinary Data Stewardship

## 1. Rationale and Objectives
The objective of this scoping review is to identify and map existing precedents for interdisciplinary data stewardship in any academic domain. By analyzing how cross-disciplinary teams successfully negotiate and govern shared data infrastructure (e.g., data commons, metadata schemas, ontologies), this review aims to extract operational models that can be adapted for the development of a FAIR-compliant data commons for the scientific study of religion.

## 2. Information Sources and Search Strategy
The OpenAlex database was used as the sole information source, accessed programmatically via the OpenAlex API. 

The search strategy was constructed around two primary conceptual pillars:
1.  **Context (Pillar 1):** Terms related to cross-disciplinary collaboration (e.g., interdisciplinary, multidisciplinary).
2.  **Data Stewardship (Pillar 2):** Terms related to data infrastructure and governance (e.g., data commons, ontology, metadata, interoperability).

To balance sensitivity and precision, the API queries used a strict field-search logic. A paper was included if it met one of the following conditions:
* Pillar 1 term in the **Title** AND Pillar 2 term in the **Title or Abstract**
* Pillar 1 term in the **Title or Abstract** AND Pillar 2 term in the **Title**

**Methodological Decision Log: Breadth vs. Exclusions**
During the initial search refinement phase, keyword co-occurrence analysis revealed a high volume of literature intersecting with computational methods (e.g., artificial intelligence, machine learning, and data mining). Pilot testing of Boolean exclusions (e.g., `NOT "artificial intelligence"`) yielded marginal reductions in dataset size (less than 1% reduction) due to overlapping vocabulary across domains (a "Boolean backdoor" effect). 

More importantly, excluding these terms risked prematurely discarding relevant literature. Consequently, the decision was made to retain the broad search string without Boolean exclusions. This preserves maximum sensitivity across all domains and defers the nuance of distinguishing between purely technical/algorithmic papers and relevant stewardship practices to the machine learning-assisted screening phase.

## 3. Data Management and Deduplication
Metadata for the resulting records (including OpenAlex ID, DOI, Title, Publication Year, Authors, Source, and Abstract) was downloaded using a custom Python pipeline. 

A hierarchical deduplication algorithm was applied to the raw dataset. To ensure the richest metadata was retained for the screening phase, records were prioritized by publication type (Article > Book Chapter > Proceedings > Book > Dissertation > Preprint) and by the presence of a complete abstract. 

Duplicates were identified and removed sequentially based on:
1.  Exact OpenAlex ID match.
2.  Exact DOI match.
3.  Normalized Title + Author Intersection: Titles were aggressively normalized (stripping punctuation and casing). If records shared a normalized title and possessed at least one overlapping author name, they were merged. Publication year was deliberately excluded from this matching criteria to successfully identify and merge preprint versions with their later peer-reviewed publication counterparts.

The finalized, deduplicated dataset was exported to a standard `.ris` format.

## 4. Selection Process
Title and abstract screening will be conducted using ASReview, an active learning tool designed for systematic reviews. 

**Model Configuration:**
* **Feature Extraction:** TF-IDF (Term Frequency-Inverse Document Frequency) will be used to mathematically cluster the distinct vocabularies of different epistemic cultures.
* **Classifier:** Naive Bayes (or Support Vector Machine) will be used to calculate relevance probabilities.

**Prior Knowledge Seeding:**
To help the model navigate the broad disciplinary vocabulary captured by the search string, the active learning model will be seeded with prior knowledge. The review team will manually select 3 to 5 "Gold Standard" papers that represent human-driven, interdisciplinary consensus in data stewardship. By marking these as "Relevant," the model will be trained to recognize the sociotechnical linguistic fingerprint of the target literature. This will allow ASReview to iteratively learn the distinction between papers that merely use data terminology in passing (e.g., applying an existing algorithm) and those that actively discuss the stewardship and governance of data, regardless of the specific scientific domain. 

Screening will stop when a predefined stopping heuristic is met (e.g., consecutive irrelevant records presented by the model).