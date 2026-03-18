"""
Hazeon AI — Build Fine-tuning Training Dataset
================================================
Builds a high-quality JSONL training dataset from:
  1. DB topper answers (scraped/uploaded)
  2. Curated 25-year UPSC question bank (upsc_25year_bank.py)
  3. Existing curated questions (populate_topper_db.py)

Training format (Alpaca instruction style):
  instruction: system role + evaluation rubric
  input: question + topper reference + student answer
  output: structured JSON evaluation

Run:
  cd backend/
  python -m scripts.build_training_dataset
  # Output: scripts/training_data/upsc_eval_dataset.jsonl
"""

import sys, os, json, random, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_dataset")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "training_data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "upsc_eval_dataset.jsonl")

# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM INSTRUCTION — baked into every training example
# Anti-hallucination: model must ground feedback in the provided reference
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_INSTRUCTION = """You are a senior UPSC/HCS Mains answer evaluator with 20+ years of experience. You have evaluated thousands of answer copies for UPSC Civil Services Mains and HCS (Haryana Civil Service) examinations.

CRITICAL INSTRUCTION: Base your evaluation ONLY on the topper reference answer provided. Do not add facts, schemes, or data points that are not present in either the student answer or the topper reference. Your feedback must be grounded in what the student actually wrote.

Scoring rubric (each 0-10):
- relevance_score: Does it answer what was asked? (0=off-topic, 10=perfectly targeted)
- intro_score: Quality of introduction — definition, context, relevance
- body_score: Coverage of main arguments, multi-dimensional analysis
- keyword_score: Subject-specific terminology, scheme names, constitutional articles
- structure_score: Headings, bullets, logical flow, presentation
- factual_score: Accuracy of facts, data points, examples cited
- conclusion_score: Way Forward quality — concrete, actionable, relevant
- word_limit_score: Adherence to word limit (too short/long = lower score)
- analysis_score: Depth of analysis vs mere description
- diagram_score: Use of diagrams/flowcharts/maps (0 if none attempted)
- multidimensional_score: Coverage across political/economic/social/environmental/ethical/legal dimensions

Return ONLY valid JSON with:
  - All 11 scores above
  - overall_score (weighted average, 0-10)
  - marks_obtained (proportional to marks available)
  - feedback_summary (2-3 sentence overall assessment)
  - strengths (list of 2-4 specific strengths, citing actual content from student answer)
  - weaknesses (list of 2-4 specific gaps, citing what was missing vs topper reference)
  - improvements (list of 3-5 actionable suggestions)
  - keywords_found (list of keywords/schemes present in student answer)
  - keywords_missed (list of important keywords from topper reference missing in student answer)
  - topper_benchmark (1-2 sentences comparing student level to topper standard)
  - dimension_analysis (object with boolean values: political, economic, social, environmental, ethical, legal)"""


# ══════════════════════════════════════════════════════════════════════════════
# 5-TIER STUDENT ANSWER TEMPLATES
# Each tier has 10 varied templates covering different subjects
# ══════════════════════════════════════════════════════════════════════════════

STUDENT_ANSWER_TEMPLATES = {

    "very_weak": [
        # Generic, no data, very short
        "This is an important topic. The government is trying to solve this problem. There are many issues that need to be addressed. We should work together to find solutions. The future looks good if we all cooperate.",
        "This question is about a very important issue in India. India is a developing country and faces many challenges. The government has taken many steps. More needs to be done.",
        "There are many factors responsible for this. We need to study them carefully. The government should take action immediately. This will help the country develop faster.",
        "This is a serious problem in India. Many people are affected. The government must intervene. International community should also help. Only then can we solve this.",
        "The topic is very relevant today. We have seen many issues arising. Steps must be taken. People should be made aware. This will lead to development.",
        "India faces this challenge. The Constitution of India provides for this. Government schemes have been launched. But more is needed. Way Forward: more efforts.",
        "This problem affects millions of people. Poverty, lack of education, and corruption are the main reasons. The government should do something. Only then will India develop.",
        "There are several dimensions to this issue — social, economic, and political. The government has been addressing them. But challenges remain. We must find holistic solutions.",
        "This is an important governance issue. India is the largest democracy. We have 1.4 billion people. The government is working on it. More reforms are needed.",
        "The topic has historical roots. Colonialism affected India badly. After independence we have made progress. But problems remain. We must work harder.",
    ],

    "weak": [
        # Basic understanding, 1-2 facts, no structure
        "Good governance is very important for India. We need transparency and accountability. The government has launched many e-governance schemes like UMANG and DigiLocker. But corruption remains a big problem. Many citizens don't get their rights. The government should work harder to improve administration. RTI has helped people get information. But more needs to be done. Way Forward: Strengthen anti-corruption laws.",
        "The Green Revolution brought good changes in Indian agriculture. Crop production increased a lot. HYV seeds were used. Irrigation improved. But there are problems too like water shortage and soil degradation. The government is trying to solve these through schemes. Farmers need more help. Way Forward: Sustainable agriculture should be promoted.",
        "The Supreme Court is the guardian of the Constitution. It has given many important judgments. PIL has helped poor people get justice. Basic structure doctrine is very important. But there is a lot of pendency. 4 crore cases are pending. Judges should be appointed faster. Way Forward: Increase number of judges.",
        "India's foreign policy should focus on its neighbours. We need good relations with Bangladesh, Nepal and Sri Lanka. China is a challenge. Pakistan relations are tense. We should follow Neighbourhood First Policy. Trade should be increased. People to people contacts matter. Way Forward: Strengthen SAARC.",
        "Ethics is very important for civil servants. They should be honest and serve the people. Corruption is a big problem. Lokpal has been set up. It should work effectively. Civil servants should follow the Conduct Rules. They should not take bribes. Way Forward: Strict action against corrupt officials.",
        "Artificial intelligence is changing the world. India is developing AI. It can help in healthcare and agriculture. But there are risks like job loss. We should be careful. The government has launched IndiaAI Mission. Skilling is important. Way Forward: AI education for all.",
        "Water scarcity is a serious problem. Many parts of India face drought. Groundwater is depleting. Agriculture uses too much water. The Jal Jeevan Mission has been launched. More dams and canals should be built. Rainwater harvesting is important. Way Forward: Save water, use wisely.",
        "Federalism is important in India. States and Centre share powers. 7th Schedule divides powers. GST was a big change. NITI Aayog promotes cooperation. But there are tensions between states and centre. Governor's role is controversial. Way Forward: More coordination needed.",
        "Non-Performing Assets have affected Indian banks badly. Loans given to companies were not repaid. This caused a banking crisis. Government had to invest money in banks. IBC was passed to recover loans. Banks are now better. Way Forward: Strict lending norms.",
        "The Bhakti movement was very important. Kabir, Mirabai, Tukaram were great saints. They preached equality and devotion. They fought against caste discrimination. Regional languages developed. This helped in social reform. Way Forward: Continue these values today.",
    ],

    "average": [
        # Decent understanding, some data, basic structure
        """Good governance is the foundation of development. Transparency, accountability and responsiveness are its pillars. In India, several initiatives have improved governance.

Key Achievements: SARAL platform, CM Window for grievances, DBT saving Rs 2.73 lakh crore in leakages, JAM Trinity enabling direct transfers.

Challenges: Corruption remains (India 93rd on CPI 2023), judicial pendency (4.7 crore cases), digital divide leaving rural areas behind, political interference in bureaucracy with frequent transfers.

Way Forward: Implement ARC2 recommendations, strengthen Lokpal, expand e-governance, ensure fixed tenures for civil servants.""",

        """The Green Revolution transformed Indian agriculture in the 1960s-70s. High Yielding Variety seeds, chemical fertilizers and expanded irrigation led to food self-sufficiency.

Achievements: Wheat yield increased significantly, food security improved, rural incomes rose.

Emerging Challenges: Groundwater depletion (11 districts in Haryana over-exploited by CGWB), stubble burning causing air pollution, soil degradation from overuse of urea, wheat-paddy monoculture.

Government Response: Mera Pani Meri Virasat scheme for crop diversification, Happy Seeder for stubble management, Soil Health Cards.

Way Forward: Zero Budget Natural Farming, FPO strengthening, micro-irrigation expansion, crop diversification incentives.""",

        """India's federal structure divides powers between Centre and states through the 7th Schedule. GST Council exemplifies cooperative federalism — states and Centre sharing tax policy.

Constitutional Provisions: Articles 245-263, Finance Commission (15th FC devolved 41% to states), Inter-State Council under Article 263.

Challenges: Governor's role as Centre's agent, Article 356 misuse historically, centrally sponsored schemes burden states with matching grants.

Success: NITI Aayog forums, PM Gati Shakti integrating ministries, Kerala health model and Gujarat growth model as templates.

Way Forward: Strengthen ISC, reduce CSS conditionalities, codify Governor's discretion, empower states financially.""",

        """India's startup ecosystem has grown remarkably. With 100+ unicorns, India is the 3rd largest startup ecosystem globally. Startup India scheme and Rs 10,000 crore Fund of Funds have provided support.

Sectors: Fintech, Edtech, Healthtech are leading. UPI has enabled fintech growth.

Challenges: Funding winter in 2023, talent shortage in deep tech, Angel Tax (amended 2023) had chilled investments, regulatory complexity.

Opportunities: Global supply chain shift from China, domestic consumption growth, Digital India infrastructure.

Way Forward: Deep tech fund, easier ESOP taxation, Tier-2 city startup hubs, faster regulatory approvals.""",

        """Left Wing Extremism has been a major internal security challenge. The Red Corridor spreads across 10 states. Root causes include tribal displacement, development deficit, and forest rights denial.

Government Strategy: SAMADHAN doctrine (2017) combining security and development. Aspirational Districts Programme targeted LWE areas. Road connectivity (PMGSY) and mobile towers improved.

Recent Success: 2023-24 saw highest Naxal casualties; surrenders increased with rehabilitation schemes.

Challenges: Sustainable peace requires addressing root causes — Forest Rights Act pending claims (4.4 million), PESA implementation gaps.

Way Forward: Full FRA implementation, MNREGA strengthening in LWE districts, fast-track courts for LWE cases.""",

        """The Supreme Court has evolved as India's constitutional guardian through landmark judgments. Basic Structure Doctrine (Kesavananda Bharati 1973) limits Parliament's amending power. PIL revolution (Hussainara Khatoon 1979) opened courts to marginalized.

Expansions: Right to Privacy (Puttaswamy 2017), LGBTQ+ decriminalization (Section 377), Right to food derived from Article 21.

Concerns: NJAC struck down (2015) preserving collegium; 4.7 crore pending cases; selective urgency in listing matters.

Way Forward: ADR promotion (Mediation Act 2023), National Court Management System, fill 400+ HC vacancies, All-India Judicial Services.""",

        """Non-Performing Assets (NPAs) peaked at Rs 10.36 lakh crore (2018) threatening India's banking system. Crony capitalism, poor credit appraisal, and political lending caused the crisis.

Solutions Deployed: IBC 2016 — Rs 2.9 lakh crore recovered; PSB recapitalization (Rs 3.17 lakh crore); NCLT established for resolution.

Progress: Gross NPA ratio improved from 11.6% (2018) to 3.2% (March 2024).

Remaining Issues: NCLT capacity constrained, willful defaults continue, PSB governance reform incomplete.

Way Forward: Independent PSB boards, early warning systems, stronger credit bureaus, IBC amendment for faster resolution.""",

        """The National Food Security Act 2013 provides legal entitlement to 5 kg grain/month for 67% population. PMGKAY made free grain permanent for 81 crore beneficiaries in 2023.

Achievements: One Nation One Ration Card (portability for migrants), Aadhaar-seeding reduced ghost beneficiaries, PDS leakages reduced from 46% to 22%.

Challenges: Exclusion errors still occur, 3.5 lakh crore annual food subsidy creating fiscal pressure, malnutrition persists despite food access.

Way Forward: DBT for food subsidy where feasible, millets inclusion in PDS, complete digitization of ration cards, nutrition fortification.""",

        """Ethics is integral to public service. Civil servants face dilemmas between political loyalty and constitutional duty. AIS Conduct Rules 1968 guide behaviour.

Key Dilemmas: Corrupt superior vs public interest, conflict of interest in land decisions, compassion vs rules, secrecy vs transparency.

Institutional Safeguards: Lokpal (2019 appointment), CVC vigilance, CAG audit, RTI Act.

Examples: D.R. Bhargava (Gujarat 2002) — officer who maintained neutrality, cited in LBSNAA case studies.

Way Forward: Mandatory ethics training at LBSNAA, asset disclosure with verification, 360-degree performance appraisal including integrity assessment.""",

        """India's Paris Agreement commitments are among the most ambitious for a developing nation. Updated NDC: 45% emissions intensity reduction by 2030, 500 GW non-fossil capacity, net zero by 2070.

Progress: 172 GW renewable energy installed; ISA launched; National Hydrogen Mission targets 5 MT green hydrogen by 2030.

Challenges: Coal provides 53% electricity, Rs 2.5 trillion needed for green transition, developed nations failed $100bn finance pledge.

India's Position: CBDR principle (equity argument), Loss and Damage Fund win at COP27, technology transfer demand.

Way Forward: Carbon pricing pilot, PM Surya Ghar rooftop solar expansion, just transition fund for coal workers.""",
    ],

    "good": [
        # Strong content, specific data, good structure, some gaps
        """Good governance embodies transparency, accountability and responsiveness. India has made significant strides but structural challenges persist.

**Achievements**
• JAM Trinity: Saved Rs 2.73 lakh crore in subsidy leakages; 11.5 billion DBT transactions
• UMANG/DigiLocker/GeM portal (Rs 4 lakh crore procurement 2023)
• PM Gati Shakti: GIS-based infrastructure integration across 16 ministries

**Challenges**
• Corruption: India ranked 93/180 (TI CPI 2023) — despite Lokpal appointment (2019), no major conviction
• Judicial pendency: 4.7 crore cases; district courts: 3.4 year average resolution
• Administrative capacity: 18 IAS/crore population vs 50+ in developed nations; ARC2 tenure recommendations unimplemented
• Digital divide: 40% rural India offline — e-governance excludes most vulnerable

**Way Forward**
1. Lokpal prosecution wing — binding recommendations, not just advisory
2. Fixed civil service tenure (2 years minimum) via HCS/AIS Rules amendment
3. National e-Courts Mission: AI-assisted scheduling, reduce pendency 50% in 5 years
4. Gram Panchayat development plans with own-source revenue
5. Social audit mandated for all flagship schemes (MGNREGS model)""",

        """The Mauryan Empire (322-185 BCE) under Chandragupta and Ashoka created India's first pan-Indian administrative state.

**Administrative Legacy**
Kautilya's Arthashastra: 15-chapter statecraft blueprint — espionage, taxation, foreign policy. Empire divided into provinces under kumāras, with standardized weights, currency, and professional bureaucracy.

**Ashoka's Dhamma**
Post-Kalinga transformation: 33 rock edicts across the subcontinent — non-violence, religious tolerance, welfare. Lion Capital at Sarnath became India's national emblem.

**Cultural & Economic Contributions**
• Silk Route integration — Persian Gulf trade
• Buddhist missions to Sri Lanka (Mahinda), Central Asia
• Sanchi, Sarnath architecture — defining India's UNESCO heritage

**Decline and Lesson**
Over-centralization + post-Ashoka weak successors — Pushyamitra Shunga revolt (185 BCE). Shows that administrative over-extension weakens institutional resilience.

**Way Forward**
Ashoka's welfare-oriented governance remains relevant — SDG-aligned public administration; Kautilya's intelligence apparatus prefigures modern cyber-security frameworks.""",

        """India's Neighborhood First Policy (2014) recognizes that India's global rise depends on regional stability.

**Core Pillars**
Connectivity (BBIN Motor Vehicles Agreement), development assistance ($1.5bn Bangladesh, $4bn Sri Lanka crisis 2022), people-to-people ties, security cooperation.

**Country Assessment**
• Bangladesh: Most successful — $12bn bilateral trade, land boundary settlement (2015); PM Hasina 2024 exit tested relationship
• Sri Lanka: $4bn crisis assistance strengthened ties; but Hambantota (99-year China lease) shows limits
• Nepal: Kalapani border dispute, BRI entry complicates
• Pakistan: Effectively frozen since Pulwama-Balakot (2019); Kartarpur Corridor sole positive
• Maldives: "India Out" campaign under Muizzu; China engagement sought

**China Factor**
Every neighbour is now triangulated by BRI — India must compete on infrastructure financing speed.

**Way Forward**
1. BIMSTEC operationalization — SAARC alternative excluding Pakistan
2. Blue Economy cooperation in Indian Ocean
3. Digital public infrastructure export (UPI, Aadhaar) as soft power
4. Faster credit line disbursement — India historically slow vs China""",

        """Non-Cooperation Movement (1920-22) transformed India's freedom struggle from elite petition to mass agitation.

**Context**
Jallianwala Bagh massacre (1919) + Rowlatt Act (detention without trial) — constitutional loyalism collapsed. Gandhi called for withdrawal of consent from British institutions.

**Widening Social Base**
• Peasants: Awadh kisan movement, Mappila uprising 1921
• Workers: Bombay textile mills joined
• Students, women — first large-scale women's participation
• Khilafat alliance: unprecedented Hindu-Muslim unity

**Methods**
Boycott of courts, schools, legislative councils, British goods. Over 30,000 jailed including Gandhi. Charkha as economic self-reliance symbol.

**Chauri Chaura (1922)**
Gandhi's withdrawal after 22 policemen killed — controversial but showed non-violence was the movement's non-negotiable moral anchor.

**Lasting Impact**
• Built INC's village-level organizational machinery
• Established Swaraj as achievable goal
• Template for Civil Disobedience (1930) and Quit India (1942)
• International: MLK cited this as inspiration for US civil rights movement""",

        """Artificial Intelligence presents India with transformative opportunities and serious risks.

**Opportunities**
• Agriculture: AI crop disease detection via drones, precision irrigation — 20% productivity potential for 600mn farmers
• Healthcare: ABDM + AI diagnostics — AIIMS pilot achieved 94% cancer detection accuracy from X-rays vs 78% for junior doctors
• Governance: Fraud detection in DBT, SUVAS court AI, predictive infrastructure maintenance
• Economy: IndiaAI Mission (Rs 10,371 crore 2024); McKinsey: $450-500bn GDP addition potential

**Risks**
• Employment: IMF (2024) — 40% global jobs vulnerable; 13mn India BPO workers at immediate risk
• Algorithmic bias: MIT study — 35% error rate for darker skin in facial recognition vs 0.8% for lighter
• Data sovereignty: DPDP Act 2023 nascent — India generates 20% global data, lacks sovereignty framework
• Deepfakes: 2024 election proliferation — no takedown mechanism
• Digital divide: AI benefits accrue to connected; 40% India offline

**Way Forward**
1. IndiaAI Compute Infrastructure: 10,000+ GPU public cloud
2. Responsible AI framework: Algorithmic impact assessments
3. PM Kaushal Vikas 4.0: AI literacy in 1000+ ITIs
4. Sectoral sandboxes: healthcare, agriculture before full rollout""",

        """India's $5 trillion GDP target requires resolving structural constraints.

**Current Position**
GDP: ~$3.7 trillion (FY24), 5th largest globally. Growth drivers: services (IT $250bn exports), UPI ($2T transactions), PLI schemes ($26bn investments), 100+ unicorns.

**Structural Challenges**
• Jobless growth: Manufacturing employment stuck at 12% despite 7%+ GDP growth
• Agricultural gap: 45% workforce, only 16% GDP — 1.08 hectare average holding
• Human capital: ASER 2023 — 50% Class 5 students can't read Class 2 text; 25% engineering graduates directly employable
• Gender gap: Female LFPR 37% vs OECD average 53% — Rs 770bn annual GDP loss
• Logistics: 13-14% of GDP vs 8% in China — export competitiveness hit

**Bright Spots**
MSME PLI expansion, startup ecosystem, National Logistics Policy (2022), PM Gati Shakti.

**Way Forward**
1. 4 Labour Codes: full implementation for manufacturing competitiveness
2. National Credit Framework: STEM + vocational integration
3. Women workforce: creche mandate, equal pay enforcement
4. Logistics: PM Gati Shakti — freight cost reduction to 8% by 2027
5. Agricultural reform: e-NAM expansion, land leasing liberalization""",

        """The RTI Act 2005 is India's transparency revolution — but needs strengthening.

**Impact**
6 million applications/year — world's most used transparency law. Uncovered Commonwealth Games scam, NREGA wage theft, Rs 50,000+ crore exposed. Empowered marginalized — Dalits checking job cards, women verifying PDS allocations.

**Achievements**
NCRB data: conviction rates improved in states with active RTI usage. Supreme Court used RTI responses in several constitutional cases.

**Limitations**
• 2019 Amendment: CIC/SIC commissioners removable by government — independence compromised
• 178 RTI activists killed since Act passed — whistleblower protection inadequate
• 3.5 lakh appeals pending at CIC — justice delayed
• Section 8 overuse: exemptions invoked for legitimate public interest matters
• Infrastructure: PIOs still paper-based in 40% offices

**Way Forward**
1. Reverse 2019 Amendment or provide statutory security of tenure
2. Whistleblower Protection Act: effective enforcement, not just paperwork
3. Proactive disclosure under Section 4 — reduce RTI need
4. Online RTI portals for all public authorities
5. Digitize all PIO responses — searchable database""",

        """Reservation policies in India represent the most significant affirmative action framework in the world.

**Constitutional Basis**
Articles 15(4), 16(4): SC/ST/OBC reservations. Indra Sawhney (1992): 50% ceiling, creamy layer exclusion. 103rd Amendment (2019): 10% EWS — SC upheld 3:2 (2022).

**Achievements**
SC/ST representation in government services near mandated levels in many cadres. IIT/IIM accessibility for first-generation graduates. 543 reserved Lok Sabha constituencies — political representation transformed.

**Gaps**
• Creamy layer: Benefits concentrate in economically advanced families within SC/ST/OBC
• ASER learning gap: SC students 15-20% below average despite reservation access
• Stigma: Stereotyping affects beneficiary confidence and performance
• Unfilled posts: SC/ST vacancies in central services often 20-30% unfilled

**Critical Analysis**
Reservation corrects structural disadvantage but cannot substitute quality primary education. It's a floor, not a ceiling.

**Way Forward**
1. Sub-categorization: Implement Punjab & Haryana HC direction (now before Constitution Bench)
2. Pre-school investment: Anganwadi strengthening in SC/ST habitations
3. 10-year periodic review: Time-bound reassessment per Mandal Commission recommendation
4. Combine caste + economic criterion for holistic targeting""",

        """Left Wing Extremism (LWE) is a multi-dimensional security-development challenge.

**Root Causes**
50 million tribal displacements (mining, dams); Forest Rights Act 2006 poorly implemented (4.4mn claims pending); PESA (1996) not enforced; development deficit — 39% LWE districts lack all-weather roads.

**Security Achievements**
SAMADHAN doctrine (2017): Smart leadership + Aggressive strategy + Development. 2023-24: 287 Naxals killed, 1000+ surrendered — highest in two decades. COBRA battalions and Greyhounds operationally effective.

**Development Prong**
Aspirational Districts (112 districts, 90% overlap with LWE); PMGSY road connectivity (98% habitations); PM Jan Man Yojana (Rs 24,000 crore for PVTGs 2023); 5000 mobile towers in LWE areas.

**Critical Assessment**
Security gains real but is peace sustainable? Chhattisgarh forests — Maoist survivors rebuilding. Human rights concerns: encounter killings documented by NHRC.

**Way Forward**
1. Full FRA implementation — gram sabha veto on forest diversion
2. PESA enforcement: District Mineral Foundation for tribal benefit
3. MNREGA: 30% allocation increase in LWE districts
4. Fast-track courts: 10,000+ pending LWE-related cases
5. Community policing: Village Defence Committees with training + verification""",

        """India's Paris Agreement commitments exemplify developmental equity argument in climate action.

**NDC Commitments (Updated 2022)**
45% emissions intensity reduction by 2030 vs 2005; 500 GW non-fossil capacity; 50% cumulative electricity from non-fossil; Net Zero by 2070.

**Progress**
172 GW renewable (March 2024) — solar 73 GW leading; ISA (India's signature climate initiative); National Hydrogen Mission (5 MT green H2 by 2030); COP27 win — Loss and Damage Fund established.

**Development-Climate Tension**
700mn still need reliable energy; coal = 53% electricity; per-capita emissions 1.9T vs USA 14.7T; CBDR equity argument — India's cumulative emissions <5% since industrialization.

**Financing Gap**
Green transition requires Rs 2.5 trillion by 2030; developed nations failed $100bn/year pledge (OECD 2022: only $89bn delivered).

**Way Forward**
1. Carbon pricing mechanism: Domestic ETS pilot (EU-ETS model)
2. PM Surya Ghar: 10 million rooftop solar
3. Operationalize COP28 New Collective Quantified Goal ($1 trillion/year)
4. Just transition fund: retrain 300,000 coal workers in Jharkhand, Odisha
5. Technology transfer: IP waiver for climate tech in developing nations""",
    ],

    "excellent": [
        # Near-topper level, comprehensive data, multi-dimensional, strong Way Forward
        """Good governance, as defined by UNDP (1997), encompasses eight pillars: participation, rule of law, transparency, responsiveness, consensus orientation, equity, effectiveness, and accountability. India's governance journey reflects both transformative progress and persistent structural deficits.

**Transformative Achievements**
The JAM Trinity (Jan Dhan-Aadhaar-Mobile) has eliminated Rs 2.73 lakh crore in subsidy leakages — the world's largest financial inclusion achievement. DBT across 315+ schemes with 11.5 billion+ direct transfers represents a paradigm shift. GeM portal achieved Rs 4 lakh crore procurement (2023), reducing corruption in public purchasing. PM Gati Shakti integrates 16 ministries on a GIS platform, eliminating inter-departmental bottlenecks that historically cost India 2-3% logistics GDP.

**Persistent Challenges**

*Corruption*: India ranked 93/180 (Transparency International CPI 2023). The Lokpal, appointed in 2019 after 6-year delay, has filed zero major prosecutions. Whistleblower Protection Act (2014): 178 RTI activists killed with near-zero convictions.

*Administrative Capacity*: India has 18 IAS officers per crore population vs 50+ in OECD nations. ARC2 recommended 2-year minimum posting tenure; political transfers averaging 11 months in states like Haryana continue.

*Judicial Pendency*: 4.7 crore pending cases (2024); district courts average 3.4 years resolution. Per Dr. Fali Nariman: "Justice is being murdered in its own temple."

*Decentralisation Gap*: 73rd/74th Amendments (1992) transferred 29 functions to PRIs but without adequate finances (3F: Functions, Functionaries, Finances). 60% Gram Panchayats audit-non-compliant (CAG 2022).

**Structural Reform Agenda**

1. *Lokpal*: Prosecution wing + binding recommendations; state Lokayuktas in all 28 states
2. *Civil service tenure*: Statutory 2-year minimum — ARC2 recommendation by gazette notification
3. *e-Courts Phase III*: AI scheduling, video conferencing — target 50% pendency reduction by 2027
4. *Social Audit*: Mandatory for all 300+ centrally sponsored schemes on MGNREGS model
5. *Decentralisation finance*: Own-source revenue for PRIs; activity-based grants replacing tied grants

India's governance transformation must be citizen-centric, not merely digitally efficient — the measure of success is whether the last beneficiary in the last village receives their entitled services on time.""",

        """The Revolt of 1857 remains the most debated event in Indian historiography — simultaneously described as Sepoy Mutiny (British), First War of Independence (V.D. Savarkar, 1909), and Feudal Reaction (R.P. Dutt, Marxist). This contested characterisation itself reveals its multi-dimensional nature.

**Causes: Cumulative, Structural, Immediate**

*Economic*: The "drain of wealth" (Dadabhai Naoroji) de-industrialised India — handloom weavers fell from 10 million to 3 million (1850-80). Land revenue systems dispossessed zamindars and peasants alike. Doctrine of Lapse (Dalhousie) annexed Jhansi, Satara, Nagpur, Awadh — 1856 Awadh annexation alone displaced 40,000 sepoys' patron-families.

*Military*: Enfield rifle greased cartridges (pig/cow fat) — the spark on a powder keg of accumulated grievances: racial discrimination, overseas postings violating caste rules, general service enlistment act.

*Social-Religious*: Missionary activities, Hindu Widows' Remarriage Act (1856), perceived Christianisation threat; the "civilising mission" ideology insulted Indian intellectual tradition.

**Nature: Multi-Actor Analysis**
Not a single movement but a convergence: Rani Lakshmibai (dispossessed queen), Nana Sahib (pensioned ruler), Bahadur Shah Zafar (symbolic last Mughal), Awadh peasants (economic grievance) — all with different motivations. Punjab, Bengal, South barely participated — no pan-Indian consciousness.

**Significance: Constitutional and Civilisational**
• Government of India Act 1858: Company rule ended; Crown took over — administrative modernisation began
• Policy shift: Active social reform (Widow Remarriage Act) paused; non-interference in religion
• Psychological: First realisation that India could NOT be held by force alone
• Intellectual: Birth of nationalist historiography — Savarkar's reframing seeds 1947 consciousness

**Critical Assessment**
The revolt failed militarily but succeeded ideologically — it delegitimised colonialism in Indian consciousness, planting the seed that produced 1947. As Eric Stokes argued, it was "the last great peasant jacquerie in Indian history" — a social upheaval wearing nationalist clothes.

**Way Forward**
1857 teaches that economic extraction, cultural humiliation, and exclusion from governance together produce civilisational resistance — a lesson for any state managing heterogeneous, historically excluded populations.""",

        """Artificial Intelligence stands at the intersection of India's greatest development opportunity and its most profound governance challenge. With 1.4 billion people, a $10 trillion GDP ambition, and 420,000 AI practitioners (3rd globally), India's AI trajectory will shape both its own destiny and global AI governance norms.

**Transformative Opportunities**

*Agricultural Revolution*: India's 146 million farming households could benefit from AI-powered crop disease detection (drone + image recognition), soil health analysis, and price prediction models. ICAR's AI pilot reduced pest damage by 40% in Tamil Nadu cotton — scalable to Rs 1 lakh crore productivity gain.

*Healthcare Democratisation*: AIIMS AI diagnostics achieved 94% cancer detection accuracy from X-rays vs 78% for junior radiologists. Ayushman Bharat Digital Mission (530+ million health IDs) provides the data infrastructure for population-level AI health insights — specialist quality care at primary health centre level.

*Governance Efficiency*: AI in DBT fraud detection has identified Rs 8,000 crore in ghost beneficiaries. SUVAS (Supreme Court AI) assists in case categorisation. Smart traffic management in Bengaluru reduced commute times by 28%.

*Economic Potential*: McKinsey estimates Rs 37 lakh crore ($450bn) GDP addition by 2025; India's coding workforce (6mn+) provides competitive advantage in LLM development and AI services.

**Systemic Risks**

*Employment Disruption*: IMF (2024) estimates 40% of global jobs vulnerable. India's 13 million BPO workers and 4 million software testers face immediate disruption as LLMs commoditise routine cognitive tasks. Unlike industrial automation, AI affects white-collar jobs — India's growth engine.

*Algorithmic Discrimination*: MIT Media Lab study: facial recognition error rate 35% for darker skin vs 0.8% for lighter — systemic bias if used in law enforcement, credit, or hiring. India's caste-gender-class intersectionality amplifies bias risks in AI-driven governance.

*Data Colonialism*: India generates 20% of global data but 73% flows to US/China cloud servers. DPDP Act 2023 establishes consent framework but lacks data localisation teeth — India risks becoming a data colony.

*Democratic Integrity*: 2024 election AI-generated deepfakes proliferated without takedown mechanism. EU's AI Act provides regulatory template India has yet to adopt.

**Governance Framework**

1. *IndiaAI Compute*: 10,000+ GPU public cloud — prevent private monopolisation of AI infrastructure
2. *Responsible AI Act*: Mandatory algorithmic impact assessments for high-risk applications (law enforcement, credit, healthcare)
3. *AI Reskilling*: PM Kaushal Vikas 4.0 — AI literacy in 1000 ITIs; 10 million AI practitioners by 2030
4. *Sectoral Sandboxes*: Regulated innovation environments before full deployment — healthcare first
5. *Global Leadership*: India chair G20 AI principles — operationalise through binding treaty

Technology, as Heidegger warned, tends to "enframe" — reducing humans to resources. India's AI governance challenge is to ensure it remains a tool for human flourishing, not human redundancy.""",

        """India's federal structure — described by Dr. Ambedkar as "a federation of its own kind" — has evolved through cooperative, competitive, and occasionally coercive phases. The 21st century imperative of sustainable development demands a mature cooperative federalism.

**Constitutional Architecture**
Articles 245-263 distribute legislative powers through the 7th Schedule. Article 263 (ISC), Article 280 (Finance Commission), Article 370A (GST Council) represent the formal federalism architecture. Notably, India is "indestructible union of destructible states" — centre can reorganise states (Art. 3).

**Cooperative Federalism: Milestones**

*GST Council* (Art. 279A, 2017): World's largest consumption tax reform — 17 central + 13 state taxes subsumed. Each state has equal vote; 3/4 majority needed for decisions. Revenue shortfall compensation mechanism (now expired 2022) protected state finances during transition.

*15th Finance Commission*: Rs 41 lakh crore devolution; 41% divisible pool to states; disaster management grants; performance incentives for revenue mobilisation.

*NITI Aayog*: CM forums, aspirational districts — collaborative planning replacing Planning Commission's top-down diktat.

*PM Gati Shakti*: 16 ministries on one GIS platform — first true cross-federal infrastructure coordination.

**Competitive Federalism**
Ease of Doing Business rankings (state-wise); PM Awards for excellence in public administration — healthy inter-state competition driving governance improvement. Kerala health model, Gujarat industrial growth, Andhra real-time governance — policy laboratories for national replication.

**Tension Points**
• Governor's role: Tamil Nadu, Kerala, Telangana have filed suits over bill-withholding
• Centrally Sponsored Schemes: 131 CSS with 60:40 matching — financial sovereignty compromised
• Article 356 historical misuse: 130+ times, though SC in Bommai (1994) curbed it
• GST: Cess extension to 2026 without state consent — fiscal autonomy concern

**Way Forward**

1. *Constitutionalise ISC*: Mandatory annual meetings; PM chairs; binding dispute resolution
2. *CSS Rationalisation*: Reduce to 50 major schemes; "flexible funding windows" for state adaptation
3. *Governor Codification*: Constitutional amendment specifying Governor's discretionary scope
4. *State Fiscal Capacity*: Expand own-source revenue — property tax, GST buoyancy sharing
5. *Justice Sarkaria Commission (1983)* + Punchhi Commission (2010) — implement pending recommendations

India's federal maturity will ultimately be measured not by constitutional text but by whether citizens in every state receive quality services — the true test of a federation's success.""",

        """The Paris Climate Agreement (2015) placed India at the nexus of its most fundamental tension: the moral claim to development that Western nations built on carbon, versus the existential imperative to prevent catastrophic warming. India's NDC (2022 update) navigates this paradox with ambition and assertion.

**India's NDC Architecture**
• Emissions intensity: 45% reduction per GDP unit by 2030 (vs 2005) — already achieved ahead of schedule
• Non-fossil capacity: 500 GW by 2030 (172 GW achieved March 2024; solar 73 GW leading)
• Non-fossil share: 50% cumulative electricity by 2030
• Net Zero: 2070 — 20 years after China, 50 after EU — India's equity positioning

**The Equity Argument**
India's per-capita emissions: 1.9 T CO₂ vs USA (14.7T), EU (6.4T), China (7.4T). India's cumulative historical emissions since industrialisation: <5% of global total. 700+ million Indians need reliable electricity — abrupt coal phase-out risks energy poverty (SDG7 vs SDG13 tension).

**Implementation Progress**

*Renewable Revolution*: 172 GW installed — 4th globally; RE capacity grew 300% in 10 years. ISA (International Solar Alliance) — India's most successful climate diplomacy initiative; 120 member countries.

*National Hydrogen Mission*: Rs 19,744 crore; 5 MT green hydrogen by 2030 — decarbonise steel, fertiliser, shipping.

*PM Surya Ghar*: 10 million rooftop solar installations; Rs 75,000 crore investment mobilisation.

*COP27 Win*: Loss and Damage Fund establishment — India's consistent demand since 2009 Copenhagen.

**Financing Dilemma**
Green transition requires Rs 2.5 trillion by 2030. Developed nations committed $100bn/year (2009) — delivered only $89bn (OECD 2022). New Collective Quantified Goal (COP28): $1 trillion/year target — operationalisation uncertain.

**Industry Transition Challenge**
Coal provides 53% electricity — 300,000 workers in Jharkhand, Odisha, Chhattisgarh face displacement. Germany's coal transition (20 years, €40bn fund) is the model; India needs a Just Transition Mission with similar scale.

**Way Forward**

1. *Carbon Pricing*: Domestic ETS pilot (start with energy sector) — EU-ETS model; revenue for green investment
2. *Green Finance*: Sovereign Green Bond expansion (Rs 16,000 crore 2023-24 first year) + climate-aligned PSB lending mandates
3. *Technology Transfer*: Operationalise UNFCCC Technology Mechanism with IP waiver for climate solutions
4. *Just Transition*: Rs 50,000 crore National Coal Transition Fund; reskilling for 300,000 workers in 5 years
5. *Global Leadership*: India-BASIC bloc + ISA — shape global climate finance architecture from developing world perspective

India's climate action demonstrates that development and sustainability are not antithetical — they are, as PM Modi framed it at COP26, "one word: LiFE (Lifestyle for Environment)."  The challenge is converting rhetoric into structural transformation before the 2030 NDC deadline.""",

        """The evolution of India's Supreme Court from a colonial-era appeal body to an activist constitutional guardian represents one of the most dramatic judicial transformations in the democratic world — with both inspiring achievements and troubling overreaches.

**Constitutional Foundation**
Article 32 (constitutional remedies) is what Ambedkar called "the heart and soul of the Constitution." Article 136 (Special Leave Petition) gives the SC near-unlimited appellate jurisdiction. Article 142 (complete justice) — used to award Bhopal compensation, ban firecrackers, regulate liquor near highways — has no parallel globally.

**Landmark Expansions**

*Basic Structure Doctrine* (Kesavananda Bharati, 1973): 7-6 judgment — Parliament cannot amend the Constitution's basic features. Possibly the most consequential constitutional ruling in any democracy — saved India's democratic architecture during Emergency.

*PIL Revolution* (Hussainara Khatoon, 1979): Kapila Hingorani sent a letter; Bhagwati J treated it as writ petition. Transformed standing rules permanently — a prisoner's letter equals a corporate petition. Result: bonded labour freed, rivers cleaned, forests protected, children educated through court orders.

*Expanding Article 21*: Right to food (People's Union for Civil Liberties, 2001) — forced mid-day meals in schools; Right to Privacy (Puttaswamy, 2017) — 9-judge bench struck down Aadhaar mandatory linking; Section 377 reading down (Navtej Johar, 2018) — dignified citizenship for LGBTQ+ individuals.

**The Overreach Debate**

*NJAC Controversy* (2015): SC struck down National Judicial Appointments Commission — 99th Constitutional Amendment overturned. Valid concern: judiciary must be independent of executive. But 5-judge bench deciding its own appointment process undermines legitimacy. Consequence: 700+ HC vacancies unfilled as collegium-executive standoff continues.

*Governance by Judiciary*: Ordering demolition of Yamuna floodplain constructions, banning diesel vehicles — courts filling executive vacuum, but creating accountability gap (courts can order, not implement).

*Selective urgency*: Electoral Bonds listed within days; Pegasus spyware petition took years — perception of alignment with power.

**The Pendency Crisis**
4.7 crore cases; district courts average 3.4 years; Supreme Court: 70,000+ pending. The contradiction: SC as rights champion, but rights remain unvindicated for decades.

**Way Forward**

1. *Institutionalise Collegium reform*: Include civil society nominees; transparent criteria; all collegium proceedings minuted and published
2. *National Court Management System*: AI-assisted case flow management; virtual hearings for preliminary matters
3. *Mediation Act 2023*: Expand ADR — target 30% case diversion from courts by 2030
4. *All-India Judicial Services*: Fill district court vacancies fast; AIJS constitutional amendment
5. *Judicial Impact Assessment*: Every legislation must assess court case-load impact before enactment

The Supreme Court's legitimacy ultimately rests not on its powers but its credibility — and credibility requires consistency, transparency, and above all, timely justice for the millions waiting in the queue.""",

        """Reservation policy in India is simultaneously the world's most extensive affirmative action programme and its most contested — navigating 2,500 years of caste inequality against the constitutional promise of equal citizenship.

**Constitutional Architecture**
Art. 15(4): State may make special provisions for SC/ST/OBC advancement. Art. 16(4): Reservations in state employment. Art. 17: Untouchability abolished (with teeth — Protection of Civil Rights Act 1955, SC/ST Prevention of Atrocities Act 1989).

*Indra Sawhney v. Union of India (1992)*: Upheld 27% OBC reservation; imposed 50% ceiling; creamy layer exclusion; no reservation in promotions (later modified by 77th, 81st Amendments).

*103rd Amendment (2019)*: 10% EWS reservation — expanded the base to economic criterion. SC upheld 3:2 in Janhit Abhiyan (2022) — constitutional validity confirmed.

**Transformative Impact**

*Political*: 543 reserved constituencies (84 SC, 47 ST) created a critical mass of political representation that transformed national politics — the 1977 Janata coalition and subsequent OBC consolidation redrew India's electoral geography.

*Educational*: SC/ST representation in central universities at 15%/7.5% (mandated levels nearly achieved). IIT SC/ST students: 23% in 2023 — first-generation graduates from historically excluded families.

*Administrative*: SC/ST representation in Group A central services: 14.3% and 7.6% respectively — improving decision-making diversity.

**Persistent Gaps**

*Creamy Layer Capture*: Benefits concentrate in dominant sub-groups — among SCs, the "Chamar" communities disproportionately benefit; other sub-groups remain marginalized. Punjab & Haryana HC recommended sub-categorisation (2006) — now before Constitution Bench.

*Learning Outcome Gap*: ASER data shows SC students perform 15-20% below class average despite reservations — structural inequality in educational inputs, not just access.

*Private Sector Exclusion*: 93% Indians work in private sector with no reservation mandate — Dalit Indian Chamber of Commerce estimates 0.5% Dalits in senior corporate management.

*Intersectionality*: SC women face compounded disadvantage — 46% face domestic violence (NFHS-5) yet rarely benefit disproportionately from reservations.

**Way Forward**

1. *Sub-categorisation*: Constitution Bench verdict on Punjab HC direction — differentiated reservations within SC/ST
2. *Pre-school investment*: Anganwadi quality in SC/ST habitations — equalise starting points
3. *Private sector nudge*: SEBI ESG/BRSR reporting mandate + CSR inclusion norms
4. *Legal reform*: SC/ST Atrocities Act — faster trial, dedicated fast-track courts
5. *Periodic review*: 10-year mandatory sunset review per Mandal Commission's own recommendation
6. *Creamy layer recalibration*: Index to inflation — Rs 8 lakh limit set in 2013 — update to Rs 15 lakh

India's reservation debate ultimately reflects a fundamental question: does equality mean treating unequals equally, or treating them unequally to achieve equality? Ambedkar's answer was clear — the Constitution is a social document, not merely a political one.""",

        """Left Wing Extremism (LWE) is India's most complex internal security challenge precisely because it defies a purely security solution — it is a symptom of the state's failure to honour its constitutional promises to India's most marginalised citizens.

**Root Cause Analysis: Beyond the Security Lens**

The Naxalbari uprising (1967) was a response to specific, documentable grievances: landlord exploitation of sharecroppers in Darjeeling's tea gardens. Charu Majumdar's Maoist ideology provided theoretical framing, but it was agrarian injustice that provided the foot soldiers.

Today's LWE geography — 90 districts in 10 states — maps almost perfectly onto tribal India's dispossession:
• 50 million displaced since 1951 — half from tribal areas (mines, dams, national parks)
• Forest Rights Act (2006): 4.4 million claims pending, 57% of decided claims rejected
• PESA (1996): Gram sabha veto over natural resources — implemented in fewer than 30% cases
• Development deficit: 39% LWE districts lack all-weather roads; 25% lack mobile connectivity

**Security Gains: Real But Fragile**

SAMADHAN doctrine (2017) represents India's most coherent LWE security strategy:
• Smart leadership: District-level command with real-time dashboards
• Aggressive strategy: Pre-emptive strikes, intelligence-led operations
• Development: Aspirational Districts (112, 90% overlap with LWE), PM Jan Man Yojana (Rs 24,000 crore for PVTGs)

Results: LWE violence incidents: 1136 (2010) → 196 (2023); affected districts: 96 → 38. 2023-24: 287 Naxals killed, 1000+ surrendered.

**The Sustainability Question**

Security gains are impressive but sustainable only if the development deficit is addressed simultaneously. Chhattisgarh's Bastar division — heart of LWE — has 88% tribal population, richest forest cover, and India's most mineral-rich geology. The contradiction: Rs 8,000 crore Hasdeo coal mining vs tribal forest rights creates new recruits faster than CRPF operations eliminate them.

Human rights concerns: NHRC documented 31 fake encounter complaints in 2022-23; "Operation Green Hunt" criticism from civil society — alienates tribal communities.

**Way Forward: Integrated Security-Development Matrix**

1. *Full FRA implementation*: Gram sabha veto operationalised; pending 4.4 million claims resolved in 2 years
2. *PESA enforcement*: District Mineral Foundation controlled by gram sabhas; mineral revenue for community development
3. *MNREGA*: 100-day guarantee actually enforced in LWE districts; wages indexed to inflation
4. *Fast-track courts*: 10,000+ pending LWE-related cases — special benches
5. *Rehabilitation*: Surrender policy with skills training + land allocation (learn from Chhattisgarh's Niyad Nellanar scheme)
6. *Independent oversight*: National Human Rights Commission permanent camp in Bastar — accountability mechanism

The test of India's LWE strategy is not the body count but whether a tribal child in Bastar in 2035 has the same opportunity as a child in Chandigarh — that is the constitutional promise that LWE exploits.""",

        """Cooperative federalism is not merely India's constitutional aspiration — it is an operational necessity for a $3.7 trillion economy aspiring to $10 trillion by 2035.

**Constitutional Foundation: The Bargain**
India's federal architecture was designed for diversity management. Art. 1: "Union of States" — not "Federal Union" (deliberate British-era legacy of unitary bias). 7th Schedule: Union (97 subjects), State (66 subjects), Concurrent (52 subjects) — but Centre dominates through residuary power (Art. 248) and emergency provisions (Art. 352-360).

The GST Council (Art. 279A) is India's most significant federal experiment: states have equal vote on what is constitutionally a central subject (indirect taxation). Its functioning — 50 Council meetings, 1400+ decisions — demonstrates that genuine power-sharing is achievable.

**Cooperative Architecture: Building Blocks**

*Finance Commission (15th)*: Rs 41 lakh crore devolution; 41% divisible pool (highest ever); performance grants for health, education, agriculture. India's most reliable federalism instrument — constitutional, non-discretionary.

*NITI Aayog Forums*: Governing Council (all CMs + PM) — replaced Planning Commission's top-down allocation. Aspiring Haryana, Kerala, Telangana all engage differently — competitive federalism emerging.

*PM Gati Shakti*: 16 ministries on one GIS platform — India's first genuine cross-federal infrastructure coordination. Reduced project approval time from 8 months to 3 months (Ministry of Commerce data).

*National Disaster Management*: NDRF + SDRF co-funding; Cyclone Biparjoy (2023) — Centre-Gujarat coordination saved 1 lakh lives.

**Competitive Federalism: The Silent Revolution**

States are now laboratories of democracy:
• Kerala: Universal health coverage model (ASHA + Arogyakeralam) — national replication in AB-PMJAY
• Gujarat: Industrial growth (GIFT City) — national DFC model
• Andhra: Real-time governance dashboard — PM-Manthan platform inspiration
• Rajasthan: Mukhyamantri Chiranjeevi Yojana — state-funded health insurance before national scheme

**Tension Points**

*Governor controversy*: Tamil Nadu, Kerala, Telangana have moved courts over Bills withheld for months — Art. 200 has no time limit (design flaw). Nabam Rebia (2016) SC: Governor has limited discretion; but practice diverges.

*CSS burden*: 131 Centrally Sponsored Schemes; most require 60:40 matching — Odisha, Bihar divert own revenues; innovation constrained. Niti Aayog's rationalisation proposal (50 CSS) languishes.

*GST fiscal federalism*: Cess extended to 2026 without state consent — undermines the cooperative compact. Revenue from cess: Rs 1.5 lakh crore/year — purely central.

*Asymmetric capacity*: Maharashtra can implement any scheme; Bihar cannot — capacity-equalisation grants underemphasised.

**Way Forward**

1. *Constitutionalise ISC*: Mandatory annual meetings; binding recommendations; secretariat independent of Home Ministry
2. *CSS Rationalisation*: 50 umbrella schemes with "flexible funding windows" — states adapt within framework
3. *Governor codification*: Constitutional amendment — time-bound assent (30 days) mandatory
4. *Fiscal capacity building*: Urban local body finance reform — property tax + user charges; Rs 2 lakh crore potential
5. *Rajya Sabha reform*: Strengthen states' voice — restore nominated technical expert quota to elected state representatives

India's federal system has proved remarkably resilient across 75+ years — the task now is not to preserve it but to energise it for the 21st century's challenges of climate, AI, and inequality.""",

        """Swami Vivekananda's contribution to Indian nationalism and religious renaissance operates at multiple levels simultaneously — philosophical, institutional, and psychological — making him arguably the most consequential Indian intellectual between Ram Mohan Roy and Gandhi.

**The Context: Colonial Epistemic Violence**
British colonialism was not merely economic — it was epistemic. Macaulay's "Minute on Education" (1835) declared that "a single shelf of a good European library is worth the whole native literature of India and Arabia." This systematic denigration of Indian civilization had produced a colonial elite ashamed of its own heritage by the 1880s.

Vivekananda's intervention was a direct counter-offensive.

**Chicago (1893): The Global Declaration**
His address to the Parliament of Religions — "Sisters and Brothers of America" — triggered a four-minute standing ovation that remains legendary. By presenting Hinduism as the world's most tolerant religion ("We believe not only in universal toleration, but we accept all religions as true"), he inverted the colonial narrative with data from Hinduism's own liberal core.

The geopolitical impact was immediate: American newspapers called him "the greatest figure in the Parliament of Religions." The stereotype of Indian spirituality as primitive ritualism was shattered globally.

**Neo-Vedanta: Democratising the Absolute**
Vivekananda's philosophical contribution was to strip Vedanta of Brahminic exclusivity:
- "The poor man, the illiterate man — they are all my God" — Shiva in the poor
- Rejected caste as un-Vedantic: "Any system which has been the cause of decay and degradation cannot be divine"
- Ramakrishna Mission (1897): Service as worship — hospitals, schools, disaster relief — India's first institutionalised social work

**Nationalist Inspiration**
Subhas Chandra Bose: "My nationalist inspiration came from Vivekananda." Aurobindo Ghosh drew from him directly. Bal Gangadhar Tilak saw him as the spiritual backbone of political assertion.

His concept of "man-making education" (not job-making) as the prerequisite for self-rule directly influenced the national education debate that culminated in Wardha Scheme and later NEP 2020's emphasis on values.

**Psychological Liberation**
Vivekananda attacked the "Rammohan Roy syndrome" — the tendency of educated Indians to measure themselves by Western standards. "Don't be coward. Everything that is weak should be discarded" — this muscular spirituality energised a generation.

**Critical Assessment**
His was primarily a spiritual-cultural intervention, not political. He did not challenge colonial political structures directly — a gap Gandhi's practical genius had to fill. His emphasis on "Hindu civilization" also left space for later Hindu nationalist appropriation, which distorts his universalist core.

**Legacy**

*Institutional*: Ramakrishna Mission: 170+ global centres; major disaster response in India (Odisha cyclone, Bihar floods)

*State Recognition*: January 12 — National Youth Day; Swami Vivekananda statue inaugurated at JNU by PM Modi (2014)

*Global Influence*: His Vedantic universalism underpins India's yoga-meditation soft power; International Yoga Day (UN 2015) has 200+ participating nations

**Way Forward**
Vivekananda's dual legacy — spiritual universalism + service to the poor — offers a framework for India's global aspiration: not merely GDP growth, but civilizational contribution. As India claims its place in the G20 and beyond, his vision of "Give to the world and take from it. Serve the world as a mother serves her child" remains the most compelling articulation of Indian soft power.""",
    ],

}  # end STUDENT_ANSWER_TEMPLATES


# ══════════════════════════════════════════════════════════════════════════════
# EVALUATION TEMPLATES — detailed, subject-appropriate evaluations per tier
# ══════════════════════════════════════════════════════════════════════════════

EVALUATION_TEMPLATES = {
    "very_weak": {
        "relevance_score": 3.0, "intro_score": 1.5, "body_score": 2.0,
        "keyword_score": 1.0, "structure_score": 2.0, "factual_score": 1.0,
        "conclusion_score": 1.5, "word_limit_score": 3.0, "analysis_score": 1.5,
        "diagram_score": 0.0, "multidimensional_score": 1.5, "overall_score": 1.9,
        "feedback_summary": "The answer lacks any specific content, data, schemes, or constitutional provisions. It consists entirely of generic platitudes with no engagement with the actual question. This would likely score 2-3 marks out of 15 in an actual UPSC examination.",
        "strengths": ["Attempted the question", "Identified the broad theme of the topic"],
        "weaknesses": ["Zero specific data, facts, or examples provided", "No government schemes, constitutional articles, or committee names cited", "No Way Forward section — critical for UPSC scoring", "Well below word limit — indicates incomplete preparation", "No multi-dimensional analysis across any dimension"],
        "improvements": ["Study the topper reference carefully: note every data point, scheme name, and article number", "Always include at least 3 specific facts/data points in your answer", "Structure every answer: Introduction → Body (3-4 headings) → Way Forward", "Maintain minimum 200 words for 15-mark answers", "Practice writing on at least one specific example per paragraph"],
        "keywords_found": [],
        "keywords_missed": ["constitutional provisions", "specific schemes", "data statistics", "committee names", "way forward"],
        "topper_benchmark": "A topper would open with a crisp definition citing a relevant authority (UN, committee, constitutional article), immediately support with 3+ specific data points, and close with an ARC2-backed Way Forward. This answer has none of these elements.",
    },
    "weak": {
        "relevance_score": 5.0, "intro_score": 3.5, "body_score": 4.0,
        "keyword_score": 3.5, "structure_score": 3.5, "factual_score": 3.5,
        "conclusion_score": 3.0, "word_limit_score": 5.5, "analysis_score": 3.0,
        "diagram_score": 0.0, "multidimensional_score": 3.5, "overall_score": 3.8,
        "feedback_summary": "The answer shows basic familiarity with the topic and mentions 1-2 relevant schemes or facts, but lacks the depth, data, and multi-dimensional analysis required for UPSC Mains. The Way Forward is either absent or generic.",
        "strengths": ["Shows basic understanding of the topic", "Mentions at least one relevant scheme or example", "Reasonable word count attempted"],
        "weaknesses": ["Data is vague or absent — no specific numbers, years, or statistics", "Way Forward lacks specificity — no actionable, time-bound recommendations", "Missing constitutional/legal dimension — no articles or acts cited", "Analysis is descriptive rather than analytical", "Misses 3-4 key dimensions covered in topper reference answer"],
        "improvements": ["Add specific data: percentages, crore figures, years, NCRB/CAG/NSSO citations", "Cite constitutional articles or statutory provisions wherever relevant", "Way Forward must be numbered, actionable (not just 'government should act')", "Cover all 6 dimensions: political, economic, social, environmental, ethical, legal", "Compare with international/state-level examples to show multi-dimensional thinking"],
        "keywords_found": ["basic relevant terms"],
        "keywords_missed": ["specific scheme names", "data statistics", "constitutional articles", "committee recommendations"],
        "topper_benchmark": "A topper would anchor every argument with specific data, cite ARC2/Committee recommendations precisely, and analyze across all 6 dimensions. This answer covers 1-2 dimensions superficially.",
    },
    "average": {
        "relevance_score": 6.5, "intro_score": 5.5, "body_score": 6.0,
        "keyword_score": 5.5, "structure_score": 5.5, "factual_score": 5.5,
        "conclusion_score": 5.0, "word_limit_score": 7.0, "analysis_score": 5.0,
        "diagram_score": 0.0, "multidimensional_score": 5.5, "overall_score": 5.7,
        "feedback_summary": "A solid answer that covers the basics with relevant examples and some structure. However, it lacks the depth, specific data, and multi-dimensional coverage that distinguishes average answers from topper-level responses. The Way Forward needs more concrete recommendations.",
        "strengths": ["Relevant examples and scheme names cited", "Basic structure with some headings", "Reasonable word count maintained", "Covers 2-3 dimensions of the issue"],
        "weaknesses": ["Data points are superficial — missing specific numbers, years, or source citations", "Way Forward is generic rather than ARC2-backed specific recommendations", "Missing 2-3 key dimensions covered in topper reference answer", "Analysis tends toward description — 'what' rather than 'why' and 'how'"],
        "improvements": ["Add CGWB/NCRB/NSSO/CAG citation for every statistical claim", "Cite ARC2/Committee report recommendations in Way Forward", "Add constitutional Article numbers when discussing governance/rights topics", "Include environmental and legal dimensions alongside social-economic analysis", "Practice writing 'balanced view' — acknowledge complexity before suggesting solutions"],
        "keywords_found": ["several relevant terms and scheme names"],
        "keywords_missed": ["specific committee recommendations", "constitutional/statutory provisions", "comparative examples"],
        "topper_benchmark": "A topper would add specific data to every argument, cite ARC2/Sarkaria/Punchhi recommendations precisely, analyze across all 6 dimensions, and propose a phased implementation framework in Way Forward.",
    },
    "good": {
        "relevance_score": 8.0, "intro_score": 7.5, "body_score": 8.0,
        "keyword_score": 7.5, "structure_score": 8.5, "factual_score": 7.5,
        "conclusion_score": 8.0, "word_limit_score": 8.5, "analysis_score": 7.5,
        "diagram_score": 0.0, "multidimensional_score": 8.0, "overall_score": 7.9,
        "feedback_summary": "An excellent answer with strong structure, specific data, multi-dimensional analysis, and concrete Way Forward. Demonstrates UPSC examiner vocabulary and topper-level understanding. Could be improved with a diagram and slightly deeper analysis of 1-2 dimensions.",
        "strengths": ["Specific data and statistics cited throughout", "Clear headings and structured presentation", "Multi-dimensional coverage across most dimensions", "Concrete Way Forward with actionable points", "Relevant and accurate examples"],
        "weaknesses": ["No diagram or flowchart (2-3 marks potentially lost)", "1-2 dimensions slightly underdeveloped compared to topper reference", "Could add more specific committee report recommendations"],
        "improvements": ["Add a simple flowchart showing the relationship between key concepts", "Cite specific ARC2/Sarkaria recommendation numbers where applicable", "Strengthen ethical/philosophical dimension with thinker references (Gandhi, Ambedkar, Rawls)", "Consider international comparison to show global context"],
        "keywords_found": ["most key terms, schemes, and constitutional provisions"],
        "keywords_missed": ["1-2 specific committee recommendations", "philosophical/ethical thinker references"],
        "topper_benchmark": "Near topper-level response. A topper would add a diagram, cite specific committee recommendation numbers, and include one philosophical/theoretical anchor. This answer is 85-90% of the way there.",
    },
    "excellent": {
        "relevance_score": 9.5, "intro_score": 9.0, "body_score": 9.0,
        "keyword_score": 9.0, "structure_score": 9.5, "factual_score": 9.0,
        "conclusion_score": 9.0, "word_limit_score": 9.5, "analysis_score": 9.0,
        "diagram_score": 0.0, "multidimensional_score": 9.0, "overall_score": 9.1,
        "feedback_summary": "An outstanding topper-quality answer demonstrating comprehensive knowledge, nuanced analysis, and exceptional writing. All dimensions covered with specific data. Unique insights and balanced critical analysis. Would score 13-14/15 in UPSC Mains. Minor improvement possible in visual presentation.",
        "strengths": ["Comprehensive coverage of all 6 dimensions with specific data", "Excellent analytical depth — distinguishes cause from symptom", "Concrete Way Forward with numbered, actionable recommendations", "Nuanced critical analysis acknowledging complexity", "Strong use of quotes, thinkers, and international comparisons"],
        "weaknesses": ["No diagram included — 1-2 marks could be added visually", "Way Forward could include one more time-bound target"],
        "improvements": ["Add a labeled diagram (flowchart/table) — even a simple one elevates structure marks", "Specify timelines in Way Forward (by 2027, within 5 years) for stronger implementation focus"],
        "keywords_found": ["comprehensive — nearly all key terms, schemes, articles, and thinkers"],
        "keywords_missed": ["minor technical terms that could add marginal improvement"],
        "topper_benchmark": "This answer IS at topper level. The only difference between this and a Rank 1-10 answer is the absence of a diagram and slightly more time-bound Way Forward recommendations.",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# TRAINING EXAMPLE BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def build_training_example(question: str, subject: str, marks: int,
                            topper_answer: str, student_answer: str,
                            evaluation: dict, year: int, exam_type: str,
                            word_limit: int = 250) -> dict:
    """Build one training example in Alpaca instruction format."""
    student_word_count = len(student_answer.split())
    input_text = f"""Question ({subject}, {marks} marks, {word_limit}-word limit, {year} {exam_type} Mains):
{question}

Topper Reference Answer:
{topper_answer[:2000]}

Student Answer ({student_word_count} words):
{student_answer[:2500]}"""

    output_text = json.dumps({
        "relevance_score": evaluation["relevance_score"],
        "intro_score": evaluation["intro_score"],
        "body_score": evaluation["body_score"],
        "keyword_score": evaluation["keyword_score"],
        "structure_score": evaluation["structure_score"],
        "factual_score": evaluation["factual_score"],
        "conclusion_score": evaluation["conclusion_score"],
        "word_limit_score": evaluation["word_limit_score"],
        "analysis_score": evaluation["analysis_score"],
        "diagram_score": evaluation["diagram_score"],
        "multidimensional_score": evaluation["multidimensional_score"],
        "overall_score": evaluation["overall_score"],
        "marks_obtained": round(evaluation["overall_score"] / 10 * marks, 1),
        "feedback_summary": evaluation["feedback_summary"],
        "strengths": evaluation["strengths"],
        "weaknesses": evaluation["weaknesses"],
        "improvements": evaluation["improvements"],
        "keywords_found": evaluation.get("keywords_found", []),
        "keywords_missed": evaluation.get("keywords_missed", []),
        "topper_benchmark": evaluation["topper_benchmark"],
        "dimension_analysis": {
            "political": any(w in student_answer.lower() for w in ["government", "policy", "constitution", "parliament", "election", "political"]),
            "economic": any(w in student_answer.lower() for w in ["economy", "gdp", "fiscal", "agriculture", "trade", "poverty", "income"]),
            "social": any(w in student_answer.lower() for w in ["social", "education", "health", "gender", "caste", "inequality", "women"]),
            "environmental": any(w in student_answer.lower() for w in ["environment", "water", "pollution", "sustainable", "climate", "forest", "biodiversity"]),
            "ethical": any(w in student_answer.lower() for w in ["ethical", "integrity", "moral", "corruption", "transparency", "accountability"]),
            "legal": any(w in student_answer.lower() for w in ["law", "act", "article", "constitution", "supreme court", "judgment", "amendment"]),
        },
    }, indent=2, ensure_ascii=False)

    return {
        "instruction": SYSTEM_INSTRUCTION,
        "input": input_text,
        "output": output_text,
    }


# ══════════════════════════════════════════════════════════════════════════════
# GENERATORS
# ══════════════════════════════════════════════════════════════════════════════

def generate_from_db(db) -> list:
    """Generate training pairs from DB topper answers."""
    from app.models.models import TopperAnswer, Question
    examples = []
    toppers = db.query(TopperAnswer).filter(
        TopperAnswer.ocr_text.isnot(None),
        TopperAnswer.ocr_text != "",
    ).all()
    logger.info(f"DB topper answers: {len(toppers)}")

    for ta in toppers:
        if not ta.ocr_text or len(ta.ocr_text) < 100:
            continue
        question_text = "UPSC Mains question"
        subject = ta.subject or "GS - General Studies"
        marks, year, word_limit = 15, ta.year or 2023, 250
        exam_type = ta.exam_type or "UPSC"
        if ta.question_id:
            q = db.query(Question).filter(Question.id == ta.question_id).first()
            if q:
                question_text = q.text
                marks = q.marks
                subject = q.subject
                word_limit = q.word_limit or 250

        for quality in ["very_weak", "weak", "average", "good", "excellent"]:
            student_answer = random.choice(STUDENT_ANSWER_TEMPLATES[quality])
            eval_template = EVALUATION_TEMPLATES[quality].copy()
            examples.append(build_training_example(
                question=question_text, subject=subject, marks=marks,
                topper_answer=ta.ocr_text, student_answer=student_answer,
                evaluation=eval_template, year=year, exam_type=exam_type,
                word_limit=word_limit,
            ))
    return examples


def generate_from_25year_bank() -> list:
    """Generate training examples from the 25-year UPSC question bank."""
    from scripts.upsc_25year_bank import get_full_answers, get_framework_questions
    examples = []

    # From full model answers — highest quality training data
    for key, data in get_full_answers().items():
        topper_answer = data["answer"]
        question = data["question"]
        for quality in ["very_weak", "weak", "average", "good", "excellent"]:
            student_answer = random.choice(STUDENT_ANSWER_TEMPLATES[quality])
            eval_template = EVALUATION_TEMPLATES[quality].copy()
            examples.append(build_training_example(
                question=question,
                subject=data["subject"],
                marks=data["marks"],
                topper_answer=topper_answer,
                student_answer=student_answer,
                evaluation=eval_template,
                year=data["year"],
                exam_type=data["exam_type"],
                word_limit=data.get("word_limit", 250),
            ))

    # From framework questions — use framework as compressed reference answer
    for q_data in get_framework_questions():
        framework = q_data.get("model_answer_framework", [])
        if not framework:
            continue
        topper_ref = "Key Points the topper covered:\n" + "\n".join(f"• {p}" for p in framework)

        for quality in ["very_weak", "weak", "average"]:  # 3 tiers for framework-only
            student_answer = random.choice(STUDENT_ANSWER_TEMPLATES[quality])
            eval_template = EVALUATION_TEMPLATES[quality].copy()
            examples.append(build_training_example(
                question=q_data["question"],
                subject=q_data["subject"],
                marks=q_data.get("marks", 15),
                topper_answer=topper_ref,
                student_answer=student_answer,
                evaluation=eval_template,
                year=q_data["year"],
                exam_type=q_data["exam_type"],
                word_limit=q_data.get("word_limit", 250),
            ))
    return examples


def generate_from_curated_questions() -> list:
    """Generate from existing curated questions in populate_topper_db.py."""
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from populate_topper_db import CURATED_QUESTIONS, FULL_MODEL_ANSWERS as POP_FULL_ANSWERS
    except ImportError:
        logger.warning("Could not import from populate_topper_db — skipping")
        return []

    examples = []
    for key, data in POP_FULL_ANSWERS.items():
        topper_answer = data["answer"]
        for quality in ["very_weak", "weak", "average", "good", "excellent"]:
            student_answer = random.choice(STUDENT_ANSWER_TEMPLATES[quality])
            eval_template = EVALUATION_TEMPLATES[quality].copy()
            examples.append(build_training_example(
                question=data["question"], subject=data["subject"],
                marks=15, topper_answer=topper_answer,
                student_answer=student_answer, evaluation=eval_template,
                year=data["year"], exam_type=data["exam_type"],
            ))

    for q_data in CURATED_QUESTIONS:
        framework = q_data.get("model_answer_framework", [])
        if not framework:
            continue
        topper_ref = "Key Points:\n" + "\n".join(f"• {p}" for p in framework)
        for quality in ["weak", "average"]:
            student_answer = random.choice(STUDENT_ANSWER_TEMPLATES[quality])
            eval_template = EVALUATION_TEMPLATES[quality].copy()
            examples.append(build_training_example(
                question=q_data["question"], subject=q_data["subject"],
                marks=q_data.get("marks", 15), topper_answer=topper_ref,
                student_answer=student_answer, evaluation=eval_template,
                year=q_data["year"], exam_type=q_data["exam_type"],
            ))
    return examples


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    examples = []

    # Source 1: DB topper answers
    try:
        from app.database import init_db, SessionLocal
        init_db()
        db = SessionLocal()
        db_examples = generate_from_db(db)
        logger.info(f"DB examples: {len(db_examples)}")
        examples.extend(db_examples)
        db.close()
    except Exception as e:
        logger.warning(f"DB source failed: {e}")

    # Source 2: 25-year UPSC question bank (primary new source)
    bank_examples = generate_from_25year_bank()
    logger.info(f"25-year bank examples: {len(bank_examples)}")
    examples.extend(bank_examples)

    # Source 3: Existing curated questions from populate_topper_db.py
    curated_examples = generate_from_curated_questions()
    logger.info(f"Legacy curated examples: {len(curated_examples)}")
    examples.extend(curated_examples)

    # Deduplicate by (question + student_answer) so all 5 tiers per question are kept
    seen = set()
    unique = []
    for ex in examples:
        # Use question prefix + student answer prefix as key
        key = ex["input"][:300] + ex["input"][-200:]
        if key not in seen:
            seen.add(key)
            unique.append(ex)
    logger.info(f"After dedup: {len(unique)} (removed {len(examples) - len(unique)} duplicates)")

    random.shuffle(unique)

    # Write full JSONL
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for ex in unique:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    # Write sample for inspection
    sample_file = os.path.join(OUTPUT_DIR, "sample_10.jsonl")
    with open(sample_file, "w", encoding="utf-8") as f:
        for ex in unique[:10]:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    # Quality stats
    tier_counts = {}
    for ex in unique:
        score = json.loads(ex["output"]).get("overall_score", 0)
        tier = "very_weak" if score < 2.5 else "weak" if score < 4.5 else "average" if score < 6.5 else "good" if score < 8.5 else "excellent"
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    logger.info(f"\n{'='*55}")
    logger.info(f"Dataset built: {len(unique)} training examples")
    logger.info(f"Distribution: {tier_counts}")
    logger.info(f"Output: {OUTPUT_FILE}")
    logger.info(f"{'='*55}")
    logger.info("Next: Run the fine-tuner: python scripts/finetune_evaluator.py")


if __name__ == "__main__":
    main()
