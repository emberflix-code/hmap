# Reference Verification, Batch 2 (refs 14 to 25 + 4 new documents)

**Source of truth audited:** `docs/v5_modules/build_chapters_docx_v5.py` (refs list lines 1608-1634; in-text citations throughout).
**Verification date:** 2026-10-21. Every fact below was checked against an online source fetched during this session (Crossref, Europe PMC full text, Semantic Scholar, WHO IRIS PDF, privacy.gov.ph, CHED legacy site / university-hosted CHED PDF, PCHRD PDF). Nothing is asserted from memory. Where a full text was paywalled the claim is marked CANNOT VERIFY rather than assumed.
**Note on suggested sentences:** written without em dashes, per the manuscript rule.

---

## 1. Summary table

| # | Reference | Exists? | Metadata correct? | Claims supported? | Reliability tier | Verdict |
|---|---|---|---|---|---|---|
| 14 | Lawson (2018) *Bayesian disease mapping* (3rd ed.) | Yes | Yes (publisher imprint is Chapman & Hall/CRC; DOI can be added) | Partly. Cluster detection: yes. Heat-map colours, KDE, "validates open-source web mapping": not supported | Book (academic monograph) | FIX CLAIM |
| 15 | NPC (2016) Circular No. 16-01 | Yes (dated 10 Oct 2016) | **URL in refs is dead (404)**; the circular has been **repealed by NPC Circular No. 2023-06** | Access-control claims: yes. "Public health purposes" wording: overstated | Official government issuance | FIX METADATA + REPLACE/ADD 2023-06 |
| 16 | Nykiforuk & Flaman (2011) *Health Promotion Practice* 12(1) | Yes | Yes | Partly. "Superior to tabular analysis" and "validates open-source web mapping / Leaflet" are not in the source | Peer-reviewed journal (review) | FIX CLAIM |
| 17 | Olana et al. (2025) *Transbound. Emerg. Dis.* Art. 7480710 | Yes | Yes (issue 1 can be added) | **No for Prophet.** Paper's Table 1: Prophet test MASE 1.23 (worse than seasonal naive); highest test MAE/RMSE of all six models. Manuscript says Prophet was "operationally viable", "validated", and that Olana "supports the choice of Prophet" | Peer-reviewed journal (Wiley) | FIX CLAIM (serious, 9 locations) |
| 18 | RA 10173 (2012) Data Privacy Act | Yes | Title truncated; not italicised | Access control, proportionality: yes. "Requires audit logging", "requires RBAC": overstated (the Act names neither) | Official law | FIX METADATA + FIX CLAIM |
| 19 | Richey & Klein (2007) | Yes | Yes | Mostly. R&K's term is "design and development research" (product and tool research), not "Applied Developmental Research" | Book (methods text) | FIX CLAIM (wording only) |
| 20 | Shaman & Karspeck (2012) PNAS | Yes | Yes | **No.** Paper uses data assimilation from numerical weather prediction, not "machine learning"; manuscript twice says it establishes ML-based forecasting | Peer-reviewed journal | FIX CLAIM |
| 21 | Shi et al. (2016) EHP 124(9) | Yes | Yes | Yes (prior audit fix applied: now described as LASSO) | Peer-reviewed journal | KEEP |
| 22 | Srivastava et al. (2025) *Infectious Diseases* 57(1) | Yes, real paper; all 5 authors, title, journal, vol/iss/pages, DOI match Crossref | Yes | Partly. Review is about diagnosis, treatment and drug discovery; mentions "detection and surveillance" and "predict disease outbreaks" only in passing. 4 of 6 manuscript claims (decision-support principle, "clinician-accessible tools", "slow reporting", "confirming... improve detection speed") are CANNOT VERIFY / OVERSTATED | Peer-reviewed journal (narrative review, closed access) | FIX CLAIM; add Villanueva-Miranda et al. (2025) for surveillance claims |
| 23 | Stroup et al. (1989) Stat Med 8(3) | Yes | Yes | Yes (with nuance: historical-limits method uses 4-week periods, 15 baseline values, 2 SD) | Peer-reviewed journal | KEEP |
| 24 | Taylor & Letham (2018) | Yes | Yes | Yes, except Ch.3 line 1268: says weekly + yearly seasonality "enabled to capture intra-annual and multi-year periodicity"; Prophet's weekly term is day-of-week and **`ml/train_prophet.py` sets `weekly_seasonality=False`** | Peer-reviewed journal | FIX CLAIM (1 sentence) |
| 25 | WHO (2014) WHO/HSE/GCR/LYO/2014.4 | Yes | Yes | **No for the threshold formula.** Document never mentions "EWARN", "mean", or "standard deviation"; it is about EWAR (Early Warning and Response) with event-based surveillance. The mean + 2 SD rule is attributed to "WHO EWARN (WHO, 2014)" in ~10 places. The actual WHO EWARN guideline (2012) says "there are no globally fixed criteria" and uses 1-case / doubling thresholds | Official WHO technical document | FIX CLAIM (serious, ~14 locations) |

### Most serious problems (top 5)
1. **Olana et al. (2025) is cited as evidence FOR Prophet, but its Table 1 shows Prophet was worse than a seasonal-naive benchmark (MASE 1.23) and had the highest test MAE and RMSE of all six models.** Nine manuscript passages depend on the opposite reading. The previous audit's "softened" wording ("Prophet ... among the operationally viable alternatives") is still wrong.
2. **The mean + 2 SD threshold is attributed to "WHO EWARN methodology (WHO, 2014)" throughout.** WHO/HSE/GCR/LYO/2014.4 contains no such formula and does not use the term EWARN. The WHO EWARN guideline (2012) uses fixed-count and doubling thresholds and states there are no globally fixed criteria. Re-attribute the formula to Stroup et al. (1989) / historical-limits literature (and DOH PIDSR practice, if confirmed in the MOP).
3. **NPC Circular 16-01 has been repealed by NPC Circular No. 2023-06** (per NPC's own FAQ), and the URL in the reference list returns 404. Also, 16-01 Sec. 18 (and its successor) requires multi-factor authentication for online access to personal data, which the manuscript's HRMO-session design does not mention.
4. **Shaman & Karspeck (2012) is presented as foundational evidence for machine-learning forecasting.** It uses data assimilation, a numerical-weather-prediction technique, so the attribution is wrong in 2 places.
5. **Srivastava et al. (2025) is now a real paper, but it covers diagnosis and treatment.** Four surveillance-specific claims (decision-support principle, clinician-accessible tools, slow manual reporting, "confirming" faster detection) cannot be traced to it. A verified systematic review on AI in early-warning surveillance (Villanueva-Miranda et al., 2025) fits these claims better. Related: RA 10173 is cited as "requiring" audit logging and RBAC, and the Act names neither.

---

## 2. Per-reference findings

### 14. Lawson (2018)

**Fetched:** `https://api.crossref.org/works/10.1201/9781351271769`; Routledge product page (ISBN 9781138575424) for TOC.
**Metadata:** Crossref: *Bayesian Disease Mapping: Hierarchical Modeling in Spatial Epidemiology*, Andrew B. Lawson, Chapman and Hall/CRC, 2018, edition 3. The manuscript entry is correct. Using "CRC Press" is acceptable; the exact imprint is Chapman and Hall/CRC. Adding the DOI is optional but helps.
**TOC (verified):** 1 Introduction; 2 Bayesian Inference and Modeling; ... 5 Disease Map Reconstruction and Relative Risk Estimation; 6 Disease Cluster Detection; 7 Regression and Ecological Analysis; 8 Putative Hazard Modeling; ... 12 Spatiotemporal Disease Mapping; 13 Disease Map Surveillance; 14 Infectious Disease Modeling; ... 18 R Code for Thematic Mapping.

**Corrected APA 7 entry (optional improvement):**
> Lawson, A. B. (2018). *Bayesian disease mapping: Hierarchical modeling in spatial epidemiology* (3rd ed.). Chapman and Hall/CRC. https://doi.org/10.1201/9781351271769

| Line | Manuscript text (short) | Class | Note / suggested fix |
|---|---|---|---|
| 627 | "Lawson (2018) similarly explains that spatial epidemiology uses GIS tools to detect clustering patterns and assess environmental risk factors" | SUPPORTED | Ch. 6 (cluster detection) and Ch. 8 (putative hazard modeling) cover this. You could drop "GIS tools" for accuracy: "...uses disease-mapping methods to detect clustering and assess environmental (putative-hazard) risk factors". |
| 647 | Heat maps: warm colours for high concentration, "enhancing situational awareness ... (Lawson, 2018)" | CANNOT VERIFY / weak fit | Lawson is a Bayesian relative-risk text; the TOC has no heat-map content. Suggest: "Disease maps of relative risk or case density support the recognition of geographic hotspots (Lawson, 2018)." and drop the colour-gradient detail from the citation. |
| 654 | "KDE ... producing a continuous ... surface of disease concentration (Lawson, 2018)" | CANNOT VERIFY | Not visible in TOC. Replace with a verified KDE-in-epidemiology source, e.g. Bithell, J. F. (1990). An application of density estimation to geographical epidemiology. *Statistics in Medicine, 9*(6), 691–701. https://doi.org/10.1002/sim.4780090616 (Crossref verified). |
| 960 | Module 2 is supported by Lawson, Boulos, Nykiforuk, "which collectively validate open-source web mapping" | MISATTRIBUTED (for Lawson) | Lawson does not address web mapping. Suggest: "Module 2 is grounded in disease-mapping methodology (Lawson, 2018) and in evidence that GIS supports public-health surveillance (Nykiforuk & Flaman, 2011), with Boulos et al. (2011) documenting web-based, standards-compliant GIS for health surveillance." |
| 1137 | GIS principles "grounded in ... (Nykiforuk & Flaman, 2011; Lawson, 2018)" | SUPPORTED | Keep. |

### 15. National Privacy Commission (2016) NPC Circular No. 16-01

**Fetched:** `https://privacy.gov.ph/npc-circular-no-16-01/` (manuscript URL) returned **HTTP 404**; `https://privacy.gov.ph/?p=35285`, which redirects to `https://privacy.gov.ph/npc-circular-16-01-security-of-personal-data-in-government-agencies/` (200, full text read); NPC FAQ on Circular 2023-06 (privacy.gov.ph/wp-content/uploads/2024/12/v12-19-2024_FAQ-NPC-Circular-2023-06_NNJ_JDN.pdf). Direct fetch was bot-blocked (403), but search excerpts of the FAQ were retrieved. digitalpolicyalert.org tracker for 2023-06.
**Verified content:** Date 10 October 2016; addressed to all government agencies including LGUs; Subject "Security of Personal Data in Government Agencies". Sec. 15 Restricted access: access granted "through the issuance of a security clearance by the head of agency, only when the performance of official functions ... directly depends on such access". Sec. 18: "Agency personnel who access personal data online shall authenticate their identity via a secure encrypted link and must use multi-factor authentication." It also requires access-control systems that record "when, where, and by whom" data centres are accessed, plus logs for physical files.
**Status:** NPC FAQ: "Circular 2023-06 repeals Circular 16-01". 2023-06 is titled "Security of Personal Data in the Government and the Private Sector". Tracker: adopted 1 Dec 2023, in force 30 Mar 2024. **Confirm the promulgation date on the official text before citing.**

**Corrected APA 7 entries:**
> National Privacy Commission. (2016, October 10). *NPC Circular No. 16-01: Security of personal data in government agencies*. https://privacy.gov.ph/npc-circular-16-01-security-of-personal-data-in-government-agencies/

Because the proposal describes a system to be deployed in 2026, cite the circular in force now (add it; keep 16-01 only as historical context, or drop it):
> National Privacy Commission. (2023). *NPC Circular No. 2023-06: Security of personal data in the government and the private sector*. https://privacy.gov.ph/ *(confirm exact page URL and date on privacy.gov.ph)*

| Line | Manuscript text | Class | Note / suggested fix |
|---|---|---|---|
| 803 | "...National Privacy Commission (NPC, 2016) guidelines for access-controlled processing of sensitive health information in government systems" | SUPPORTED (Sec. 15, 18) | Add 2023-06. Note: Sec. 18 MFA requirement should be acknowledged in the authentication design (Ch.3), or the panel may raise it. |
| 835 | "NPC (2016) has issued guidelines emphasizing that personal data collected for public health purposes must be protected through technical and organizational measures appropriate to the risk" | OVERSTATED | 16-01 is not specific to public health. Suggest: "The National Privacy Commission requires government agencies to protect personal data through organizational, physical, and technical measures identified through a privacy impact assessment, to restrict access to personnel with security clearance, and to require multi-factor authentication for online access (NPC, 2016, 2023)." |
| 997-998, 1038, 1594 | "National Privacy Commission guidelines" (no year) | SUPPORTED but undated | Add year in text: (NPC, 2023). |

### 16. Nykiforuk & Flaman (2011)

**Fetched:** Crossref `10.1177/1524839909334624`; Europe PMC abstract (PMID 19546198).
**Metadata:** Matches: Candace I. J. Nykiforuk & Laura M. Flaman; *Health Promotion Practice* 12(1), 63–73; print Jan 2011 (online first 22 Jun 2009). APA uses 2011. Correct as is.
**Abstract evidence:** review "conducted in 2007"; four themes: "disease surveillance (n = 227), risk analysis (n = 189), health access and planning (n = 138), and community health profiling (n = 115)"; it "critically examine[s] the issues, strengths, and challenges".

| Line | Manuscript text | Class | Note / suggested fix |
|---|---|---|---|
| 623 | GIS "an established tool for mapping disease distribution" | SUPPORTED | Disease surveillance is the largest theme. |
| 623-627 | "found that GIS-based approaches consistently provided superior capacity for spatial disease visualization compared with traditional tabular analysis" | OVERSTATED | No comparative finding in the abstract; it is a scoping-type review. Suggest: "Nykiforuk and Flaman (2011) reviewed GIS applications in public health and found disease surveillance to be the most common use (227 studies), followed by risk analysis, health access and planning, and community health profiling, while noting methodological challenges such as data quality and confidentiality." *(If you keep "data quality and confidentiality", check the full text; otherwise end after "community health profiling".)* |
| 960-962 | "...collectively validate open-source web mapping" | MISATTRIBUTED | The review covers literature up to 2007 and is not about open-source web mapping. Use the Module 2 rewrite under ref 14. |
| 984-986 | "Leaflet.js with OpenStreetMap, have reached functional maturity ... (Boulos et al., 2011; Nykiforuk & Flaman, 2011)" | MISATTRIBUTED | Leaflet was first released in 2011, after this review's 2007 search. Remove Nykiforuk from this sentence. |
| 1136 | GIS literature grounding | SUPPORTED | Keep. |

### 17. Olana et al. (2025)

**Fetched:** Crossref `10.1155/tbed/7480710`; Europe PMC full-text XML (PMC12543447), read in full for Methods, Table 1, Results and Discussion.
**Metadata:** Matches: Kenny Oriel Aranas Olana, Napaphat Poprom, Pallop Siewchaisakul, Veerasak Punyapornwithaya, Aksara Thongprachum; *Transboundary and Emerging Diseases* vol. 2025, issue 1, article 7480710 (online 15 Oct 2025). Correct; APA can include issue (1).
**Key evidence (verbatim):**
- Data: "reported dengue cases in the Philippine provinces and chartered cities from January 2017 to December 2024 was obtained from the Philippine Department of Health, Epidemiology Bureau", which follows the PIDSR 2014 MOP case classification. Training: Jan 2017 to Dec 2023; test: Jan to Dec 2024; monthly.
- Table 1 (test set) MAE / MAPE / MASE / RMSE: SARIMA 16116.83 / 32.22 / 1.16 / 23719.20; **NNAR 5506.36 / 13.23 / 0.40 / 8256.99**; **RF 10887.72 / 27.95 / 0.78 / 16322.85**; LSTM 14905.57 / 52.86 / 1.07 / 18703.31; TBATS 16190.12 / 37.76 / 1.17 / 21862.34; **Prophet 17129.33 / 40.23 / 1.23 / 23807.89**.
- "Both NNAR and RF achieved MASE values below 1.0, indicating superior performance compared to a seasonal naive benchmark, while the other models performed worse than this simple baseline (MASE > 1.0). This indicates that NNAR and RF showed acceptable generalization capability."
- "SARIMA and the Prophet intervals go below zero."

**Corrected APA 7 entry:**
> Olana, K. O. A., Poprom, N., Siewchaisakul, P., Punyapornwithaya, V., & Thongprachum, A. (2025). Spatial distribution analysis and comparative forecasting of dengue resurgence in the Philippines (2025–2027): A nationwide study. *Transboundary and Emerging Diseases, 2025*(1), Article 7480710. https://doi.org/10.1155/tbed/7480710

| Line | Manuscript text | Class | Suggested corrected sentence |
|---|---|---|---|
| 397-400 | "...Olana et al. (2025) at the national level, have demonstrated that AI models such as Random Forest and Prophet can achieve reliable predictive accuracy" | MISATTRIBUTED (Prophet) | "...and Olana et al. (2025) at the national level have shown that machine learning models such as Random Forest and Neural Network Autoregression can forecast dengue incidence more accurately than a seasonal-naive benchmark, although not every model does so; Prophet, for example, did not outperform that benchmark in the national Philippine test." |
| 434 | standalone models not integrated into platforms | SUPPORTED | Keep. |
| 466-468 | Obj. 1d: Prophet + RF "validated in the Philippine context by Olana et al. (2025) and Carvajal et al. (2018)" | MISATTRIBUTED | "...using the Random Forest algorithm, informed by Philippine dengue forecasting studies (Carvajal et al., 2018; Olana et al., 2025), with each Prophet forecast gated by a seasonal-naive backtest." |
| 534 | Significance: gap "identified in the Philippine machine learning literature by Carvajal et al. (2018) and Olana et al. (2025)" (no operational platform) | SUPPORTED | Keep. |
| 554-556 | Scope: "Prophet-based weekly case forecasts and Random Forest ... consistent with methodologies validated in the Philippine context by Carvajal et al. (2018) and Olana et al. (2025)" | MISATTRIBUTED (Prophet) | "...Random Forest barangay risk classifications informed by Philippine dengue forecasting studies (Carvajal et al., 2018; Olana et al., 2025), with Prophet forecasts released only for diseases where they outperform a seasonal-naive baseline." |
| 735-745 | "...While NNAR achieved the highest predictive accuracy ..., Prophet and Random Forest were among the models that produced operationally acceptable forecasts ... providing the most current Philippine evidence for the forecasting approach employed in H-MAP" | MISATTRIBUTED | "Olana et al. (2025) compared SARIMA, NNAR, Random Forest, LSTM, TBATS, and Prophet for nationwide Philippine dengue forecasting using monthly 2017 to 2024 surveillance data from the DOH Epidemiology Bureau. On the 2024 hold-out year, only NNAR (MASE = 0.40) and Random Forest (MASE = 0.78) outperformed a seasonal-naive benchmark, while Prophet performed worse than that benchmark (MASE = 1.23). This evidence supports H-MAP's use of Random Forest and motivates its policy of deploying Prophet only for diseases in which it beats a seasonal-naive baseline in local backtesting." |
| 775-777 | did not integrate models into platforms | SUPPORTED | Keep. |
| 902-911 | "...with NNAR achieving the highest accuracy and Prophet and Random Forest among the operationally viable alternatives" | MISATTRIBUTED (Prophet) | "...with NNAR achieving the highest accuracy, Random Forest the second-best, and Prophet, TBATS, SARIMA, and LSTM failing to outperform a seasonal-naive benchmark on the 2024 test year." |
| 967-969 | "Olana et al. (2025) for the most current Philippine evidence on Prophet's viability for dengue forecasting" | MISATTRIBUTED | "...and Olana et al. (2025) for current Philippine evidence that forecasting models must be benchmarked against a seasonal-naive baseline, which Random Forest passed and Prophet did not at the national monthly scale." |
| 994-997 | Synthesis: "...Prophet and Random Forest among the operationally viable alternatives" | MISATTRIBUTED | Same fix as 902-911. Also delete the lead sentence at 990-992 ("Prophet and Random Forest have demonstrated reliable performance ... in the Philippine context specifically"). It is unsupported for Prophet. |
| 1001-1004 | Carvajal and Olana produced standalone models | SUPPORTED | Keep. |
| 1035-1036 | IPO: "Prophet additive regression model (Taylor & Letham, 2018; Olana et al., 2025)" | OVERSTATED | Cite Olana under a "benchmarking" knowledge item, not as Prophet support. |
| 1141-1142 | "two machine learning approaches previously validated in the Philippine dengue context, namely Prophet ... (Taylor & Letham, 2018; Olana et al., 2025)" | MISATTRIBUTED | "...namely Prophet time-series forecasting (Taylor & Letham, 2018), which H-MAP subjects to a seasonal-naive backtest because it underperformed that benchmark in national Philippine dengue data (Olana et al., 2025), and Random Forest classification (Breiman, 2001; Carvajal et al., 2018; Olana et al., 2025)." |
| 1281-1283 | "Olana et al. (2025) reported analogous backtest comparisons at the national level for dengue, supporting the choice of Prophet for diseases with strong seasonal structure." | **CONTRADICTED** | "Olana et al. (2025) reported an analogous hold-out comparison for national Philippine dengue data in which Prophet did not outperform a seasonal-naive benchmark (MASE = 1.23), which is precisely why H-MAP gates each disease's Prophet model on a local seasonal-naive backtest." *(This was audit Step 4, para 188, and it was never applied.)* |

### 18. Republic Act No. 10173 (2012)

**Fetched:** `https://privacy.gov.ph/data-privacy-act/` (full text, 200). The Official Gazette URL in refs returned 403 to an automated client (bot protection; the URL pattern is the standard OG one for an Act approved 15 Aug 2012, so it is likely valid for browsers).
**Verified text:** Full title: "An Act Protecting Individual Personal Information in Information and Communications Systems in the Government and the Private Sector, Creating for This Purpose a National Privacy Commission, and for Other Purposes". Sec. 3(l)(2): health information is *sensitive personal information*. Sec. 11(d): personal information must be "adequate and not excessive". Sec. 20(a): "reasonable and appropriate organizational, physical and technical measures". Sec. 22: heads of agencies are responsible for securing sensitive personal information. Sec. 23(a): "no employee of the government shall have access to sensitive personal information ... unless the employee has received a security clearance from the head of the source agency". The Act does not mention audit logs or role-based access control.

**Corrected APA 7 entry** (title complete and italicised; APA 7 has no fixed rule for Philippine statutes, so this follows the reference-list form already used):
> Republic Act No. 10173. (2012). *An act protecting individual personal information in information and communications systems in the government and the private sector, creating for this purpose a National Privacy Commission, and for other purposes* (Data Privacy Act of 2012). https://www.officialgazette.gov.ph/2012/08/15/republic-act-no-10173/

| Line | Manuscript text | Class | Suggested fix |
|---|---|---|---|
| 414-415 | access restricted to active employees, "directly addressing the access control requirements of RA 10173" | SUPPORTED (Sec. 20, 23) | Keep. Optionally name Sec. 23. |
| 470-471, 1584 | "CSV exports with full audit logging in compliance with the Data Privacy Act" | OVERSTATED | "...with audit logging as a technical security measure under Section 20 of Republic Act No. 10173 (2012) and NPC issuances (NPC, 2023)." |
| 832-834 | RA 10173 "requires that health information systems implement access controls that limit data exposure to personnel with a legitimate need" | OVERSTATED (mild) | "Republic Act No. 10173 classifies health information as sensitive personal information and bars government employees from accessing such information without a security clearance from the head of the agency (Republic Act No. 10173, 2012, Secs. 3, 23)." |
| 846 | "data minimization principle under RA 10173" | SUPPORTED | The Act's term is *proportionality* (Sec. 11(d), "adequate and not excessive"). Consider "proportionality (data minimization) principle". |
| 955 | RBAC and employment-verified access as requirements "under RA 10173" | OVERSTATED | "...access restrictions required for sensitive personal information under Republic Act No. 10173 (2012), which H-MAP implements through role-based access control." |
| 976 | "RA 10173 requirements for audit logging" | OVERSTATED | "...and in the security-measure obligations of Republic Act No. 10173 (2012) and NPC issuances, which H-MAP satisfies in part through audit logging." |
| 997-999 | RA 10173 and NPC "establish data privacy and RBAC as non-negotiable requirements" | OVERSTATED (RBAC) | Replace "data privacy and RBAC" with "access restriction and security safeguards". |
| 1074, 1243, 1413 | audit log "in support of RA 10173 accountability requirements" | SUPPORTED | Sec. 21 is the Principle of Accountability. "In support of" is fine. |

### 19. Richey & Klein (2007)

**Fetched:** Crossref `10.4324/9780203826034` (Routledge 2014 e-reissue of the same book); FSU-hosted Richey & Klein (2005) article and SAGE encyclopedia entry (search excerpts) for the definition.
**Metadata:** *Design and development research: Methods, strategies, and issues*, Lawrence Erlbaum Associates, 2007. Correct. KEEP as is (the 2007 print has no DOI; do not mix in the 2014 Routledge DOI unless you cite that version).
**Definition:** design and development research is "the systematic study of design, development, and evaluation processes" aimed at an empirical basis for creating products and tools. R&K split it into (1) product and tool research and (2) model research.

| Line | Manuscript text | Class | Suggested fix |
|---|---|---|---|
| 1124-1126 | "This study employs an Applied Developmental Research design, which is appropriate for projects that produce a functional technological artifact and subject it to systematic evaluation (Richey & Klein, 2007)." | OVERSTATED (terminology) | Substance is supported, but R&K do not use the label "Applied Developmental Research". Suggest: "This study employs a design and development research approach, specifically product and tool research, which Richey and Klein (2007) describe as the systematic study of the design, development, and evaluation of a specific product or tool." If the program requires the label "Applied Developmental Research", keep it but write "...consistent with what Richey and Klein (2007) term design and development research". |

### 20. Shaman & Karspeck (2012)

**Fetched:** Crossref `10.1073/pnas.1208772109`; Europe PMC abstract (PMC3528592).
**Metadata:** Matches: PNAS 109(50), 20425–20430. Correct.
**Abstract evidence:** "we develop a framework for initializing real-time forecasts of seasonal influenza outbreaks, using a data assimilation technique commonly applied in numerical weather prediction ... web-based estimates ... 2003-2008 influenza seasons in New York City ... predictions of peak timing can be made more than 7 wk in advance."

| Line | Manuscript text | Class | Suggested fix |
|---|---|---|---|
| 727-730 | "...forecasted using time-series modeling and statistical inference techniques, establishing the foundational evidence that machine learning-based forecasting can provide operationally useful lead time" | MISATTRIBUTED | "Shaman and Karspeck (2012) showed that seasonal influenza outbreaks in New York City could be forecast in real time by combining an epidemic model with a data-assimilation technique borrowed from numerical weather prediction, predicting peak timing more than seven weeks in advance and establishing that quantitative outbreak forecasting can give public health agencies useful lead time." |
| 874-877 | "...establishing that machine learning methods can generate reliable short-term outbreak predictions" | MISATTRIBUTED | Use the same sentence, or: "...demonstrated that statistically rigorous real-time influenza forecasts are feasible when surveillance data are assimilated into an epidemic model." |

### 21. Shi et al. (2016)

**Fetched:** Crossref `10.1289/ehp.1509981`; Europe PMC abstract (PMC5010413).
**Metadata:** Matches: all 14 authors in order; EHP 124(9), 1369–1375 (online Dec 2015, issue Sept 2016). Correct.
**Abstract evidence:** "statistical models using least absolute shrinkage and selection operator (LASSO) methods to forecast the weekly incidence of dengue notifications over a 3-month time horizon ... recent case data, meteorological data, vector surveillance data, and population-based national statistics ... the LASSO approach provided more accurate forecasts than the other methods".

| Line | Manuscript text | Class |
|---|---|---|
| 766-770 | LASSO models integrating case, meteorological, vector and population data, 3-month-ahead forecasts | SUPPORTED |
| 882-886 | same, Singapore | SUPPORTED |
| 971-973 | "Chakraborty ... and Shi ... providing parallel evidence ... that hybrid and regularized statistical-learning approaches support dengue early-warning systems" | SUPPORTED (for Shi) |

Verdict: KEEP. The prior audit's fix has been applied.

### 22. Srivastava et al. (2025)

**Fetched:** Crossref `10.1080/23744235.2024.2425712`; Europe PMC (PMID 39540872, abstract); Semantic Scholar (status CLOSED access, publicationTypes Review); tandfonline.com page returned 403, so the full text could not be read.
**Authenticity check (as requested):**
- DOI resolves to: "Role of artificial intelligence in early diagnosis and treatment of infectious diseases".
- Authors (Crossref order): Vartika Srivastava, Ravinder Kumar, Mohmmad Younus Wani, Keven Robinson, Aijaz Ahmad. All five match the reference list, in order.
- Journal: *Infectious Diseases* (Informa/Taylor & Francis), vol. 57, issue 1, pp. 1–26. Online 14 Nov 2024, issue 2 Jan 2025, so APA year 2025 is correct.
- **The entry is genuine and its metadata is exact.** The earlier fabricated "Srivastava, Sharma, & Verma (2024)" entry is gone from the script.

**Content check:** The abstract describes "AI-driven diagnostic tools ... enhance the accuracy and efficiency of disease detection and surveillance", "the potential of AI to predict disease outbreaks, optimise treatment strategies, and personalise interventions", drug discovery, and "ethical considerations, challenges, and limitations". So the paper is mainly about clinical diagnosis, treatment and drug discovery. Surveillance and outbreak prediction appear as one strand. It supports generic statements that AI can aid detection, surveillance and outbreak prediction. It does not demonstrably support public-health-surveillance-specific claims about operations, reporting delays, dashboards or decision-support design.

**Recommended companion source (verified via Crossref + Europe PMC):**
> Villanueva-Miranda, I., Xiao, G., & Xie, Y. (2025). Artificial intelligence in early warning systems for infectious disease surveillance: A systematic review. *Frontiers in Public Health, 13*, Article 1609615. https://doi.org/10.3389/fpubh.2025.1609615

PRISMA review of 67 studies. Abstract: "The major benefits identified include earlier outbreak detection and improved prediction accuracy. However, significant challenges persist regarding data quality and bias, model transparency ..., system integration difficulties, and ethical considerations"; it calls for "collaboration between AI developers and public health experts."

| Line | Manuscript text | Class | Suggested fix |
|---|---|---|---|
| 352-356 | AI "has significantly expanded the analytical capabilities ... enabling automated outbreak detection, predictive forecasting, and data-driven decision support ... (Srivastava et al., 2025)" | OVERSTATED | "...has expanded the analytical capabilities available to health agencies, with reviews reporting earlier outbreak detection and improved prediction accuracy in AI-enabled early warning systems (Srivastava et al., 2025; Villanueva-Miranda et al., 2025)." |
| 393-395 | "traditional surveillance methods are constrained by manual data collection and slow reporting (Srivastava et al., 2025)" | CANNOT VERIFY | Use WHO (2014), verified: "data provided by conventional surveillance ... is often delayed, incomplete, or concerns only a limited number of known public health risks." Suggest: "...reflecting the broader observation that conventional surveillance data are often delayed and incomplete (WHO, 2014)." |
| 707-712 | "documented the expanding role of AI in early diagnosis and treatment ... noting that AI-assisted surveillance systems analyze historical data patterns, generate automated alerts, and support clinical and public health decision-making in ways that manual surveillance cannot match" | First clause SUPPORTED; remainder OVERSTATED | "Srivastava et al. (2025) reviewed the role of AI in the early diagnosis and treatment of infectious diseases, including its use in disease detection, surveillance, and outbreak prediction, and Villanueva-Miranda et al. (2025) found in a systematic review of 67 studies that AI-enabled early warning systems were associated with earlier outbreak detection and improved prediction accuracy." |
| 722-723 | "principle identified by Srivastava et al. (2025) that AI in surveillance should serve as a decision-support layer rather than a replacement for epidemiological expertise" | CANNOT VERIFY | "This design reflects the recommendation that AI in early warning systems be developed in collaboration with public health experts, with attention to model transparency (Villanueva-Miranda et al., 2025); in H-MAP, AI outputs serve as decision support rather than as a replacement for epidemiological judgment." |
| 819-824 | Srivastava "confirm that AI outputs are most useful when integrated into clinician-accessible tools" | CANNOT VERIFY | Cite Villanueva-Miranda et al. (2025) for "system integration difficulties" as a barrier: "...a systematic review identified system integration as a persistent barrier to AI early warning systems (Villanueva-Miranda et al., 2025), supporting the principle that embedding AI outputs in accessible visualization tools bridges model accuracy and practical utility." |
| 887-890 | "provided a comprehensive review ... confirming that AI-assisted surveillance and decision-support systems improve detection speed and decision-support quality across a range of health system contexts" | OVERSTATED | "Srivastava et al. (2025) provided a narrative review of AI in the early diagnosis and treatment of infectious diseases, including outbreak prediction, while noting ethical and implementation limitations." |

### 23. Stroup et al. (1989)

**Fetched:** Crossref `10.1002/sim.4780080312`; Europe PMC abstract (PMID 2540519); CDC MMWR "Update: Graphic Method for Presentation of Notifiable Disease Data, United States, 1990" (cdc.gov/mmwr/preview/mmwrhtml/00001917.htm) for the operational historical-limits rule.
**Metadata:** Matches: Stroup, D. F., Williamson, G. D., Herndon, J. L., & Karon, J. M.; *Statistics in Medicine* 8(3), 323–329. Correct.
**Evidence:** The abstract says the paper "discusses three analytic methods for identifying aberrations ... illustrated on ... the National Notifiable Diseases Surveillance System". The CDC MMWR describes the resulting historical-limits display: "compares provisional reports for a 4-week period with the mean of 15 4-week totals ... Ratios that exceed national historical limits (calculated based on two standard deviations of the historical baseline)".

| Line | Manuscript text | Class | Note |
|---|---|---|---|
| 680-683 | threshold = mean of same week across previous five years + 2 SD, "grounded in the aberration-detection statistical literature (Stroup et al., 1989; Hutwagner et al., 2003)" | SUPPORTED (with nuance) | Stroup's historical-limits method uses 4-week periods and 15 baseline values (comparable, preceding and following periods over 5 years), with 2 SD limits. H-MAP's single-week, 5-value variant is an adaptation. Consider adding "an adaptation of the historical-limits method". Make Stroup, not WHO, the primary source of the formula (see ref 25). |

Verdict: KEEP. This should become the main citation for the threshold.

### 24. Taylor & Letham (2018)

**Fetched:** Crossref `10.1080/00031305.2017.1380080`; Semantic Scholar abstract; Prophet official documentation (facebook.github.io/prophet). The PeerJ preprint returned 403. Also read `ml/train_prophet.py` lines 250-254 to compare against the Ch.3 description.
**Metadata:** Matches: *The American Statistician* 72(1), 37–45. Correct.
**Evidence:** abstract: "a modular regression model with interpretable parameters ... analyst-in-the-loop". Docs: "additive model where non-linear trends are fit with yearly, weekly, and daily seasonality, plus holiday effects ... robust to missing data and shifts in the trend ... released by Facebook's Core Data Science team."

| Line | Manuscript text | Class | Suggested fix |
|---|---|---|---|
| 731-734 | Prophet developed by "Meta's Core Data Science team"; trend, yearly, weekly, holiday components; robust to missing data | SUPPORTED | Minor: "Facebook's (now Meta's) Core Data Science team". |
| 1100, 1229, 967 | Prophet definition / foundational methodology | SUPPORTED | Keep. |
| 1266-1268 | "with weekly and yearly seasonality components enabled to capture both intra-annual and multi-year periodicity (Taylor & Letham, 2018)" | INACCURATE (and contradicts code) | In Prophet, "weekly seasonality" is a day-of-week pattern, which cannot be identified from weekly-aggregated counts. Yearly seasonality captures *intra-annual* patterns. Neither captures multi-year cycles. `ml/train_prophet.py` sets `yearly_seasonality=True, weekly_seasonality=False`. Suggest: "...with the yearly seasonality component enabled to capture the intra-annual (seasonal) pattern and the weekly (day-of-week) component disabled because the series are aggregated by morbidity week (Taylor & Letham, 2018)." |
| 1274-1275 | "eighty percent posterior confidence intervals" | Not cited, but imprecise | Prophet's default fit gives 80% *uncertainty intervals* (MAP fit with simulated trend uncertainty), not posterior intervals unless MCMC sampling is used. Suggest "eighty percent uncertainty intervals". |

### 25. WHO (2014) WHO/HSE/GCR/LYO/2014.4

**Fetched:** `https://iris.who.int/handle/10665/112667`, which redirects to the item page; metadata: title "Early detection, assessment and response to acute public health events: implementation of early warning and response with a focus on event-based surveillance: interim version", WHO, 2014-04-29, report no. WHO/HSE/GCR/LYO/2014.4. English PDF (64 pp.) downloaded and searched in full. For comparison, the WHO EWARN guideline was also fetched: *Outbreak surveillance and response in humanitarian emergencies: WHO guidelines for EWARN implementation* (WHO/HSE/GAR/DCE/2012.1; PDF via medbox.org; WHO page at who.int/publications/i/item/outbreak-surveillance-and-response-in-humanitarian-emergencies-who-guidelines-for-ewarn-implementation).
**Metadata:** The entry is correct.
**What WHO 2014 actually says:**
- It uses the acronym **EWAR** (Early Warning and Response), never "EWARN" or "Early Warning and Response Network".
- No occurrence of "standard deviation", "mean", or a five-year baseline.
- On thresholds: "For more common diseases, thresholds can be set depending upon the rate observed over a given time period ..., or based on an increase in comparison with baseline data". Also: "Data are analysed in comparison with baseline values and thresholds to determine unusual disease patterns."
- On conventional surveillance: "data provided by conventional surveillance is essential to EWAR, this is often delayed, incomplete, or concerns only a limited number of known public health risks."
- On automation: "In modern surveillance systems, this can be automated to a high degree. Ideally, statistical methodology is used to verify clustering, patterns or trends in data."

**What WHO EWARN (2012) says:** "Although there are internationally accepted signals that constitute an alert for some conditions, there are no globally fixed criteria, and thresholds may need to be revised". Its Table 1 examples are "One case", "double the weekly average number of cases", "Twice the average number of cases seen in the previous 3 weeks". There is no mean + 2 SD. EWARN is also a humanitarian-emergency system, not routine city surveillance.

**Conclusion:** The prior audit swapped WHO 2018 for WHO 2014 correctly at the bibliographic level, but its premise that 2014.4 "prescribes the EWARN ... framework H-MAP uses" and the mean + 2 SD formula is false.

**APA entry (correct as is; optional report-number style):**
> World Health Organization. (2014). *Early detection, assessment and response to acute public health events: Implementation of early warning and response with a focus on event-based surveillance* (Interim version; WHO/HSE/GCR/LYO/2014.4). https://iris.who.int/handle/10665/112667

| Line(s) | Manuscript text | Class | Suggested fix |
|---|---|---|---|
| 425 | gaps "documented in surveillance systems that rely on passive reporting (WHO, 2014; German et al., 2001)" | SUPPORTED | Keep. |
| 462-464 (Obj. 1c), 552, 598-599, 678-679, 1034, 1103-1104, 1137-1138, 1181, 1220, 1295, 1409 | "WHO Early Warning and Response Network (EWARN)" | MISLABELLED | Replace with "WHO early warning and response (EWAR) guidance" or simply "statistical threshold". Glossary entry "WHO EWARN" (1103) should become "Early Warning and Response (EWAR)". |
| 595-600 | WHO identifies surveillance as core function; EWARN provides guidance for event-based surveillance (WHO, 2014) | SUPPORTED except the label | Change "EWARN" to "EWAR". |
| 678-684 | "consistent with the WHO EWARN methodology, defines the epidemic threshold as the mean ... plus two standard deviations, consistent with WHO EWARN practice (WHO, 2014)" | **MISATTRIBUTED** | "The most widely used statistical approach, the historical-limits method, flags an aberration when current counts exceed the mean of comparable historical periods over the previous five years by more than two standard deviations (Stroup et al., 1989); WHO guidance likewise recommends that indicator-based surveillance data be compared against baseline values and thresholds to detect unusual disease patterns (WHO, 2014)." |
| 963-966 | "WHO (2014) EWARN methodology and German et al. (2001) EARS documentation, which establish the two-standard-deviation epidemic threshold" | **MISATTRIBUTED** | "...is grounded in the historical-limits aberration-detection method (Stroup et al., 1989), the CDC Early Aberration Reporting System (Hutwagner et al., 2003), and WHO guidance on threshold-based indicator surveillance (WHO, 2014)." (Also: German et al. 2001 is not EARS documentation. Batch-1 issue, flagged for cross-check.) |
| 983, 986-989 | Synthesis: "The WHO EWARN epidemic threshold methodology and CDC EARS provide statistically principled ... standards ... (WHO, 2014; German et al., 2001; DOH, 2014)" | **MISATTRIBUTED** | "Historical-limits thresholds (Stroup et al., 1989) and the CDC EARS algorithms (Hutwagner et al., 2003) provide statistically principled methods for automated outbreak detection, consistent with WHO guidance on threshold-based early warning (WHO, 2014) and directly computable from PIDSR-formatted data (DOH, 2014)." |
| 1082 | Glossary: threshold = mean + 2 SD "(WHO EWARN methodology; WHO, 2014)" | **MISATTRIBUTED** | "...plus two standard deviations (historical-limits method; Stroup et al., 1989)". |
| 1104 | Op. def.: WHO EWARN "prescribes statistical thresholds for automated outbreak alerting based on historical disease case baselines (WHO, 2014)" | OVERSTATED | "WHO guidance for early warning and response, which calls for indicator-based surveillance data to be compared with baseline values and thresholds to detect unusual disease patterns (WHO, 2014)." |
| 1409 | "following the WHO EWARN mean-plus-2σ methodology" | **MISATTRIBUTED** | "following the historical-limits mean-plus-2σ method (Stroup et al., 1989)". |

**Optional extra:** if the DOH PIDSR MOP (2014) states the mean + 2 SD epidemic threshold, cite DOH (2014) next to Stroup. That would be the strongest local authority, but this batch did not verify it.

---

## 3. New documents to cite

### 3.1 CHED Memorandum Order No. 15, Series of 2019

**Fetched:** CHED official listing page `https://legacy.ched.gov.ph/2019-ched-memorandum-orders/`, which links to `https://legacy.ched.gov.ph/wp-content/uploads/CMO-No.-15-Series-of-2019-–-Policies-Standards-and-Guidelines-for-Graduate-Programs-Updated.pdf` (direct download blocked by the server for automated clients). The full 30-page signed text was read from the FEU-hosted copy `https://www.feu.edu.ph/wp-content/uploads/2024/05/CHED-Memorandum-Order-No.-15-Series-of-2019-compressed.pdf` (scanned; OCR'd).

**Exact title:** "Policies, Standards, and Guidelines for Graduate Programs". Signed by J. Prospero E. De Vera III, Chairman, Quezon City, 19 December 2019 (Referendum No. R070-2019). It repeals CMO 36 s. 1998 and CMO 9 s. 2003.

**Important: CMO 15 s. 2019 does NOT mention the Master in Information Technology program, system development, or system management.** It is a general PSG for all graduate programs. Its only IT mention is in the description of MS programs. Relevant verbatim text:
- "Graduate Programs in the Sciences - Master of Science programs focus on specialized professional fields and are commonly applied in programs related to the natural sciences, engineering and mathematics sciences, and information technology. ... Thesis is a requirement for graduation."
- "The Master's programs have two (2) major tracks. These are the thesis track and the non-thesis track. The thesis track is research intensive while the non-thesis track is often referred to as a professional or course-based master's program."
- "B. Non-Thesis Track (Master's Degree — Professional Track) ... It is a professional track at the master's level with the primary purpose of applying knowledge in professional practice. ... The professional master's degree program has at least thirty (30) units of coursework ... wherein at least three (3) units of which shall be labeled as a capstone course or practiced-based project. This program requires students to pass a comprehensive examination and complete a capstone project."
- "A capstone project culminates the student's academic or learning experience. It provides the student an opportunity to exhibit the knowledge and skills obtained during the course of graduate study. ... A typical form is when a student may be required to choose a topic or a problem that interests them, perform a research on these topics and generate a final output (for example, in the form of essay, case study, research paper, or a short film or multimedia presentation) indicative of the student's acquisition of learning. The student presents the capstone project to a panel or committee of experts for grading and evaluation."

> Commission on Higher Education. (2019). *Policies, standards, and guidelines for graduate programs* (CHED Memorandum Order No. 15, Series of 2019). https://legacy.ched.gov.ph/wp-content/uploads/CMO-No.-15-Series-of-2019-–-Policies-Standards-and-Guidelines-for-Graduate-Programs-Updated.pdf

**The MIT-specific language is in CMO No. 07, s. 2010**, which is not repealed by CMO 15 except where inconsistent, and no newer IT-graduate PSG was found. Fetched: `https://elibrary.judiciary.gov.ph/thebookshelf/showdocs/42/52790` (full text); official CHED PDF linked at `https://legacy.ched.gov.ph/wp-content/uploads/2017/10/CMO-No.07-s2010.pdf`. Title: "Revised Policies, Standards and Guidelines for Graduate Program Information Technology Education (ITE)", 20 May 2010. Verbatim:
- Sec. 3.1: "Professional Programs are defined to be graduate level programs that shall require student completion of graduate level courses and immersion and/or involvement in a project relevant to industry including business, education and government."
- Sec. 3.1.1: MIT "emphasizes the acquisition of concepts and technologies preparing and enabling the student for the industrial practice of systems integration, systems administration, systems planning systems implementation and other activities that maintain the integrity and proper functionality of a system and its components."
- Sec. 4.1.1: "The Master in Information Technology (MIT) program aims to develop among its students the knowledge of information technology (IT) concepts, techniques and principles, and skills in using IT to provide solutions to problems of organizations and society."
- Sec. 10.1.1: "A Masters' Capstone Project is a culminating activity that generates an output useful in the development of IT solutions. This may be but not limited to application development that focuses on software engineering process or application design that focuses on effective testing procedure or a study on application development processes. The student concerned must hold a key responsibilities towards the development of the Capstone Project. The Capstone Project may be pilot tested and the result of the research and development must be presented in a national or international public forum."

> Commission on Higher Education. (2010). *Revised policies, standards and guidelines for graduate program information technology education (ITE)* (CHED Memorandum Order No. 07, Series of 2010). https://legacy.ched.gov.ph/wp-content/uploads/2017/10/CMO-No.07-s2010.pdf

**Recommendation:** Cite CMO 15 s. 2019 for the professional (non-thesis) track and capstone definition. Cite CMO 07 s. 2010 for the MIT's systems/IT-solutions orientation and the capstone as "an output useful in the development of IT solutions". The words "system development" and "system management" do not appear verbatim in either; the closest are "application development", "systems integration, systems administration, systems planning systems implementation". Do not attribute an MIT-specific statement to CMO 15.

### 3.2 NPC Circular No. 16-03, Personal Data Breach Management

**Fetched:** NPC resolutions on privacy.gov.ph quoting the circular verbatim: Resolution NPC BN 21-078 (Bombardier) and NPC BN 20-124 (E-Science). The circular's own page `https://privacy.gov.ph/npc-circular-16-03-personal-data-breach-management/` blocks automated clients (403/404), but NPC's site search lists it at that URL. Date 15 December 2016, per NPC Order NPC BN 21-054 (search excerpt). No amendment or repeal was found.
**72-hour rule (verbatim, Secs. 17(A) and 18(A)):** "The Commission shall be notified within seventy-two (72) hours upon knowledge of or the reasonable belief by the personal information controller or personal information processor that a personal data breach has occurred." / "The data subjects shall be notified within seventy-two (72) hours upon knowledge of or reasonable belief by the personal information controller or personal information processor that a personal data breach has occurred." Notification may rest on available information if the breach "is likely to give rise to a real risk to the rights and freedoms of data subjects". Postponement of data-subject notice requires a request to the Commission (Sec. 18(B)).

> National Privacy Commission. (2016, December 15). *NPC Circular No. 16-03: Personal data breach management*. https://privacy.gov.ph/npc-circular-16-03-personal-data-breach-management/

Summary paragraph: NPC Circular 16-03 requires personal information controllers, including LGU offices, to have a breach-management policy and a data-breach response team. Breaches involving sensitive personal information (which includes health data under RA 10173 Sec. 3(l)) that are likely to create a real risk of serious harm must be reported to the NPC and to the affected data subjects within 72 hours of knowledge or reasonable belief of the breach. H-MAP's incident-response plan in Ch.3 should name this 72-hour obligation and the CESU/City DPO as responsible party.

### 3.3 PHREB National Ethical Guidelines (2022)

**Fetched:** `https://www.pchrd.dost.gov.ph/wp-content/uploads/2023/05/2022-NEGRIHP_Official-Gazatte_Ver-5-1.pdf` (440 pp.; front matter read). Search showed no newer edition as of Oct 2026. A UP page called NEGRIHP "soon to be updated" (undated); recheck before final submission.
**Verified:** Title page: "National Ethical Guidelines for Research Involving Human Participants 2022"; "Prepared by the Philippine Health Research Ethics Board Ad Hoc Committee for Updating the National Ethical Guidelines, May 2022"; "Published by: Philippine Council for Health Research and Development", Taguig City; ISBN 978-971-8662-50-2 (print), 978-971-8662-51-9 (PDF); approved by PHREB Resolution No. 001 s. 2022 (ad referendum 1 March 2022) under RA 10532. It replaces the 2017 *National Ethical Guidelines for Health and Health-Related Research*.

> Philippine Health Research Ethics Board. (2022). *National ethical guidelines for research involving human participants 2022*. Philippine Council for Health Research and Development. https://www.pchrd.dost.gov.ph/wp-content/uploads/2023/05/2022-NEGRIHP_Official-Gazatte_Ver-5-1.pdf

Summary paragraph: The 2022 NEGRIHP is the current national standard for any Philippine research involving human participants, including their identifiable data, and not only biomedical research. It is relevant to H-MAP in two ways: (a) the ISO/IEC 25010 evaluation survey of CESU staff and IT professionals (informed consent, voluntary participation, confidentiality); and (b) the secondary use of identifiable PIDSR patient records for model training (ethics review, data-privacy safeguards, de-identification). The manuscript should state that the protocol will go to a PHREB-accredited ethics committee, or explain why it qualifies for exemption under the guidelines.

### 3.4 Braun & Clarke (2006)

**Fetched:** Crossref `10.1191/1478088706qp063oa`. Verified: "Using thematic analysis in psychology", Virginia Braun & Victoria Clarke, *Qualitative Research in Psychology* 3(2), 77–101, 2006 (Informa).

> Braun, V., & Clarke, V. (2006). Using thematic analysis in psychology. *Qualitative Research in Psychology, 3*(2), 77–101. https://doi.org/10.1191/1478088706qp063oa

Summary paragraph: This paper defines thematic analysis as a flexible method for "identifying, analysing and reporting patterns (themes) within data". It sets out six phases: familiarisation, generating initial codes, searching for themes, reviewing themes, defining and naming themes, and producing the report. It is the standard citation for analysing open-ended survey responses or interview/FGD data, e.g. CESU staff feedback during requirements gathering or user acceptance. *(The quoted definition and six-phase list are standard but were not re-read from the full text in this session; the bibliographic data is Crossref-verified.)*

---

## 4. CITATION_AUDIT_v5.md fixes: status in the current script

| Audit step | Status in `build_chapters_docx_v5.py` | Remaining problem |
|---|---|---|
| 1. WHO 2018 → WHO 2014 (refs + in-text) | **Applied.** No "WHO, 2018" remains; entry is WHO/HSE/GCR/LYO/2014.4. Surveillance definition and four types now cite Klaucke 1988 / German 2001. | **The audit's premise was wrong.** WHO 2014 does not contain the mean + 2 SD formula or the term EWARN. About 14 passages still attribute the formula/label to "WHO EWARN (WHO, 2014)". See ref 25. |
| 2. Replace fabricated Srivastava 2024 | **Applied.** Real 2025 paper; metadata exact. | Surveillance-specific claims at lines 395, 722, 819, 887 still exceed what the paper (a diagnosis/treatment review) supports. See ref 22. |
| 3. Chakraborty: ARIMA-NNAR, not Prophet | **Applied** (lines 745-749, 878-882). | Out of batch. Line 882's "contexts directly comparable to Parañaque City" was not verified here (check Chakraborty's study sites in batch 1). |
| 4. Soften Olana (paras 77, 113, 188) | **Partially applied.** Lines 735-745, 902-911 and 994-997 were softened. **Line 1281-1283 (audit para 188) NOT applied:** it still says Olana supports "the choice of Prophet". Lines 397-400, 466-468, 967-969, 1035-1036 and 1141-1142 were never addressed. | **The softened text is itself inaccurate.** Olana's Table 1 shows Prophet worse than seasonal naive (MASE 1.23). "Operationally viable alternatives" must not include Prophet. See ref 17. |
| 5. Shi: LASSO, not RF | **Applied** (lines 766, 882, 971). | None. |
| Audit's "clean" list | Not independently reliable. | The audit marked Shaman & Karspeck, Nykiforuk & Flaman, Lawson, RA 10173 and NPC as clean; this batch finds claim problems in all five, plus a dead NPC URL and a repealed circular. |

### Cross-batch notes (outside refs 14-25, for the batch-1 owner)
- Line 964: "German et al. (2001) EARS documentation". German et al. (2001) is the CDC surveillance-*evaluation* guideline, not EARS; EARS is Hutwagner et al. (2003).
- Line 1409: thresholds "restricted to Confirmed and Probable case classifications". Project notes (`reference_cesu_5yrave_basis`) record that CESU's 5-year average sums *all* classifications. This is a consistency issue, not a citation issue, but a panel may notice it.
