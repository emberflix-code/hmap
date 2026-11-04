# New Studies 2022–2026 for the Chapter 1–3 Revision

Literature search for the revised Chapters 1–3 of *Web-Based Disease Outbreak Management System for the City Epidemiology and Surveillance Unit (CESU) of Parañaque City*.

**Search date:** 2026-10-21
**Search source:** Europe PMC REST search (title, abstract, and year filters, ranked by citations), with targeted searches for Philippine, Southeast Asian, and LMIC local-government settings.
**How each source was checked:**
1. Every DOI below was resolved through the Crossref API (`api.crossref.org/works/<DOI>`). Title, full author list, year, journal, volume, issue, and pages or article number come from the Crossref record.
2. Every key finding was taken from the abstract retrieved through Europe PMC (`resultType=core`) for that DOI. No finding is inferred from the title alone.
3. Retraction check: none of the included records has a Crossref `updated-by` retraction notice or a Europe PMC "retracted publication" flag. (PLOS NTD 10.1371/journal.pntd.0013175 carries only a publisher "new version" notice, which is not a retraction.)

**What was excluded:**
- Preprints (Research Square, medRxiv, Preprints.org).
- Frieden et al. (2021) *Lancet* 7-1-7 commentary: the DOI verified, but no abstract was available to read.
- Jiang et al. (2025) *JAMA Netw Open*: a research letter whose abstract is one descriptive sentence.
- Owusu et al. (2023), Sekarrini et al. (2022), and Mohd Hardy Abdullah et al. (2025): descriptive abstracts that do not fit the themes well enough.
- An Acta Medica Philippina health smart card paper: Crossref has no author list for it.

**How dates are given:** the year is Crossref's `issued` date, except for articles that also have a print issue date, where the print year is used (Schneider et al., 2025; Hussein et al., 2023). Two BMC articles were published online in December 2025 inside 2026 volumes (Rattananen et al., 2025; Olana et al., 2025b) and are cited as 2025.

Theme codes: **T1** local digital or web-based surveillance and adoption gaps; **T2** spatio-temporal cluster or hotspot detection; **T3** early warning alerts, notification, and timeliness; **T4** decision support and resource allocation for outbreak response; **T5** Prophet and comparable forecasting models; **T6** security and privacy of health information systems; **T7** workforce, facility, and budget constraints of local health units; **T8** HIS evaluation (ISO/IEC 25010, usability, and acceptance).

---

## T1. Digital and web-based disease surveillance at the local level, and adoption gaps

| Author (Year) | Title | Venue | DOI | Country/setting | Key finding (from abstract) | How it supports the manuscript |
|---|---|---|---|---|---|---|
| Kaburi et al. (2023) | Facilitators and barriers in the implementation of a digital surveillance and outbreak response system in Ghana before and during the COVID-19 pandemic | JMIR Formative Research, 7 | 10.2196/45715 | Ghana; national to district SORMAS roll-out; 22 stakeholder interviews | SORMAS helped through real-time reporting, case-based data, and IDSR alignment. The barriers were unstable interoperability, reliance on a private IT company for hosting, unreliable internet and power, too few devices, and dependence on external funding. Inadequate funding, limited IT infrastructure, and lack of software development expertise reinforced one another. | Shows that adoption gaps are infrastructural and financial, not algorithmic. Justifies hosting the system on LGU-owned infrastructure with a locally maintainable stack (also T7). |
| Joseph et al. (2022) | Improvements in malaria surveillance through the electronic Integrated Disease Surveillance and Response (eIDSR) system in mainland Tanzania, 2013–2021 | Malaria Journal, 21 | 10.1186/s12936-022-04353-w | Tanzania; 7,471 facilities on DHIS2-based eIDSR | Weekly eIDSR completeness rose to 90.2% (2020) and 93.9% (2021). Weekly and monthly incidence agreed in very-low-transmission strata. The authors conclude that eIDSR could support early outbreak detection and case-based surveillance. | Evidence that weekly electronic case reporting, the same cadence as PIDSR, is reliable enough to drive outbreak detection (also T3). |
| Zuniga et al. (2026) | Development and implementation of an interoperable local health information exchange platform for the attainment of universal health coverage in the Philippines | Frontiers in Digital Health, 7 | 10.3389/fdgth.2025.1650273 | Philippines; Pulilan (Bulacan), Cagayan de Oro City, Pangasinan | LGU health systems suffer from fragmented, non-standardized HIS and siloed data. An open-source, FHIR-based LHIE (SMILHIS) was feasible in three LGUs, reduced data duplication, provided real-time dashboards, and strengthened LGU digital health governance. | The closest Philippine LGU-level precedent: it shows LGU-hosted platforms are feasible, and it addresses data exchange rather than outbreak analytics. That leaves the surveillance analytics gap open (also T6, T7). |
| Murai, Ventura, & Gaite (2022) | Timeliness of reporting process in the national routine health information system: The case of 19-year experience of Field Health Services Information System in Palawan, the Philippines | PLOS ONE, 17(2) | 10.1371/journal.pone.0264681 | Philippines; 22 health centers in Palawan, 1996–2014 | Timely FHSIS reports rose from 6.7% to 22.4% only after the deadline was extended. Introducing unfamiliar tasks increased delay. Effective interventions in low-resource settings should extend existing routines rather than replace them. | Philippine evidence that reporting timeliness is chronically poor. Also supports a design that extends the existing PIDSR workflow instead of replacing it (also T3, T7). |
| Sucaldito et al. (2025) | Challenges and opportunities for health information systems in primary care clinics: A mixed-method study among health workers in Manila, Philippines | Applied Clinical Informatics, 16(4) | 10.1055/a-2595-2824 | Philippines; NGO clinic and public health center in Manila; PRISM tools | Both clinics scored low on HIS governance. The barriers were inadequate training and resources; digitalization disrupted workflow; IT infrastructure differed with facility size and funding. | Metro Manila evidence of local HIS governance and resource gaps (also T7, T8). |
| Ong (2026) | Implementation of fireworks-related injury surveillance in Metro Manila, Philippines, 2023–2024 | Western Pacific Surveillance and Response Journal, 17(1) | 10.5365/wpsar.2026.17.1.1272 | Philippines; Metro Manila RESU and sentinel hospitals | Low-cost digital strategies (virtual coordination spaces and data dashboards) cut report turnaround from 31 to 8 minutes. Staff commitment offset time and human-resource limits, but more funding is needed for sustainability. | Direct NCR evidence that a surveillance unit gains timeliness from dashboards while working under staffing and budget limits (also T3, T7). |
| Sanchez Tejeda et al. (2023) | Early warning and response system for dengue outbreaks: Moving from research to operational implementation in Mexico | PLOS Global Public Health, 3(9) | 10.1371/journal.pgph.0001691 | Mexico; national vector-control program | Evidence of integrating outbreak-prediction tools into control programs is scarce. EWARS was integrated stepwise into the national surveillance platform, which showed the need to link disease, vector, and climate data. | Shows that integrating an alerting tool into the routine surveillance platform is the rare and valued step (also T3). |
| Prakash Nayak, Pai B., & Govindan (2025) | Leveraging geographic information system for dengue surveillance: A scoping review | Tropical Medicine and Health, 53 | 10.1186/s41182-025-00783-9 | Global, concentrated in South and Southeast Asia; 64 studies, 2015–2024 | Risk mapping and hotspot detection were the most common GIS uses (n = 26), followed by vector control (n = 23). GIS has evolved into a decision-support system, and real-time monitoring and early warning are the emerging trends. | Frames GIS mapping, hotspot detection, and decision support as one continuum, which is the system's design premise (also T2, T4). |
| Cabaro et al. (2023) | Establishing a national indicator-based surveillance system for hospital bed utilization by COVID-19 patients in the Philippines | Western Pacific Surveillance and Response Journal, 14(5) | 10.5365/wpsar.2023.14.5.1038 | Philippines; DOH DataCollect Bed Tracker, 1,906 facilities | A web-based DOH application collected bed, ventilator, human-resource, and PPE/supplies data from all hospitals. It informed national and local response and showed that adaptive web surveillance is achievable with available technology. | Philippine precedent for web-based surveillance that tracks resources (personnel and supplies) alongside cases (also T4). |

**APA 7 references (T1)**

Cabaro III, B., Dela Paz, G. A., Dotingco, J., Almirol, B. J., Borlongan, G., Cebreros, R. O., Diangco, P., Quijalvo, K. P., Tan, J. P., & Tonato, R. R. (2023). Establishing a national indicator-based surveillance system for hospital bed utilization by COVID-19 patients in the Philippines. *Western Pacific Surveillance and Response Journal, 14*(5), 33–39. https://doi.org/10.5365/wpsar.2023.14.5.1038

Joseph, J. J., Mkali, H. R., Reaves, E. J., Mwaipape, O. S., Mohamed, A., Lazaro, S. N., Aaron, S., Chacky, F., Mahendeka, A., Rulagirwa, H. S., Mwenesi, M., Mwakapeje, E., Ally, A. Y., Kitojo, C., Serbantez, N., Nyinondi, S., Lalji, S. M., Wilillo, R., Al-mafazy, A.-W., . . . Ngondi, J. M. (2022). Improvements in malaria surveillance through the electronic Integrated Disease Surveillance and Response (eIDSR) system in mainland Tanzania, 2013–2021. *Malaria Journal, 21*, Article 321. https://doi.org/10.1186/s12936-022-04353-w

Kaburi, B. B., Wyss, K., Kenu, E., Asiedu-Bekoe, F., Hauri, A. M., Laryea, D. O., Klett-Tammen, C. J., Leone, F., Walter, C., & Krause, G. (2023). Facilitators and barriers in the implementation of a digital surveillance and outbreak response system in Ghana before and during the COVID-19 pandemic: Qualitative analysis of stakeholder interviews. *JMIR Formative Research, 7*, Article e45715. https://doi.org/10.2196/45715

Murai, S., Ventura, R. J. C., & Gaite, J. T. (2022). Timeliness of reporting process in the national routine health information system: The case of 19-year experience of Field Health Services Information System in Palawan, the Philippines. *PLOS ONE, 17*(2), Article e0264681. https://doi.org/10.1371/journal.pone.0264681

Ong, K. P. (2026). Implementation of fireworks-related injury surveillance in Metro Manila, Philippines, 2023–2024. *Western Pacific Surveillance and Response Journal, 17*(1), 53–60. https://doi.org/10.5365/wpsar.2026.17.1.1272

Prakash Nayak, P., Pai B., J., & Govindan, S. (2025). Leveraging geographic information system for dengue surveillance: A scoping review. *Tropical Medicine and Health, 53*, Article 102. https://doi.org/10.1186/s41182-025-00783-9

Sanchez Tejeda, G., Benitez Valladares, D., Correa Morales, F., Toledo Cisneros, J., Espinoza Tamarindo, B. E., Hussain-Alkhateeb, L., Merle, C. S., & Kroeger, A. (2023). Early warning and response system for dengue outbreaks: Moving from research to operational implementation in Mexico. *PLOS Global Public Health, 3*(9), Article e0001691. https://doi.org/10.1371/journal.pgph.0001691

Sucaldito, M. S. F., Malhotra, R., Palileo-Villanueva, L., Besa, J. J., Echague, P. A., Saquilayan, M. J., Banzuela, J. M., Mendoza, K., Elepaño, A., Yan, L. L., & Østbye, T. (2025). Challenges and opportunities for health information systems in primary care clinics: A mixed-method study among health workers in Manila, Philippines. *Applied Clinical Informatics, 16*(4), 1077–1085. https://doi.org/10.1055/a-2595-2824

Zuniga, P. C., Carpio, J. J., Tayam, Q. A., Garcia, P. L., Lacsina, A., Calderon, J., Santiago, J. F., & Batangan, D. (2026). Development and implementation of an interoperable local health information exchange platform for the attainment of universal health coverage in the Philippines. *Frontiers in Digital Health, 7*, Article 1650273. https://doi.org/10.3389/fdgth.2025.1650273

---

## T2. Spatio-temporal cluster and hotspot detection for dengue

| Author (Year) | Title | Venue | DOI | Country/setting | Key finding (from abstract) | How it supports the manuscript |
|---|---|---|---|---|---|---|
| Rotejanaprasert et al. (2024a) | Evaluation and comparison of spatial cluster detection methods for improved decision making of disease surveillance: A case study of national dengue surveillance in Thailand | BMC Medical Research Methodology, 24 | 10.1186/s12874-023-02135-9 | Thailand; simulation plus 2019 national data | No general guidance exists on which cluster method suits dengue. Getis-Ord and Local Moran missed most clusters in the case study, and misdetections concentrated at boundaries. SaTScan suited large regular outbreaks. Bayesian mapping was most precise. | Polygon-based statistics misdetect at area boundaries. This supports a distance-based rule on case points that is not limited by barangay borders (also T4). |
| Rotejanaprasert et al. (2024b) | Comparative evaluation of spatiotemporal methods for effective dengue cluster detection with a case study of national surveillance data in Thailand | Scientific Reports, 14 | 10.1038/s41598-024-82212-1 | Thailand; monthly national data 2018–2020 | Bayesian models and FlexScan performed best. Getis-Ord and Moran's I performed poorly. SaTScan's rigid window tended to flag oversized clusters. Space-time interaction matters. | Supports detection that is explicitly space-time (200 m within 4 weeks) rather than spatial-only. Frames cluster detection as a resource-allocation input (also T4). |
| Rotejanaprasert, Areechokchai, & Maude (2024c) | Two-step spatiotemporal anomaly detection corrected for lag reporting time with application to real-time dengue surveillance in Thailand | BMC Medical Research Methodology, 24 | 10.1186/s12874-024-02141-5 | Thailand; weekly surveillance data | Combining space-time nowcasting (to correct reporting delays) with anomaly detection identified elevated-risk clusters in real time. The authors note that timely notification systems are needed for vector control. | Shows that weekly, prospective cluster detection is operationally useful, and that reporting lag is a design concern (also T3). |
| Rattananen, Sahavechaphan, & Areechokchai (2025) | Identifying high-risk subdistricts for targeted dengue interventions: A spatio-temporal study in Mueang Chonburi district, Thailand, 2011–2020 | BMC Public Health, 26 | 10.1186/s12889-025-25952-7 | Thailand; 18 subdistricts of one urban district | District-level programs mask subdistrict risk. A 5-year average incidence plus SaTScan identified persistent high-endemic subdistricts. Subdistrict-level, timely interventions are recommended. | Sub-city analogue of barangay-level targeting, and it uses a 5-year average baseline like the CESU threshold (also T4). |
| Sena et al. (2025) | Geospatial clustering reveals dengue hotspots across Brazilian municipalities, 2024 | Frontiers in Public Health, 13 | 10.3389/fpubh.2025.1620914 | Brazil; all municipalities, 2024 epidemic | Multivariate DBSCAN, with eps and minPts chosen by k-distance and sensitivity analysis, identified 25 high-burden clusters. Monthly runs showed persistent clusters. The authors call DBSCAN reproducible and operationally relevant for guiding vector control. | The only verified 2022–2026 DBSCAN dengue application. It supports DBSCAN and parameter sensitivity, but at municipal-centroid scale, not case addresses (also T4). |
| Olana et al. (2025b) | Determination of dengue high-risk areas in the Philippines: A kernel density estimation, inverse distance weighting, and ecological niche modeling | Parasites & Vectors, 19 | 10.1186/s13071-025-07200-4 | Philippines; national, 2017–2024 | Case intensity peaked in 2019, with consistently high density in the NCR. The MaxEnt model (AUC 0.847) found nighttime lights, land cover, and population density to be key. NCR is a high-risk area, and the authors recommend risk-based, geospatially targeted surveillance. | Establishes Metro Manila (Parañaque's region) as a persistent high-risk area, which justifies city-level hotspot tooling. |
| Abd Naeeim & Abdul Rahman (2022) | Spatio-temporal clustering analysis using two different scanning windows: A case study of dengue fever in Peninsular Malaysia | Spatial and Spatio-temporal Epidemiology, 41 | 10.1016/j.sste.2022.100496 | Malaysia; 86 districts, 2015–2017 | Kulldorff cylindrical and prismatic scan windows produced similar clusters. Clusters included dense districts and their adjacent neighbours. Identifying them makes vector-control decisions more objective. | Clusters spill into neighbouring units, which parallels the cross-barangay cluster finding (also T4). |
| Osako et al. (2026) | Comprehensive spatiotemporal analysis of dengue epidemics in Vietnam reveals key hotspots and transmission dynamics | International Journal of Infectious Diseases, 165 | 10.1016/j.ijid.2026.108445 | Vietnam; national, 1998–2020 | SaTScan identified high-risk zones (Mekong Delta, southern metropolitan areas, Hanoi) with distinct seasonal peaks. The evidence is presented as a basis for optimizing resource allocation in resource-constrained settings. | Southeast Asian evidence linking hotspot detection to resource allocation (also T4). |
| Ramadona et al. (2023) | Predicting the dengue cluster outbreak dynamics in Yogyakarta, Indonesia: A modelling study | The Lancet Regional Health – Southeast Asia, 15 | 10.1016/j.lansea.2023.100209 | Indonesia; neighbourhood level within one city | A Bayesian spatiotemporal model predicted within-city cluster dynamics one month ahead. Mobility-based adjacency improved fit, while weather added nothing at this scale. | Supports within-city (sub-municipal) cluster analysis and short-horizon prediction (also T5). |
| Buebos-Esteve & Dagamac (2024) | Spatiotemporal models of dengue epidemiology in the Philippines: Integrating remote sensing and interpretable machine learning | Acta Tropica, 255 | 10.1016/j.actatropica.2024.107225 | Philippines; provincial, dekadal, 2016–2020 | Random-forest learners with temporal clustering best predicted incidence and mortality, reflecting seasonality. Rainfall (incidence) and NDVI (mortality) were the key long-term features. | Philippine spatiotemporal modelling remains provincial. This is one of the gaps a city-level, case-address system addresses (also T5). |

**APA 7 references (T2)**

Abd Naeeim, N. S., & Abdul Rahman, N. (2022). Spatio-temporal clustering analysis using two different scanning windows: A case study of dengue fever in Peninsular Malaysia. *Spatial and Spatio-temporal Epidemiology, 41*, Article 100496. https://doi.org/10.1016/j.sste.2022.100496

Buebos-Esteve, D. E., & Dagamac, N. H. A. (2024). Spatiotemporal models of dengue epidemiology in the Philippines: Integrating remote sensing and interpretable machine learning. *Acta Tropica, 255*, Article 107225. https://doi.org/10.1016/j.actatropica.2024.107225

Olana, K. O. A., Thongprachum, A., Poprom, N., Li, W., & Punyapornwithaya, V. (2025b). Determination of dengue high-risk areas in the Philippines: A kernel density estimation, inverse distance weighting, and ecological niche modeling. *Parasites & Vectors, 19*, Article 48. https://doi.org/10.1186/s13071-025-07200-4

Osako, H., Tayama, Y., Ueda, M., Ihara, M., Yamasato, K., Tun, M. M. N., Thuy, N. T. T., Hang, N. L. K., Phuong, H. V. M., Abe, H., Hashizume, M., Hasebe, F., Takamatsu, Y., & Mai, L. T. Q. (2026). Comprehensive spatiotemporal analysis of dengue epidemics in Vietnam reveals key hotspots and transmission dynamics. *International Journal of Infectious Diseases, 165*, Article 108445. https://doi.org/10.1016/j.ijid.2026.108445

Ramadona, A. L., Tozan, Y., Wallin, J., Lazuardi, L., Utarini, A., & Rocklöv, J. (2023). Predicting the dengue cluster outbreak dynamics in Yogyakarta, Indonesia: A modelling study. *The Lancet Regional Health – Southeast Asia, 15*, Article 100209. https://doi.org/10.1016/j.lansea.2023.100209

Rattananen, M., Sahavechaphan, N., & Areechokchai, D. (2025). Identifying high-risk subdistricts for targeted dengue interventions: A spatio-temporal study in Mueang Chonburi district, Thailand, 2011–2020. *BMC Public Health, 26*, Article 303. https://doi.org/10.1186/s12889-025-25952-7

Rotejanaprasert, C., Chinpong, K., Lawson, A. B., Chienwichai, P., & Maude, R. J. (2024a). Evaluation and comparison of spatial cluster detection methods for improved decision making of disease surveillance: A case study of national dengue surveillance in Thailand. *BMC Medical Research Methodology, 24*, Article 14. https://doi.org/10.1186/s12874-023-02135-9

Rotejanaprasert, C., Chinpong, K., Lawson, A. B., & Maude, R. J. (2024b). Comparative evaluation of spatiotemporal methods for effective dengue cluster detection with a case study of national surveillance data in Thailand. *Scientific Reports, 14*, Article 31064. https://doi.org/10.1038/s41598-024-82212-1

Rotejanaprasert, C., Areechokchai, D., & Maude, R. J. (2024c). Two-step spatiotemporal anomaly detection corrected for lag reporting time with application to real-time dengue surveillance in Thailand. *BMC Medical Research Methodology, 24*, Article 10. https://doi.org/10.1186/s12874-024-02141-5

Sena, B. F., Herrera, B. B., Martins, D. B. G., & Lima Filho, J. L. (2025). Geospatial clustering reveals dengue hotspots across Brazilian municipalities, 2024. *Frontiers in Public Health, 13*, Article 1620914. https://doi.org/10.3389/fpubh.2025.1620914

*Note on the 2024a/b/c suffixes:* APA orders same-author, same-year works by title. If the reference list is alphabetised strictly, reassign the letters so that "Comparative evaluation…" = 2024a, "Evaluation and comparison…" = 2024b, and "Two-step…" = 2024c. The Rotejanaprasert, Areechokchai, and Maude paper has a different author set, so strictly it needs no suffix. The suffixes above are working labels only.

---

## T3. Outbreak early warning alerts, SMS and email notification, and timeliness

| Author (Year) | Title | Venue | DOI | Country/setting | Key finding (from abstract) | How it supports the manuscript |
|---|---|---|---|---|---|---|
| Bochner et al. (2023) | Implementation of the 7-1-7 target for detection, notification, and response to public health threats in five countries | The Lancet Global Health, 11(6) | 10.1016/S2214-109X(23)00133-X | Brazil, Ethiopia, Liberia, Nigeria, Uganda; 41 events | Only 27% of events met the full 7-1-7 target. Delays in notification (44% of bottlenecks) and response (39%) were most often at the intermediate (municipal, district, or province) level. Investment at that level is recommended. | Strong evidence that the city or municipal tier is where notification and response stall, which is CESU's tier (also T7). |
| Thayer et al. (2025) | Dengue epidemic alert thresholds for surveillance and decision-making in Puerto Rico | BMJ Open, 15(9) | 10.1136/bmjopen-2025-106182 | Puerto Rico; 86,282 cases, 1986–2024 | A 75th-percentile model-based threshold best balanced false alarms against missed detections, improved on endemic channels, and triggered a real public-health emergency declaration in March 2024. | Supports historical-baseline thresholds and the need to balance false alarms (alert fatigue) against sensitivity. |
| Nansikombi et al. (2023) | Timeliness and completeness of weekly surveillance data reporting on epidemic prone diseases in Uganda, 2020–2021 | BMC Public Health, 23 | 10.1186/s12889-023-15534-w | Uganda; 146 districts, mTRAC SMS to DHIS2 | National timeliness was only 44% to 49%, and no region met the 80% target. Kampala (the urban capital) had the lowest timeliness (19%). | Weekly mobile-to-web reporting does not by itself fix timeliness, and urban districts can perform worst (also T1). |
| Franklin et al. (2025) | Text message surveillance for rapid salmonella outbreak detection: A novel public health approach | Epidemiology and Infection, 153 | 10.1017/S0950268825100617 | Australia (NSW); notified salmonellosis cases | Personalised two-way SMS achieved a 56% response rate (best of letters, online surveys, and SMS) and enabled detection of 10 point-source outbreaks. SMS improved timeliness where resources are constrained. | Direct evidence that SMS is an efficient, acceptable channel for surveillance under resource limits. |
| Schneider et al. (2025) | Implementing an alert system for communicating actionable wastewater surveillance results to school communities, Houston, Texas, 2023–2024 | Public Health Reports, 140(2–3) | 10.1177/00333549241275408 | USA; city health department, 43 schools | The city health department built a text- and email-based alert system from existing city resources and sent 5,178 alerts in six months. It is offered as a framework other agencies can scale to their resources. | A city-level, text and email alert implementation that mirrors the SMS and email module (also T1). |
| Baharom et al. (2022) | Dengue early warning system as outbreak prediction tool: A systematic review | Risk Management and Healthcare Policy, 15 | 10.2147/RMHP.S361106 | Global; 17 studies | Dengue EWS sensitivity ranged from 50% to 100%, specificity from 74% to 94.7%, and PPV from 43% to 86%. EWS supports district health managers but depends heavily on timely, high-quality national surveillance data. | Low PPV in some EWS means false alerts. Supports transparent, rule-based alert logic and data quality (also T5). |
| Cardenas et al. (2022) | The Early Warning and Response System (EWARS-TDR) for dengue outbreaks: Can it also be applied to chikungunya and Zika outbreak warning? | BMC Infectious Diseases, 22 | 10.1186/s12879-022-07197-6 | Mexico (9 districts) and one Colombian city | Alarm sensitivity was 92% to 100% for dengue, with PPV 68% to 83% and 3 to 5 weeks of lead time. Validity varied by disease and was weaker in low-endemic settings. | Supports per-disease alert validation, consistent with the finding that one method does not fit all diseases. |
| Manahan et al. (2024) | Establishing an early warning surveillance system in jails in Calabarzon, the Philippines, 2021 | Western Pacific Surveillance and Response Journal, 15(2) | 10.5365/wpsar.2024.15.2.1083 | Philippines; 21 jails, DOH pilot | Ten events were detected, nine reported within 24 hours, and the local health unit responded with medicines and IPC. The challenges were insufficient workforce, slow internet, and multitasking. | Philippine local-health-unit evidence linking early warning to response (medicines provided) and documenting workforce and connectivity limits (also T7, T4). |
| Stewart-Ibarra et al. (2022) | Co-learning during the co-creation of a dengue early warning system for the health sector in Barbados | BMJ Global Health, 7(Suppl 7) | 10.1136/bmjgh-2021-007842 | Barbados; Ministry of Health with climate agencies | A co-created EWS delivers forecast reports, risk maps, and bulletins. Sustained cross-sector partnership was critical, and implementation is long-term. | Supports co-design with end users (CESU) and the bulletin- or report-style output (Weekly Report tab) (also T4). |

**APA 7 references (T3)**

Baharom, M., Ahmad, N., Hod, R., & Abdul Manaf, M. R. (2022). Dengue early warning system as outbreak prediction tool: A systematic review. *Risk Management and Healthcare Policy, 15*, 871–886. https://doi.org/10.2147/RMHP.S361106

Bochner, A. F., Makumbi, I., Aderinola, O., Abayneh, A., Jetoh, R., Yemanaberhan, R. L., Danjuma, J. S., Lazaro, F. T., Mahmoud, H. J., Yeabah, T. O., Nakiire, L., Yahaya, A. K., Teixeira, R. A., Lamorde, M., Nabukenya, I., Oladejo, J., Adetifa, I. M. O., Oliveira, W., McClelland, A., & Lee, C. T. (2023). Implementation of the 7-1-7 target for detection, notification, and response to public health threats in five countries: A retrospective, observational study. *The Lancet Global Health, 11*(6), e871–e879. https://doi.org/10.1016/S2214-109X(23)00133-X

Cardenas, R., Hussain-Alkhateeb, L., Benitez-Valladares, D., Sánchez-Tejeda, G., & Kroeger, A. (2022). The Early Warning and Response System (EWARS-TDR) for dengue outbreaks: Can it also be applied to chikungunya and Zika outbreak warning? *BMC Infectious Diseases, 22*, Article 235. https://doi.org/10.1186/s12879-022-07197-6

Franklin, N., Hope, K., Glass, K., & Kirk, M. (2025). Text message surveillance for rapid salmonella outbreak detection: A novel public health approach. *Epidemiology and Infection, 153*, Article e118. https://doi.org/10.1017/S0950268825100617

Manahan, K. M., De Guzman, A., Segarra, A., Sucaldito, M. N., & Martinez, R. E. (2024). Establishing an early warning surveillance system in jails in Calabarzon, the Philippines, 2021. *Western Pacific Surveillance and Response Journal, 15*(2), 19–25. https://doi.org/10.5365/wpsar.2024.15.2.1083

Nansikombi, H. T., Kwesiga, B., Aceng, F. L., Ario, A. R., Bulage, L., & Arinaitwe, E. S. (2023). Timeliness and completeness of weekly surveillance data reporting on epidemic prone diseases in Uganda, 2020–2021. *BMC Public Health, 23*, Article 647. https://doi.org/10.1186/s12889-023-15534-w

Schneider, R., Domakonda, K., Bhandari, S., Stadler, L., Ensor, K. B., Mulenga, A., Johnson, C. D., & Hopkins, L. (2025). Implementing an alert system for communicating actionable wastewater surveillance results to school communities, Houston, Texas, 2023–2024. *Public Health Reports, 140*(2–3), 150–155. https://doi.org/10.1177/00333549241275408

Stewart-Ibarra, A. M., Rollock, L., Best, S., Brown, T., Diaz, A. R., Dunbar, W., Lippi, C. A., Mahon, R., Ryan, S. J., Trotman, A., Van Meerbeeck, C. J., & Lowe, R. (2022). Co-learning during the co-creation of a dengue early warning system for the health sector in Barbados. *BMJ Global Health, 7*(Suppl 7), Article e007842. https://doi.org/10.1136/bmjgh-2021-007842

Thayer, M. B., Marzan-Rodriguez, M., Torres Aponte, J., Rivera, A., Rodriguez, D. M., Madewell, Z. J., Rysava, K., Paz-Bailey, G., Adams, L. E., & Johansson, M. A. (2025). Dengue epidemic alert thresholds for surveillance and decision-making in Puerto Rico: Development and prospective application of an early warning system using routine surveillance data. *BMJ Open, 15*(9), Article e106182. https://doi.org/10.1136/bmjopen-2025-106182

*Note on "alert fatigue":* no peer-reviewed 2022–2026 study measuring alert fatigue among surveillance officers was found. Thayer et al. (2025) and Cardenas et al. (2022) address false alarms and PPV, and Truong et al. (2026, matrix #17, not peer-reviewed) addresses prolonged alarms. Present alert fatigue as an inferred design risk, not an established finding.

---

## T4. Decision support and resource allocation for outbreak response

| Author (Year) | Title | Venue | DOI | Country/setting | Key finding (from abstract) | How it supports the manuscript |
|---|---|---|---|---|---|---|
| García et al. (2022) | Real-time, spatial decision support to optimize malaria vector control: The case of indoor residual spraying on Bioko Island, Equatorial Guinea | PLOS Digital Health, 1(5) | 10.1371/journal.pdig.0000025 | Equatorial Guinea; 100 m × 100 m map sectors, 2017–2021 | A spatial decision support system (CIMS) raised IRS operational efficiency to 37.7% and cut overspraying to 18.7%. Fine spatial granularity and real-time follow-up of field teams improved delivery. | The strongest verified evidence that a spatial decision-support system improves the allocation of vector-control resources and personnel (also T2). |
| Rajvanshi et al. (2021) | A comprehensive mobile application tool for disease surveillance, workforce management and supply chain management for Malaria Elimination Demonstration Project | Malaria Journal, 20 | 10.1186/s12936-021-03623-3 | India; district malaria elimination project | A single web and mobile tool combined surveillance, workforce (attendance, tour plans), and supply-chain management. Stock accountability improved 60% and data accuracy reached 99.6%. | Precedent for coupling surveillance with personnel and supplies management in one system (2021, slightly older; also T1, T7). |
| Shea et al. (2023) | Multiple models for outbreak decision support in the face of uncertainty | Proceedings of the National Academy of Sciences, 120(18) | 10.1073/pnas.2207537120 | USA; mid-sized county, 17 modelling teams | Model projections differed in magnitude but agreed on the ranking of interventions. Aggregated outputs gave usable risk quantification for county-level decisions. | Supports presenting ranked, rule-based recommendations rather than precise quantities, and county or city as the decision unit (also T5). |
| Gouveia et al. (2025) | Unraveling regional variability in dengue outbreaks in Brazil: Leveraging the Moving Epidemics Method (MEM) and climate data to optimize vector control strategies | PLOS Neglected Tropical Diseases, 19(6) | 10.1371/journal.pntd.0013175 | Brazil; 120 health macro-regions, 2010–2023 | MEM thresholds plus climate clustering defined four regions with different outbreak onsets. Preventive and control measures should be sequenced region by region, integrated with monitoring systems. | Shows that historical thresholds can drive when and where vector-control resources go (also T2, T3). |
| Saadatian-Elahi et al. (2025) | Effectiveness of integrated vector management on the incidence of dengue in urban Malaysia: A cluster-randomised controlled trial | The Lancet Infectious Diseases, 25(9) | 10.1016/S1473-3099(25)00086-6 | Malaysia; Kuala Lumpur and Putrajaya housing blocks | Targeted IVM (outdoor residual spraying, autodissemination, community engagement) did not significantly reduce overall incidence (RR 0.86, p = 0.17). Targeting high-risk areas warrants further testing. | A caution: resource recommendations should be framed as decision support for CESU judgement, not as proven efficacy. |
| Low et al. (2025) | The effectiveness of dengue vector control: A meta-review | Tropical Medicine & International Health, 30(10) | 10.1111/tmi.70018 | Global; 15 systematic reviews | There is insufficient evidence to recommend one vector-control method. Community mobilisation and insecticide-treated materials were weakly effective, so local governments' vector-control management remains vital. | Justifies a configurable, rule-based recommender aligned with local (CESU and DOH) protocols rather than a fixed optimisation. |

**APA 7 references (T4)**

García, G. A., Atkinson, B., Donfack, O. T., Hilton, E. R., Smith, J. M., Eyono, J. N. M., Iyanga, M. M., Vaz, L. M., Mba Nguema Avue, R., Pollock, J., Ratsirarson, J., Aldrich, E. M., Phiri, W. P., Smith, D. L., Schwabe, C., & Guerra, C. A. (2022). Real-time, spatial decision support to optimize malaria vector control: The case of indoor residual spraying on Bioko Island, Equatorial Guinea. *PLOS Digital Health, 1*(5), Article e0000025. https://doi.org/10.1371/journal.pdig.0000025

Gouveia, A. S., Gomes, M. F. da C., de Almeida, I. F., Lana, R. M., Bastos, L. S., Bianchi, L. M., Oliveira, S. de S., Araujo, E. C., Ferreira, D. A. da C., Oliveira, D. M. B., Godinho, V. B., Vacaro, L. B., Riback, T. I. S., Cruz, O. G., Coelho, F. C., & Codeço, C. T. (2025). Unraveling regional variability in dengue outbreaks in Brazil: Leveraging the Moving Epidemics Method (MEM) and climate data to optimize vector control strategies. *PLOS Neglected Tropical Diseases, 19*(6), Article e0013175. https://doi.org/10.1371/journal.pntd.0013175

Low, G. K. K., Jiee, S. F., Lim, S. H., Omosumwen, O. F., & Shanmuganathan, S. (2025). The effectiveness of dengue vector control: A meta-review. *Tropical Medicine & International Health, 30*(10), 1069–1086. https://doi.org/10.1111/tmi.70018

Rajvanshi, H., Jain, Y., Kaintura, N., Soni, C., Chandramohan, R., Srinivasan, R., Telasey, V., Bharti, P. K., Jain, D., Surve, M., Saxena, S., Gangamwar, V., Anand, M. S., & Lal, A. A. (2021). A comprehensive mobile application tool for disease surveillance, workforce management and supply chain management for Malaria Elimination Demonstration Project. *Malaria Journal, 20*, Article 91. https://doi.org/10.1186/s12936-021-03623-3

Saadatian-Elahi, M., Rabilloud, M., Möhlmann, T. W. R., Langlois-Jacques, C., Ariffin, F. D., Farenhorst, M., Elsensohn, M.-H., Schmitt, F., Richardson, J. H., Baur, F., Leduc, M., Romli, N. N., Tan, L. K., Norazman, M.-R., Shahar, H., Mudin, R. N., Alexander, N., & Ab Hamid, N. (2025). Effectiveness of integrated vector management on the incidence of dengue in urban Malaysia: A cluster-randomised controlled trial. *The Lancet Infectious Diseases, 25*(9), 977–985. https://doi.org/10.1016/S1473-3099(25)00086-6

Shea, K., Borchering, R. K., Probert, W. J. M., Howerton, E., Bogich, T. L., Li, S.-L., van Panhuis, W. G., Viboud, C., Aguás, R., Belov, A. A., Bhargava, S. H., Cavany, S. M., Chang, J. C., Chen, C., Chen, J., Chen, S., Chen, Y., Childs, L. M., Chow, C. C., . . . Runge, M. C. (2023). Multiple models for outbreak decision support in the face of uncertainty. *Proceedings of the National Academy of Sciences, 120*(18), Article e2207537120. https://doi.org/10.1073/pnas.2207537120

*Note on what this theme lacks:* no peer-reviewed study (2020–2026) was found that describes a rule-based or knowledge-based recommender that maps detected dengue hotspots to medicines, personnel, and supply quantities for a city or municipal health unit. The verified evidence covers spatial decision support for vector control (García et al., 2022), integrated workforce and supply tracking (Rajvanshi et al., 2021; Cabaro et al., 2023), and hotspot-to-resource-allocation framing (Rotejanaprasert et al., 2024a, 2024b; Osako et al., 2026). This absence is itself part of the novelty argument.

---

## T5. Prophet and comparable existing forecasting models for infectious disease, 2022–2026

| Author (Year) | Title | Venue | DOI | Country/setting | Key finding (from abstract) | How it supports the manuscript |
|---|---|---|---|---|---|---|
| Fuller et al. (2025) | Comparison of ARIMA and FB-Prophet time series models for the prediction of national and regional malaria incidence in Uganda | Malaria Journal, 24 | 10.1186/s12936-025-05547-8 | Uganda; DHIS2 data, 2020–2023 | ARIMA outperformed Prophet nationally and in 14 of 15 regions (regional MAPE 31.2 vs 47.8). Both are judged usable to guide resource allocation. | Shows that Prophet is a practical, existing tool but must be benchmarked locally, consistent with the system's seasonal-naive comparison (also T4). |
| Chen et al. (2024) | Prediction of influenza outbreaks in Fuzhou, China: Comparative analysis of forecasting models | BMC Public Health, 24 | 10.1186/s12889-024-18583-x | China; city-level, 2013–2022 | Among SARIMA, Prophet, Holt-Winters, and XGBoost, XGBoost had the lowest errors on city influenza data. | City-scale comparison: Prophet is not the most accurate model for influenza. Supports limiting Prophet's claimed role by disease. |
| Xu et al. (2024) | Epidemiological characteristics and prediction model construction of hand, foot and mouth disease in Quzhou City, China, 2005–2023 | Frontiers in Public Health, 12 | 10.3389/fpubh.2024.1474855 | China; city-level HFMD | SARIMA predicted HFMD better than Prophet. The models are intended as a foundation for early warning and resource allocation. | Matches the internal result that Prophet loses on HFMD; city scale (also T3). |
| Luo et al. (2022) | A combined model of SARIMA and Prophet models in forecasting AIDS incidence in Henan Province, China | International Journal of Environmental Research and Public Health, 19(10) | 10.3390/ijerph19105910 | China; provincial monthly AIDS incidence | Prophet beat SARIMA, and a combined L1-norm model was best. | Example where Prophet outperforms SARIMA. Model suitability depends on the series. |
| Fuad, Milki, & Aziz (2026) | Tactical vs. strategic: An adaptable framework for horizon-dependent dengue forecasting using data-driven approaches with serotype and climate covariates in Bangladesh | PLOS One, 21(8) | 10.1371/journal.pone.0353069 | Bangladesh; district panel | No single model was best across horizons. SARIMAX was best for one-step outbreak alerting, and Prophet was best for pooled magnitude forecasting at horizons 2 to 6. Models should be chosen by decision objective. | Newest dengue evidence that Prophet suits short-to-medium trend forecasting, while alerting should rely on threshold or statistical rules, which is the system's division of labour (also T3). |
| Singh et al. (2025) | Comparative estimation of the spread of acute diarrhea and dengue in India using statistical mathematical and deep learning models | Scientific Reports, 15 | 10.1038/s41598-025-00650-x | India; weekly national data, 2011–2024 | Of ten models including Prophet, ARIMA was best for diarrhoea and Seq2Seq best for dengue. Model selection matters for allocating resources. | Further evidence that Prophet is one viable, not dominant, option. Supports using an existing model as-is with transparent benchmarking. |

**APA 7 references (T5)**

Chen, Q., Zheng, X., Shi, H., Zhou, Q., Hu, H., Sun, M., Xu, Y., & Zhang, X. (2024). Prediction of influenza outbreaks in Fuzhou, China: Comparative analysis of forecasting models. *BMC Public Health, 24*, Article 1399. https://doi.org/10.1186/s12889-024-18583-x

Fuad, M. M., Milki, M. S., & Aziz, R. A. (2026). Tactical vs. strategic: An adaptable framework for horizon-dependent dengue forecasting using data-driven approaches with serotype and climate covariates in Bangladesh. *PLOS One, 21*(8), Article e0353069. https://doi.org/10.1371/journal.pone.0353069

Fuller, B., Ssekitoleko, R., Kyozira, C., Colston, J. M., Makumbi, I., Bakainaga, A., Moore, C. C., & Kiirya, H. I. (2025). Comparison of ARIMA and FB-Prophet time series models for the prediction of national and regional malaria incidence in Uganda. *Malaria Journal, 24*, Article 289. https://doi.org/10.1186/s12936-025-05547-8

Luo, Z., Jia, X., Bao, J., Song, Z., Zhu, H., Liu, M., Yang, Y., & Shi, X. (2022). A combined model of SARIMA and Prophet models in forecasting AIDS incidence in Henan Province, China. *International Journal of Environmental Research and Public Health, 19*(10), Article 5910. https://doi.org/10.3390/ijerph19105910

Singh, A., Kumar Sharma, K., Wamanrao Kalare, K., Tripathi, A., Sharma, A., & Bajpai, M. K. (2025). Comparative estimation of the spread of acute diarrhea and dengue in India using statistical mathematical and deep learning models. *Scientific Reports, 15*, Article 34672. https://doi.org/10.1038/s41598-025-00650-x

Xu, W., Zheng, C., Fu, C., Gong, X., Fang, Q., & Yin, Z. (2024). Epidemiological characteristics and prediction model construction of hand, foot and mouth disease in Quzhou City, China, 2005–2023. *Frontiers in Public Health, 12*, Article 1474855. https://doi.org/10.3389/fpubh.2024.1474855

*Also in the existing matrix for T5:* Olana et al. (2025a), Chen and Moraga (2025), and Baker et al. (2025). Together with the six sources above, that gives nine Prophet-benchmarking studies from 2022 to 2026.

---

## T6. Security and privacy in health information systems (RBAC, audit logging, encryption, backup)

| Author (Year) | Title | Venue | DOI | Country/setting | Key finding (from abstract) | How it supports the manuscript |
|---|---|---|---|---|---|---|
| He et al. (2021) | Health care cybersecurity challenges and solutions under the climate of COVID-19: Scoping review | Journal of Medical Internet Research, 23(4) | 10.2196/21747 | Global | The review identified 9 cybersecurity challenges, 11 solutions, and 4 capacity areas needing strengthening. Phishing, ransomware, DDoS, and malware were the dominant pandemic-era attacks on health organisations. | Threat model for the security module (backups against ransomware, access control against phishing). |
| Neprash et al. (2022) | Trends in ransomware attacks on US hospitals, clinics, and other health care delivery organizations, 2016–2021 | JAMA Health Forum, 3(12) | 10.1001/jamahealthforum.2022.4873 | USA; 374 attacks | Attacks doubled (43 to 91 per year) and exposed the PHI of nearly 42 million patients. 44.4% disrupted care, most often through electronic system downtime (41.7%). | Quantitative justification for encrypted, offline-capable secure backups and recovery. |
| Wasserman & Wasserman (2022) | Hospital cybersecurity risks and gaps: Review (for the non-cyber professional) | Frontiers in Digital Health, 4 | 10.3389/fdgth.2022.862221 | USA; 35 core articles | Interoperability and constant accessibility raise risk. Hospital defensive strategies were found to be weak. Training, technical protections, and expert collaboration are needed. | Supports layered controls and staff training in a resource-limited public health office. |
| Nageshwaran, Harris, & Guerche-Seblain (2021) | Review of the role of big data and digital technologies in controlling COVID-19 in Asia: Public health interest vs. privacy | Digital Health, 7 | 10.1177/20552076211002953 | Taiwan, South Korea, Hong Kong, Singapore | Dashboards, case-location maps, and linked databases strengthened response. Balancing privacy and the public good was a key challenge whose resolution would improve uptake. | Asian evidence that case-location mapping, which the system performs, creates privacy obligations (also T1). |
| Lee et al. (2021) | Protecting privacy and transforming COVID-19 case surveillance datasets for public use | Public Health Reports, 136(5) | 10.1177/00333549211026817 | USA CDC; 8 million+ case records | CDC suppressed fields to reduce re-identification risk and kept public and restricted tiers (the latter under data-use agreements). Automated generation improved timeliness. | Supports the anonymised demo environment and tiered (role-based) data exposure. |
| Hussein et al. (2023) | A guiding framework for creating a comprehensive strategy for mHealth data sharing, privacy, and governance in low- and middle-income countries (LMICs) | Journal of the American Medical Informatics Association, 30(4) | 10.1093/jamia/ocac198 | LMICs | Recommends establishing data rights and ownership, building trust, and adopting regulatory frameworks for data protection, while enhancing interoperability. | LMIC governance framing, alongside RA 10173 and NPC Circular 16-01 (already in the reference list). |
| Kannampallil & Adler-Milstein (2022) | Using electronic health record audit log data for research: Insights from early efforts | Journal of the American Medical Informatics Association, 30(1) | 10.1093/jamia/ocac173 | USA | EHR audit logs are time-sequenced records of user activity. Measures derived from them should be transparent, validated, and standardised. | Supports the audit-log feature as both an accountability control and a source for usage evaluation. |
| Kang & Kim (2022) | Secure collaborative platform for health care research in an open environment: Perspective on accountability in access control | Journal of Medical Internet Research, 24(10) | 10.2196/37978 | South Korea; health big data platform | Attribute-based encryption gave fine-grained access control and encryption at rest. Accountability (detecting and blocking illegal users) was added through logging on a blockchain. | Shows that access control, encryption at rest, and accountability logging are treated together as core requirements. |
| de Carvalho Junior & Bandiera-Paiva (2020) | Strengthen electronic health records system (EHR-S) access-control to cope with GDPR explicit consent | Journal of Medical Systems, 44(10) | 10.1007/s10916-020-01631-5 | Brazil / GDPR context | Extends RBAC with patient-centric control and encryption so that data access respects explicit consent under a data protection law. | Directly about RBAC under a privacy statute. Pre-2022, but the only verified RBAC-plus-law source. |
| Argyridou et al. (2023) | Cyber hygiene methodology for raising cybersecurity and data privacy awareness in health care organizations: Concept study | Journal of Medical Internet Research, 25 | 10.2196/41294 | Three European health organisations | Humans are the weakest link. A survey-based risk method recommends targeted human-centric controls for each employee group. | Supports the role-specific training and policies that accompany the RBAC design. |
| Murdoch (2021) | Privacy and artificial intelligence: Challenges for protecting health information in a new era | BMC Medical Ethics, 22 | 10.1186/s12910-021-00687-3 | Global | New algorithms can re-identify de-identified data. Regulation should emphasise consent and stronger anonymisation and protection. | Supports keeping forecasting and analytics on LGU-hosted servers and anonymising data in the demo environment. |

**APA 7 references (T6)**

Argyridou, E., Nifakos, S., Laoudias, C., Panda, S., Panaousis, E., Chandramouli, K., Navarro-Llobet, D., Mora Zamorano, J., Papachristou, P., & Bonacina, S. (2023). Cyber hygiene methodology for raising cybersecurity and data privacy awareness in health care organizations: Concept study. *Journal of Medical Internet Research, 25*, Article e41294. https://doi.org/10.2196/41294

de Carvalho Junior, M. A., & Bandiera-Paiva, P. (2020). Strengthen electronic health records system (EHR-S) access-control to cope with GDPR explicit consent. *Journal of Medical Systems, 44*(10), Article 172. https://doi.org/10.1007/s10916-020-01631-5

He, Y., Aliyu, A., Evans, M., & Luo, C. (2021). Health care cybersecurity challenges and solutions under the climate of COVID-19: Scoping review. *Journal of Medical Internet Research, 23*(4), Article e21747. https://doi.org/10.2196/21747

Hussein, R., Griffin, A. C., Pichon, A., & Oldenburg, J. (2023). A guiding framework for creating a comprehensive strategy for mHealth data sharing, privacy, and governance in low- and middle-income countries (LMICs). *Journal of the American Medical Informatics Association, 30*(4), 787–794. https://doi.org/10.1093/jamia/ocac198

Kang, G., & Kim, Y.-G. (2022). Secure collaborative platform for health care research in an open environment: Perspective on accountability in access control. *Journal of Medical Internet Research, 24*(10), Article e37978. https://doi.org/10.2196/37978

Kannampallil, T., & Adler-Milstein, J. (2022). Using electronic health record audit log data for research: Insights from early efforts. *Journal of the American Medical Informatics Association, 30*(1), 167–171. https://doi.org/10.1093/jamia/ocac173

Lee, B., Dupervil, B., Deputy, N. P., Duck, W., Soroka, S., Bottichio, L., Silk, B., Price, J., Sweeney, P., Fuld, J., Weber, J. T., & Pollock, D. (2021). Protecting privacy and transforming COVID-19 case surveillance datasets for public use. *Public Health Reports, 136*(5), 554–561. https://doi.org/10.1177/00333549211026817

Murdoch, B. (2021). Privacy and artificial intelligence: Challenges for protecting health information in a new era. *BMC Medical Ethics, 22*, Article 122. https://doi.org/10.1186/s12910-021-00687-3

Nageshwaran, G., Harris, R. C., & Guerche-Seblain, C. E. (2021). Review of the role of big data and digital technologies in controlling COVID-19 in Asia: Public health interest vs. privacy. *Digital Health, 7*, Article 20552076211002953. https://doi.org/10.1177/20552076211002953

Neprash, H. T., McGlave, C. C., Cross, D. A., Virnig, B. A., Puskarich, M. A., Huling, J. D., Rozenshtein, A. Z., & Nikpay, S. S. (2022). Trends in ransomware attacks on US hospitals, clinics, and other health care delivery organizations, 2016–2021. *JAMA Health Forum, 3*(12), Article e224873. https://doi.org/10.1001/jamahealthforum.2022.4873

Wasserman, L., & Wasserman, Y. (2022). Hospital cybersecurity risks and gaps: Review (for the non-cyber professional). *Frontiers in Digital Health, 4*, Article 862221. https://doi.org/10.3389/fdgth.2022.862221

*Note on Philippine sources:* no peer-reviewed, DOI-indexed study that evaluates Philippine health information systems against RA 10173 was found. The Philippine Data Privacy Act context should rest on the primary legal sources already in the reference list (Republic Act No. 10173, 2012; NPC Circular 16-01, 2016), with the studies above as international technical support. Six of the eleven T6 sources predate 2022 (four from 2021, one from 2020, and one from 2022, Hussein et al., cited 2023). They are kept because they are the most directly relevant verified sources.

---

## T7. Health workforce, facility, and budget constraints of Philippine local health units

| Author (Year) | Title | Venue | DOI | Country/setting | Key finding (from abstract) | How it supports the manuscript |
|---|---|---|---|---|---|---|
| Pepito et al. (2025) | Health workforce issues and recommended practices in the implementation of Universal Health Coverage in the Philippines: A qualitative study | Human Resources for Health, 23 | 10.1186/s12960-025-00988-3 | Philippines; national, regional, and local levels | Restrictive government hiring policies, budget caps on personnel services, poor working conditions, uncompetitive salaries, lack of trained personnel, and overseas migration hinder UHC. The authors recommend revisiting the Local Government Code. | Core urgency evidence: LGU health offices cannot simply hire more surveillance staff, so automation of routine analysis is warranted. |
| Escano-Arias et al. (2025) | Strengthening local health systems and governance for Universal Health Coverage: Experiences and lessons from the COVID-19 pandemic response in Quezon City, Philippines | Health Policy and Planning, 40(3) | 10.1093/heapol/czaf002 | Philippines; Quezon City LGU | Quezon City used the pandemic to strengthen its local health system and governance through partnerships and foresight. The paper also identifies constraints and recommendations for consolidating the gains. | A neighbouring Metro Manila LGU precedent for city-led system strengthening (also T1). |
| de Claro et al. (2024) | The role of local health officers in advancing public health and primary care integration: Lessons from the ongoing Universal Health Coverage reforms in the Philippines | BMJ Global Health, 9(1) | 10.1136/bmjgh-2023-014118 | Philippines; devolved LGUs | Decentralised settings show fragmentation, poor coordination, and impeded timely information sharing and resource allocation. The UHC law promotes digital health technologies. | Links devolution directly to delayed information sharing and resource allocation, the two problems the system targets. |
| Maravilla et al. (2023) | Exploring indirect impacts of COVID-19 on local health systems from the perspectives of health workers and higher education stakeholders in the Philippines using a phenomenological approach | The Lancet Regional Health – Western Pacific, 30 | 10.1016/j.lanwpc.2022.100585 | Philippines; 29 public health workers and others | Public health workers reported work overload, stress, pressure to learn new technology, and digital-equity challenges. Effective workforce management and equitable digital innovation are needed. | Workforce strain plus technology burden: supports a design that reduces manual work and is easy to learn (also T8). |
| Ravishankar et al. (2024) | Reconciling devolution with health financing and public financial management: Challenges and policy options for the health sector | BMJ Global Health, 9(5) | 10.1136/bmjgh-2024-015216 | Seven countries including the Philippines and Indonesia | Subnational governments depend on central transfers, and most have no required minimum health budget share. Weak budget planning, delayed transfers, and line-item budgets constrain them. Digitalised information systems can improve expenditure management. | Budget-constraint evidence that includes the Philippines. Supports low-cost, LGU-hosted deployment. |
| Yu et al. (2023) | 'Kontra-partido': Untangling oppositional local politics and healthcare devolution in the Philippines | Health Policy and Planning, 38(7) | 10.1093/heapol/czad039 | Philippines; multi-sited fieldwork | Under devolution, local politics leads to politicised appointments, a hampered grassroots workforce, and preference for "visible" over sustainable projects. | Explains why local health information systems are often unsustained, and supports institutionalising the system within CESU workflow. |
| Liwanag et al. (2022) | Cocreation in health workforce planning to shape the future of the health care system in the Philippines | Global Health: Science and Practice, 10(6) | 10.9745/GHSP-D-22-00176 | Philippines; DOH national HRH projection | The most extensive DOH workforce projection to date assessed workforce quantity, skill mix, and distribution against WHO density targets, informing the National HRH Master Plan (task shifting and related proposals). | Official-level evidence of workforce shortfalls and endorsement of task shifting, which automation supports. |
| Boehme et al. (2022) | Operational challenges of the Philippine Antimicrobial Resistance Surveillance Program during the COVID-19 pandemic | Western Pacific Surveillance and Response Journal, 13(3) | 10.5365/wpsar.2022.13.3.917 | Philippines; national ARSP sentinel sites | Human, infrastructure, and financial resources were reallocated to the pandemic and data submission fell. Automated data submission and supply-chain strengthening were key to sustaining surveillance. | Philippine surveillance-program evidence that automation preserves surveillance under staff diversion (also T1). |
| Garcia, De La Vega, & Mercado (2022) | Health information systems for older persons in select government tertiary hospitals and health centers in the Philippines: Cross-sectional study | Journal of Medical Internet Research, 24(2) | 10.2196/29541 | Philippines; 27 hospitals and 16 health centers | HIS were fragmented. The challenges were inadequately trained personnel, offline facility-based systems, unstable internet, and non-uniform reporting. | Facility-level infrastructure and training gaps in Philippine government health facilities (also T1). |

**APA 7 references (T7)**

Boehme, K., Sia, S., Ablola, F., Gayeta, J., & Alea, M. C. (2022). Operational challenges of the Philippine Antimicrobial Resistance Surveillance Program during the COVID-19 pandemic. *Western Pacific Surveillance and Response Journal, 13*(3), 58–63. https://doi.org/10.5365/wpsar.2022.13.3.917

de Claro, V., Lava, J. B., Bondoc, C., & Stan, L. (2024). The role of local health officers in advancing public health and primary care integration: Lessons from the ongoing Universal Health Coverage reforms in the Philippines. *BMJ Global Health, 9*(1), Article e014118. https://doi.org/10.1136/bmjgh-2023-014118

Escano-Arias, E. A., Abarquez, R. A. D. G., Cruz, R. V., Espeleta, R., Ong, M. M., Loreche, A. M., Pepito, V. C. F., Gomez, V., & Dayrit, M. M. (2025). Strengthening local health systems and governance for Universal Health Coverage: Experiences and lessons from the COVID-19 pandemic response in Quezon City, Philippines. *Health Policy and Planning, 40*(3), 436–442. https://doi.org/10.1093/heapol/czaf002

Garcia, A. P., De La Vega, S. F., & Mercado, S. P. (2022). Health information systems for older persons in select government tertiary hospitals and health centers in the Philippines: Cross-sectional study. *Journal of Medical Internet Research, 24*(2), Article e29541. https://doi.org/10.2196/29541

Liwanag, H. J., Uy, J., Politico, M. R., Padilla, M. J., Arzobal, M. C., Manuel, K., Cagouia, A. L., Tolentino, P., Frahsa, A., & Ronquillo, K. (2022). Cocreation in health workforce planning to shape the future of the health care system in the Philippines. *Global Health: Science and Practice, 10*(6), Article e2200176. https://doi.org/10.9745/GHSP-D-22-00176

Maravilla, J., Catiwa, J., Guariño, R., Yap, J. F., Pagatpatan, C., Orolfo, D. D., de Silos, J., Leigh, M. C., Babate, J., & Lopez, V. (2023). Exploring indirect impacts of COVID-19 on local health systems from the perspectives of health workers and higher education stakeholders in the Philippines using a phenomenological approach. *The Lancet Regional Health – Western Pacific, 30*, Article 100585. https://doi.org/10.1016/j.lanwpc.2022.100585

Pepito, V. C. F., Loreche, A. M., Legaspi, R. S., Guinaran, R. C., Capeding, T. P. J. Z., Ong, M. M., & Dayrit, M. M. (2025). Health workforce issues and recommended practices in the implementation of Universal Health Coverage in the Philippines: A qualitative study. *Human Resources for Health, 23*, Article 21. https://doi.org/10.1186/s12960-025-00988-3

Ravishankar, N., Mathauer, I., Barroy, H., Vîlcu, I., Chaitkin, M., Offosse, M. J., Co, P. A., Nakyanzi, A., Mbuthia, B., Lourenço, S., Mardani, H., & Kutzin, J. (2024). Reconciling devolution with health financing and public financial management: Challenges and policy options for the health sector. *BMJ Global Health, 9*(5), Article e015216. https://doi.org/10.1136/bmjgh-2024-015216

Yu, V. G., Lasco, G., David, C. C., & Baysic, I. S. (2023). 'Kontra-partido': Untangling oppositional local politics and healthcare devolution in the Philippines. *Health Policy and Planning, 38*(7), 840–850. https://doi.org/10.1093/heapol/czad039

*Additional Philippine T7 evidence placed under other themes:* Murai et al. (2022), Sucaldito et al. (2025), Ong (2026), Manahan et al. (2024), and Zuniga et al. (2026). *Note on PIDSR:* no peer-reviewed 2022–2026 evaluation of PIDSR or ESR implementation itself was found in Europe PMC. Herbuela et al. (2021, T8) states in its abstract that Philippine dengue surveillance is passive (notification-based). For PIDSR-specific constraints, cite the DOH PIDSR Manual of Procedures (already referenced) and, if available, DOH or WHO grey literature verified separately.

---

## T8. Evaluation of health information systems (ISO/IEC 25010, usability, and acceptance by health workers)

| Author (Year) | Title | Venue | DOI | Country/setting | Key finding (from abstract) | How it supports the manuscript |
|---|---|---|---|---|---|---|
| Al Ani et al. (2022) | Which electronic health record system should we use? A systematic review | Medical Principles and Practice, 31(4) | 10.1159/000525135 | UK/USA; 40 studies | The review appraised EHRs against the eight ISO/IEC 25010 characteristics. Usability (25 studies) was the most assessed and security (2 studies) the least. | Precedent for ISO/IEC 25010 in health IS evaluation. Shows security is the least-evaluated characteristic, which the evaluation can address (also T6). |
| Mamani-Pari et al. (2026) | Development and psychometric validation of a usability instrument based on ISO 25010 for electronic health record systems in Peruvian health care settings | JMIR Human Factors, 13 | 10.2196/81377 | Peru (LMIC); 115 physicians, nurses, and administrative staff | A 23-item ISO 25010-based instrument showed α = .968 and Aiken's V = 0.95, and 81.7% rated usability very high. Aligning with local regulatory standards was emphasised. | The closest methodological analogue for an ISO 25010 questionnaire with health workers in an LMIC, aligned to national regulation (here RA 10173 and DOH). |
| Barletta et al. (2023) | Clinical-chatbot AHP evaluation based on "quality in use" of ISO/IEC 25010 | International Journal of Medical Informatics, 170 | 10.1016/j.ijmedinf.2022.104951 | Italy | Proposes measures for each ISO/IEC 25010 quality-in-use characteristic (effectiveness, efficiency, satisfaction, freedom from risk, context coverage) for health software. | Supports operationalising ISO 25010 characteristics into measurable items. |
| Greulich, Hegselmann, & Dugas (2021) | An open-source, standard-compliant, and mobile electronic data capture system for medical research (OpenEDC): Design and evaluation study | JMIR Medical Informatics, 9(11) | 10.2196/29176 | Germany | Twenty requirements were categorised by ISO/IEC 25010 (functional suitability, availability, compatibility, usability, security) and followed by a usability evaluation. | Precedent for structuring requirements and evaluation of a web health system by ISO 25010 (also T6). |
| De Mesa et al. (2024) | Facing the digital frontier: Exploring user acceptance of electronic health records in an urban, rural and remote setting in the Philippines | BMJ Open Quality, 13(2) | 10.1136/bmjoq-2023-002621 | Philippines; 128 users including physicians, nurses, midwives, and BHWs | Over 94% intended to use the EHR (UTAUT). Self-efficacy was the only significant predictor (+31% per unit). Co-production with primary care providers sustains systems. | Philippine health-worker acceptance evidence. Supports co-design with CESU and training (also T1). |
| Ndlovu et al. (2022) | Acceptance of the District Health Information System Version 2 platform for malaria case-based surveillance by health care workers in Botswana: Web-based survey | JMIR Formative Research, 6(3) | 10.2196/32722 | Botswana; 27 district core users | TAM-based survey showed high acceptance of DHIS2 for case-based surveillance, with organisational readiness flagged as a risk. | Acceptance of a surveillance platform by district users (also T1). |
| Hailemariam et al. (2024) | Intention to use an electronic community health information system among health extension workers in rural northwest Ethiopia | JMIR Human Factors, 11 | 10.2196/47081 | Ethiopia; 456 health extension workers | Only 39.3% intended to use the eCHIS. Effort expectancy, social influence, and hedonic motivation were significant. | Shows that ease of use determines uptake by frontline workers. |
| Herbuela et al. (2021) | Early detection of dengue fever outbreaks using a surveillance app (Mozzify): Cross-sectional mixed methods usability study | JMIR Public Health and Surveillance, 7(3) | 10.2196/19034 | Philippines; 948 participants including 79 health professionals | Notes that Philippine dengue surveillance is passive (notifications from barangay to city offices and hospitals). The app scored above 4 out of 5 on MARS and uMARS. | Philippine dengue surveillance usability precedent, and confirms the passive-surveillance baseline (also T1, T3). |
| Almasi et al. (2023) | Usability evaluation of dashboards: A systematic literature review of tools | BioMed Research International, 2023 | 10.1155/2023/9990933 | Global; 29 studies | SUS, TAM, SART, QUIS, UTAUT, and Health-ITUES were the most used dashboard instruments. Dashboard-specific criteria (usefulness, operability, learnability, situational awareness) are proposed. | Supports adding dashboard-specific usability items to the ISO 25010 instrument. |

**APA 7 references (T8)**

Al Ani, M., Garas, G., Hollingshead, J., Cheetham, D., Athanasiou, T., & Patel, V. (2022). Which electronic health record system should we use? A systematic review. *Medical Principles and Practice, 31*(4), 342–351. https://doi.org/10.1159/000525135

Almasi, S., Bahaadinbeigy, K., Ahmadi, H., Sohrabei, S., & Rabiei, R. (2023). Usability evaluation of dashboards: A systematic literature review of tools. *BioMed Research International, 2023*, Article 9990933. https://doi.org/10.1155/2023/9990933

Barletta, V. S., Caivano, D., Colizzi, L., Dimauro, G., & Piattini, M. (2023). Clinical-chatbot AHP evaluation based on "quality in use" of ISO/IEC 25010. *International Journal of Medical Informatics, 170*, Article 104951. https://doi.org/10.1016/j.ijmedinf.2022.104951

De Mesa, R. Y. H., Galingana, C. L. T., Tan-Lim, C. S. C., Javelosa, M. A. U., Panganiban, J. M. S., Fabian, N. M. C., Calderon, Y., Rey, M. P., Bernal-Sundiang, N., Sanchez, J. T., Dans, L. F., Casile, R. U., & Dans, A. L. (2024). Facing the digital frontier: Exploring user acceptance of electronic health records in an urban, rural and remote setting in the Philippines. *BMJ Open Quality, 13*(2), Article e002621. https://doi.org/10.1136/bmjoq-2023-002621

Greulich, L., Hegselmann, S., & Dugas, M. (2021). An open-source, standard-compliant, and mobile electronic data capture system for medical research (OpenEDC): Design and evaluation study. *JMIR Medical Informatics, 9*(11), Article e29176. https://doi.org/10.2196/29176

Hailemariam, T., Atnafu, A., Gezie, L., Kaasbøll, J., Klein, J., & Tilahun, B. (2024). Intention to use an electronic community health information system among health extension workers in rural northwest Ethiopia: Cross-sectional study using the Unified Theory of Acceptance and Use of Technology 2 model. *JMIR Human Factors, 11*, Article e47081. https://doi.org/10.2196/47081

Herbuela, V. R. D. M., Karita, T., Carvajal, T. M., Ho, H. T., Lorena, J. M. O., Regalado, R. A., Sobrepeña, G. D., & Watanabe, K. (2021). Early detection of dengue fever outbreaks using a surveillance app (Mozzify): Cross-sectional mixed methods usability study. *JMIR Public Health and Surveillance, 7*(3), Article e19034. https://doi.org/10.2196/19034

Mamani-Pari, D., Peñaloza-Hualpa, A. F., Humpiri-Flores, M. E., Gutierrez-Quispe, E., & Otazu-Luque, J. E. (2026). Development and psychometric validation of a usability instrument based on ISO 25010 for electronic health record systems in Peruvian health care settings: Methodological study. *JMIR Human Factors, 13*, Article e81377. https://doi.org/10.2196/81377

Ndlovu, K., Mauco, K. L., Keetile, M., Kadimo, K., Senyatso, R. Y., Ntebela, D., Valela, B., & Murambi, C. (2022). Acceptance of the District Health Information System Version 2 platform for malaria case-based surveillance by health care workers in Botswana: Web-based survey. *JMIR Formative Research, 6*(3), Article e32722. https://doi.org/10.2196/32722

*Note on Almasi et al. (2023):* BioMed Research International (Hindawi/Wiley) had a large batch of retractions in 2023. This article carries no retraction or expression-of-concern notice in Crossref or Europe PMC as of the search date, but re-check it before final submission, or replace it if the panel is sensitive to the venue.

---

## 2. Mapping the existing pool to themes T1–T8

### 2a. The 31 literature-matrix sources (`literature_matrix_export.md`)

| # | Source | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | Note for the revision |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Olana et al. (2025a), TBED |  | ✓ |  |  | ✓ |  |  |  | Keep; national Prophet benchmark |
| 2 | Chakraborty et al. (2019) |  |  |  |  | ✓ |  |  |  | Background only |
| 3 | Chen & Moraga (2025) |  |  |  |  | ✓ |  |  |  | Keep; Prophet best at 12-week horizon |
| 4 | Zhao et al. (2020) |  |  |  |  | ✓ |  |  |  | RF-specific; lower priority if RF development is out of scope |
| 5 | Tian et al. (2024) |  |  |  |  | ✓ |  |  |  | Lower priority |
| 6 | Liu et al. (2025) |  |  |  |  | ✓ |  | ✓* |  | *LMIC resource-constrained framing only |
| 7 | Salim et al. (2021) |  |  | ✓ |  | ✓ |  |  |  | Week-of-year feature |
| 8 | Yavari Nejad & Varathan (2021) |  |  |  |  | ✓ |  |  |  | Lower priority |
| 9 | Ismail et al. (2022) |  |  | ✓ |  | ✓ |  |  |  | Keep; EWS practicality |
| 10 | Patil & Pandya (2021) |  | ✓ |  |  | ✓ |  |  |  | Includes Prophet |
| 11 | Baker et al. (2025) |  |  |  |  | ✓ |  |  |  | Keep; Prophet not superior |
| 12 | Olana et al. (2026), Front Public Health |  | ✓ |  |  |  |  |  |  | Keep; calls for barangay drill-down |
| 13 | Ygoña et al. (2025) |  | ✓ |  |  |  |  |  |  | Keep; Philippine scan statistic |
| 14 | Medina et al. (2023) |  | ✓ |  | ✓ |  |  |  |  | Keep; Quezon City hotspots |
| 15 | Medina et al. (2025) |  | ✓ |  |  |  |  |  |  | Keep |
| 16 | Santos-Silva et al. (2025) | ✓ |  | ✓ |  |  |  |  |  | Keep; municipal EWS |
| 17 | Truong et al. (2026) [not peer-reviewed] |  |  | ✓ |  |  |  |  |  | Label as working paper |
| 18 | Hu et al. (2024) |  |  | ✓ |  | ✓ |  |  |  | Integration gap |
| 19 | Villanueva-Miranda et al. (2025) | ✓ |  | ✓ |  |  | ✓ |  |  | Deployment and privacy barriers |
| 20 | Shen et al. (2025) | ✓ |  | ✓ |  |  |  | ✓ |  | Local capacity |
| 21 | Dong et al. (2020) | ✓ | ✓ |  |  |  |  |  |  | Web GIS dashboard |
| 22 | Reynolds et al. (2022) | ✓ |  | ✓ |  |  |  | ✓ |  | DHIS2; workforce limits |
| 23 | Ibrahim et al. (2021) | ✓ |  | ✓ |  |  |  |  |  | eIDSR in LGAs |
| 24 | Sanglard et al. (2025) | ✓ | ✓ |  |  |  |  |  |  | Geocoding |
| 25 | Leung et al. (2023) |  |  |  |  | ✓ |  |  |  | External validation gap |
| 26 | Sylvestre et al. (2022) |  |  |  |  | ✓ |  |  |  | Background |
| 27 | Olawade et al. (2023) |  |  |  | ✓ |  | ✓ | ✓ |  | Privacy and infrastructure barriers |
| 28 | Srivastava et al. (2025) |  |  |  | ✓ |  |  |  |  | AI as decision support |
| 29 | Taylor & Letham (2018) [seminal] |  |  |  |  | ✓ |  |  |  | Keep; Prophet method |
| 30 | Carvajal et al. (2018) [seminal, local] |  |  |  |  | ✓ |  |  |  | Metro Manila dengue |
| 31 | Breiman (2001) [seminal] |  |  |  |  | ✓ |  |  |  | Only if an RF component remains in scope |

**Coverage of the matrix:** T5 has 17 sources, T3 9, T2 8, T1 7, T7 4 (one with a caveat), T4 3, T6 2, T8 0. The existing pool is heavily weighted toward forecasting (T5). It is thin on alerts and notification channels, recommenders, security, workforce constraints, and evaluation, and the new sources above were chosen to fill those themes. Because the revised scope uses Prophet as-is without model development, items 2, 4, 5, 8, 26, and 31 can be shortened or moved to background.

### 2b. Existing manuscript references (`build_chapters_docx_v5.py`, `refs = [`)

| Reference | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 |
|---|---|---|---|---|---|---|---|---|
| Beck et al. (2001) Agile Manifesto | | | | | | | | (methodology only) |
| Boulos et al. (2011) | ✓ | ✓ | | | | | | |
| Breiman (2001) | | | | | ✓ | | | |
| Carvajal et al. (2018) | | | | | ✓ | | | |
| Chakraborty et al. (2019) | | | | | ✓ | | | |
| Department of Health (2014) PIDSR MOP | ✓ | | ✓ | | | | ✓ | |
| Dong et al. (2020) | ✓ | ✓ | | | | | | |
| Dowding et al. (2015) | ✓ | | | | | | | ✓ |
| Freifeld et al. (2008) HealthMap | ✓ | | ✓ | | | | | |
| German et al. (2001) CDC guidelines | | | ✓ | | | | | ✓ |
| Hutwagner et al. (2003) EARS | | | ✓ | | | | | |
| ISO (2011) ISO/IEC 25010 | | | | | | ✓ | | ✓ |
| Klaucke et al. (1988) | | | ✓ | | | | | ✓ |
| Lawson (2018) | | ✓ | | | | | | |
| National Privacy Commission (2016) Circular 16-01 | | | | | | ✓ | | |
| Nykiforuk & Flaman (2011) | ✓ | ✓ | | | | | | |
| Olana et al. (2025a) | | ✓ | | | ✓ | | | |
| Republic Act No. 10173 (2012) | | | | | | ✓ | | |
| Richey & Klein (2007) | | | | | | | | (methodology only) |
| Shaman & Karspeck (2012) | | | ✓ | | ✓ | | | |
| Shi et al. (2016) | | | ✓ | ✓ | ✓ | | | |
| Srivastava et al. (2025) | | | | ✓ | | | | |
| Stroup et al. (1989) | | | ✓ | | | | | |
| Taylor & Letham (2018) | | | | | ✓ | | | |
| WHO (2014) EWARN / EBS | | | ✓ | | | | ✓ | |

---

## 3. Draft thematic gap analysis

*(About 890 words. No em dashes. Cites only DOI-verified sources: those in this file and in the existing 31-item matrix.)*

**Thematic Gap Analysis**

The literature on digital disease surveillance converges on a clear conclusion: the barrier to better outbreak control in low- and middle-income settings is no longer the availability of analytical methods but their integration into the routine work of local health units. The evidence below is organised into five themes; each strand is credible alone, yet none is joined to the others in a city-level workflow.

*Digitisation without analysis.* Electronic surveillance platforms consistently improve reporting completeness and, to a lesser degree, timeliness. Tanzania's eIDSR reached more than 90% weekly completeness (Joseph et al., 2022), and Nigeria's local government areas raised timeliness from 43% to 73% (Ibrahim et al., 2021). Implementation studies, however, show that these gains depend on infrastructure, funding, and in-country software capacity. In Ghana, unstable interoperability, reliance on private hosting, unreliable power and connectivity, and dependence on external funding constrained SORMAS (Kaburi et al., 2023). In the Philippines, routine reporting has been chronically late (Murai et al., 2022), local health information systems remain fragmented and weakly governed (Sucaldito et al., 2025; Garcia et al., 2022), and the most advanced LGU platform documented, an interoperable health information exchange piloted in three LGUs, addresses data exchange rather than outbreak analytics (Zuniga et al., 2026). Digitisation, in short, has produced data that local units still analyse by hand.

*Spatial analysis that stops at description.* Spatio-temporal methods for dengue are mature. Comparative studies in Thailand show that polygon-based statistics such as Getis-Ord and Local Moran misdetect at area boundaries, while rigid scan windows overstate cluster size (Rotejanaprasert et al., 2024a, 2024b). Philippine studies confirm persistent dengue intensity in the National Capital Region (Olana et al., 2025b) and unstable barangay-level hotspots in Quezon City (Medina et al., 2023). Their authors call for barangay-level, area-based surveillance (Olana et al., 2026). Yet these studies are retrospective and aggregate cases to administrative units. The one recent DBSCAN application to dengue works at the municipal-centroid scale (Sena et al., 2025). None of the reviewed studies implements the case-address, distance-based rule (three or more cases within 200 metres within four weeks) that city surveillance units apply manually, so clusters that straddle barangay boundaries remain invisible to existing tools.

*Alerts that do not reach responders in time.* Threshold-based early warning is well validated. Model-based dengue thresholds in Puerto Rico balanced false alarms against missed detections and triggered a real emergency declaration (Thayer et al., 2025), and EWARS achieved high sensitivity with several weeks of lead time (Cardenas et al., 2022). The weakest link, however, is notification and response. Across five countries, only 27% of public health events met the 7-1-7 timeliness target, and notification and response delays clustered at the intermediate, municipal, or district level (Bochner et al., 2023). Low-cost channels can close part of this gap. Personalised SMS achieved the highest response rate in outbreak follow-up (Franklin et al., 2025), and a city health department delivered thousands of text and email alerts using existing municipal resources (Schneider et al., 2025). Integration of alerting tools into national surveillance platforms nevertheless remains rare (Sanchez Tejeda et al., 2023).

*Decision support without a resource recommender.* Hotspot detection is repeatedly justified as an input to resource allocation (Osako et al., 2026; Rotejanaprasert et al., 2024b). Spatial decision support improved the efficiency of malaria vector-control deployment (García et al., 2022), and integrated tools have combined surveillance with workforce and supply-chain management (Rajvanshi et al., 2021). Forecasts are likewise framed as guides for allocating medicines and diagnostics (Fuller et al., 2025). However, no reviewed study translates detected dengue hotspots into explicit recommendations for medicines, personnel, and supplies for a city health unit. Given that evidence for any single vector-control method remains insufficient (Low et al., 2025; Saadatian-Elahi et al., 2025), a transparent, rule-based recommender that supports rather than replaces epidemiologist judgement is the defensible design.

*Constraints that make integration urgent.* Philippine local health units operate under restrictive hiring rules, budget caps on personnel services, and workforce migration (Pepito et al., 2025). Devolution fragments coordination and delays information sharing and resource allocation (de Claro et al., 2024), and subnational health budgets depend on delayed central transfers (Ravishankar et al., 2024). Surveillance staff report work overload and pressure to learn new technologies (Maravilla et al., 2023). When staff are diverted, automated data submission is what keeps surveillance running (Boehme et al., 2022). Meanwhile, ransomware increasingly disrupts health information systems (Neprash et al., 2022), and case-location mapping raises privacy obligations (Nageshwaran et al., 2021). These conditions make role-based access, audit logging, encryption, and secure backups mandatory under the Data Privacy Act of 2012, not optional. Evaluations of health information systems increasingly use ISO/IEC 25010 (Al Ani et al., 2022; Mamani-Pari et al., 2026), yet security remains the least-evaluated quality characteristic.

*The gap.* Taken together, the literature shows credible evidence for digitised reporting, spatio-temporal cluster detection, statistical threshold alerting, forecasting with existing models such as Prophet (Fuad et al., 2026; Chen & Moraga, 2025), and decision support, each in isolation. What is absent is an integrated, city-level system that connects threshold detection (WHO mean plus two standard deviations and the CESU five-year average), case-address spatio-temporal hotspot detection, short-term forecasting, hotspot-based resource-allocation recommendation, and SMS and email notification within one CESU workflow, hosted on LGU infrastructure and governed by the Data Privacy Act. The present study addresses this gap for the City Epidemiology and Surveillance Unit of Parañaque City and evaluates the resulting system with its intended users against ISO/IEC 25010.

---

## 4. Theme × source matrix (new sources, thesis-ready)

✓ = the source's abstract directly supports the theme. Primary theme listed first in the "Primary" column.

| # | Source | Primary | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Kaburi et al. (2023) | T1 | ✓ | | | | | | ✓ | |
| 2 | Joseph et al. (2022) | T1 | ✓ | | ✓ | | | | | |
| 3 | Zuniga et al. (2026) | T1 | ✓ | | | | | ✓ | ✓ | |
| 4 | Murai et al. (2022) | T1 | ✓ | | ✓ | | | | ✓ | |
| 5 | Sucaldito et al. (2025) | T1 | ✓ | | | | | | ✓ | ✓ |
| 6 | Ong (2026) | T1 | ✓ | | ✓ | | | | ✓ | |
| 7 | Sanchez Tejeda et al. (2023) | T1 | ✓ | | ✓ | | | | | |
| 8 | Prakash Nayak et al. (2025) | T1 | ✓ | ✓ | | ✓ | | | | |
| 9 | Cabaro et al. (2023) | T1 | ✓ | | | ✓ | | | | |
| 10 | Rotejanaprasert et al. (2024a) | T2 | | ✓ | | ✓ | | | | |
| 11 | Rotejanaprasert et al. (2024b) | T2 | | ✓ | | ✓ | | | | |
| 12 | Rotejanaprasert et al. (2024c) | T2 | | ✓ | ✓ | | | | | |
| 13 | Rattananen et al. (2025) | T2 | | ✓ | | ✓ | | | | |
| 14 | Sena et al. (2025) | T2 | | ✓ | | ✓ | | | | |
| 15 | Olana et al. (2025b) | T2 | | ✓ | | | | | | |
| 16 | Abd Naeeim & Abdul Rahman (2022) | T2 | | ✓ | | ✓ | | | | |
| 17 | Osako et al. (2026) | T2 | | ✓ | | ✓ | | | | |
| 18 | Ramadona et al. (2023) | T2 | | ✓ | | | ✓ | | | |
| 19 | Buebos-Esteve & Dagamac (2024) | T2 | | ✓ | | | ✓ | | | |
| 20 | Bochner et al. (2023) | T3 | | | ✓ | | | | ✓ | |
| 21 | Thayer et al. (2025) | T3 | | | ✓ | | | | | |
| 22 | Nansikombi et al. (2023) | T3 | ✓ | | ✓ | | | | | |
| 23 | Franklin et al. (2025) | T3 | | | ✓ | | | | | |
| 24 | Schneider et al. (2025) | T3 | ✓ | | ✓ | | | | | |
| 25 | Baharom et al. (2022) | T3 | | | ✓ | | ✓ | | | |
| 26 | Cardenas et al. (2022) | T3 | | | ✓ | | | | | |
| 27 | Manahan et al. (2024) | T3 | ✓ | | ✓ | ✓ | | | ✓ | |
| 28 | Stewart-Ibarra et al. (2022) | T3 | | | ✓ | ✓ | | | | |
| 29 | García et al. (2022) | T4 | | ✓ | | ✓ | | | | |
| 30 | Rajvanshi et al. (2021) | T4 | ✓ | | | ✓ | | | ✓ | |
| 31 | Shea et al. (2023) | T4 | | | | ✓ | ✓ | | | |
| 32 | Gouveia et al. (2025) | T4 | | ✓ | ✓ | ✓ | | | | |
| 33 | Saadatian-Elahi et al. (2025) | T4 | | | | ✓ | | | | |
| 34 | Low et al. (2025) | T4 | | | | ✓ | | | | |
| 35 | Fuller et al. (2025) | T5 | | | | ✓ | ✓ | | | |
| 36 | Chen et al. (2024) | T5 | | | | | ✓ | | | |
| 37 | Xu et al. (2024) | T5 | | | ✓ | | ✓ | | | |
| 38 | Luo et al. (2022) | T5 | | | | | ✓ | | | |
| 39 | Fuad et al. (2026) | T5 | | | ✓ | | ✓ | | | |
| 40 | Singh et al. (2025) | T5 | | | | | ✓ | | | |
| 41 | He et al. (2021) | T6 | | | | | | ✓ | | |
| 42 | Neprash et al. (2022) | T6 | | | | | | ✓ | | |
| 43 | Wasserman & Wasserman (2022) | T6 | | | | | | ✓ | | |
| 44 | Nageshwaran et al. (2021) | T6 | ✓ | | | | | ✓ | | |
| 45 | Lee et al. (2021) | T6 | | | | | | ✓ | | |
| 46 | Hussein et al. (2023) | T6 | | | | | | ✓ | | |
| 47 | Kannampallil & Adler-Milstein (2022) | T6 | | | | | | ✓ | | |
| 48 | Kang & Kim (2022) | T6 | | | | | | ✓ | | |
| 49 | de Carvalho Junior & Bandiera-Paiva (2020) | T6 | | | | | | ✓ | | |
| 50 | Argyridou et al. (2023) | T6 | | | | | | ✓ | | |
| 51 | Murdoch (2021) | T6 | | | | | | ✓ | | |
| 52 | Pepito et al. (2025) | T7 | | | | | | | ✓ | |
| 53 | Escano-Arias et al. (2025) | T7 | ✓ | | | | | | ✓ | |
| 54 | de Claro et al. (2024) | T7 | | | | | | | ✓ | |
| 55 | Maravilla et al. (2023) | T7 | | | | | | | ✓ | |
| 56 | Ravishankar et al. (2024) | T7 | | | | | | | ✓ | |
| 57 | Yu et al. (2023) | T7 | | | | | | | ✓ | |
| 58 | Liwanag et al. (2022) | T7 | | | | | | | ✓ | |
| 59 | Boehme et al. (2022) | T7 | ✓ | | | | | | ✓ | |
| 60 | Garcia, De La Vega, & Mercado (2022) | T7 | ✓ | | | | | | ✓ | |
| 61 | Al Ani et al. (2022) | T8 | | | | | | ✓ | | ✓ |
| 62 | Mamani-Pari et al. (2026) | T8 | | | | | | | | ✓ |
| 63 | Barletta et al. (2023) | T8 | | | | | | | | ✓ |
| 64 | Greulich et al. (2021) | T8 | | | | | | ✓ | | ✓ |
| 65 | De Mesa et al. (2024) | T8 | ✓ | | | | | | | ✓ |
| 66 | Ndlovu et al. (2022) | T8 | ✓ | | | | | | | ✓ |
| 67 | Hailemariam et al. (2024) | T8 | | | | | | | | ✓ |
| 68 | Herbuela et al. (2021) | T8 | ✓ | | ✓ | | | | | ✓ |
| 69 | Almasi et al. (2023) | T8 | | | | | | | | ✓ |
| | **Total ✓ per theme** | | **20** | **13** | **18** | **17** | **10** | **14** | **17** | **10** |
| | **Primary per theme** | | 9 | 10 | 9 | 6 | 6 | 11 | 9 | 9 |

**Same-surname disambiguation for in-text citations:**
- Olana et al. (2025a) is the TBED forecasting paper (matrix #1). Olana et al. (2025b) is the Parasites & Vectors high-risk-areas paper.
- Garcia, A. P. (2022, T7) and García, G. A. (2022, T4) are different first authors. APA 7 §8.20 requires initials in text: "A. P. Garcia et al. (2022)" and "G. A. García et al. (2022)".
- Chen, Q. et al. (2024) and Chen and Moraga (2025) are distinct works.
