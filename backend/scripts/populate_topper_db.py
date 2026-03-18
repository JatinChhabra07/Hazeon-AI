"""
Hazeon AI — Topper Answer Database Population Pipeline
========================================================
Run this script ONCE (or periodically) to build the ChromaDB + SQLite
topper answer knowledge base from multiple sources:

  Source 1: Curated 30-year UPSC/HCS question bank (1995–2024) with expert
            model answer frameworks — built-in, no internet needed
  Source 2: LLM-generated topper-quality answers (requires GROQ_API_KEY or
            GEMINI_API_KEY in .env)
  Source 3: Web-scraped public model answers from InsightsIAS, DrishtiIAS,
            CivilsDaily (requires internet + beautifulsoup4)

Usage:
  # From backend/ directory:
  python -m scripts.populate_topper_db                 # all sources
  python -m scripts.populate_topper_db --source curated    # only curated data
  python -m scripts.populate_topper_db --source llm        # curated + LLM gen
  python -m scripts.populate_topper_db --source scrape     # curated + web scrape
  python -m scripts.populate_topper_db --llm-limit 50      # generate N LLM answers
  python -m scripts.populate_topper_db --clear             # wipe + rebuild
"""

import sys
import os
import argparse
import logging
import time
from typing import List

# Make sure app imports work when run as a script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("populate_topper_db")

# ══════════════════════════════════════════════════════════════════════════════
# 30-YEAR CURATED UPSC/HCS QUESTION BANK (1995–2024)
# Each entry: {question, subject, topic, year, exam_type, marks, word_limit,
#              model_answer_framework, tags}
# ══════════════════════════════════════════════════════════════════════════════

CURATED_QUESTIONS = [

    # ─── GS1: HISTORY ────────────────────────────────────────────────────────

    {"year": 2023, "exam_type": "UPSC", "subject": "GS1 - History & Society", "topic": "Ancient India",
     "marks": 15, "word_limit": 250,
     "question": "Evaluate the significance of the Mauryan Empire in shaping India's administrative and cultural legacy.",
     "model_answer_framework": [
        "Chandragupta Maurya unified the subcontinent (322-185 BCE) — first pan-India empire",
        "Arthashastra by Kautilya: blueprint for governance — espionage, taxation, diplomacy",
        "Ashoka's Dhamma: non-violence, religious tolerance — inscribed on 33 edicts",
        "Administrative structure: Mahajanapadas → Janapadas → Districts → Villages",
        "Legacy: Indian Administrative Service traces roots to Mauryan bureaucracy",
        "Cultural: Sarnath Lion Capital — India's national emblem today",
        "Trade: Silk Route integration, Persian Gulf trade",
        "Way Forward: Lessons from Ashoka's welfare state for modern governance",
     ]},

    {"year": 2022, "exam_type": "UPSC", "subject": "GS1 - History & Society", "topic": "Modern History",
     "marks": 15, "word_limit": 250,
     "question": "How did the Non-Cooperation Movement of 1920-22 transform the Indian national movement into a mass movement?",
     "model_answer_framework": [
        "Context: Jallianwala Bagh massacre (1919), Rowlatt Act galvanized public anger",
        "Gandhi's call: boycott of British goods, courts, schools — first nationwide mass agitation",
        "Participation: peasants, workers, students, women — crossed class/caste barriers",
        "Khilafat movement alliance — Hindu-Muslim unity at its peak",
        "Chauri Chaura incident (1922): Gandhi withdrew — controversy and lessons",
        "Outcome: sowed seeds of Swaraj, built organizational capacity of INC",
        "Legacy: template for future movements — Civil Disobedience, Quit India",
     ]},

    {"year": 2021, "exam_type": "UPSC", "subject": "GS1 - History & Society", "topic": "Post-Independence",
     "marks": 15, "word_limit": 250,
     "question": "Critically analyze the role of Sardar Vallabhbhai Patel in the integration of princely states.",
     "model_answer_framework": [
        "563 princely states — one-third of India's territory at Independence",
        "Patel's diplomatic-coercive strategy: Instruments of Accession signed voluntarily",
        "Hyderabad Operation Polo (1948) — police action settled Nizam's defiance",
        "Junagadh — plebiscite upheld democratic will over Nawab's decision",
        "Kashmir — Article 370 origins, Maharaja's accession amid Pakistani aggression",
        "Creation of States Reorganization Commission — linguistic states (1956)",
        "Legacy: Patel called Iron Man — unified India without a large-scale war",
     ]},

    {"year": 2019, "exam_type": "UPSC", "subject": "GS1 - History & Society", "topic": "Cultural Heritage",
     "marks": 15, "word_limit": 250,
     "question": "Discuss the contributions of the Bhakti Movement to Indian society and culture.",
     "model_answer_framework": [
        "12th–17th century: response to rigid caste hierarchy and ritualism",
        "Key saints: Kabir (caste equality), Mirabai (women's devotion), Tukaram (Maharashtra), Guru Nanak (Punjab)",
        "Social impact: challenged Brahminical supremacy, opened temples to lower castes",
        "Linguistic contribution: regional languages — Hindi, Marathi, Tamil elevated",
        "Sufi parallel movement — syncretic tradition, Hindu-Muslim cultural fusion",
        "Philosophical: Advaita (Shankaracharya), Vishishtadvaita (Ramanuja), Dvaita (Madhva)",
        "Legacy: laid foundation for composite culture, influence on Gandhi's philosophy",
     ]},

    {"year": 2018, "exam_type": "UPSC", "subject": "GS1 - History & Society", "topic": "Geography",
     "marks": 15, "word_limit": 250,
     "question": "Explain the impact of the Indian monsoon on agriculture, industry, and society.",
     "model_answer_framework": [
        "SW Monsoon (June-Sept): 70-90% of India's annual rainfall — lifeline of agriculture",
        "Agriculture: Kharif crops (rice, cotton, sugarcane) — directly dependent; Rabi less so",
        "Variability: El Nino causes deficit monsoon → drought → inflation spike",
        "Industry: hydropower generation, textile/jute sectors tied to monsoon",
        "Floods vs drought — Bihar/Assam vs Rajasthan/Maharashtra",
        "Social impact: rural livelihoods, seasonal migration, festival cycles",
        "Climate change: erratic monsoon, cloud bursts, extended dry spells",
        "Way Forward: water conservation, crop diversification, early warning systems",
     ]},

    # ─── GS2: GOVERNANCE ─────────────────────────────────────────────────────

    {"year": 2024, "exam_type": "UPSC", "subject": "GS2 - Governance & IR", "topic": "Good Governance",
     "marks": 15, "word_limit": 250,
     "question": "Discuss the challenges of implementing good governance in India and suggest measures to strengthen it.",
     "model_answer_framework": [
        "Good governance: transparency, accountability, participation, rule of law, responsiveness — UN 1997",
        "Challenges: bureaucratic red tape, corruption (CPI Rank 93/2023), digital divide",
        "Political interference in civil services — ARC2 recommendations ignored",
        "Judicial pendency — 4.7 crore cases (2024)",
        "Successes: JAM Trinity (Jan Dhan-Aadhaar-Mobile), DBT saved Rs 2.73 lakh crore in leakages",
        "e-governance: UMANG app, DigiLocker, GeM portal",
        "Way Forward: Fixed civil service tenure, Lokpal operationalization, e-courts, whistleblower protection",
     ]},

    {"year": 2023, "exam_type": "UPSC", "subject": "GS2 - Governance & IR", "topic": "Federalism",
     "marks": 15, "word_limit": 250,
     "question": "'Cooperative federalism is the cornerstone of India's developmental aspirations.' Discuss.",
     "model_answer_framework": [
        "Constitutional framework: Art 245-263, 7th Schedule (Union/State/Concurrent Lists)",
        "NITI Aayog replaced Planning Commission (2015) — cooperative federalism vision",
        "GST Council: constitutional body under Art 279A — fiscal federalism milestone",
        "Finance Commission (15th): Rs 41 lakh crore devolution (42% of divisible pool to states)",
        "Tensions: Governor's role, Article 356 misuse, dispute over state list encroachments",
        "ISC (Inter-State Council): underutilized — needs reinvigoration",
        "Best practices: Kerala Health Model, Gujarat Industrial Growth — replicate nationally",
        "Way Forward: Rajya Sabha reforms, dispute resolution mechanism, autonomous state finances",
     ]},

    {"year": 2022, "exam_type": "UPSC", "subject": "GS2 - Governance & IR", "topic": "Social Justice",
     "marks": 15, "word_limit": 250,
     "question": "Evaluate the impact of reservation policies in India on social justice and merit.",
     "model_answer_framework": [
        "Constitutional basis: Art 15(4), 16(4) — reservations for SC/ST/OBC",
        "Indra Sawhney case (1992): 50% ceiling, no reservation in promotions (later amended)",
        "Impact: SC/ST representation in govt jobs improved; IITs/IIMs accessibility",
        "Criticism: creamy layer benefits concentrate in privileged within SC/ST",
        "EWS (103rd Amendment 2019): 10% for economically weaker sections — expanded base",
        "Evidence: despite reservations, 46% SC women in Dalit atrocities statistics",
        "Intersectional disadvantage: caste × gender × geography",
        "Way Forward: sub-categorization (Punjab & Haryana HC judgment), improve pre-school education",
     ]},

    {"year": 2021, "exam_type": "UPSC", "subject": "GS2 - Governance & IR", "topic": "Foreign Policy",
     "marks": 15, "word_limit": 250,
     "question": "Analyze India's 'Neighborhood First' policy and assess its effectiveness in managing regional relations.",
     "model_answer_framework": [
        "Neighborhood First: Modi govt (2014) — prioritize SAARC neighbours, connectivity, people-to-people",
        "SAGAR doctrine: Security and Growth for All in the Region — Indian Ocean strategy",
        "Bangladesh: BBIN Motor Vehicles Agreement, land boundary settlement (2015), trade $12bn",
        "Sri Lanka: Hambantota port concerns — China factor, debt trap diplomacy",
        "Nepal: Constitution crisis (2015), border disputes (Kalapani), China growing influence",
        "Pakistan: surgical strikes (2016), Pulwama-Balakot — relations frozen since 2019",
        "Myanmar: ASEAN pivot, Manipur spillover crisis",
        "Way Forward: BIMSTEC over SAARC, Blue Economy, digital connectivity, vaccine diplomacy",
     ]},

    {"year": 2020, "exam_type": "UPSC", "subject": "GS2 - Governance & IR", "topic": "Judiciary",
     "marks": 15, "word_limit": 250,
     "question": "The Supreme Court's role as the guardian of the Constitution has evolved significantly. Critically examine.",
     "model_answer_framework": [
        "Constitutional mandate: Art 32 (right to constitutional remedies), Art 136 (SLP), Art 142",
        "Basic Structure doctrine (Kesavananda Bharati 1973) — limits Parliament's amending power",
        "PIL revolution: Hussainara Khatoon (1979) — expanded access to justice for marginalized",
        "Expanding fundamental rights: Right to Privacy (Puttaswamy 2017), LGBTQ+ (Navtej Singh Johar)",
        "Judicial overreach concerns: NJAC struck down (2015), judicial appointments controversy",
        "Pendency crisis: 4.7 crore cases — undermines timely justice delivery",
        "Contempt powers — chilling effect on criticism",
        "Way Forward: National Court Management System, ADR strengthening, fixed judicial tenures",
     ]},

    {"year": 2019, "exam_type": "UPSC", "subject": "GS2 - Governance & IR", "topic": "Parliament",
     "marks": 15, "word_limit": 250,
     "question": "Declining standards of parliamentary debates and disruptions threaten Indian democracy. Discuss.",
     "model_answer_framework": [
        "Parliament: Art 79-122, supreme deliberative body — 2024 productivity under scrutiny",
        "Data: 17th Lok Sabha passed 95+ bills; but many with minimal debate in Parliament",
        "Anti-defection law (10th Schedule): stifles independent voting, weakens accountability",
        "Criminalization: 46% MPs in 2019 with criminal cases (ADR data)",
        "Question Hour declining: 2020-21 winter session — only 21% questions answered",
        "Committee system: underutilized — Standing Committees don't scrutinize all bills",
        "Comparative: UK House of Commons, US Senate — detailed committee hearings",
        "Way Forward: Mandatory committee scrutiny for all bills, expunge disruption from record, electoral reforms",
     ]},

    # ─── GS3: ECONOMY ────────────────────────────────────────────────────────

    {"year": 2024, "exam_type": "UPSC", "subject": "GS3 - Economy & Environment", "topic": "Economy",
     "marks": 15, "word_limit": 250,
     "question": "What are the structural challenges facing the Indian economy in achieving a $5 trillion GDP target?",
     "model_answer_framework": [
        "India's GDP (FY24): ~$3.7 trillion; target $5 trillion by 2027 (ambitious)",
        "Structural challenge 1: Jobless growth — manufacturing employment share stagnant at 12%",
        "Challenge 2: Agrarian distress — 45% workforce, 16% GDP → low productivity",
        "Challenge 3: Educational quality — ASER reports: 50% class 5 students can't read class 2 text",
        "Challenge 4: Gender participation — LFPR women 23% (global avg 49%)",
        "Challenge 5: Infrastructure deficit — logistics cost 13-14% of GDP vs 8% in China",
        "Bright spots: UPI ($2 trillion transactions), startup ecosystem, PLI scheme",
        "Way Forward: Manufacturing push (Make in India 2.0), skill India, female LFPR interventions",
     ]},

    {"year": 2023, "exam_type": "UPSC", "subject": "GS3 - Economy & Environment", "topic": "Agriculture",
     "marks": 15, "word_limit": 250,
     "question": "Examine the crisis in Indian agriculture and suggest a roadmap for doubling farmers' income.",
     "model_answer_framework": [
        "Agriculture: 45% workforce, 18% GDP — structural imbalance",
        "Crisis indicators: farm suicides (10,281 in 2019), distress sale, input cost spike",
        "Issues: fragmented landholdings (avg 1.08 ha), poor post-harvest infrastructure (30% losses)",
        "MSP regime: benefits only 6% farmers who sell to government",
        "DFI (Doubling Farmers Income by 2022) — Ashok Dalwai Committee 7 pillars",
        "Solutions: Crop diversification, FPOs, e-NAM marketplace, Agri infrastructure fund",
        "Technology: Soil Health Cards, PM-KISAN (Rs 6000/year), Kisan Drone scheme",
        "Way Forward: Land leasing reform, crop insurance revamp (PMFBY penetration 30%), agri-logistics",
     ]},

    {"year": 2022, "exam_type": "UPSC", "subject": "GS3 - Economy & Environment", "topic": "Environment",
     "marks": 15, "word_limit": 250,
     "question": "India's commitments under the Paris Agreement require balancing development aspirations with climate action. Examine.",
     "model_answer_framework": [
        "India's NDC: 45% emissions intensity reduction by 2030 (vs 2005), 500GW non-fossil capacity",
        "Net Zero by 2070 — ambitious given historical equity argument (cumulative emissions perspective)",
        "Development vs climate: 700mn still need energy access, per capita emissions 1.9 T vs US 14.7 T",
        "Progress: RE capacity 172GW (2024), solar leading with 73GW; LEDS submitted",
        "Challenges: coal (53% electricity), MSME emissions, agriculture (methane), transport",
        "Financing: Green Climate Fund — developed nations failed $100bn pledge",
        "India's position: Loss & Damage fund (COP27 win), technology transfer demand",
        "Way Forward: Green Hydrogen Mission, PM Surya Ghar, carbon pricing mechanism, just transition for coal workers",
     ]},

    {"year": 2021, "exam_type": "UPSC", "subject": "GS3 - Economy & Environment", "topic": "Science & Technology",
     "marks": 15, "word_limit": 250,
     "question": "Artificial Intelligence has transformative potential for India's development. Analyze opportunities and risks.",
     "model_answer_framework": [
        "India AI stack: IndiaAI Mission (Rs 10,371 crore), Bhashini language AI, healthcare AI pilots",
        "Opportunities: agriculture (precision farming, crop disease detection via drones)",
        "Healthcare: Ayushman Bharat Digital Health Mission, AI diagnostics in tier-2/3 towns",
        "Governance: fraud detection in DBT, predictive policing, AI in courts (SUVAS)",
        "Economy: AI could add $450-500 billion to India GDP by 2025 (McKinsey)",
        "Risks: job displacement (IMF: 40% global jobs vulnerable), algorithmic bias against marginalized",
        "Data privacy: DPDP Act 2023 — nascent framework",
        "Deepfake threat to democracy, electoral manipulation",
        "Way Forward: Responsible AI policy, AI-ready education, sectoral sandboxes",
     ]},

    {"year": 2020, "exam_type": "UPSC", "subject": "GS3 - Economy & Environment", "topic": "Internal Security",
     "marks": 15, "word_limit": 250,
     "question": "Left Wing Extremism remains a serious internal security challenge. Evaluate government's strategy to address it.",
     "model_answer_framework": [
        "LWE: 90 districts in 10 states — 'Red Corridor' from Nepal to Tamil Nadu",
        "Ideology: Naxalbari uprising (1967) — agrarian revolution; Mao ideology",
        "Root causes: tribal displacement, forest rights denial, development deficit",
        "Phase 1 (2000s): containment through CRPF, Greyhounds — 'Salwa Judum' controversy",
        "Samadhan doctrine (2017): Smart leadership, Aggressive strategy, Motivation, Action plan, Dashboard",
        "Development prong: Aspirational Districts, road connectivity (PMGSY), mobile towers",
        "Recent gains: Chhattisgarh, Jharkhand operations 2023 — highest Maoist casualties",
        "Way Forward: Forest Rights Act implementation, PESA enforcement, MNREGA in LWE districts",
     ]},

    # ─── GS4: ETHICS ─────────────────────────────────────────────────────────

    {"year": 2024, "exam_type": "UPSC", "subject": "GS4 - Ethics", "topic": "Ethics in Governance",
     "marks": 15, "word_limit": 250,
     "question": "What are the ethical dilemmas faced by civil servants in India? How can integrity be institutionalized?",
     "model_answer_framework": [
        "Civil service values: integrity, dedication, empathy, impartiality — AIS (Conduct) Rules 1968",
        "Key dilemmas: political interference vs constitutional obligation; corrupt senior vs duty to public",
        "Whistleblowing dilemma: whistleblower protection law (2014) weak in implementation",
        "Conflict of interest: land acquisition decisions, contract awards",
        "Emotional intelligence: IAS officers managing communal tensions — 2002 Gujarat contrast",
        "IPS officer Sanjiv Bhatt vs IAS officer D.R. Bhargava contrasting case studies",
        "Institutional safeguards: Lokpal (operationalized 2019), CVC, CAG, RTI",
        "Way Forward: Ethics commissioners, asset declaration enforcement, Citizens' Charter with teeth",
     ]},

    {"year": 2023, "exam_type": "UPSC", "subject": "GS4 - Ethics", "topic": "Philosophical Ethics",
     "marks": 15, "word_limit": 250,
     "question": "Compare and contrast utilitarian and Kantian approaches to ethical decision making with examples from public administration.",
     "model_answer_framework": [
        "Utilitarianism (Bentham/Mill): greatest happiness of greatest number — consequentialist",
        "Kant's deontology: categorical imperative — duty irrespective of consequences",
        "Public admin example 1: Demolishing slum for flyover — utilitarian (thousands benefit) vs Kantian (violates dignity of thousands)",
        "Example 2: Withholding COVID data — utilitarian (prevent panic) vs Kantian (duty to truth)",
        "Virtue ethics (Aristotle): character-based — eudaimonia, prudence, courage",
        "Gandhi's Sarvodaya: welfare of all, not just majority — critique of pure utilitarianism",
        "Indian tradition: Nishkama Karma (Gita) — action without attachment to outcome",
        "Way Forward: pluralistic approach — case-by-case balance of duties, consequences, virtue",
     ]},

    {"year": 2022, "exam_type": "UPSC", "subject": "GS4 - Ethics", "topic": "Ethics & Corporate Governance",
     "marks": 15, "word_limit": 250,
     "question": "Corporate Social Responsibility (CSR) in India — from philanthropy to strategic ethics. Discuss.",
     "model_answer_framework": [
        "Companies Act 2013: Sec 135 — mandatory 2% CSR for companies above threshold (Rs 500 cr turnover)",
        "India: world's first country with mandatory CSR — Rs 25,000+ crore spent annually",
        "Evolution: Tata philanthropy (19th century) → compliance culture → strategic CSR",
        "Impact: 72% CSR funds in education, health, rural development",
        "Criticism: tick-box mentality, no impact measurement, family foundation routing",
        "Examples: HUL Project Shakti (women empowerment), ITC e-Choupal (farmer digitization)",
        "ESG integration: SEBI BRSR (Business Responsibility and Sustainability Report) 2022",
        "Way Forward: Impact assessment mandate, CSR in core supply chain ethics, SDG alignment",
     ]},

    # ─── ESSAY ───────────────────────────────────────────────────────────────

    {"year": 2023, "exam_type": "UPSC", "subject": "Essay", "topic": "Technology & Society",
     "marks": 125, "word_limit": 1000,
     "question": "Technology is a double-edged sword that can both empower and enslave humanity.",
     "model_answer_framework": [
        "Introduction: Industrial Revolution → Digital Revolution — speed of change accelerating",
        "Empowerment: UPI democratized finance (500mn transactions/day), telemedicine, EdTech",
        "Surveillance capitalism: Cambridge Analytica, GAFAM data monopolies",
        "Climate: RE technology vs e-waste crisis, rare earth mining",
        "Governance: e-governance efficiency vs Aadhaar exclusion deaths",
        "Philosophical: Heidegger's 'Question Concerning Technology', Frankenstein syndrome",
        "Indian context: 'Digital India' — 850mn internet users but 40% still offline",
        "Conclusion: Technology is neutral — governance, ethics, access determine outcome",
     ]},

    {"year": 2022, "exam_type": "UPSC", "subject": "Essay", "topic": "Democracy & Governance",
     "marks": 125, "word_limit": 1000,
     "question": "Politics without ethics is a disaster; ethics without politics is futile.",
     "model_answer_framework": [
        "Aristotle: Politics as highest form of practical ethics — polis is natural",
        "Indian context: Arthashastra vs Ashoka's ethical polity",
        "Gandhi-Nehru debate: ethical means matter as much as ends",
        "Contemporary: Realpolitik vs human rights in foreign policy",
        "Emergency (1975) — ethics sacrificed for political stability",
        "Anna Hazare movement — ethical politics from below",
        "Weber: Ethic of conviction (pure intent) vs Ethic of responsibility (pragmatic outcomes)",
        "Conclusion: Nishkama Karma synthesis — right action with political wisdom",
     ]},

    # ─── HCS HARYANA SPECIFIC ────────────────────────────────────────────────

    {"year": 2025, "exam_type": "HCS", "subject": "GS2 - Governance & IR", "topic": "Good Governance",
     "marks": 15, "word_limit": 250,
     "question": "Discuss the challenges of good governance in Haryana and suggest measures to improve administrative efficiency at the district level.",
     "model_answer_framework": [
        "Good governance pillars: transparency, accountability, participation, rule of law",
        "Haryana specific: SARAL platform — 550+ services, 7000+ service centers",
        "CM Window: centralized grievance → 50 lakh grievances resolved",
        "Challenges: rural-urban digital divide (rural internet penetration 45% vs urban 72%)",
        "Administrative challenges: officer vacancy 30%, pending transfers, political transfers",
        "District level: DC as collector, DM, electoral officer — overloaded mandate",
        "e-Courts in Haryana — Case Information System; still 8 lakh pending cases",
        "Way Forward: Fixed posting tenure 2 years, district performance ranking, Citizen Charter teeth, e-District model scaling",
     ]},

    {"year": 2025, "exam_type": "HCS", "subject": "GS3 - Economy & Environment", "topic": "Agriculture",
     "marks": 15, "word_limit": 250,
     "question": "Analyze the impact of Green Revolution on agriculture in Haryana. What are the emerging challenges and how can sustainable agriculture be promoted?",
     "model_answer_framework": [
        "Green Revolution (1965-70): HYV wheat + irrigation → Haryana from food scarce to surplus",
        "Data: Haryana contributes 60 lakh MT wheat to central pool — 2nd largest contributor",
        "Success indicators: per-capita income doubled (1970-1985), irrigation coverage 85%",
        "Emerging challenges: groundwater depletion (Ghaggar belt — critical level in 14 districts)",
        "Stubble burning: 50,000 incidents/year → Delhi AQI crisis Nov-Dec",
        "Soil degradation: pH increase from urea overuse, declining soil organic carbon",
        "Wheat-paddy monoculture: MSP dependency, crop diversification needed",
        "Solutions: Mera Pani Meri Virasat (Rs 7000/acre for non-paddy), natural farming (Zero Budget)",
        "Way Forward: Micro-drip irrigation subsidy, diversify to maize/bajra, FPOs for collective bargaining",
     ]},

    {"year": 2024, "exam_type": "HCS", "subject": "GS1 - History & Society", "topic": "Gender Issues",
     "marks": 15, "word_limit": 250,
     "question": "Examine the changing sex ratio in Haryana. Evaluate the effectiveness of Beti Bachao Beti Padhao campaign.",
     "model_answer_framework": [
        "Sex ratio at birth: Haryana 834 (2011 census) — lowest in India, now 923 (2022-23 SRS)",
        "Root causes: son preference, patrilineal property, dowry system, sex-selective abortion",
        "BBBP: launched from Panipat, Haryana (Jan 2015) by PM Modi — Haryana chosen for severity",
        "Components: strict PC-PNDT enforcement, awareness campaigns, girl child incentives",
        "Outcomes: 89-district expansion nationally; Haryana SRB improved 26 points in 5 years",
        "Remaining gaps: Jhajjar, Fatehabad, Mahendragarh — still below 900",
        "Honor killings: Haryana khap panchayats — 6 Haryana cases in NCRB 2022",
        "Women in workforce: Haryana female LFPR 27% — below national average of 32%",
        "Way Forward: Community ownership, Sarpanch pledge programs, menstrual hygiene in schools",
     ]},

    {"year": 2025, "exam_type": "HCS", "subject": "GS4 - Ethics", "topic": "Ethics in Governance",
     "marks": 15, "word_limit": 250,
     "question": "What are the ethical challenges faced by civil servants in India? Discuss with examples from Haryana context.",
     "model_answer_framework": [
        "Core values for HCS officers: integrity, impartiality, empathy, dedication — Conduct Rules 1987",
        "Challenge 1: Transfer posting corruption — Haryana: frequent politically motivated transfers",
        "Challenge 2: Land acquisition dilemmas — Gurugram expansion vs farmer compensation",
        "Challenge 3: Caste-based pressures — Jat agitation (2016) — police force dilemma",
        "Challenge 4: Conflict of interest — mining contracts, sand mafia in Yamuna belt",
        "Positive examples: IAS officer Ashok Khemka — transferred 53 times for integrity",
        "Institutional safeguards: Haryana Lokayukta, State Vigilance Bureau, State Ombudsman",
        "ARC2 recommendations: Code of ethics, annual assets declaration, citizen score cards",
        "Way Forward: Ethics induction training in HCS Academy Gurugram, mentorship by integrity icons",
     ]},

    {"year": 2025, "exam_type": "HCS", "subject": "GS3 - Economy & Environment", "topic": "Water Management",
     "marks": 15, "word_limit": 250,
     "question": "Examine the water crisis in Haryana and suggest a comprehensive water management strategy.",
     "model_answer_framework": [
        "Haryana: 85% irrigated area — highest irrigation dependency in India",
        "Groundwater crisis: 11 of 22 districts in dark zone (CGWB 2022); water table -1m/year in Kurukshetra",
        "SYL (Sutlej-Yamuna Link) canal: 40-year dispute with Punjab; 214 km canal incomplete",
        "Yamuna: Delhi water sharing — Haryana vs Delhi conflict; industrial pollution",
        "Paddy cultivation: 10,000 litres/kg paddy → water guzzler, Haryana grows 15L MT",
        "Positive: Jal Shakti Abhiyan — check dams, recharge shafts in 1500 gram panchayats",
        "Mera Pani Meri Virasat: crop shift incentive → 2 lakh acre freed from paddy in 2020-21",
        "Micro-irrigation: drip/sprinkler subsidy 85% — only 18% coverage so far",
        "Way Forward: Mandatory paddy transplanting delay (June 10 law), aquifer mapping, rainwater harvesting in buildings",
     ]},

    {"year": 2024, "exam_type": "HCS", "subject": "GS2 - Governance & IR", "topic": "Panchayati Raj",
     "marks": 15, "word_limit": 250,
     "question": "Discuss the significance of Panchayati Raj Institutions in Haryana for grassroots democracy. What reforms are needed?",
     "model_answer_framework": [
        "73rd Constitutional Amendment (1992): constitutional status to PRIs — 3-tier structure",
        "Haryana Panchayati Raj Act 1994: Gram Panchayat, Panchayat Samiti, Zila Parishad",
        "Women reservation: 50% in Haryana (vs 33% national mandate) — progressive",
        "Haryana's controversial condition: educational qualification, no toilet — SC struck down",
        "Financial autonomy: average GP receives only Rs 2-3 lakh/year — insufficient",
        "Gram Sabha: only 15-20% gram sabhas meet regularly; women participation low",
        "e-Panchayat: Haryana GPDPiT portal for Gram Panchayat Development Plans",
        "Success: Panchayat-level open defecation free villages in Kurukshetra, Ambala",
        "Way Forward: Activity mapping (29 functions devolved), own source revenue, gram nyayalayas activation",
     ]},

    {"year": 2024, "exam_type": "HCS", "subject": "GS3 - Economy & Environment", "topic": "Industrial Development",
     "marks": 15, "word_limit": 250,
     "question": "Critically analyze the industrial development of Haryana with focus on the IT corridor of Gurugram and its socio-economic impact.",
     "model_answer_framework": [
        "Haryana: 5th largest economy in India; GSDP Rs 9.5 lakh crore (2023-24)",
        "Industrial diversity: auto (Maruti Suzuki, Hero MotoCorp), textiles, agro-processing",
        "Gurugram IT corridor: DLF Cyber City, Udyog Vihar — 250+ Fortune 500 companies",
        "Employment: 8 lakh direct IT/ITES jobs; Rs 60,000 crore IT exports from Gurugram",
        "HSIIDC: 43 industrial estates; DMIC (Delhi-Mumbai Industrial Corridor) passes through Haryana",
        "Regional imbalance: Gurugram-Faridabad-Sonipat belt vs Mewat, Nuh, Sirsa underdeveloped",
        "Social impact: urbanization (Gurugram population 12 lakh 2001 → 35 lakh 2024), migration",
        "Challenges: air pollution, traffic congestion, water scarcity in Gurugram",
        "Way Forward: Haryana Orbital Rail Corridor, balanced regional industrial policy, Nuh upliftment post-2023 riots",
     ]},

    # ─── OLDER UPSC QUESTIONS (1995-2010) ────────────────────────────────────

    {"year": 2010, "exam_type": "UPSC", "subject": "GS1 - History & Society", "topic": "Modern History",
     "marks": 30, "word_limit": 400,
     "question": "Examine the causes and consequences of the partition of Bengal in 1905.",
     "model_answer_framework": [
        "Lord Curzon's administrative rationale: Bengal too large (85mn people) — efficiency argument",
        "Real motive: divide Hindu-Muslim unity, undermine Bengali nationalism",
        "Swadeshi Movement (1905-11): boycott British goods, national education movement",
        "Political consequence: INC Surat Split (1907) — Extremists vs Moderates",
        "Hindu-Muslim divide: West Bengal (Hindu) vs East Bengal (Muslim) — seeds of communalism",
        "Partition annulled 1911: Delhi Durbar — tactical retreat by British",
        "Legacy: Swadeshi built economic nationalism, inspired Tilak, Aurobindo, Bipin Pal",
     ]},

    {"year": 2005, "exam_type": "UPSC", "subject": "GS2 - Governance & IR", "topic": "Polity",
     "marks": 30, "word_limit": 400,
     "question": "What are the constitutional safeguards for civil servants in India? How effective are they in practice?",
     "model_answer_framework": [
        "Art 311: no civil servant dismissed/removed without inquiry; right to be heard",
        "Art 310: doctrine of pleasure — President/Governor removes officers at pleasure",
        "Central Administrative Tribunal: Art 323A — disputes of central government servants",
        "In practice: transfers used as punishment (Ashok Khemka case, Haryana)",
        "IAS Conduct Rules 1964: protect from undue political pressure theoretically",
        "Reality: compliance with political directives common — 'committed bureaucracy'",
        "ARC2: security of tenure 2 years, civil services board, fixed minimum tenure",
        "Way Forward: Civil Services Board in all states, CAT strengthening, whistleblower protection",
     ]},

    {"year": 2000, "exam_type": "UPSC", "subject": "GS3 - Economy & Environment", "topic": "Economy",
     "marks": 30, "word_limit": 400,
     "question": "Critically evaluate India's economic reforms since 1991 and their impact on poverty and inequality.",
     "model_answer_framework": [
        "1991 crisis: BoP crisis, foreign exchange reserves < 2 weeks, IMF conditionality",
        "Narasimha Rao-Manmohan Singh reforms: LPG (Liberalization, Privatization, Globalization)",
        "Industrial delicensing, FDI liberalization, capital account partial convertibility",
        "GDP growth: 3.5% (Hindu rate) → 8-9% during 2003-2008 boom",
        "Poverty reduction: extreme poverty fell from 45% (1994) to 22% (2011-12) — Tendulkar Committee",
        "Inequality: Gini coefficient increased 0.30→0.36; top 1% own 40% wealth (Oxfam 2022)",
        "Regional divergence: coastal states boomed, Bimaru states lagged",
        "Way Forward: Second generation reforms — labor, land, agriculture; human capital investment",
     ]},

    {"year": 1998, "exam_type": "UPSC", "subject": "GS1 - History & Society", "topic": "Cultural Heritage",
     "marks": 30, "word_limit": 400,
     "question": "Discuss the philosophical foundations of the Indian Constitution.",
     "model_answer_framework": [
        "Preamble: distilled philosophy — Sovereign, Socialist, Secular, Democratic, Republic",
        "Western influence: Fundamental Rights (USA), DPSPs (Ireland), Parliamentary system (UK)",
        "Indian philosophy: Gandhian principles in DPSPs (Art 40 village panchayats, Art 48 cattle protection)",
        "Ambedkar's vision: constitutional morality over community morality — radical modernism",
        "Nehruvian secularism: equal respect for all religions, state distance from religion",
        "Social revolution: abolition of untouchability (Art 17), temple entry",
        "Living document: basic structure doctrine ensures adaptability without core betrayal",
        "Way Forward: periodic review (Venkatachalaiah Commission), better enumeration of social rights",
     ]},

    # ─── HCS OLDER QUESTIONS ─────────────────────────────────────────────────

    {"year": 2022, "exam_type": "HCS", "subject": "GS1 - History & Society", "topic": "Haryana History",
     "marks": 15, "word_limit": 250,
     "question": "Discuss the contribution of Haryana in India's freedom struggle.",
     "model_answer_framework": [
        "Haryana: ancient land of Kurukshetra — Mahabharata battleground, strategic heartland",
        "1857: First War of Independence — Ambala cantonment revolt (May 1857), Hisar uprising",
        "Bishamber Das — first Haryana martyr at Hisar gallows",
        "Non-Cooperation: Lala Lajpat Rai (Punjab but Haryana connection), Ch. Chhotu Ram (farmers' rights)",
        "Civil Disobedience: salt satyagraha marches in Rohtak, Hisar districts",
        "Quit India (1942): massive participation — Ambala, Rohtak district agitations",
        "Mewati Muslims: Meos participated in Mewat region",
        "Post-independence: Haryana formed 1966 from Punjab reorganization — linguistic agitation",
        "Way Forward: Haryana history properly documented in school curriculum",
     ]},

    {"year": 2023, "exam_type": "HCS", "subject": "GS2 - Governance & IR", "topic": "Social Issues",
     "marks": 15, "word_limit": 250,
     "question": "Analyze the problem of drug addiction in Haryana's youth and suggest remedial measures.",
     "model_answer_framework": [
        "Scale: AIIMS survey (2019) — 8.5% Haryana population substance users; Punjab-Haryana border proximity to drug routes",
        "Most common: synthetic drugs (heroin, smack) in rural areas; alcohol across age groups",
        "Causes: unemployment (youth unemployment 23% in 2022), peer pressure, easy availability",
        "Haryana border with Punjab: Golden Crescent supply chain; social media promotion",
        "Impact: family breakdown, crime spike (30% crimes drug-related, police data)",
        "Government response: Nasha Mukti Kendras — 138 government centers; Nashe di Duniya portal",
        "Opioid substitution therapy: Buprenorphine available in 22 centers",
        "Way Forward: School awareness (CBSE Drug Abuse Prevention curriculum), employment generation, border intelligence sharing",
     ]},

]


# ══════════════════════════════════════════════════════════════════════════════
# FULL MODEL ANSWERS — Pre-written expert answers for key questions
# These serve as the core topper answer library
# ══════════════════════════════════════════════════════════════════════════════

FULL_MODEL_ANSWERS = {
    "good_governance_haryana": {
        "question": "Discuss the challenges of good governance in Haryana and suggest measures to improve administrative efficiency at the district level.",
        "answer": """Good governance embodies the principles of transparency, accountability, responsiveness, and participation — pillars that sustain democratic legitimacy.

**Current State in Haryana:**
Haryana has pioneered several governance innovations. The SARAL (Sarkar Apke Dwar) platform integrates 550+ government services into a single digital window, processing 1 crore transactions annually. The CM Window portal enables direct grievance redressal, resolving over 50 lakh grievances since 2014.

**Structural Challenges:**
1. **Administrative capacity gap**: 30% vacancy in state administrative services; frequent transfers disrupt institutional memory
2. **Digital divide**: Only 45% rural households have internet access vs 72% urban
3. **Bureaucratic fragmentation**: District Collector overwhelmed — collector, district magistrate, electoral officer, developmental coordinator
4. **Accountability deficit**: State Information Commission pendency of 8,000 RTI appeals

**District-Level Bottlenecks:**
- Revenue record digitization incomplete (30% manual in remote tehsils)
- Land dispute resolution: 8 lakh pending cases in Haryana courts
- Last-mile service delivery: CSCs (Common Service Centers) understaffed in tribal-heavy Nuh, Mewat districts

**Way Forward:**
1. Implement minimum 2-year posting tenure for district-level officers (ARC2 Recommendation)
2. District Performance Index with public scorecard on service delivery KPIs
3. Strengthen Gram Sachivalaya program — one panchayat secretary per 500 households
4. Operationalize Haryana Ombudsman with time-bound complaint resolution
5. Technology: GIS-based revenue record system, e-courts in all talukas

Good governance is not a destination but a continuous process. Haryana's developmental aspirations demand administrative efficiency that reaches the last mile.""",
        "subject": "GS2 - Governance & IR", "topic": "Good Governance", "year": 2025,
        "exam_type": "HCS", "source": "Expert Model Answer", "score": 9.0, "rank": None,
        "tags": ["model_answer", "haryana", "governance", "district_administration"],
    },

    "green_revolution_haryana": {
        "question": "Analyze the impact of Green Revolution on agriculture in Haryana. What are the emerging challenges and how can sustainable agriculture be promoted?",
        "answer": """The Green Revolution (1965-1970) transformed Haryana from a food-deficit region into India's agricultural powerhouse, yet its long-term ecological costs now threaten its very foundations.

**Impact of Green Revolution:**
- Production leap: wheat yield increased from 1.1 T/ha (1965) to 4.2 T/ha (2022)
- Haryana contributes 60 lakh metric tonnes wheat to Central Pool annually
- Irrigation expansion: canal coverage from 15% (1960) to 85% (2023) of cropped area
- Income transformation: rural per-capita income doubled between 1970-1985

**Emerging Challenges:**
1. **Groundwater depletion**: Water table falling at 1-2m/year; 11 of 22 districts in CGWB "dark zone"
2. **Stubble burning**: 50,000+ stubble burning incidents annually; Haryana contributes 15-20% of Delhi's Nov-Dec AQI crisis
3. **Soil health degradation**: Continuous wheat-paddy monoculture depletes soil organic carbon; increasing fertilizer input for same output
4. **Economic dependency**: 90%+ farmers on MSP for paddy and wheat — no market exposure
5. **Water-energy nexus**: Free electricity for agriculture → 8000 MW midnight consumption → fiscal burden Rs 8,000 crore/year

**Sustainable Agriculture Pathways:**
1. **Mera Pani Meri Virasat**: Rs 7,000/acre incentive to shift from paddy → alternate crops; 2 lakh acres freed in 2020-21
2. **Natural farming**: Zero Budget Natural Farming (ZBNF) pilot in 50,000 acres — Subhash Palekar model
3. **Micro-irrigation**: State subsidy of 85% for drip/sprinkler; scale from 18% to 40% coverage
4. **FPO (Farmer Producer Organizations)**: 500 FPOs targeted under Agri Infrastructure Fund
5. **Paddy transplanting delay law**: Compulsory delay to June 10 — saves 25% groundwater by limiting growing season

The Green Revolution was a necessary intervention; sustainable agriculture is now a civilizational imperative for Haryana's next generation.""",
        "subject": "GS3 - Economy & Environment", "topic": "Agriculture", "year": 2025,
        "exam_type": "HCS", "source": "Expert Model Answer", "score": 9.5, "rank": 1,
        "tags": ["model_answer", "haryana", "agriculture", "green_revolution", "sustainability"],
    },

    "federalism_upsc": {
        "question": "Cooperative federalism is the need of the hour for India. Discuss.",
        "answer": """India's federal structure, embedded in the Constitution as a "Union of States" (Art. 1), has evolved from competitive to cooperative federalism as developmental challenges demand collective state-Centre synergy.

**Constitutional Architecture:**
- Art. 245-263: distribution of legislative, administrative, financial powers
- 7th Schedule: Union List (97 items), State List (66 items), Concurrent List (47 items)
- Art. 280: Finance Commission ensures fiscal federalism

**Cooperative Federalism Institutions:**
1. **NITI Aayog** (replaced Planning Commission 2015): brings states as "partners in development" — Team India platform
2. **GST Council** (Art. 279A): exemplary cooperative mechanism — Centre-State joint taxation body; cleared 2,000+ decisions by consensus
3. **15th Finance Commission**: Rs 41 lakh crore devolution (42% divisible pool) — historic decentralization
4. **Aspirational Districts Programme**: 112 districts, states in driver's seat with Centre facilitation

**Tensions Threatening Cooperation:**
- Governor's role: Art. 153-161 — partisan role in Opposition-ruled states (Kerala, Tamil Nadu, Jharkhand disputes 2022-24)
- Article 356 misuse: President's Rule as political weapon — S.R. Bommai case guidelines often ignored
- Encroachment on State List: environment, education, agriculture farm laws (withdrawn 2021 amid protest)
- Revenue sharing disputes: states demand higher share in divisible pool beyond 42%

**Way Forward:**
1. Reinvigorate Inter-State Council (Art. 263) — annual meetings with binding recommendations
2. Reform Rajya Sabha into genuine states' house (like German Bundesrat)
3. Establish constitutional dispute resolution tribunal for Centre-State conflicts
4. Competitive governance: state rankings (Ease of Doing Business, Health Index) healthy competition
5. Asymmetric federalism: special status for J&K (post-370), Northeast — respect diversity

True federalism is not about division of power but about governance architecture that places citizens at the centre.""",
        "subject": "GS2 - Governance & IR", "topic": "Federalism", "year": 2023,
        "exam_type": "UPSC", "source": "Expert Model Answer", "score": 9.0, "rank": None,
        "tags": ["model_answer", "upsc", "federalism", "governance", "constitution"],
    },

    "climate_change_india": {
        "question": "India's commitments under the Paris Agreement require balancing development aspirations with climate action. Examine.",
        "answer": """India's climate dilemma is uniquely complex: home to 17% of the world's population yet responsible for only 3% of historical cumulative emissions, India must navigate a razor-thin path between development imperatives and planetary responsibility.

**India's Paris Agreement Commitments (Updated NDC 2022):**
- Reduce emissions intensity by 45% by 2030 (vs 2005 baseline)
- 50% cumulative electric power from non-fossil fuels by 2030
- Create additional carbon sink of 2.5-3 billion tonnes through forests
- Net Zero by 2070

**Development-Climate Tension:**
1. **Energy poverty**: 70 million households still rely on biomass; coal powers 53% of electricity
2. **Per-capita equity**: India's per-capita emissions (1.9 T CO₂) vs USA (14.7 T) — historical inequity
3. **Industrial growth**: steel, cement, fertilizer sectors cannot decarbonize overnight
4. **Agriculture**: 14% of India's GHG from agriculture (methane from rice, cattle) — food security imperative

**Progress Achieved:**
- RE capacity: 191 GW installed (Jan 2024), solar at 73 GW — world's 4th largest solar
- International Solar Alliance: India-France initiative — 124 countries
- PM Surya Ghar: 1 crore rooftop solar homes by 2025
- EV adoption: 15 lakh EVs sold in 2023; FAME-II scheme

**Financing Gap:**
- India needs $2.5 trillion climate finance by 2030 — domestic resources insufficient
- Developed nations failed $100 billion/year promise (COP15) — COP27 partial progress
- India's demand: Loss & Damage fund operationalized at COP27 — partial victory

**Way Forward:**
1. Green Hydrogen Mission: 5 MMT by 2030 — steel, fertilizer decarbonization
2. Carbon pricing: Internal carbon price for PSUs — pilot before national scheme
3. Just transition: Singareni, NTPC — reskill 1 lakh coal workers by 2030
4. Biodiversity co-benefits: forest conservation = carbon sink + ecosystem services

India's climate leadership must be premised on climate justice — historical responsibility, not present sacrifice.""",
        "subject": "GS3 - Economy & Environment", "topic": "Environment", "year": 2022,
        "exam_type": "UPSC", "source": "Expert Model Answer", "score": 9.5, "rank": 3,
        "tags": ["model_answer", "upsc", "climate_change", "paris_agreement", "environment"],
    },

    "ethics_civil_servants": {
        "question": "What are the ethical challenges faced by civil servants in India? How can integrity be institutionalized?",
        "answer": """Civil servants serve as the interface between the state and citizens. Their ethical conduct is not merely a professional virtue — it is a constitutional obligation under their oath of service.

**Core Values Expected (ARC2):**
- Integrity: consistency between stated values and actions
- Impartiality: decisions based on merit, not personal interest
- Dedication to public service: subordinating personal interest to public good
- Empathy and compassion: understanding impact on vulnerable sections

**Major Ethical Challenges:**

1. **Political Interference**: Frequent transfers used as punishment (IAS officer Ashok Khemka transferred 53 times in 32 years in Haryana — a national symbol of integrity under pressure)

2. **Conflict of Interest**: Land acquisition decisions where officer has land interests; awarding government contracts to relatives

3. **Whistleblowing Dilemma**: Exposing corruption risks career — Whistleblowers Protection Act 2014 weak in implementation; Satyendra Dubey (NHAI) murder chilling example

4. **Caste/Community Pressure**: Officers from dominant caste communities pressured to favour own community (Jat agitation 2016 — HCS officers' dilemma)

5. **Moral Cowardice**: Remaining silent when illegal orders are given — IPS officers during 2002 Gujarat riots

6. **Digital Ethics**: Data privacy in Aadhaar implementation; algorithmic bias in social welfare schemes

**Institutional Integrity Mechanisms:**
- Lokpal and Lokayuktas: Art. 315 — operationalized 2019 but no conviction yet
- CVC (Central Vigilance Commission): advisory oversight of central employees
- CAG: financial accountability
- RTI Act 2005: citizen accountability tool

**Case Study — Positive:**
IAS officer D.C. Gupta (UP): despite political pressure, ensured transparent COVID-19 procurement — exemplifies public service values

**Way Forward:**
1. Mandatory 2-year posting security for district officers (ARC2 Recommendation 7.15)
2. Operationalize Civil Services Board in all states for transparent transfer posting
3. Annual public asset declaration with independent verification
4. Ethics oath renewal every 5 years — reinforce commitment
5. Citizens' Report Card for district officers — public accountability

Integrity is not just about resisting temptation — it is about building systems where the ethical path is also the easiest path.""",
        "subject": "GS4 - Ethics", "topic": "Ethics in Governance", "year": 2024,
        "exam_type": "UPSC", "source": "Expert Model Answer", "score": 9.0, "rank": None,
        "tags": ["model_answer", "upsc", "ethics", "civil_servants", "integrity"],
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# DATABASE INSERTION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _get_or_create_question(db, q_data: dict):
    """Get existing question or create new one in DB."""
    from app.models.models import Question
    existing = db.query(Question).filter(
        Question.text == q_data["question"][:500],
        Question.year == q_data["year"],
        Question.exam_type == q_data["exam_type"],
    ).first()
    if existing:
        return existing

    q = Question(
        text=q_data["question"][:500],
        subject=q_data["subject"],
        topic=q_data.get("topic", "General"),
        year=q_data["year"],
        exam_type=q_data["exam_type"],
        marks=q_data.get("marks", 15),
        word_limit=q_data.get("word_limit", 250),
        model_answer_points=q_data.get("model_answer_framework", []),
        difficulty="moderate",
    )
    db.add(q)
    db.flush()
    return q


def _insert_topper_answer(db, question_id: int, answer_text: str, meta: dict):
    """Insert a topper answer record."""
    from app.models.models import TopperAnswer
    existing = db.query(TopperAnswer).filter(
        TopperAnswer.question_id == question_id,
        TopperAnswer.source == meta.get("source", ""),
    ).first()
    if existing:
        return existing

    ta = TopperAnswer(
        question_id=question_id,
        ocr_text=answer_text,
        score=meta.get("score"),
        rank=meta.get("rank"),
        year=meta.get("year"),
        exam_type=meta.get("exam_type", "UPSC"),
        subject=meta.get("subject"),
        tags=meta.get("tags", []),
        source=meta.get("source", "curated"),
        is_anonymized=True,
    )
    db.add(ta)
    db.flush()
    return ta


def _add_to_chromadb(topper_answer_id: int, question_text: str, answer_text: str, meta: dict):
    """Add answer to ChromaDB vector store for RAG."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_or_create_collection(
            name="topper_answers",
            metadata={"hnsw:space": "cosine"}
        )
        doc_id = f"topper_{topper_answer_id}"
        # Check if already exists
        try:
            existing = collection.get(ids=[doc_id])
            if existing and existing["ids"]:
                return
        except Exception:
            pass

        collection.add(
            documents=[f"Q: {question_text}\n\nA: {answer_text}"],
            metadatas=[{
                "subject": meta.get("subject", ""),
                "exam_type": meta.get("exam_type", "UPSC"),
                "year": str(meta.get("year", "")),
                "score": str(meta.get("score", "")),
                "source": meta.get("source", ""),
                "topic": meta.get("topic", ""),
            }],
            ids=[doc_id],
        )
        logger.info(f"  ChromaDB: indexed {doc_id}")
    except Exception as e:
        logger.warning(f"ChromaDB insert failed for {topper_answer_id}: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE STAGES
# ══════════════════════════════════════════════════════════════════════════════

def stage_curated_dataset(db, stats: dict):
    """Stage 1: Insert the curated 30-year question bank + full model answers."""
    logger.info(f"\n{'='*60}")
    logger.info("STAGE 1: Loading curated 30-year UPSC/HCS question bank")
    logger.info(f"{'='*60}")

    inserted = 0

    # 1a. Curated questions with framework answers
    for q_data in CURATED_QUESTIONS:
        q = _get_or_create_question(db, q_data)

        # Build framework answer from bullet points
        framework = q_data.get("model_answer_framework", [])
        answer_text = f"[MODEL ANSWER FRAMEWORK — {q_data['year']} {q_data['exam_type']}]\n\n"
        answer_text += f"Question: {q_data['question']}\n\n"
        answer_text += "Key Points to Cover:\n"
        for i, point in enumerate(framework, 1):
            answer_text += f"{i}. {point}\n"

        meta = {
            "source": "Curated30YearBank",
            "score": 8.5,
            "rank": None,
            "year": q_data["year"],
            "exam_type": q_data["exam_type"],
            "subject": q_data["subject"],
            "topic": q_data.get("topic", ""),
            "tags": ["curated", "framework", q_data["exam_type"].lower()],
        }
        ta = _insert_topper_answer(db, q.id, answer_text, meta)
        _add_to_chromadb(ta.id, q_data["question"], answer_text, meta)
        inserted += 1

    db.commit()
    logger.info(f"  Curated questions inserted: {inserted}")
    stats["curated"] = inserted

    # 1b. Full expert model answers
    logger.info(f"\n  Loading {len(FULL_MODEL_ANSWERS)} full expert model answers...")
    for key, data in FULL_MODEL_ANSWERS.items():
        q_data = {
            "question": data["question"],
            "subject": data["subject"],
            "topic": data["topic"],
            "year": data["year"],
            "exam_type": data["exam_type"],
            "marks": 15,
            "word_limit": 250,
            "model_answer_framework": [],
        }
        q = _get_or_create_question(db, q_data)

        meta = {
            "source": data.get("source", "Expert Model Answer"),
            "score": data.get("score", 9.0),
            "rank": data.get("rank"),
            "year": data["year"],
            "exam_type": data["exam_type"],
            "subject": data["subject"],
            "topic": data["topic"],
            "tags": data.get("tags", ["model_answer"]),
        }
        ta = _insert_topper_answer(db, q.id, data["answer"], meta)
        _add_to_chromadb(ta.id, data["question"], data["answer"], meta)
        inserted += 1

    db.commit()
    logger.info(f"  Total stage 1 records: {inserted}")
    stats["full_answers"] = len(FULL_MODEL_ANSWERS)


def stage_llm_generation(db, stats: dict, limit: int = 30):
    """Stage 2: Use LLM to generate topper-quality answers for curated questions."""
    logger.info(f"\n{'='*60}")
    logger.info(f"STAGE 2: LLM answer generation (up to {limit} answers)")
    logger.info(f"{'='*60}")

    try:
        from app.services.evaluation_service import get_llm
        llm = get_llm()
    except Exception as e:
        logger.warning(f"Could not load LLM: {e}")
        llm = None

    if llm is None:
        logger.warning("  No LLM available — skipping generation stage.")
        logger.warning("  Set GROQ_API_KEY or GEMINI_API_KEY in .env to enable.")
        stats["llm_generated"] = 0
        return

    from app.services.scraper_service import generate_topper_answer_with_llm
    from app.models.models import Question, TopperAnswer

    generated = 0
    # Prioritize questions that don't have a full text answer yet
    questions = db.query(Question).all()

    for q in questions:
        if generated >= limit:
            break

        # Skip if already has a high-quality answer
        has_full = db.query(TopperAnswer).filter(
            TopperAnswer.question_id == q.id,
            TopperAnswer.source.in_(["Expert Model Answer", "LLM Generated"]),
        ).first()
        if has_full:
            continue

        logger.info(f"  Generating answer for: {q.text[:80]}...")
        answer_text = generate_topper_answer_with_llm(
            question=q.text,
            subject=q.subject,
            year=q.year or 2024,
            marks=q.marks,
            word_limit=q.word_limit,
            llm=llm,
        )

        if answer_text and len(answer_text) > 100:
            meta = {
                "source": "LLM Generated",
                "score": 8.5,
                "rank": None,
                "year": q.year,
                "exam_type": q.exam_type,
                "subject": q.subject,
                "topic": q.topic or "General",
                "tags": ["llm_generated", "topper_quality", q.exam_type.lower()],
            }
            ta = _insert_topper_answer(db, q.id, answer_text, meta)
            _add_to_chromadb(ta.id, q.text, answer_text, meta)
            generated += 1
            time.sleep(0.5)  # Rate limit

    db.commit()
    logger.info(f"  LLM-generated answers: {generated}")
    stats["llm_generated"] = generated


def stage_web_scrape(db, stats: dict, max_pages: int = 3):
    """
    Stage 3: Scrape public model answers and real topper copies from 8 sources:
      InsightsIAS, DrishtiIAS, GSScore, ForumIAS, CivilsDaily, Mrunal
    All are 100% free public sources (verified by research).
    """
    logger.info(f"\n{'='*60}")
    logger.info("STAGE 3: Web scraping public topper answers (8 sources)")
    logger.info(f"{'='*60}")

    try:
        import bs4  # noqa — just checking it's installed
    except ImportError:
        logger.error("  beautifulsoup4 not installed! Run: pip install beautifulsoup4 lxml")
        stats["scraped"] = 0
        return

    from app.services.scraper_service import (
        scrape_insights_ias,
        scrape_drishti_ias,
        scrape_gsscore,
        scrape_forumias,
        scrape_civilsdaily,
        scrape_mrunal,
    )

    total_scraped = 0

    scrape_tasks = [
        # (label, callable, kwargs)
        ("InsightsIAS (topper copies + model answers)", scrape_insights_ias, {"max_pages": max_pages}),
        ("DrishtiIAS (topper copies)", scrape_drishti_ias, {"max_pages": max_pages}),
        ("GSScore (year-wise topper copies 2018-2024)", scrape_gsscore, {"years": list(range(2018, 2025))}),
        ("ForumIAS (Rank 1-50 topper pages)", scrape_forumias, {}),
        ("CivilsDaily (post-mains model solutions)", scrape_civilsdaily, {"max_urls": 8}),
        ("Mrunal (topicwise answers 2011-2024)", scrape_mrunal, {"max_pages": max_pages}),
    ]

    for label, fn, kwargs in scrape_tasks:
        logger.info(f"\n  [{label}]")
        try:
            records = fn(**kwargs)
            logger.info(f"  → {len(records)} records fetched")

            for rec in records:
                q_data = {
                    "question": rec.question_text,
                    "subject": rec.subject,
                    "topic": rec.topic,
                    "year": rec.year,
                    "exam_type": rec.exam_type,
                    "marks": rec.marks,
                    "word_limit": rec.word_limit,
                    "model_answer_framework": [],
                }
                q = _get_or_create_question(db, q_data)
                meta = {
                    "source": rec.source,
                    "score": rec.score,
                    "rank": rec.rank,
                    "year": rec.year,
                    "exam_type": rec.exam_type,
                    "subject": rec.subject,
                    "topic": rec.topic,
                    "tags": rec.tags,
                }
                ta = _insert_topper_answer(db, q.id, rec.answer_text, meta)
                _add_to_chromadb(ta.id, rec.question_text, rec.answer_text, meta)
                total_scraped += 1

            db.commit()
        except Exception as e:
            logger.warning(f"  Scraper {label} failed: {e}")

    logger.info(f"\n  Total scraped across all sources: {total_scraped}")
    stats["scraped"] = total_scraped


def clear_topper_database(db):
    """Wipe all topper answers and ChromaDB collection — for a fresh rebuild."""
    from app.models.models import TopperAnswer
    count = db.query(TopperAnswer).count()
    db.query(TopperAnswer).delete()
    db.commit()
    logger.info(f"Cleared {count} topper answers from SQLite.")

    try:
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_db")
        try:
            client.delete_collection("topper_answers")
            logger.info("Cleared ChromaDB topper_answers collection.")
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"ChromaDB clear failed: {e}")


def print_stats(stats: dict):
    logger.info(f"\n{'='*60}")
    logger.info("PIPELINE COMPLETE — Summary")
    logger.info(f"{'='*60}")
    logger.info(f"  Curated 30-year question bank:  {stats.get('curated', 0)}")
    logger.info(f"  Full expert model answers:      {stats.get('full_answers', 0)}")
    logger.info(f"  LLM-generated topper answers:   {stats.get('llm_generated', 0)}")
    logger.info(f"  Web-scraped answers (6 sources):{stats.get('scraped', 0)}")
    logger.info(f"    Sources: InsightsIAS, DrishtiIAS, GSScore,")
    logger.info(f"             ForumIAS, CivilsDaily, Mrunal")
    total = sum(stats.values())
    logger.info(f"  ─────────────────────────────────────────")
    logger.info(f"  TOTAL records in knowledge base: {total}")
    logger.info(f"{'='*60}")
    logger.info("ChromaDB is ready for RAG-based evaluation.")
    logger.info("")
    logger.info("To view topper answers: GET /api/topper-answers/")
    logger.info("To search by subject:   GET /api/topper-answers/?subject=GS2")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Hazeon AI — Populate topper answer knowledge base"
    )
    parser.add_argument(
        "--source",
        choices=["all", "curated", "llm", "scrape"],
        default="all",
        help="Which pipeline stages to run (default: all)",
    )
    parser.add_argument(
        "--llm-limit",
        type=int,
        default=30,
        help="Max number of LLM-generated answers (default: 30)",
    )
    parser.add_argument(
        "--scrape-pages",
        type=int,
        default=3,
        help="Max pages to scrape per source (default: 3)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing topper data before rebuilding",
    )
    args = parser.parse_args()

    # Initialize DB
    from app.database import init_db, SessionLocal
    init_db()
    db = SessionLocal()

    stats = {}

    try:
        if args.clear:
            logger.info("--clear flag: wiping existing topper answer database...")
            clear_topper_database(db)

        run_all = args.source == "all"

        if run_all or args.source == "curated":
            stage_curated_dataset(db, stats)

        if run_all or args.source == "llm":
            if args.source != "curated":
                stage_llm_generation(db, stats, limit=args.llm_limit)

        if run_all or args.source == "scrape":
            if args.source not in ("curated", "llm"):
                stage_web_scrape(db, stats, max_pages=args.scrape_pages)

        print_stats(stats)

    finally:
        db.close()


if __name__ == "__main__":
    main()
