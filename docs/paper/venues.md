# Publication venues (researched 2026-11-17)

Labels: **[fact]** read from the cited page; **[EST]** estimate extrapolated from the prior year, not announced.
Web search was unavailable; everything below comes from fetching official pages directly. LREC/ACL-family Portuguese workshops were NOT researched (see Gaps).

## Venues

| Venue | Next dates | Limits | Language | Template | Review | Preprint |
|---|---|---|---|---|---|---|
| **STIL 2027** (SBC NLP symposium, usually co-located with BRACIS/ENIAC; STIL 2026 was Cuiabá, 19-22 Oct 2026) | **Not announced.** [fact] The bracis.sbc.org.br/2027/stil page currently only holds a copy of the 2026 text. 2026 dates for reference: abstract 30 Mar, paper deadline extended 30 Mar -> 20 Apr -> 6 May -> 15 May (grace 17 May), notification 11 Jul, camera-ready 26 Jul. **[EST] STIL 2027 deadline ~Apr-May 2027, event ~Oct 2027.** | Long: 10 pp + unlimited refs. Short: 6 pp + refs (work in progress, negative results, apps; poster). Needs Limitations, Ethics statement, gen-AI disclosure (extra page). | PT, EN or ES | SBC format (Overleaf available) | Double-anonymous | Allowed with conditions, see arXiv section |
| **BRACIS 2027** (general AI conf, Springer LNAI + SOL) | **Not announced.** [fact] 2027 page is under maintenance / template. 2026: registration 13 Apr / 27 Apr, submission 20 Apr -> 4 May, notification 1-10 Jun, camera-ready 29 Jun. **[EST] ~Apr-May 2027.** | 15 pp including refs and appendices (full). | **English only** | Springer LNCS/LNAI | Double-anonymous, mandatory reviewing by authors | Allowed: may submit an anonymous version if a non-anonymous arXiv version predates submission; tell PC chairs; do not update or promote it during review |
| **PROPOR** (biennial, ACL Anthology) | PROPOR 2026 (17th) already took place (proceedings April 2026). **[EST] next is PROPOR 2028, outside your window.** I did not find the PROPOR site or its 2026 CFP (propor.org did not respond). | Not verified | Not verified | Not verified | Not verified | Not verified |
| **Linguamática** (open-access journal, rolling) | No deadline [fact] | Research article up to 30 pp excluding refs/acks; "Projectos" short section 8 pp | PT/ES/GL/CA/EU preferred. **English accepted only if no author can write in an Iberian language and editors judge it relevant** | LaTeX template (Overleaf) | **Open review: non-anonymous, reviewers sign.** Student section exists | **Preprints (arXiv) explicitly accepted** if stated in the document |
| **JBCS** (Journal of the Brazilian Computer Society, Springer) | Rolling | Not verified (site blocked by a JS challenge) | Not verified | Not verified | Not verified | Not verified |

Sources: STIL 2026 CFP https://bracis.sbc.org.br/2026/stil/ ; STIL 2026 proceedings https://sol.sbc.org.br/index.php/stil (89 submissions, 37 accepted, 41.6%; published in SOL and ACL Anthology, indexed in DBLP); BRACIS 2026 CFP https://bracis.sbc.org.br/2026/bracis/ ; BRACIS 2027 placeholder https://bracis.sbc.org.br/2027/stil/ ; PROPOR on ACL Anthology https://aclanthology.org/venues/propor/ ; Linguamática https://www.linguamatica.com/index.php/linguamatica/about and https://www.linguamatica.com/index.php/linguamatica/about/submissions ; JBCS guidelines https://link.springer.com/journal/13173/submission-guidelines (not readable).

STIL topics list explicitly includes "Evaluation and empirical methods in NLP", "Approaches to NLP with low resources or reduced computation", "Speech processing", "Question answering" and "Dialogue and interactive systems", which matches contributions (a)-(d). STIL 2026 accepted papers included small-model evaluations for Portuguese (e.g. "Prompt Engineering for Small Language Models: Evaluating ICL for Portuguese Sentiment Analysis"), so the topic is in scope.

## arXiv

- First-time submitters must be endorsed per category. An institutional email plus a claimed co-authored paper can auto-endorse; otherwise you need one personal endorsement from an established author in that category. Start a submission, pick the category, and arXiv emails an endorsement link to give to endorsers. Do not mass-email endorsers. Source: https://info.arxiv.org/help/endorsement.html
- No endorsement difference between cs.CL and cs.LG is documented on that page; it says most top-level areas are endorsement domains. **Unverified:** whether all of cs is one domain (my belief is yes, so one endorsement would cover both). Check at submit time.
- Anonymity conflicts (STIL 2026 rules; BRACIS similar, assume STIL 2027 repeats them): the anonymity period runs from 1 month before the deadline until notification. During it you may NOT post a non-anonymous version (arXiv included), nor update or promote one. Posting before the window starts is allowed if you submit an anonymous version that doesn't cite it and you tell the chairs. Source: https://bracis.sbc.org.br/2026/stil/ . **Practical rule: post to arXiv at least ~5 weeks before the deadline, or wait until notification.** Linguamática has no conflict.

## Prior work (all returned by the arXiv API on 2026-11-17; titles as listed; I did not read full texts, so closeness is judged from titles)

Statistical / CI methodology
- Miller, "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations" (2024) https://arxiv.org/abs/2411.00640 (clustered standard errors, paired comparisons; the key reference for contribution (b))
- "Statistical Methods for Multiple Language Model Comparison on a Shared Evaluation" (2026) https://arxiv.org/abs/2608.22659
- "Spark-LLM-Eval: A Distributed Framework for Statistically Rigorous Large Language Model Evaluation" (2026) https://arxiv.org/abs/2603.28769 (bootstrap CIs in an eval framework)

Local / consumer-hardware evaluation
- "GraphRAG on Consumer Hardware: Benchmarking Local LLMs for Healthcare EHR Schema Retrieval" (2026) https://arxiv.org/abs/2605.20815
- "Benchmarking Local LLMs for Natural-Language-to-SQL Querying in Biopharmaceutical Manufacturing: An Empirical Benchmark on Consumer-Grade Hardware" (2026) https://arxiv.org/abs/2606.01338
- "Production-Grade Local LLM Inference on Apple Silicon: A Comparative Study of MLX, MLC-LLM, Ollama, llama.cpp, and PyTorch MPS" (2025) https://arxiv.org/abs/2511.05502

PT-BR evaluation
- "CAPITU: A Benchmark for Evaluating Instruction-Following in Brazilian Portuguese with Literary Context" (2026) https://arxiv.org/abs/2603.22576
- "P3B3: A Multi-Turn Conversational Benchmark for Measuring European and Brazilian Portuguese Variety Bias in LLMs" (2026) https://arxiv.org/abs/2606.16753

Local judge (contribution (d))
- "When Consistency Does Not Mean Reliability: Evaluating Local LLM Judges Against Human Ratings" (2026) https://arxiv.org/abs/2609.13824

Caveat: some arXiv IDs returned by the API have month prefixes that do not match their published dates (e.g. 2608.18107 dated June 2026); verify each link opens to the stated title before citing.

## Gaps
- LREC / ACL-family workshops for Portuguese or Ibero-American languages not researched (no search tool).
- PROPOR 2026 CFP details and the PROPOR site not retrieved; JBCS guidelines blocked.
- No STIL/BRACIS 2027 dates exist yet; all 2027 dates above are estimates.
