/**
 * UDYAMSetu — Internationalization & Multi-Language Switcher (English / हिन्दी)
 * Provides seamless client-side language switching and stores preference in localStorage.
 */

const I18N_DICTIONARY = {
  en: {
    // Brand & Header
    "brand.title": "UDYAMSetu",
    "brand.tagline": "Concessional Finance Navigator & Eligibility Shield",
    "nav.matcher": "1. Scheme Matcher",
    "nav.compare": "2. Compare Lenders",
    "nav.navigator": "3. EMI Calculator & Partner Map",

    // Index / Form Page
    "index.hero_title": "Find Your Concessional Government Scheme",
    "index.hero_subtitle": "Answer a few straightforward profile questions. Our transparent rules engine evaluates eligibility, computes compatibility scores, and details exact qualification reasons.",
    "index.err_invalid_input": "Missing Information: Please ensure every profile field is completed (including gender, caste, education, disability, and credit status).",
    "index.err_age_range": "Invalid Age: Applicant age must be between 18 and 99 years.",
    "index.legend_profile": "Applicant Profile",
    "index.label_age": "Your Age (Years) *",
    "index.placeholder_age": "e.g. 26",
    "index.label_gender": "Gender *",
    "index.opt_gender_select": "Select gender",
    "index.opt_male": "Male",
    "index.opt_female": "Female",
    "index.opt_other": "Other",
    "index.label_caste": "Social / Caste Category *",
    "index.opt_caste_select": "Select category",
    "index.opt_sc": "Scheduled Caste (SC)",
    "index.opt_st": "Scheduled Tribe (ST)",
    "index.opt_obc": "Other Backward Class (OBC)",
    "index.opt_general": "General",
    "index.label_education": "Highest Education Qualification *",
    "index.opt_edu_select": "Select education level",
    "index.opt_edu_0": "No formal education",
    "index.opt_edu_1": "Below 8th pass",
    "index.opt_edu_2": "8th pass",
    "index.opt_edu_3": "10th pass (Matriculation)",
    "index.opt_edu_4": "12th pass (Intermediate)",
    "index.opt_edu_5": "Graduate (Degree)",
    "index.opt_edu_6": "Post-graduate & Above",
    "index.legend_special": "Special Eligibility & Credit History",
    "index.label_pwd": "Are you a Person with Disability (Divyang)? *",
    "index.label_default": "Do you have a history of bank loan defaults or settlement write-offs? *",
    "index.opt_yes": "Yes",
    "index.opt_no": "No",
    "index.opt_default_yes": "Yes (History of default)",
    "index.opt_default_no": "No (Clean credit record)",
    "index.btn_submit": "Show My Matching Schemes →",

    // Results Page
    "results.hero_title": "Your Evaluated Scheme Compatibility",
    "results.hero_subtitle": "Based on your profile, here is the transparent breakdown of which central and state concessional loan schemes match your requirements, ranked by compatibility.",
    "results.eval_profile": "Evaluated Profile:",
    "results.btn_edit": "Edit Profile",
    "results.match_compat": "Eligibility Compatibility",
    "results.match_pct": "Match",
    "results.max_loan": "Max Loan:",
    "results.interest_rate": "Interest Rate:",
    "results.scheme_id": "Scheme ID:",
    "results.why_qualify": "Why You Qualify",
    "results.areas_gap": "Areas of Non-Compliance / Gaps",
    "results.roadmap": "Application & Sanction Roadmap",
    "results.contacts": "Designated Contact & Application Channels",
    "results.portal": "Official Portal",
    "results.helpline": "Toll-Free Helpline",
    "results.email": "Official Support Email",
    "results.office": "Physical Office / Desk",
    "results.btn_calc": "Calculate EMI for this Scheme →",
    "results.btn_locate": "Locate Nearby Disbursing Branch →",
    "results.btn_check_another": "Check Another Profile",
    "results.btn_compare_all": "Compare All Lenders & Schemes →",

    // Compare Page
    "compare.hero_title": "Multi-Channel Lender & Scheme Comparison",
    "compare.hero_subtitle": "Compare borrowing options across 3 distinct routes: Central Concessional Schemes, Disbursing Partner Banks & NBFCs, and Block-Level Direct Schemes. Review interest rates, disbursal turnaround times, and moratorium windows.",
    "compare.sort_label": "Sort By:",
    "compare.sort_rate_asc": "Lowest Interest Rate (Default)",
    "compare.sort_safety_speed": "Fastest Disbursal & Lowest NPA Risk",
    "compare.sort_amount_desc": "Highest Max Loan Amount",
    "compare.sort_moratorium_desc": "Longest Moratorium Grace",
    "compare.filter_label": "Channel Route:",
    "compare.opt_all_channels": "All Lending Channels (8)",
    "compare.opt_govt": "Government Concessional",
    "compare.opt_psb": "Public Sector Bank (PSB)",
    "compare.opt_rrb": "Regional Rural Bank (RRB)",
    "compare.opt_nbfc": "NBFC-MFI Microfinance",
    "compare.opt_block": "Block-Level Direct Desk",
    "compare.th_lender": "Lender / Scheme",
    "compare.th_type": "Channel Type",
    "compare.th_rate": "Interest Rate",
    "compare.th_max_loan": "Max Loan",
    "compare.th_moratorium": "Moratorium",
    "compare.th_disbursal": "Avg. Disbursal",
    "compare.th_actions": "Actions",
    "compare.btn_check_exact": "Check Exact Eligibility Match →",
    "compare.btn_open_calc": "Open Interactive EMI Simulator",
    "compare.badge_best_rate": "Best Rate",
    "compare.badge_fastest": "Fastest & Safest",
    "compare.simulate_emi": "Simulate EMI →",
    "compare.months": "Months",
    "compare.days": "Business Days",

    // Navigator Page (EMI & Map)
    "navigator.hero_title": "Financial Navigator & Partner Locator",
    "navigator.hero_subtitle": "Estimate monthly repayments with scheme-aware moratorium rules, and locate nearby channel agencies and branches ranked by weighted fund health & NPA safety.",
    "navigator.tab_calc": "1. EMI Calculator",
    "navigator.tab_locator": "2. Nearest Channel Partner",
    "navigator.tab_quick": "3. Quick Filter",
    "navigator.calc_select_scheme": "Select Concessional Scheme *",
    "navigator.calc_loan_amt": "Required Loan Principal (₹):",
    "navigator.calc_tenure": "Repayment Tenure (Months):",
    "navigator.calc_rate": "Interest Rate (% p.a. - Scheme Set):",
    "navigator.out_monthly_emi": "Estimated Monthly EMI",
    "navigator.out_principal": "Principal Amount",
    "navigator.out_interest": "Total Interest Payable",
    "navigator.out_total": "Total Amount (Principal + Int)",
    "navigator.out_moratorium": "Moratorium Window",
    "navigator.locator_heading": "Approved Channel Partners Near Your Location",
    "navigator.btn_locate": "📍 Use My GPS Location",
    "navigator.status_ranking": "Showing partners ranked by weighted formula: distance + fund liquidity + NPA security.",
    "navigator.quick_heading": "Instant Scheme & Lender Filter",
    "navigator.quick_age": "Your Age:",
    "navigator.quick_gender": "Gender:",
    "navigator.quick_income": "Annual Household Income (₹):",
    "navigator.quick_purpose": "Loan Purpose:",
    "navigator.quick_purpose_all": "All Purposes",
    "navigator.quick_purpose_micro": "Micro / Small Business Trade",
    "navigator.quick_purpose_term": "Term Loan / Greenfield Project",
    "navigator.quick_purpose_edu": "Higher Education",
    "navigator.quick_amount": "Required Loan Amount (₹):",
    "navigator.btn_quick_find": "Find Matching Options →",
    "navigator.rec_branch": "Recommended Branch",
    "navigator.usable_branch": "Usable",
    "navigator.low_headroom": "Low Headroom",

    // Footers
    "footer.disclaimer_index": "This platform provides deterministic, explainable eligibility matching based on official guidelines. Always confirm final loan sanction with the designated bank or channel agency.",
    "footer.disclaimer_results": "This match report is generated deterministically from government scheme rule matrices. Final loan appraisal is conducted by the disbursing financial institution.",
    "footer.disclaimer_compare": "All loan figures, processing timelines, and interest rates are benchmarked against official circulars and RBI priority sector lending norms.",
    "footer.disclaimer_navigator": "Interest rates, moratorium periods, and channel partner rankings are indicative and derived from official RBI and NSFDC notifications.",
    "footer.attribution": "Developed for <strong>Smart India Hackathon (SIH)</strong> · Team <strong>UDYAMSetu</strong>"
  },

  hi: {
    // Brand & Header
    "brand.title": "UDYAMSetu",
    "brand.tagline": "रियायती वित्त नेविगेटर एवं पात्रता शील्ड",
    "nav.matcher": "1. योजना पात्रता",
    "nav.compare": "2. ऋणदाता तुलना",
    "nav.navigator": "3. ईएमआई कैलकुलेटर व मैप",

    // Index / Form Page
    "index.hero_title": "अपनी उपयुक्त सरकारी रियायती ऋण योजना खोजें",
    "index.hero_subtitle": "कुछ आसान प्रोफ़ाइल प्रश्नों के उत्तर दें। हमारा पारदर्शी नियम इंजन पात्रता की जाँच करता है, अनुकूलता स्कोर देता है और योग्यता के स्पष्ट कारण बताता है।",
    "index.err_invalid_input": "अपूर्ण जानकारी: कृपया सुनिश्चित करें कि प्रोफ़ाइल का प्रत्येक फ़ील्ड भरा गया है (लिंग, जाति, शिक्षा, दिव्यांगता और क्रेडिट स्थिति सहित)।",
    "index.err_age_range": "अमान्य आयु: आवेदक की आयु 18 से 99 वर्ष के बीच होनी चाहिए।",
    "index.legend_profile": "आवेदक प्रोफ़ाइल (Applicant Profile)",
    "index.label_age": "आपकी आयु (वर्ष) *",
    "index.placeholder_age": "उदा. 26",
    "index.label_gender": "लिंग (Gender) *",
    "index.opt_gender_select": "लिंग चुनें",
    "index.opt_male": "पुरुष (Male)",
    "index.opt_female": "महिला (Female)",
    "index.opt_other": "अन्य (Other)",
    "index.label_caste": "सामाजिक / जाति श्रेणी *",
    "index.opt_caste_select": "श्रेणी चुनें",
    "index.opt_sc": "अनुसूचित जाति (SC)",
    "index.opt_st": "अनुसूचित जनजाति (ST)",
    "index.opt_obc": "अन्य पिछड़ा वर्ग (OBC)",
    "index.opt_general": "सामान्य (General)",
    "index.label_education": "उच्चतम शैक्षणिक योग्यता *",
    "index.opt_edu_select": "शिक्षा स्तर चुनें",
    "index.opt_edu_0": "कोई औपचारिक शिक्षा नहीं",
    "index.opt_edu_1": "8वीं से कम",
    "index.opt_edu_2": "8वीं पास",
    "index.opt_edu_3": "10वीं पास (मैट्रिक)",
    "index.opt_edu_4": "12वीं पास (इंटरमीडिएट)",
    "index.opt_edu_5": "स्नातक (Graduate / Degree)",
    "index.opt_edu_6": "स्नातकोत्तर व उच्च (Post-Graduate & Above)",
    "index.legend_special": "विशेष पात्रता व क्रेडिट इतिहास",
    "index.label_pwd": "क्या आप दिव्यांग (Person with Disability) हैं? *",
    "index.label_default": "क्या आपका बैंक ऋण डिफ़ॉल्ट या सेटलमेंट राइट-ऑफ का कोई इतिहास है? *",
    "index.opt_yes": "हाँ (Yes)",
    "index.opt_no": "नहीं (No)",
    "index.opt_default_yes": "हाँ (डिफ़ॉल्ट का इतिहास है)",
    "index.opt_default_no": "नहीं (साफ़ क्रेडिट रिकॉर्ड)",
    "index.btn_submit": "मेरी पात्र योजनाएं देखें →",

    // Results Page
    "results.hero_title": "आपकी मूल्यांकित योजना अनुकूलता",
    "results.hero_subtitle": "आपकी प्रोफ़ाइल के आधार पर, यहाँ केंद्रीय और राज्य रियायती ऋण योजनाओं का पारदर्शी विवरण है जो आपकी आवश्यकताओं से मेल खाते हैं।",
    "results.eval_profile": "मूल्यांकित प्रोफ़ाइल:",
    "results.btn_edit": "प्रोफ़ाइल बदलें",
    "results.match_compat": "पात्रता अनुकूलता",
    "results.match_pct": "मिलान",
    "results.max_loan": "अधिकतम ऋण:",
    "results.interest_rate": "ब्याज दर:",
    "results.scheme_id": "योजना आईडी:",
    "results.why_qualify": "आप क्यों पात्र हैं",
    "results.areas_gap": "गैर-अनुपालन / कमियां",
    "results.roadmap": "आवेदन व स्वीकृति रोडमैप",
    "results.contacts": "नामित संपर्क एवं आवेदन चैनल",
    "results.portal": "आधिकारिक पोर्टल",
    "results.helpline": "टोल-फ्री हेल्पलाइन",
    "results.email": "आधिकारिक सहायता ईमेल",
    "results.office": "कार्यालय / संपर्क केंद्र",
    "results.btn_calc": "इस योजना के लिए EMI निकालें →",
    "results.btn_locate": "निकटतम वितरण शाखा खोजें →",
    "results.btn_check_another": "अन्य प्रोफ़ाइल जांचें",
    "results.btn_compare_all": "सभी ऋणदाताओं और योजनाओं की तुलना करें →",

    // Compare Page
    "compare.hero_title": "मल्टी-चैनल ऋणदाता एवं योजना तुलना",
    "compare.hero_subtitle": "3 विशिष्ट माध्यमों में ऋण विकल्पों की तुलना करें: केंद्रीय रियायती योजनाएं, वितरण भागीदार बैंक व एनबीएफसी, और ब्लॉक-स्तरीय प्रत्यक्ष योजनाएं। ब्याज दरों, वितरण समय और मोराटोरियम अवधि की समीक्षा करें।",
    "compare.sort_label": "क्रमबद्ध करें:",
    "compare.sort_rate_asc": "न्यूनतम ब्याज दर (डिफ़ॉल्ट)",
    "compare.sort_safety_speed": "सबसे तेज़ वितरण व कम NPA जोखिम",
    "compare.sort_amount_desc": "अधिकतम ऋण राशि",
    "compare.sort_moratorium_desc": "अधिकतम मोराटोरियम छूट",
    "compare.filter_label": "चैनल प्रकार:",
    "compare.opt_all_channels": "सभी ऋण चैनल (8)",
    "compare.opt_govt": "सरकारी रियायती (Govt Concessional)",
    "compare.opt_psb": "सार्वजनिक क्षेत्र के बैंक (PSB)",
    "compare.opt_rrb": "क्षेत्रीय ग्रामीण बैंक (RRB)",
    "compare.opt_nbfc": "एनबीएफसी-एमएफआई (NBFC-MFI)",
    "compare.opt_block": "ब्लॉक-स्तरीय प्रत्यक्ष डेस्क (Block Desk)",
    "compare.th_lender": "ऋणदाता / योजना",
    "compare.th_type": "चैनल प्रकार",
    "compare.th_rate": "ब्याज दर",
    "compare.th_max_loan": "अधिकतम ऋण",
    "compare.th_moratorium": "मोराटोरियम",
    "compare.th_disbursal": "औसत वितरण समय",
    "compare.th_actions": "कार्रवाई",
    "compare.btn_check_exact": "सटीक पात्रता जांचें →",
    "compare.btn_open_calc": "इंटरएक्टिव EMI सिम्युलेटर खोलें",
    "compare.badge_best_rate": "सर्वोत्तम दर",
    "compare.badge_fastest": "सबसे तेज़ व सुरक्षित",
    "compare.simulate_emi": "ईएमआई निकालें →",
    "compare.months": "महीने",
    "compare.days": "कार्य दिवस",

    // Navigator Page (EMI & Map)
    "navigator.hero_title": "वित्तीय नेविगेटर एवं पार्टनर लोकेटर",
    "navigator.hero_subtitle": "योजना-विशिष्ट मोराटोरियम नियमों के साथ मासिक किस्त (EMI) का अनुमान लगाएं, और फंड उपलब्धता व एनपीए सुरक्षा रैंकिंग के आधार पर नजदीकी चैनल शाखाओं का पता लगाएं।",
    "navigator.tab_calc": "1. ईएमआई कैलकुलेटर",
    "navigator.tab_locator": "2. निकटतम चैनल पार्टनर",
    "navigator.tab_quick": "3. त्वरित फ़िल्टर",
    "navigator.calc_select_scheme": "रियायती योजना चुनें *",
    "navigator.calc_loan_amt": "आवश्यक ऋण मूलधन (₹):",
    "navigator.calc_tenure": "चुकौती अवधि (महीने):",
    "navigator.calc_rate": "ब्याज दर (% प्रति वर्ष - योजना निर्धारित):",
    "navigator.out_monthly_emi": "अनुमानित मासिक किस्त (EMI)",
    "navigator.out_principal": "मूल ऋण राशि",
    "navigator.out_interest": "कुल देय ब्याज",
    "navigator.out_total": "कुल देय राशि (मूल + ब्याज)",
    "navigator.out_moratorium": "मोराटोरियम अवधि",
    "navigator.locator_heading": "आपके स्थान के निकट अनुमोदित चैनल भागीदार",
    "navigator.btn_locate": "📍 मेरा स्थान उपयोग करें (GPS Location)",
    "navigator.status_ranking": "दूरी + फंड उपलब्धता + एनपीए सुरक्षा के आधार पर क्रमबद्ध।",
    "navigator.quick_heading": "त्वरित योजना एवं ऋणदाता फ़िल्टर",
    "navigator.quick_age": "आपकी आयु:",
    "navigator.quick_gender": "लिंग:",
    "navigator.quick_income": "वार्षिक पारिवारिक आय (₹):",
    "navigator.quick_purpose": "ऋण का उद्देश्य:",
    "navigator.quick_purpose_all": "सभी उद्देश्य (All Purposes)",
    "navigator.quick_purpose_micro": "माइक्रो / छोटा व्यवसाय व दुकान",
    "navigator.quick_purpose_term": "टर्म लोन / नया उद्यम (Project)",
    "navigator.quick_purpose_edu": "उच्च शिक्षा (Higher Education)",
    "navigator.quick_amount": "आवश्यक ऋण राशि (₹):",
    "navigator.btn_quick_find": "पात्र विकल्प खोजें →",
    "navigator.rec_branch": "अनुशंसित शाखा",
    "navigator.usable_branch": "उपयोगी",
    "navigator.low_headroom": "कम सीमा",

    // Footers
    "footer.disclaimer_index": "यह प्लेटफ़ॉर्म आधिकारिक दिशानिर्देशों के आधार पर पारदर्शी पात्रता मिलान प्रदान करता है। अंतिम ऋण स्वीकृति हमेशा नामित बैंक या चैनल एजेंसी द्वारा की जाती है।",
    "footer.disclaimer_results": "यह रिपोर्ट आधिकारिक योजना नियमों के आधार पर पारदर्शी रूप से तैयार की गई है। ऋण की अंतिम जांच संबंधित वित्तीय संस्थान द्वारा की जाएगी।",
    "footer.disclaimer_compare": "सभी ऋण आंकड़े, प्रसंस्करण समय और ब्याज दरें आधिकारिक परिपत्रों और आरबीआई प्राथमिक क्षेत्र ऋण मानकों पर आधारित हैं।",
    "footer.disclaimer_navigator": "ब्याज दरें, मोराटोरियम अवधि और चैनल पार्टनर रैंकिंग सांकेतिक हैं और आधिकारिक आरबीआई एवं एनएसएफडीसी अधिसूचनाओं से ली गई हैं।",
    "footer.attribution": "स्मार्ट इंडिया हैकथॉन (SIH) के लिए विकसित · टीम <strong>UDYAMSetu</strong>"
  }
};

let currentLang = localStorage.getItem('udyamsetu_lang') || 'en';

function setLanguage(lang) {
  if (!I18N_DICTIONARY[lang]) return;
  currentLang = lang;
  localStorage.setItem('udyamsetu_lang', lang);

  // Update button active state
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });

  // Translate all elements with data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (I18N_DICTIONARY[lang][key]) {
      el.textContent = I18N_DICTIONARY[lang][key];
    }
  });

  // Translate all elements with data-i18n-html
  document.querySelectorAll('[data-i18n-html]').forEach(el => {
    const key = el.getAttribute('data-i18n-html');
    if (I18N_DICTIONARY[lang][key]) {
      el.innerHTML = I18N_DICTIONARY[lang][key];
    }
  });

  // Translate placeholders with data-i18n-placeholder
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (I18N_DICTIONARY[lang][key]) {
      el.setAttribute('placeholder', I18N_DICTIONARY[lang][key]);
    }
  });

  // Trigger page-specific re-renders if available
  if (typeof applyFilters === 'function') {
    applyFilters();
  }
  if (typeof renderPartners === 'function') {
    renderPartners();
  }
}

// Auto-run on DOM ready
window.addEventListener('DOMContentLoaded', () => {
  setLanguage(currentLang);
});
