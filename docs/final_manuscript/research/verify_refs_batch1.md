# Reference Verification, Batch 1 (refs 1 to 13)

**Manuscript source:** `docs/v5_modules/build_chapters_docx_v5.py` (refs list at line 1608; line numbers below refer to this script)
**Prior audit re-checked:** `docs/submitted_pdf_qa/CITATION_AUDIT_v5.md` (25 May 2026)
**Verification date:** 21 October 2026
**Method:** Crossref API for every DOI; Europe PMC (abstracts and PMC full text) for papers; official pages (cdc.gov MMWR, iso.org, agilemanifesto.org) and a copy of the DOH manual for grey/official documents. Every in-text occurrence of each author was located by grep and read in context. Suggested sentences below avoid em dashes (house rule for Ch.1-3).

Classification key: SUPPORTED / OVERSTATED / MISATTRIBUTED / CANNOT VERIFY.

---

## 1. Summary table

| # | Reference | Exists? | Metadata correct? | Claims supported? | Reliability tier | Verdict |
|---|---|---|---|---|---|---|
| 1 | Beck et al. (2001) Agile Manifesto | Yes | Yes | Yes (1/1) | Website / practitioner grey literature | KEEP |
| 2 | Boulos et al. (2011) IJHG 10:67 | Yes | Minor: first author surname is "Kamel Boulos" | **No.** Core claim (open-source web mapping replaces proprietary desktop GIS; zero licensing cost) is not in the paper | Peer-reviewed journal (BMC, OA) | **REPLACE** for the web-GIS claim (or FIX CLAIM + FIX METADATA if kept) |
| 3 | Breiman (2001) Random forests | Yes | Yes | Yes | Peer-reviewed journal (seminal) | KEEP |
| 4 | Carvajal et al. (2018) BMC Infect Dis 18:183 | Yes | Yes (APA: "Article 183" preferred) | Partly: 3 claims misread/overstated | Peer-reviewed journal | FIX CLAIM |
| 5 | Chakraborty, Chattopadhyay & Ghosh (2019) Physica A 527:121266 | Yes | Yes (APA: "Article 121266" preferred) | Partly: MAPE metric, "urban", "Asia-Pacific", "directly comparable" not supported | Peer-reviewed journal (preprint on bioRxiv) | FIX CLAIM |
| 6 | DOH (2014) PIDSR Manual of Procedures 3rd ed. | Yes (April 2014, Vol. 1, National Epidemiology Center) | Minor: add Vol. 1, issuing unit; "Government of the Philippines" is not the publisher | Partly: 2 misattributed, 3 overstated, 6 supported | Official government document | FIX METADATA + FIX CLAIM |
| 7 | Dong, Du & Gardner (2020) Lancet Infect Dis 20(5) | Yes | Yes | Partly: "significantly improved situational awareness", "relational databases", "chart-based summaries" not in the letter | Peer-reviewed journal (correspondence, not a research article) | FIX CLAIM |
| 8 | Dowding et al. (2015) Int J Med Inform 84(2) | Yes | Yes | Partly: "visual clarity and actionability" and "design for public-health audiences" not supported | Peer-reviewed journal (literature review) | FIX CLAIM |
| 9 | Freifeld et al. (2008) JAMIA 15(2) | Yes | Yes | Yes | Peer-reviewed journal | KEEP |
| 10 | German et al. (2001) MMWR 50(RR-13) | Yes | Mostly (series name and URL should be added) | **No for 6 of 10 citations.** It is cited as "EARS documentation" (it predates and never mentions EARS), for a 4-type surveillance taxonomy, GIS, and "significant" timeliness gains it does not claim | Official government guideline (CDC) | **FIX CLAIM (serious)** + FIX METADATA |
| 11 | Hutwagner et al. (2003) J Urban Health 80(Suppl 1) | Yes | Yes | Partly: cited for 5-year same-week mean + 2 SD, which EARS C1-C3 do not use | Peer-reviewed journal | FIX CLAIM |
| 12 | ISO/IEC 25010:2011 | Yes, but **withdrawn**, superseded by ISO/IEC 25010:2023 (published 2023-11) | Title OK; add URL; status issue | Supported with caveats (list incomplete; one definition uses 2023 wording) | International standard | FIX METADATA (cite 2023, see recommendation) |
| 13 | Klaucke et al. (1988) MMWR 37(S-5) | Yes | Yes (minor issue format) | Definition SUPPORTED; 4-type taxonomy MISATTRIBUTED | Official government guideline (CDC) | FIX CLAIM |

---

## 2. Per-reference findings

### 2.1 Beck et al. (2001), Manifesto for Agile Software Development

**Verification sources**
- https://agilemanifesto.org/ (17 signatories, "© 2001, the above authors", four values)
- https://agilemanifesto.org/principles.html ("Deliver working software frequently...", "Welcome changing requirements...", "At regular intervals, the team reflects...")

**Metadata:** All 17 signatories match, in the site's order, which is also alphabetical. APA 7 allows up to 20 authors, so listing all is correct. No discrepancy.

**Claims**
| Line | Manuscript | Verdict | Evidence |
|---|---|---|---|
| 1146-1147 | "An Agile-Inspired Iterative Prototyping Model was adopted to support incremental development and continuous refinement (Beck et al., 2001)." | SUPPORTED | Principles on frequent delivery, welcoming change, regular reflection and adjustment. The "Iterative Prototyping Model" itself is the author's own framing, correctly labelled "Agile-inspired". |

**Verdict:** KEEP.

---

### 2.2 Boulos et al. (2011), International Journal of Health Geographics, 10, 67

**Verification sources**
- Crossref: https://api.crossref.org/works/10.1186/1476-072X-10-67
- Europe PMC (abstract + PMC3271966 full text): https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3271966/fullTextXML

**Metadata discrepancies**
- First author's surname is **Kamel Boulos** (Crossref family name "Kamel Boulos"; PubMed "Kamel Boulos MN"; the paper's own copyright line reads "Kamel Boulos et al."). In-text citations should read "Kamel Boulos et al. (2011)" and the entry should be alphabetized under K (between Hutwagner and Klaucke).
- Last author is "Kuo-Yu Slayer Chuang" (full text), so "Chuang, K.-Y. S." is correct.
- APA 7 for BMC article numbers: "*10*, Article 67" (issue optional).

Corrected entry (if retained):
> Kamel Boulos, M. N., Resch, B., Crowley, D. N., Breslin, J. G., Sohn, G., Burtner, R., Pike, W. A., Jezierski, E., & Chuang, K.-Y. S. (2011). Crowdsourcing, citizen sensing and sensor web technologies for public and environmental health surveillance and crisis management: Trends, OGC standards and application examples. *International Journal of Health Geographics, 10*, Article 67. https://doi.org/10.1186/1476-072X-10-67

**What the paper is:** A state-of-the-art review of the Sensor Web, citizen sensing ("human-in-the-loop sensing"), crowdsourced data (Twitter, Ushahidi, GeoChat), and OGC standards (Sensor Web Enablement, Open GeoSMS) for public health surveillance and crisis informatics. A full-text search finds **zero** occurrences of "proprietary", "disease mapping", "Leaflet", "OpenLayers", or "open-source"; "licens" occurs only in the CC-BY licence line; "desktop" occurs once, about user movement between environments. There is no comparison of open-source web mapping against proprietary desktop GIS and no finding about licensing costs.

**Claims**
| Line | Manuscript | Verdict |
|---|---|---|
| 632-635 | "Boulos et al. (2011) found that open-source web mapping platforms provide sufficient functionality for disease mapping tasks previously requiring proprietary desktop GIS software, with zero licensing costs identified as a key practical advantage..." | **MISATTRIBUTED** |
| 864-869 | Same finding repeated; "Their review directly supports the Leaflet.js and OpenStreetMap approach adopted in H-MAP." | **MISATTRIBUTED** (OpenStreetMap is mentioned only as a crowdsourced "Wikipedia of the Earth"; Leaflet is never mentioned) |
| 960-962 | Boulos "collectively validate[s] open-source web mapping as an effective tool for communicating disease distribution" | **OVERSTATED** |
| 986 | "(Boulos et al., 2011; Nykiforuk & Flaman, 2011)" for "Leaflet.js with OpenStreetMap ... functional maturity ... without proprietary licensing costs" | **MISATTRIBUTED** |

**Recommended fix.** Replace Boulos for the cost/open-source claim with a source that actually tests it. Verified candidate (Crossref + Europe PMC abstract):

> Fisher, R. P., & Myers, B. A. (2011). Free and simple GIS as appropriate for health mapping in a low resource setting: A case study in eastern Indonesia. *International Journal of Health Geographics, 10*, Article 15. https://doi.org/10.1186/1476-072X-10-15

Its abstract states GIS software "can be expensive and complex" in low-resource settings, pilots "open source GIS software" for health-indicator mapping, and concludes GIS "can be a useful and inexpensive tool for the decentralisation of health data analysis ... through the use of free and simple software." (It studies desktop open-source GIS, not web mapping, so do not claim it validates Leaflet.)

Suggested sentence (lines 632-635):
> "Fisher and Myers (2011) showed that free and open-source GIS tools allowed district and clinic health staff in a low-resource setting to map health indicators and use the results for planning, concluding that GIS can be an inexpensive tool for decentralizing health data analysis. Leaflet.js, the open-source JavaScript library selected for H-MAP, extends this approach to the browser..."

If Boulos is kept, cite it only for what it says, e.g.: "Kamel Boulos et al. (2011) reviewed how crowdsourced geographic data such as OpenStreetMap and OGC-standard sensor web services are being used in public and environmental health surveillance."

**Verdict:** REPLACE for the web-GIS/licensing claim (and FIX METADATA if retained for a narrower claim). The prior audit marked this "Clean"; that verdict was wrong.

---

### 2.3 Breiman (2001), Random forests

**Verification sources**
- Crossref: https://api.crossref.org/works/10.1023/A:1010933404324 (Breiman, Leo; *Machine Learning* 45(1), 5-32, Oct 2001)
- Abstract via Semantic Scholar API (note: S2's author field for this record is corrupted; Crossref is authoritative)

**Metadata:** Correct.

**Claims**
| Line | Manuscript | Verdict | Evidence |
|---|---|---|---|
| 757-761 | RF "constructs multiple decision trees ... outputs the class predicted by the majority of trees (Breiman, 2001). It is valued ... for its robustness to overfitting, its ability to handle mixed feature types, and its capacity to capture complex interactions" | SUPPORTED (core); last two attributes are general textbook knowledge, not stated in the abstract | Abstract: "combination of tree predictors"; "generalization error ... converges a.s. to a limit as the number of trees ... becomes large" (basis of the no-overfitting-with-more-trees result); "more robust with respect to noise" |
| 969, 1036, 1102, 1143, 1231, 1287 | RF algorithm attribution | SUPPORTED | Original RF paper |

**Verdict:** KEEP.

---

### 2.4 Carvajal et al. (2018), BMC Infectious Diseases, 18, 183

**Verification sources**
- Crossref: https://api.crossref.org/works/10.1186/s12879-018-3066-0
- Europe PMC abstract (PMID 29665781, PMC5905126)

**Metadata:** Authors, order, title, volume, article number and DOI all correct. APA 7 refinement: "*BMC Infectious Diseases, 18*, Article 183."

**What the paper found:** Compared GAM, SARIMAX, Random Forest and Gradient Boosting on Metropolitan Manila dengue incidence, Jan 2009 to Dec 2013, with meteorological covariates (flood, precipitation, temperature, SOI, relative humidity, wind). "Among the statistical modeling techniques, Random Forest showed the **best** predictive accuracy"; RF with lagged meteorological effects was the best model; relative humidity was the most important variable. It is a temporal (city-wide) incidence model, not a spatial or barangay-level classifier.

**Claims**
| Line | Manuscript | Verdict | Note |
|---|---|---|---|
| 397-400 | Carvajal (with Olana) "demonstrated that AI models such as Random Forest and Prophet can achieve reliable predictive accuracy" | SUPPORTED for RF (Prophet part rests on Olana, outside this batch) | |
| 431-434, 534, 750-like gap statements | Models were not integrated into operational platforms | SUPPORTED (reasonable characterization of a modelling paper) | |
| 467-468, 555-556, 1141-1143 | RF "validated in the Philippine context" | SUPPORTED with caveat: validated for temporal incidence forecasting, not barangay risk classification | |
| 761-765 | "Random Forest achieved competitive predictive accuracy and identified temporal patterns that single-technique models could not reliably capture." | **OVERSTATED / misread** | The paper found RF *best*, not merely competitive. The "single technique" remark in the abstract criticizes *prior studies* for using only one technique; the paper did not show RF captured patterns other models missed. |
| 893-899 | "Random Forest achieved competitive predictive performance and revealed temporal patterns associated with meteorological variables that single-technique models missed." | **OVERSTATED / misread** | Same as above. |
| 970 | "Philippine-context Random Forest dengue forecasting validation" | SUPPORTED | |
| 990-993 | "Prophet and Random Forest have demonstrated reliable performance in communicable disease forecasting and **spatial risk classification** in the Philippine context" | **OVERSTATED** | Neither Carvajal nor Olana performed spatial risk classification. |
| 1311-1313 | "Carvajal et al. (2018) reported analogous Random Forest performance for dengue in Metropolitan Manila" (context: accuracy and macro-F1 vs a stratified-random classifier) | **OVERSTATED** | Carvajal reported regression-type predictive accuracy for incidence, not classification accuracy/F1 against a random baseline. |
| 1313-1315 | Carvajal employed rainfall, temperature and humidity | SUPPORTED | |

Suggested sentences:
- Lines 761-765 and 893-899: "Their study found that Random Forest, particularly when using lagged meteorological variables, gave the best predictive accuracy of the four techniques, with relative humidity emerging as the most important meteorological predictor."
- Lines 990-993: "...have demonstrated reliable performance in communicable disease forecasting in the Philippine context. Their application to barangay-level risk classification has not yet been reported and is the extension H-MAP undertakes."
- Lines 1311-1313: "...Carvajal et al. (2018) found Random Forest the most accurate of four techniques for predicting dengue incidence in Metropolitan Manila, supporting the choice of the algorithm, although their task was temporal regression rather than barangay-level classification."

**Verdict:** FIX CLAIM (reference itself is sound).

---

### 2.5 Chakraborty, Chattopadhyay & Ghosh (2019), Physica A, 527, 121266

**Verification sources**
- Crossref: https://api.crossref.org/works/10.1016/j.physa.2019.121266 (vol. 527, Aug 2019, article 121266)
- Europe PMC preprint record PPR65068 (bioRxiv 10.1101/498394), full abstract
- ISI Kolkata repository: https://digitalcommons.isical.ac.in/journal-articles/761
- RePEc: https://ideas.repec.org/a/eee/phsmap/v527y2019ics0378437119307320.html
- Secondary: Lober, Rodrigues & Roster, "Neural networks for dengue forecasting: a systematic review", arXiv:2106.12905 (via search summary). Full text of the article itself was not retrievable (Elsevier/bioRxiv blocked automated access).

**Metadata:** Correct. APA 7 refinement: "*527*, Article 121266."

**What the paper is:** A hybrid ARIMA plus Neural Network Autoregression (NNAR) model, applied as a pure time-series problem (no meteorological variables) to **three datasets: San Juan (Puerto Rico), Iquitos (Peru), and the Philippines**. Abstract: the hybrid "is found to give better forecasting accuracy in comparison to the state-of-the-art." No Prophet. The systematic review reports the metrics as MAE, RMSE and SMAPE (not MAPE) and that pure NNAR, not the hybrid, was best for the Philippines at the 6-month horizon.

**Prior-audit fix status:** Applied (the Prophet misattribution is gone).

**Claims**
| Line | Manuscript | Verdict | Note |
|---|---|---|---|
| 745-749 | hybrid ARIMA-NNAR "produce dengue forecasts with substantially lower mean absolute percentage errors than pure ARIMA models" | **OVERSTATED / CANNOT VERIFY metric** | Abstract supports "better accuracy than state-of-the-art"; MAPE is not the reported metric per secondary source; "substantially" is unquantified. |
| 750-751 | standalone model, no dashboard integration | SUPPORTED | |
| 878-882 | "for dengue forecasting in **tropical urban settings** ... MAPE substantially lower than pure ARIMA ... in contexts **directly comparable to Parañaque City**" | **OVERSTATED** | One series is national Philippine data; San Juan and Iquitos are in the Americas. Nothing in the paper is city-level Philippine. |
| 971-973 | Chakraborty provides "parallel evidence from **Asia-Pacific** tropical urban settings" | **OVERSTATED** | Two of three datasets are Latin American. |

Suggested sentence (745-749 and 878-882):
> "Chakraborty et al. (2019) proposed a hybrid model in which ARIMA captures linear structure and a Neural Network Autoregression models the residual nonlinearity, and reported better forecasting accuracy than single-model benchmarks on dengue series from San Juan, Iquitos, and the Philippines, illustrating the value of hybrid statistical and machine-learning approaches for dengue prediction."

For line 971-973, replace "from Asia-Pacific tropical urban settings" with "from dengue-endemic settings, including national Philippine data (Chakraborty et al., 2019) and Singapore (Shi et al., 2016)".

**Verdict:** FIX CLAIM. Note that the Philippines dataset is a genuine strength the manuscript currently does not mention.

---

### 2.6 Department of Health (2014), PIDSR Manual of Procedures, 3rd ed.

**Verification sources**
- Copy of the manual (120 pp.): https://medbox.org/index.php/dl/5e148832db60a2044c2d3bf2. Title page: "Manual of Procedures for the Philippine Integrated Disease Surveillance and Response, 3rd Edition, April 2014, National Epidemiology Center, Department of Health, VOL 1"; editorial board headed by Enrique Tayag (Director IV, NEC).
- Government corroboration: Pangasinan Executive Order 0054-2023 (https://pangasinan.gov.ph/wp-content/uploads/eo/0054-2023.pdf) cites the April 2014 DOH MOP.
- No official doh.gov.ph download link was found; cite as a print government document.

**Metadata discrepancies:** The issuing unit (National Epidemiology Center) and "Vol. 1" are missing; "Government of the Philippines" is not the publisher. Corrected entry:

> Department of Health. (2014). *Manual of procedures for the Philippine Integrated Disease Surveillance and Response* (3rd ed., Vol. 1). National Epidemiology Center.

**Key content found (page numbers are the manual's printed pages):**
- p. 57: "To compute for the alert threshold: compute for the weekly/monthly average of a particular disease during the past 3 to 5 years and add 1 standard deviation. To compute for the epidemic threshold: compute for the weekly/monthly average ... during the past 3 or 5 years and add 2 standard deviation."
- p. 58, Table 5: disease-specific thresholds override this for some diseases (e.g., measles and AFP: 1 suspect case = alert).
- p. 72: "The spatial distribution of the data collected can best be presented and interpreted if projected on a map, preferably through the use of a Geographic Information System (GIS)-enabled system."
- Glossary: defines active surveillance, alert/epidemic thresholds, NESSS (sentinel), syndromic report; event-based surveillance described in Sections 1 and 8.
- FHSIS appears only as the parent of the Notifiable Disease Reporting System (glossary) and as a record source for case finding.

**This manual is the best primary source in the whole reference list for the mean + 2 SD epidemic threshold.** It should be cited (with page) wherever the formula appears (lines 676-684, 692-696, 964-966, 1219-1221).

**Claims**
| Line | Manuscript | Verdict | Note |
|---|---|---|---|
| 358-360, 959, 1098 | PIDSR is the national framework for notifiable diseases | SUPPORTED | |
| 608-612, 1198-1200 | Case report forms include classification, outcome, demographics, facility, location | SUPPORTED | Forms and required case information described in Section 4 |
| 427-431 | "The nationally maintained PIDSR electronic reporting system ... does not include city-specific spatial visualization, threshold alerting, or AI-assisted predictive analytics (DOH, 2014)" | **CANNOT VERIFY / partly contradicted** | A 2014 procedures manual does not document software features; it actually *prescribes* thresholds (p. 57) and GIS mapping (p. 72) as local tasks. |
| 692-696 | "The same mathematical basis is used in the Philippines' own national PIDSR five-year average alert tables, prepared annually by the National Epidemiology Center (DOH, 2014)" | **OVERSTATED** | Manual says 3-to-5-year average + 2 SD (epidemic) / + 1 SD (alert) for national data; "prepared annually" and "tables" are not in the manual. |
| 912-915 | "Studies evaluating the PIDSR system at the local level have consistently identified the gap ... (DOH, 2014)" | **MISATTRIBUTED** | The manual is not an evaluation study. Needs an actual PIDSR evaluation paper, or delete the "studies" framing. |
| 934-941 | PIDSR and FHSIS "are oriented toward national-level reporting ... rather than city-level spatial analysis" (DOH, 2014) | **OVERSTATED** | Manual expects local units to analyze, graph and map data (p. 72). |
| 986-989 | Threshold methods compatible with PIDSR data (WHO 2014; German 2001; DOH 2014) | SUPPORTED for DOH | |

Suggested sentences:
- Lines 692-696: "The same mathematical basis is prescribed in the PIDSR Manual of Procedures, which computes the alert threshold as the weekly or monthly average of the past three to five years plus one standard deviation, and the epidemic threshold as that average plus two standard deviations (DOH, 2014, p. 57)."
- Lines 427-431: "The PIDSR Manual of Procedures directs local surveillance units to compare current counts against alert and epidemic thresholds and to present the spatial distribution of cases on maps, preferably through a GIS-enabled system (DOH, 2014, pp. 57, 72), but it leaves the tools for doing so to each local unit."  (This framing turns the gap into a DOH-mandated requirement, which is stronger.)
- Lines 912-915: "The PIDSR Manual of Procedures assigns data analysis, threshold monitoring, and mapping to local epidemiology and surveillance units (DOH, 2014), yet at the city level these tasks remain dependent on spreadsheet tools." (Remove "studies ... consistently identified" unless a real evaluation study is cited.)
- Add the first-use abbreviation in-text: "(Department of Health [DOH], 2014)".

**Verdict:** FIX METADATA + FIX CLAIM. Also note for methodology: Table 5 shows that for measles, AFP, cholera and similar diseases PIDSR uses case-count triggers (one case), not mean + 2 SD; H-MAP's universal mean + 2 SD rule should acknowledge this.

---

### 2.7 Dong, Du & Gardner (2020), The Lancet Infectious Diseases, 20(5), 533-534

**Verification sources**
- Crossref: https://api.crossref.org/works/10.1016/S1473-3099(20)30120-1
- Europe PMC full text PMC7159018: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7159018/fullTextXML

**Metadata:** Correct. Note: it is a two-page **Correspondence** letter (no abstract); it was corrected on 12 June 2020 (erratum 20(9), e215). No change needed to the entry.

**What it says:** The JHU CSSE dashboard "illustrates the location and number of confirmed COVID-19 cases, deaths, and recoveries"; reports at province (China), city (USA, Australia, Canada) and country level; data shared via Google Sheets, then GitHub and Esri Living Atlas; semi-automated feed from DXY every 15 min plus manual updates; reported newly infected countries ahead of WHO in most cases; built for "researchers, public health authorities, and the general public". It does not measure situational awareness or decision-making, and does not mention relational databases or chart/tabular summaries.

**Claims**
| Line | Manuscript | Verdict |
|---|---|---|
| 667-671 | "showed that geospatial visualization in a web-based format **significantly improved global situational awareness and informed public health decision-making**" | **OVERSTATED** (no evaluation in the letter) |
| 671-674 | Benchmark for map plus tabular/chart design | SUPPORTED as the author's own design choice (not a claim about the source) |
| 815-817 | dashboard "combined real-time GIS mapping with tabular and chart-based case summaries" | **CANNOT VERIFY** from the letter (map and counts only) |
| 870-874 | multiple geographic scales; operational at scale; browser-based, diverse users | SUPPORTED |
| 928-931 | "scalable architecture combining GIS, **relational databases**, and web technologies" | **MISATTRIBUTED detail** (letter names Google Sheets, GitHub, Esri; no relational database) |

Suggested sentences:
- Lines 667-671: "Dong et al. (2020) described the Johns Hopkins University COVID-19 Dashboard, which mapped confirmed cases, deaths, and recoveries in near real time at province, city, and country levels, and which reported newly affected countries ahead of official WHO situation reports in most instances."
- Lines 928-931: "...further demonstrates a scalable architecture combining GIS layers, openly published case data, and web technologies..."

**Verdict:** FIX CLAIM.

---

### 2.8 Dowding et al. (2015), International Journal of Medical Informatics, 84(2), 87-100

**Verification sources**
- Crossref: https://api.crossref.org/works/10.1016/j.ijmedinf.2014.10.001 (11 authors, order matches)
- Europe PMC abstract (PMID 25453274)

**Metadata:** Correct.

**What it says:** Review of 11 studies (1996-2012) of **clinical and quality dashboards** in health care. "In contexts where dashboards were easily accessible to clinicians ... their use was associated with improved care processes and patient outcomes." Conclusion: "further high quality detailed research studies need to be conducted to obtain evidence of their efficacy and **establish guidelines for their design**."

**Claims**
| Line | Manuscript | Verdict |
|---|---|---|
| 807-811 | "found that effective dashboards depend on the accessibility, **visual clarity, and actionability** of the indicators presented" | **OVERSTATED** (only accessibility is supported) |
| 811-814 | Extension to surveillance contexts, preference for trend/bar charts | Author's inference, labelled as such ("By extension"); acceptable |
| 974-975 | Module 5 "grounded in Dowding et al. (2015) on dashboard and report design for clinical and **public-health** audiences" | **OVERSTATED** (clinical only; the review says design guidelines are not yet established) |

Suggested sentences:
- Lines 807-811: "Dowding et al. (2015) reviewed clinical and quality dashboards and found that where dashboards were easily accessible to clinicians, their use was associated with improved care processes and patient outcomes, although evidence-based design guidelines had yet to be established."
- Line 974: "...is informed by Dowding et al. (2015) on the value of readily accessible dashboards for health professionals..."

**Verdict:** FIX CLAIM.

---

### 2.9 Freifeld et al. (2008), JAMIA, 15(2), 150-157

**Verification sources**
- Crossref: https://api.crossref.org/works/10.1197/jamia.M2544
- Europe PMC abstract (PMID 18096908, PMC2274789)

**Metadata:** Correct.

**Claims**
| Line | Manuscript | Verdict | Evidence |
|---|---|---|---|
| 920-925 | HealthMap "processes internet-based data sources to detect emerging disease threats through automated classification algorithms"; "operational feasibility of AI-driven disease detection as a complement to traditional surveillance" | SUPPORTED | Abstract: automated system for "querying, filtering, integrating and visualizing unstructured reports"; text-processing classifier with 84% accuracy on 778 reports; overlays on an interactive map. "AI-driven" is a fair description of an automated text classifier. |

**Verdict:** KEEP.

---

### 2.10 German et al. (2001), MMWR Recommendations and Reports, 50(RR-13), 1-35

**Verification sources**
- CDC MMWR page: https://www.cdc.gov/mmwr/preview/mmwrhtml/rr5013a1.htm (read via WebFetch)
- Europe PMC/PubMed record PMID 18634202: MMWR Recomm Rep 50(RR-13):1-35, July 2001; German RR, Lee LM, Horan JM, Milstein RL, Pertowski CA, Waller MN, Guidelines Working Group

**Metadata:** Authors, volume, report number and pages correct. APA refinement: the series is *MMWR Recommendations and Reports*, and a URL should be added.

Corrected entry:
> German, R. R., Lee, L. M., Horan, J. M., Milstein, R. L., Pertowski, C. A., & Waller, M. N. (2001). Updated guidelines for evaluating public health surveillance systems: Recommendations from the Guidelines Working Group. *MMWR Recommendations and Reports, 50*(RR-13), 1–35. https://www.cdc.gov/mmwr/preview/mmwrhtml/rr5013a1.htm

**What it says:** Defines surveillance as "the ongoing, systematic collection, analysis, interpretation, and dissemination of data regarding a health-related event for use in public health action..."; gives an evaluation framework (simplicity, flexibility, data quality, acceptability, sensitivity, PPV, representativeness, timeliness, stability). On electronic systems: electronic data collection "might promote timeliness". It does **not** classify surveillance into passive/active/sentinel/syndromic ("syndromic" does not appear), does **not** mention GIS or mapping, and does **not** mention EARS or mean + 2 SD thresholds. (EARS was developed after 11 September 2001; this report was published in July 2001.)

**Claims**
| Line | Manuscript | Verdict |
|---|---|---|
| 347-349, 591-593 | Surveillance definition (with Klaucke) | SUPPORTED |
| 363-367 | CDC framework "has emphasized that electronic and digital surveillance systems **significantly improve timeliness, completeness, and response efficiency**" | **OVERSTATED** (source: "might promote timeliness"; nothing on completeness or response efficiency) |
| 424-425 | Passive reporting limits timeliness and precision (WHO, 2014; German et al., 2001) | SUPPORTED (weak; German discusses passive vs active completeness) |
| 601-602 | "four types: passive, active, sentinel, and syndromic (Klaucke et al., 1988; German et al., 2001)" | **MISATTRIBUTED** |
| 605-607 | "German et al. (2001) have emphasized that enhancing passive systems with digital data management and **geospatial visualization** improves detection of outbreak clusters" | **MISATTRIBUTED** |
| 712-714 | "German et al. (2001) similarly acknowledge that digital ... systems **significantly improve timeliness and detection accuracy**" | **OVERSTATED** |
| 963-966 | "German et al. (2001) **EARS documentation**, which establish the two-standard-deviation epidemic threshold and moving-average aberration detection" | **MISATTRIBUTED** (serious: wrong document for EARS) |
| 981-983 | digital platforms "significantly improve both dimensions compared with manual, spreadsheet-based approaches (WHO, 2014; German et al., 2001)" | **OVERSTATED** |
| 986-989 | "The WHO EWARN ... and CDC EARS provide ... standards (WHO, 2014; German et al., 2001; DOH, 2014)" | **MISATTRIBUTED** for German (should be Hutwagner et al., 2003) |
| 1034-1035 | "CDC EARS automated aberration detection (German et al., 2001)" | **MISATTRIBUTED** (should be Hutwagner et al., 2003) |

Suggested sentences:
- Lines 363-367: "The Centers for Disease Control and Prevention surveillance evaluation guidelines identify timeliness, data quality, and sensitivity as core attributes of a surveillance system and note that electronic data collection might promote timeliness (German et al., 2001), highlighting..."
- Lines 601-607: "Surveillance may be provider-initiated (passive) or health-department-initiated (active) (Klaucke et al., 1988), and the Philippine framework additionally operates hospital-based sentinel surveillance through NESSS and event-based surveillance (DOH, 2014). Although passive surveillance remains widely used ..., limitations in timeliness and completeness persist; German et al. (2001) recommend evaluating surveillance systems explicitly on these attributes." (Delete the GIS/cluster sentence or support it with DOH, 2014, p. 72.)
- Lines 712-714: "German et al. (2001) note that the increasing use of electronic data collection might promote timeliness."
- Lines 963-966: "...is grounded in the PIDSR threshold procedure (DOH, 2014), WHO (2014) EWARN guidance, and the CDC Early Aberration Reporting System (Hutwagner et al., 2003), which together establish the standard-deviation epidemic threshold and moving-baseline aberration detection..."
- Line 989 and line 1035: replace "German et al., 2001" with "Hutwagner et al., 2003".

**Verdict:** FIX CLAIM (serious) + FIX METADATA. The prior audit's entry "CDC (2019) ✅ Clean" referred to this document under a wrong year; the year is now fixed, but the claims were never checked.

---

### 2.11 Hutwagner et al. (2003), Journal of Urban Health, 80(2 Suppl 1), i89-i96

**Verification sources**
- Crossref: https://api.crossref.org/works/10.1007/PL00022319 (Hutwagner, Thompson, Seeman, Treadwell; vol 80, issue S1, i89-i96, March 2003)
- Europe PMC abstract (PMID 12791783, PMC3456557). Full text PDF blocked for automated access.
- Method details from the companion CDC paper: Hutwagner, Browne, Seeman & Fleischauer (2005), *Emerging Infectious Diseases, 11*(2), 314-316, https://wwwnc.cdc.gov/eid/article/11/2/04-0587_article : C1 uses mean and SD "from the past 7 days"; C2/C3 use 7 days ignoring the 2 most recent; "For C1 and C2, the CUSUM threshold reduces to the mean plus 3 standard deviations"; the separate historical limits method uses the preceding 5 years.

**Metadata:** Correct. ("80(2 Suppl 1)" follows PubMed; Crossref shows issue "S1". Either is acceptable; APA form "*80*(Suppl. 1)" is also fine.)

**Claims**
| Line | Manuscript | Verdict | Note |
|---|---|---|---|
| 676-684 | Threshold = same-week mean of previous five years + 2 SD, "grounded in the aberration-detection statistical literature (Stroup et al., 1989; Hutwagner et al., 2003)" | **OVERSTATED** for Hutwagner | EARS C1-C3 use a 7-day baseline and mean + 3 SD. Supports "aberration detection" in general only. Primary source for the exact formula is DOH (2014, p. 57). |
| 696-698 | EARS "uses moving averages and standard deviation thresholds to identify abnormal disease activity" | SUPPORTED | |
| 925-928 | EARS uses "moving averages and standard deviation methods ..., **the same mathematical foundations** that H-MAP will implement" | **OVERSTATED** | Same family (baseline mean + k·SD), different baseline and multiplier. |

Suggested sentence (925-928): "...using short moving baselines and standard-deviation-based thresholds (Hutwagner et al., 2003), the same family of baseline-plus-standard-deviation methods on which H-MAP's longer five-year threshold is based." Lines 680-683: cite "(DOH, 2014, p. 57; WHO, 2014)" for the formula and keep Stroup/Hutwagner as general aberration-detection background.

**Verdict:** FIX CLAIM. Also move the two German-for-EARS citations (lines 964, 1035) here.

---

### 2.12 ISO/IEC 25010:2011

**Verification sources**
- ISO catalogue page for 25010:2023: https://www.iso.org/standard/78176.html ("Life cycle: Previously **Withdrawn** ISO/IEC 25010:2011; Now Published ISO/IEC 25010:2023"; Publication date 2023-11; Edition 2; "composed of nine characteristics")
- https://www.iso.org/standard/35733.html (2011 page; blocked by bot-check, status taken from the 2023 life-cycle panel)
- ANSI preview summary: https://webstore.ansi.org/preview-pages/ISO/preview_ISO+IEC+25010-2023.pdf (usability replaced by interaction capability, portability by flexibility, safety added)
- https://iso25000.com/index.php/en/iso-25000-standards/iso-25010 (2023 definitions)

**Status: ISO/IEC 25010:2011 is withdrawn and superseded by ISO/IEC 25010:2023** (title changed to "... Product quality model"). 2023 characteristics: functional suitability, performance efficiency, compatibility, interaction capability (formerly usability), reliability, security, maintainability, flexibility (formerly portability), safety (new).

**Claims**
| Line | Manuscript | Verdict | Note |
|---|---|---|---|
| 849-852 | Model "specifies quality characteristics including functional suitability, reliability, usability, performance efficiency, security, maintainability, and portability (ISO, 2011)" | SUPPORTED but incomplete | 2011 has eight; **compatibility** is omitted. |
| 852-855 | "widely adopted [in the Philippines] as the conceptual basis for system evaluation" | CANNOT VERIFY (uncited claim) | Add a Philippine study or soften. |
| 1473-1483 | Characteristic definitions | SUPPORTED with caveat | Functional suitability, reliability, usability, maintainability wording follows 2011; the performance efficiency wording ("within stated time and resource constraints") is closer to 2023 ("within specified time and throughput parameters"). Mixed editions. |
| 571, 1037, 1131 | General attribution | SUPPORTED | |

**Recommendation on which edition to cite:** Cite **ISO/IEC 25010:2023**, because citing a withdrawn standard in a 2026 manuscript invites an easy panel objection. Four of the five chosen characteristics (functional suitability, performance efficiency, reliability, maintainability) carry over unchanged in name; rename "Usability" to "Interaction Capability (formerly Usability)". If the instrument must remain the 2011-based one for comparability with earlier Philippine studies, keep 2011 but add one sentence: "The instrument is adapted from the 2011 edition, since superseded by ISO/IEC 25010:2023, to remain comparable with prior local evaluation studies; the five characteristics used are retained in the 2023 model, with usability renamed interaction capability."

Corrected entry (preferred):
> International Organization for Standardization. (2023). *Systems and software engineering: Systems and software Quality Requirements and Evaluation (SQuaRE): Product quality model* (ISO/IEC Standard No. 25010:2023). https://www.iso.org/standard/78176.html

If 2011 is kept:
> International Organization for Standardization. (2011). *Systems and software engineering: Systems and software Quality Requirements and Evaluation (SQuaRE): System and software quality models* (ISO/IEC Standard No. 25010:2011). https://www.iso.org/standard/35733.html

(Colons replace the official em dashes in the title, per the house no-em-dash rule.)

**Verdict:** FIX METADATA (edition), minor FIX CLAIM (add compatibility; harmonize definitions to one edition).

---

### 2.13 Klaucke et al. (1988), MMWR, 37(S-5), 1-18

**Verification sources**
- CDC MMWR page: https://www.cdc.gov/mmwr/preview/mmwrhtml/00001769.htm (authors: Douglas N. Klaucke, James W. Buehler, Stephen B. Thacker, R. Gibson Parrish, Frederick L. Trowbridge, Ruth L. Berkelman, and the Surveillance Coordination Group)
- Europe PMC/PubMed PMID 3131659: "Guidelines for evaluating surveillance systems", MMWR Suppl 37(5):1-18, May 1988 (PubMed lists CDC as corporate author)

**Metadata:** Authors, title, year, volume, pages correct. APA refinement: "*Morbidity and Mortality Weekly Report, 37*(Suppl. 5), 1–18." plus URL.

> Klaucke, D. N., Buehler, J. W., Thacker, S. B., Parrish, R. G., Trowbridge, F. L., & Berkelman, R. L. (1988). Guidelines for evaluating surveillance systems. *Morbidity and Mortality Weekly Report, 37*(Suppl. 5), 1–18. https://www.cdc.gov/mmwr/preview/mmwrhtml/00001769.htm

**What it says:** "Epidemiologic surveillance is the ongoing and systematic collection, analysis, and interpretation of health data..." (with the CDC "essential to the planning, implementation, and evaluation of public health practice" formulation). Mentions "health-department-initiated (active) surveillance and provider-initiated (passive) surveillance". "Sentinel" and "syndromic" do not appear. On computers: "may promote timeliness".

**Claims**
| Line | Manuscript | Verdict |
|---|---|---|
| 347-349, 591-593 | Surveillance definition | SUPPORTED |
| 601-602 | four types: passive, active, sentinel, syndromic | **MISATTRIBUTED** (only passive/active; "syndromic surveillance" postdates 1988) |

Suggested sentence: see German, lines 601-607.

**Verdict:** FIX CLAIM.

---

## 3. Status of CITATION_AUDIT_v5.md fixes in the current script

| Prior recommendation | Status in `build_chapters_docx_v5.py` |
|---|---|
| Step 1: WHO 2018 to WHO 2014 (WHO/HSE/GCR/LYO/2014.4) | **Applied** (no "WHO, 2018" remains; ref at line 1633) |
| Step 1b: re-source surveillance definition and 4-type taxonomy (suggested Lee et al. 2010 / Langmuir) | **Partly applied.** Re-cited to Klaucke 1988 + German 2001. Definition is now fine, but the 4-type taxonomy (line 602) is still unsupported by either source. |
| Step 2: Srivastava 2024 to Srivastava 2025 | **Applied** (outside this batch) |
| Step 3: Chakraborty no longer cited for Prophet | **Applied**, but new wording introduces an unverified MAPE claim and "directly comparable to Parañaque" / "Asia-Pacific" overstatements |
| Step 4: soften Olana | **Partly applied** (lines 735-749, 902-911, 994-997). **Not applied** at lines 397-400 ("RF and Prophet can achieve reliable predictive accuracy"), 467-468 ("validated in the Philippine context by Olana"), 968 ("Prophet's viability"), 1141-1142 ("previously validated in the Philippine dengue context"), and **1281-1283 (prior audit para 188: "Olana et al. (2025) reported analogous backtest comparisons ... supporting the choice of Prophet")**. Olana is outside this batch; flagged for the batch that covers it. |
| Step 5: Shi rewritten as LASSO, removed from RF validation | **Applied** (lines 766-770, 882-886, 971) |
| "CDC (2019)" entry | Replaced by German et al. (2001) with correct year; prior audit never checked its claims (see 2.10). |

**Prior "clean" verdicts that do not hold up:** Boulos et al. (2011) (misattributed), Dong et al. (2020) (overstated), Dowding et al. (2015) (overstated), DOH (2014) (two misattributed/one overstated uses), CDC/German (multiple misattributions), Carvajal et al. (2018) (misread "single-technique" point and classification analogy).

---

## 4. Additional sources used for replacement suggestions (verified)
- Fisher, R. P., & Myers, B. A. (2011). *International Journal of Health Geographics, 10*, Article 15. https://doi.org/10.1186/1476-072X-10-15 (Crossref + Europe PMC abstract checked)
- Hutwagner, L., Browne, T., Seeman, G. M., & Fleischauer, A. T. (2005). Comparing aberration detection methods with simulated data. *Emerging Infectious Diseases, 11*(2), 314–316. (CDC EID page checked; usable if the manuscript needs an explicit source for EARS C1-C3 parameters)
