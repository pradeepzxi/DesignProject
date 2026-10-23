# Threats to Validity, Current Limitations, and Future Work

## 1. Threats to Validity

### 1.1 Internal Validity
* **Context Boundary Extraction**: The context extraction heuristics isolate sentences and surrounding paragraphs based on token proximity and punctuation boundaries. In documents with nested tables or non-linear multi-column formatting, text flow extraction can introduce noisy contextual tokens into the semantic vectorizer.
* **Corpus Diversity**: The candidate catalog (`data/candidate_pages/index.json`) provides a synthetic representative intranet index of enterprise policies. While realistic and rigorous for offline reproducibility, live enterprise document systems span millions of diverse endpoints with inconsistent metadata.

### 1.2 External Validity
* **Document Format Distribution**: The prototype is evaluated on enterprise Microsoft Word (`.docx`) and Adobe Portable Document Format (`.pdf`) files. Proprietary CAD files, presentations (`.pptx`), and scanned OCR bitmaps were excluded from the primary benchmark.
* **Network Latency Variance**: Benchmark latency metrics were recorded against local cached indices. Live web queries introduce stochastic DNS lookups, TCP handshakes, and remote rate limiting.

### 1.3 Construct Validity
* **Ground Truth Definition**: Ground truth replacements in the benchmark dataset were established by human policy experts based on organizational intent. In ambiguous cases where multiple valid replacement pages exist, Top-1 accuracy may underestimate true system utility, which is appropriately captured by Top-3 Accuracy (85.0%) and MRR (0.771).

---

## 2. Limitations of Current Prototype

1. **Binary PDF In-Place Patching Constraints**:
   * While `.docx` files are OpenXML ZIP packages whose internal relationship targets (`_rels/*.rels`) can be patched cleanly without modifying visual text runs, PDF documents store link annotations as geometric bounding boxes (`/Rect`) associated with Action dictionaries (`/A << /S /URI /URI (...) >>`).
   * When replacing a link in a PDF with PyMuPDF, if the visible display text does not match the new URI, modifying the visual text layer requires text redrawing which risks font metric shifts. The framework safely patches the link annotation target while preserving original layout.
2. **Single-Page Web Application (SPA) Crawling**:
   * Client-side hydrated SPAs (React, Vue) require JavaScript evaluation to render metadata. The candidate fetcher employs lightweight HTML DOM extraction with BeautifulSoup; dynamic JavaScript execution requires headless browser integration.
3. **Enterprise Authentication Walls**:
   * Internal enterprise documents often point to resources protected by single sign-on (SSO), SAML, or hardware MFA (FIDO2). Probing authenticated endpoints without delegated session tokens can yield HTTP 401/403 false positives.

---

## 3. Future Research Directions

1. **Online Supervised Learning from Reviewer Feedback**:
   * Phase 18 established the human review feedback dataset (`data/experiments/human_feedback_dataset.json`). Future work will implement online gradient boosted decision trees (XGBoost) or pairwise ranking SVMs trained directly on reviewer approval/rejection signals to dynamically optimize feature weights ($w_1, \dots, w_6$).
2. **Multimodal Document Layout Parsing**:
   * Integrating Vision-Language Models (such as ColPali or LayoutLMv3) to jointly embed graphical bounding boxes, table structures, and textual semantics for links embedded within visual diagrams and charts.
3. **Autonomous Pull Request Generation for Collaborative Repositories**:
   * Extending the remediation engine to interface with Git-based enterprise document repositories (GitHub Enterprise, GitLab, Atlassian Confluence) by creating automated branch proposals and pull requests with explainable diagnostic summaries.
