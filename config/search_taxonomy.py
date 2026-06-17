"""Search taxonomy: the single source of truth for what we search for.

Design goals
------------
1. Broad, all-jobs discovery is FIRST-CLASS and the DEFAULT. Food service is NOT
   the governing universe anymore; it is one optional domain preset among many.
2. Adding or expanding a domain is a data edit here (or in ``industries/``),
   never a code edit in the API route layer.
3. No I/O. Pure data + tiny pure helpers. Safe to import anywhere.

The per-domain query banks and keyword sets live in the ``industries/`` package
(``industries.get_route(key)``). This module adds the broad, cross-industry
query layer that the old code never had, plus light negative-term hints used
only when a caller explicitly opts into a domain preset.
"""

from __future__ import annotations

from typing import Dict, List

DEFAULT_CITY = "Salt Lake City, UT"
DEFAULT_POSTAL = "84115"

# Broad, high-recall query seeds. Intentionally industry-neutral so that the
# default discovery run surfaces jobs from every working provider rather than
# only restaurants. ``{city}`` and ``{postal}`` are filled by the query builder.
BROAD_QUERY_TEMPLATES: List[str] = [
    "jobs near {postal} {city}",
    "hiring now {city}",
    "full time jobs {city}",
    "part time jobs {city}",
    "entry level jobs {city}",
    "warehouse jobs {city}",
    "customer service jobs {city}",
    "retail jobs {city}",
    "administrative assistant jobs {city}",
    "healthcare support jobs {city}",
    "driver jobs {city}",
    "general labor jobs {city}",
    "maintenance jobs {city}",
    "call center jobs {city}",
]

# ---------------------------------------------------------------------------
# Large cross-industry keyword bank
# Each list below covers one occupational cluster. Final exported value is a
# flat de-duplicated list (JOB_TITLE_KEYWORDS) assembled at module load time.
# All entries are lowercase plain titles — no format strings.
# ---------------------------------------------------------------------------

_FOOD_SERVICE: List[str] = [
    "server", "waiter", "waitress", "busser", "food runner", "host",
    "hostess", "line cook", "prep cook", "cook", "dishwasher", "kitchen helper",
    "chef", "sous chef", "executive chef", "pastry chef", "head chef",
    "barista", "cafe worker", "coffee specialist", "bakery associate",
    "deli worker", "grill cook", "pizza maker", "sandwich maker",
    "food service worker", "catering assistant", "catering coordinator",
    "expo", "expeditor", "steward", "kitchen steward", "dish machine operator",
    "shift lead", "shift leader", "kitchen supervisor", "restaurant supervisor",
    "dining room attendant", "table buser", "banquet server",
    "banquet setup", "food prep", "food handler", "cook helper",
    "drive-thru crew", "fast food worker", "crew member", "team member food",
    "restaurant associate", "restaurant cashier", "counter attendant",
    "short order cook", "fry cook", "grill operator", "saute cook",
    "pantry cook", "garde manger", "culinary intern", "culinary apprentice",
    "dietary aide", "dietary technician", "dietary cook", "food production worker",
    "school cafeteria worker", "hospital food service", "nutrition aide",
    "concession stand worker", "food court worker", "sushi chef",
    "baker", "bread baker", "pastry assistant", "chocolatier",
    "ice cream scooper", "smoothie maker", "juice bar attendant",
    "wine steward", "sommelier", "mixologist", "bartender", "bar back",
    "cocktail server", "bottle service", "craft beer specialist",
]

_HOSPITALITY: List[str] = [
    "front desk agent", "front desk associate", "hotel front desk",
    "hotel receptionist", "guest services agent", "guest services associate",
    "concierge", "bell person", "bellhop", "door person", "valet attendant",
    "valet parker", "shuttle driver", "hotel driver",
    "housekeeper", "room attendant", "hotel housekeeper", "hotel cleaner",
    "laundry attendant", "linen attendant", "housekeeping supervisor",
    "hotel maintenance technician", "hotel engineer", "facilities technician",
    "hotel general manager", "assistant general manager hotel", "hotel manager",
    "rooms division manager", "director of rooms", "front office manager",
    "revenue manager", "hotel sales coordinator", "group sales manager",
    "events coordinator hotel", "banquet manager", "banquet coordinator",
    "banquet captain", "event set up crew", "ballroom setup",
    "food and beverage manager", "restaurant manager", "outlet manager",
    "pool attendant", "pool server", "cabana attendant", "spa attendant",
    "spa receptionist", "massage therapist hotel", "fitness attendant",
    "night auditor", "reservations agent", "central reservations", "pbx operator",
    "housekeeping aide", "turndown attendant", "amenity runner",
    "resort associate", "resort activities coordinator",
]

_RETAIL: List[str] = [
    "retail associate", "retail sales associate", "sales floor associate",
    "cashier", "lead cashier", "head cashier", "customer service associate",
    "stock associate", "stocker", "replenishment associate", "freight team",
    "inventory associate", "merchandise associate", "merchandiser",
    "loss prevention associate", "asset protection specialist",
    "department manager retail", "assistant store manager", "store manager",
    "shift manager retail", "key holder", "keyholder",
    "visual merchandiser", "display coordinator", "window dresser",
    "fitting room attendant", "dressing room attendant",
    "grocery associate", "grocery clerk", "produce clerk", "meat clerk",
    "deli clerk", "bakery clerk", "floral clerk", "seafood clerk",
    "pharmacy technician", "pharmacy clerk", "optical associate",
    "electronics associate", "mobile phone sales associate",
    "home improvement associate", "tool rental associate", "paint associate",
    "garden center associate", "nursery associate",
    "sporting goods associate", "outdoor recreation associate",
    "pet care associate", "pet store worker", "groomer",
    "book store associate", "toy store associate",
]

_WAREHOUSE_LOGISTICS: List[str] = [
    "warehouse associate", "warehouse worker", "warehouse team member",
    "warehouse lead", "warehouse supervisor", "warehouse manager",
    "fulfillment associate", "fulfillment center worker", "picker",
    "packer", "pick and pack", "order picker", "order selector", "order filler",
    "shipping associate", "receiving associate", "shipping and receiving clerk",
    "inventory clerk", "inventory control specialist", "cycle counter",
    "forklift operator", "forklift driver", "reach truck operator",
    "cherry picker operator", "stand-up forklift", "sit-down forklift",
    "pallet jack operator", "electric pallet jack", "slip sheet operator",
    "material handler", "material mover", "freight handler",
    "freight loader", "unloader", "loader", "dock worker", "dock associate",
    "logistics coordinator", "dispatch coordinator", "dispatcher",
    "supply chain coordinator", "inventory planner", "demand planner",
    "import specialist", "export specialist", "customs broker",
    "freight broker", "carrier relations", "transportation planner",
    "operations associate logistics", "distribution center worker",
    "cross-dock associate", "sortation associate", "sorter",
    "package handler", "small package handler", "parcel handler",
]

_DRIVER_DELIVERY: List[str] = [
    "cdl driver", "cdl-a driver", "cdl-b driver", "truck driver",
    "semi truck driver", "tractor trailer driver", "flatbed driver",
    "tanker driver", "hazmat driver", "otr driver", "regional driver",
    "local driver", "delivery driver", "delivery associate",
    "courier", "messenger", "route driver", "route sales driver",
    "box truck driver", "straight truck driver", "sprinter van driver",
    "cargo van driver", "last mile delivery", "last mile associate",
    "food delivery driver", "pizza delivery driver",
    "shuttle driver", "airport shuttle driver", "paratransit driver",
    "school bus driver", "bus driver", "transit operator", "light rail operator",
    "ride share driver", "chauffeur", "limousine driver",
    "forklift driver", "reach truck driver", "order selector driver",
    "driver helper", "driver assistant", "delivery helper",
    "armored courier", "bank courier", "medical courier",
]

_CUSTOMER_SERVICE: List[str] = [
    "customer service representative", "customer service associate",
    "customer service specialist", "customer support representative",
    "customer support specialist", "customer support agent",
    "call center representative", "call center agent", "call center specialist",
    "inbound call center agent", "outbound call center agent",
    "collections agent", "billing specialist", "billing representative",
    "account service representative", "account manager entry level",
    "client services associate", "client care representative",
    "help desk analyst", "help desk specialist", "help desk agent",
    "service desk analyst", "technical support representative",
    "tier 1 support", "tier 2 support",
    "live chat agent", "chat support specialist",
    "email support representative", "ticket resolver",
    "member services representative", "benefits advisor",
    "insurance customer service", "claims representative",
    "retail customer service", "guest experience associate",
    "enrollment specialist", "intake specialist",
    "order management specialist", "returns associate",
    "after hours support agent", "weekend customer service",
    "remote customer service agent", "work from home customer service",
]

_ADMIN_OFFICE: List[str] = [
    "administrative assistant", "executive assistant", "senior executive assistant",
    "office administrator", "office coordinator", "office manager",
    "receptionist", "front desk receptionist", "medical receptionist",
    "legal receptionist", "salon receptionist", "dental receptionist",
    "data entry clerk", "data entry specialist", "data entry operator",
    "file clerk", "records clerk", "document control specialist",
    "administrative coordinator", "administrative specialist",
    "program assistant", "program coordinator", "program administrator",
    "project coordinator", "project assistant", "project administrator",
    "clerical assistant", "general clerical worker", "office clerk",
    "mailroom clerk", "mail handler", "copy center associate",
    "scheduler", "scheduling coordinator", "appointment scheduler",
    "office support specialist", "operations assistant", "operations coordinator",
    "business support analyst", "administrative analyst",
    "facilities coordinator", "building coordinator",
    "office services assistant", "reprographics specialist",
    "executive coordinator", "chief of staff assistant", "board liaison",
]

_HEALTHCARE_CLINICAL: List[str] = [
    "registered nurse", "rn", "licensed practical nurse", "lpn",
    "licensed vocational nurse", "lvn", "certified nursing assistant", "cna",
    "medical assistant", "clinical medical assistant", "back office medical assistant",
    "phlebotomist", "phlebotomy technician",
    "emergency medical technician", "emt", "paramedic",
    "surgical technician", "surgical tech", "sterile processing technician",
    "operating room technician", "or tech",
    "radiology technician", "x-ray technician", "mri technician",
    "ultrasound technician", "sonographer",
    "respiratory therapist", "respiratory therapy aide",
    "physical therapy aide", "physical therapy technician",
    "occupational therapy aide", "occupational therapy assistant",
    "speech therapy assistant", "slp assistant",
    "dental assistant", "dental hygienist", "dental receptionist", "dental sterilization tech",
    "optometry assistant", "optical technician",
    "pharmacy technician", "pharmacy aide", "pharmacy intern",
    "laboratory technician", "lab tech", "clinical lab assistant",
    "medical laboratory technician", "histotechnician",
    "nuclear medicine technologist", "cardiovascular tech",
    "polysomnographic technician", "sleep tech",
    "patient care technician", "patient care aide", "patient sitter",
    "nurse aide", "patient transporter", "hospital transporter",
    "health information technician", "medical coder", "medical biller",
    "prior authorization specialist", "referral coordinator",
    "medical records coordinator", "release of information specialist",
    "sterile processing associate", "central supply tech",
    "medical transcriptionist", "scribe", "medical scribe",
    "health coach", "wellness coordinator", "population health coordinator",
]

_HEALTHCARE_SUPPORT: List[str] = [
    "direct support professional", "dsp", "direct care worker",
    "residential support worker", "residential aide",
    "personal care aide", "pca", "home health aide", "hha",
    "homemaker aide", "companion aide", "respite care worker",
    "adult day program worker", "day program aide",
    "community support worker", "community health worker", "chw",
    "peer support specialist", "peer recovery coach", "recovery coach",
    "recovery support specialist", "peer advocate",
    "behavioral health technician", "bht", "behavioral technician",
    "registered behavior technician", "rbt", "aba technician",
    "mental health technician", "psychiatric technician", "psych tech",
    "crisis intervention specialist", "crisis counselor", "mobile crisis worker",
    "case aide", "case assistant", "benefits navigator",
    "care coordinator", "care manager", "patient advocate",
    "health navigator", "patient liaison",
    "substance use counselor assistant", "chemical dependency technician",
    "detox technician", "detox aide",
    "group home worker", "group home supervisor", "house manager",
    "transitional housing coordinator", "shelter worker", "shelter staff",
    "intake coordinator", "intake specialist social services",
    "social service assistant", "social services coordinator",
    "family support worker", "family advocate",
]

_SOCIAL_SERVICES: List[str] = [
    "case manager", "case management coordinator",
    "social worker", "licensed social worker", "bachelor social worker", "bsw",
    "msw social worker", "clinical social worker",
    "child welfare caseworker", "child protective services worker", "cps investigator",
    "foster care worker", "adoption specialist",
    "juvenile justice counselor", "probation officer assistant",
    "youth worker", "youth development specialist", "youth counselor",
    "after school program staff", "after school coordinator",
    "school social worker", "school counselor aide",
    "domestic violence advocate", "dv advocate", "victim advocate",
    "sexual assault advocate", "crisis advocate",
    "community outreach worker", "community liaison",
    "outreach coordinator", "street outreach worker", "homeless outreach",
    "food bank coordinator", "food pantry worker", "food distribution worker",
    "volunteer coordinator", "volunteer manager", "volunteer specialist",
    "grant writer", "grant coordinator", "development coordinator nonprofit",
    "program director nonprofit", "program manager nonprofit",
    "housing navigator", "housing specialist", "tenant services coordinator",
    "employment specialist", "job developer", "vocational counselor",
    "disability services coordinator", "ada coordinator",
    "aging services coordinator", "senior services coordinator",
    "meal delivery coordinator", "meals on wheels driver",
]

_SALES: List[str] = [
    "sales representative", "sales associate", "sales consultant",
    "inside sales representative", "inside sales agent",
    "outside sales representative", "field sales representative",
    "business development representative", "bdr", "sdr", "sales development rep",
    "account executive", "junior account executive", "mid-market account executive",
    "account manager", "territory manager", "territory sales representative",
    "retail sales representative", "consumer sales agent",
    "insurance sales agent", "insurance producer", "licensed insurance agent",
    "real estate agent", "real estate assistant", "buyer's agent",
    "mortgage loan officer", "loan originator", "mortgage consultant",
    "financial advisor", "financial planner", "financial services representative",
    "investment advisor assistant", "brokerage associate",
    "car sales associate", "automotive sales consultant",
    "solar sales consultant", "energy consultant", "green energy sales",
    "pharmaceutical sales rep", "medical sales representative", "device sales rep",
    "telemarketer", "phone sales representative", "tele-sales agent",
    "door to door sales", "direct sales representative",
    "advertising sales representative", "media sales representative",
    "sponsorship sales coordinator", "event sales coordinator",
    "luxury sales associate", "high-end retail sales",
    "franchise sales consultant", "franchise development representative",
]

_SKILLED_TRADES: List[str] = [
    "electrician", "journeyman electrician", "master electrician",
    "electrician apprentice", "electrical helper",
    "plumber", "journeyman plumber", "master plumber", "plumber apprentice",
    "pipefitter", "steamfitter", "gas fitter",
    "hvac technician", "hvac installer", "hvac service tech",
    "refrigeration technician", "boiler technician",
    "carpenter", "finish carpenter", "rough carpenter", "framer",
    "cabinet maker", "millwork installer",
    "welder", "tig welder", "mig welder", "structural welder",
    "pipewelding technician", "welding inspector",
    "ironworker", "structural ironworker", "reinforcing ironworker",
    "sheet metal worker", "hvac sheet metal fabricator",
    "roofer", "roofing laborer", "roofing installer",
    "insulation installer", "insulator",
    "glazier", "glass installer", "window installer",
    "tile setter", "ceramic tile installer", "flooring installer",
    "hardwood floor installer", "carpet installer",
    "painter", "commercial painter", "industrial painter", "sandblaster",
    "drywall installer", "drywall finisher", "plasterer",
    "masonry worker", "bricklayer", "block mason", "concrete finisher",
    "cement mason", "terrazzo worker",
    "elevator mechanic", "elevator installer", "elevator helper",
    "locksmith", "locksmith apprentice",
]

_CONSTRUCTION: List[str] = [
    "construction laborer", "general laborer", "construction worker",
    "site laborer", "job site helper", "construction helper",
    "project manager construction", "superintendent construction",
    "foreman", "job foreman", "site supervisor",
    "civil engineer field technician", "survey technician", "land surveyor",
    "estimator construction", "construction estimator",
    "safety coordinator construction", "safety officer",
    "demolition worker", "demo laborer",
    "excavator operator", "backhoe operator", "bulldozer operator",
    "crane operator", "boom lift operator", "scissor lift operator",
    "equipment operator", "heavy equipment operator",
    "concrete laborer", "concrete pump operator", "shotcrete nozzleman",
    "earthwork laborer", "grading crew", "grading operator",
    "traffic control flagger", "flagger", "traffic control specialist",
    "construction inspector", "building inspector", "code inspector",
    "landscape laborer", "landscape installer", "irrigation installer",
    "underground utility worker", "water main worker", "pipe layer",
    "solar installer", "solar panel installer", "solar technician",
]

_MANUFACTURING: List[str] = [
    "production worker", "manufacturing associate", "line worker",
    "assembly line worker", "assembler", "general assembler",
    "machine operator", "cnc machine operator", "cnc machinist",
    "press operator", "punch press operator", "stamping press operator",
    "injection molding operator", "extrusion operator",
    "quality control inspector", "quality assurance inspector", "qc technician",
    "quality technician", "metrology technician",
    "maintenance technician manufacturing", "industrial maintenance mechanic",
    "millwright", "equipment maintenance technician",
    "tooling technician", "die maker", "mold maker",
    "electronic assembly technician", "pcb assembler", "smt operator",
    "production supervisor", "shift supervisor manufacturing",
    "production planner", "scheduler manufacturing",
    "process technician", "process engineer technician",
    "packaging operator", "packaging machine operator", "packaging associate",
    "material handler manufacturing", "parts runner",
    "industrial painter manufacturing", "powder coat painter",
    "heat treat operator", "surface finish technician",
    "welder fabricator", "structural fabricator", "metal fabricator",
]

_MAINTENANCE_JANITORIAL: List[str] = [
    "janitor", "custodian", "custodial worker", "building custodian",
    "housekeeping aide", "cleaning technician", "commercial cleaner",
    "office cleaner", "industrial cleaner", "environmental services worker",
    "evs technician", "hospital cleaner", "hospital housekeeper",
    "janitorial supervisor", "custodial supervisor", "lead custodian",
    "groundskeeper", "grounds maintenance worker", "grounds crew",
    "facility maintenance worker", "building maintenance technician",
    "maintenance helper", "maintenance associate", "maintenance tech",
    "apartment maintenance technician", "property maintenance technician",
    "hvac maintenance technician", "preventive maintenance technician",
    "pool maintenance technician", "pool tech",
    "equipment cleaner", "vehicle cleaner", "fleet cleaner",
    "window cleaner", "power washer", "pressure washer",
    "carpet cleaner", "carpet cleaning technician",
    "waste management worker", "sanitation worker", "recycling coordinator",
    "litter crew", "park maintenance worker",
]

_SECURITY: List[str] = [
    "security guard", "security officer", "security associate",
    "unarmed security officer", "armed security officer",
    "campus security officer", "hospital security officer",
    "retail security officer", "loss prevention officer",
    "site security officer", "patrol officer security",
    "event security staff", "event security guard",
    "access control officer", "gate security",
    "overnight security guard", "weekend security officer",
    "security dispatcher", "security supervisor", "lead security officer",
    "surveillance officer", "cctv operator",
    "private investigator", "pi", "skip tracer",
    "alarm technician", "security systems installer",
    "fire watch officer", "fire prevention monitor",
    "parking enforcement officer", "parking attendant",
]

_EDUCATION_CHILDCARE: List[str] = [
    "preschool teacher", "preschool aide", "preschool assistant",
    "kindergarten teacher", "elementary teacher", "teacher",
    "special education aide", "special education paraprofessional", "paraeducator",
    "teaching assistant", "teacher's aide", "classroom assistant",
    "instructional aide", "instructional assistant",
    "substitute teacher", "long-term substitute",
    "childcare worker", "daycare worker", "daycare teacher",
    "infant room teacher", "toddler room teacher",
    "after school worker", "after school teacher", "after school tutor",
    "camp counselor", "summer camp counselor", "recreation counselor",
    "youth group leader", "youth program leader",
    "tutor", "private tutor", "academic tutor", "math tutor",
    "reading specialist assistant", "literacy aide",
    "school bus monitor", "bus aide",
    "school lunch aide", "cafeteria monitor",
    "library aide", "media center assistant",
    "college advisor assistant", "admissions coordinator",
    "early childhood educator", "ece worker",
]

_FINANCE_ACCOUNTING: List[str] = [
    "bookkeeper", "full charge bookkeeper", "accounting clerk",
    "accounts payable clerk", "accounts payable specialist",
    "accounts receivable clerk", "accounts receivable specialist",
    "payroll clerk", "payroll specialist", "payroll administrator",
    "billing clerk", "billing specialist", "invoicing specialist",
    "staff accountant", "junior accountant", "accountant",
    "tax preparer", "tax associate", "tax specialist",
    "auditor", "internal auditor", "audit associate",
    "financial analyst", "junior financial analyst",
    "budget analyst", "cost analyst", "pricing analyst",
    "credit analyst", "underwriter", "underwriting assistant",
    "loan processor", "mortgage processor", "loan officer assistant",
    "teller", "bank teller", "credit union teller",
    "personal banker", "retail banker", "relationship banker",
    "branch manager banking", "assistant branch manager",
    "investment operations associate", "trade support analyst",
    "treasury analyst", "cash management analyst",
    "finance coordinator", "finance assistant",
    "collections representative", "debt collector",
]

_IT_TECH: List[str] = [
    "help desk technician", "it support technician", "desktop support technician",
    "technical support specialist", "it specialist", "it technician",
    "systems administrator", "sysadmin", "junior sysadmin",
    "network administrator", "network technician", "network support",
    "it analyst", "business analyst it", "systems analyst",
    "database administrator", "database analyst", "sql developer",
    "software developer", "software engineer", "junior software developer",
    "web developer", "front-end developer", "back-end developer", "full-stack developer",
    "mobile developer", "ios developer", "android developer",
    "devops engineer", "site reliability engineer", "cloud engineer",
    "cybersecurity analyst", "information security analyst", "security operations analyst",
    "data analyst", "data scientist", "machine learning engineer",
    "bi developer", "business intelligence analyst",
    "technical writer", "documentation specialist",
    "it project manager", "scrum master", "agile coach",
    "qa analyst", "quality assurance engineer", "software tester",
    "ui designer", "ux designer", "product designer",
    "product manager", "technical product manager",
    "computer technician", "computer repair technician", "field technician it",
    "telecommunications technician", "fiber technician", "cable installer",
]

_MARKETING_CREATIVE: List[str] = [
    "marketing coordinator", "marketing assistant", "marketing associate",
    "digital marketing specialist", "seo specialist", "sem specialist",
    "social media coordinator", "social media manager", "social media specialist",
    "content creator", "content writer", "content strategist",
    "copywriter", "copy editor", "proofreader",
    "graphic designer", "junior graphic designer", "visual designer",
    "brand coordinator", "brand ambassador",
    "event coordinator", "event planner", "event marketing coordinator",
    "email marketing specialist", "crm specialist",
    "public relations coordinator", "pr specialist", "media relations",
    "communications coordinator", "communications specialist",
    "video producer", "videographer", "video editor",
    "photographer", "studio photographer", "product photographer",
    "art director", "creative director assistant",
    "advertising coordinator", "media buyer", "media planner",
    "influencer marketing coordinator",
    "market research coordinator", "consumer insights analyst",
    "trade show coordinator", "promotions coordinator",
]

_HR: List[str] = [
    "hr assistant", "human resources assistant", "hr coordinator",
    "human resources coordinator", "hr generalist", "hr specialist",
    "recruiter", "talent acquisition specialist", "corporate recruiter",
    "sourcer", "technical recruiter",
    "hr administrator", "personnel administrator",
    "benefits administrator", "benefits coordinator", "benefits specialist",
    "compensation analyst", "compensation specialist",
    "training coordinator", "learning and development specialist",
    "onboarding coordinator", "employee experience coordinator",
    "hr business partner", "hrbp", "labor relations specialist",
    "employee relations specialist", "workplace investigator",
    "payroll hr coordinator", "workforce planning analyst",
    "applicant tracking system admin", "ats admin",
    "hr data analyst", "people analytics specialist",
]

_LEGAL: List[str] = [
    "legal assistant", "legal secretary", "legal administrative assistant",
    "paralegal", "junior paralegal", "litigation paralegal",
    "corporate paralegal", "real estate paralegal",
    "court clerk", "court reporter", "court transcriptionist",
    "docket clerk", "case manager legal", "file clerk legal",
    "legal receptionist", "law firm receptionist",
    "contracts administrator", "contracts specialist", "contracts coordinator",
    "compliance coordinator", "compliance specialist", "compliance analyst",
    "regulatory specialist", "regulatory affairs coordinator",
    "title examiner", "title searcher", "title clerk",
    "escrow officer", "escrow assistant",
    "immigration paralegal", "immigration specialist",
    "intellectual property assistant", "patent clerk",
    "legal billing specialist", "legal collections specialist",
]

_AUTOMOTIVE: List[str] = [
    "automotive technician", "auto mechanic", "master technician automotive",
    "lube technician", "quick lube technician", "oil change technician",
    "tire technician", "tire installer",
    "automotive service advisor", "service writer", "service advisor",
    "auto parts specialist", "auto parts counter person", "parts driver",
    "car detailer", "auto detailer", "detailing technician",
    "car wash attendant", "auto wash technician",
    "lot attendant", "lot porter", "automotive porter",
    "automotive body technician", "collision repair technician", "auto body painter",
    "frame technician", "estimator collision",
    "diesel mechanic", "diesel technician", "heavy truck mechanic",
    "fleet mechanic", "fleet technician", "fleet manager",
    "motorcycle mechanic", "small engine mechanic",
    "glass technician auto", "windshield installer",
    "alignment technician", "brake technician",
]

_BEAUTY_PERSONAL_CARE: List[str] = [
    "hair stylist", "hairdresser", "cosmetologist",
    "barber", "master barber", "barber apprentice",
    "nail technician", "manicurist", "pedicurist",
    "esthetician", "skincare specialist", "facial specialist",
    "makeup artist", "cosmetics artist",
    "waxing specialist", "eyebrow specialist", "lash technician",
    "spa therapist", "body wrap technician", "hydrotherapy technician",
    "massage therapist", "licensed massage therapist", "lmt",
    "salon coordinator", "salon receptionist", "spa coordinator",
    "salon assistant", "shampoo assistant",
    "colorist", "hair colorist", "hair extension specialist",
    "beauty advisor", "beauty consultant", "cosmetics sales associate",
    "tanning salon associate",
]

_LANDSCAPING: List[str] = [
    "landscaper", "landscape laborer", "landscape worker",
    "groundskeeper", "grounds maintenance", "grounds worker",
    "lawn care specialist", "lawn technician", "grass cutting crew",
    "irrigation technician", "irrigation installer", "irrigation repair",
    "tree trimmer", "arborist assistant", "tree removal worker",
    "tree climber", "tree service worker",
    "hardscape installer", "paver installer", "retaining wall installer",
    "mulch installer", "bark crew", "landscape maintenance crew",
    "snow removal worker", "snow plow operator", "de-icing technician",
    "pest control technician", "exterminator", "fumigator",
    "landscape designer", "landscape project manager",
    "nursery worker", "greenhouse worker", "horticulturist assistant",
    "agricultural worker", "farm laborer", "crop worker",
]

_BANKING_FINANCE_FRONT: List[str] = [
    "bank teller", "credit union teller", "head teller",
    "personal banker", "universal banker", "retail banker",
    "branch associate", "new accounts specialist",
    "financial services associate", "investment associate",
    "insurance agent", "life insurance agent", "property casualty agent",
    "insurance broker", "insurance underwriter assistant",
    "claims adjuster", "claims specialist", "claims analyst",
    "loss control specialist", "risk management coordinator",
    "real estate agent", "real estate associate", "buyer agent",
    "listing coordinator", "transaction coordinator", "closing coordinator",
    "property manager", "assistant property manager",
    "leasing agent", "leasing consultant", "apartment leasing agent",
    "hoa coordinator", "community association manager",
    "mortgage closer", "title officer",
]

_GOVERNMENT_NONPROFIT: List[str] = [
    "government clerk", "government administrative specialist",
    "public works laborer", "utilities worker", "water plant operator",
    "wastewater plant operator", "treatment plant operator",
    "code enforcement officer", "building code officer",
    "animal control officer", "animal shelter worker",
    "public health aide", "public health worker",
    "parks and recreation worker", "recreation aide",
    "city clerk", "county clerk", "court clerk",
    "postal worker", "mail carrier", "usps associate",
    "transit worker", "bus operator", "light rail operator",
    "nonprofit program coordinator", "nonprofit case manager",
    "nonprofit outreach worker", "development associate nonprofit",
    "grant administrator", "grant specialist",
    "community organizer", "policy analyst assistant",
    "public affairs coordinator", "government relations coordinator",
    "eligibility worker", "benefits eligibility specialist",
    "employment services worker", "workforce development specialist",
]

_MISC_CROSS_INDUSTRY: List[str] = [
    "general manager", "assistant manager", "store manager",
    "operations manager", "business operations associate",
    "project manager", "senior project coordinator",
    "quality assurance specialist", "quality control specialist",
    "safety specialist", "safety coordinator",
    "environmental health safety technician", "ehs specialist",
    "logistics analyst", "supply chain analyst",
    "purchasing coordinator", "procurement specialist", "buyer",
    "customer success manager", "customer experience specialist",
    "trainer", "corporate trainer", "training specialist",
    "instructional designer", "learning specialist",
    "interpreter", "translator", "language specialist",
    "sign language interpreter",
    "transcriptionist", "captioner",
    "research assistant", "research coordinator",
    "survey researcher", "data collector",
    "ticket agent", "gate agent", "reservation agent",
    "flight attendant", "passenger service agent",
    "rental car associate", "car rental agent",
    "hotel shuttle driver", "airport driver",
    "event staff", "event attendant", "festival worker",
    "sports facility worker", "arena worker", "stadium staff",
    "box office associate", "ticket seller",
    "museum guide", "gallery attendant", "docent",
    "fitness instructor", "group fitness instructor", "personal trainer",
    "yoga instructor", "pilates instructor",
    "aquatics instructor", "swim instructor", "lifeguard",
    "recreation specialist", "activity aide",
    "animal caretaker", "kennel worker", "dog groomer",
    "dog trainer", "veterinary assistant", "vet tech",
    "animal shelter volunteer coordinator",
    "funeral home attendant", "funeral service worker",
    "cemetery worker", "cremation technician",
    "laundry worker", "linen service worker", "dry cleaning associate",
    "seamstress", "alterations specialist", "tailor",
    "photo lab technician", "darkroom technician",
    "print shop associate", "offset press operator", "digital press operator",
    "bindery worker", "fulfillment associate printing",
    "moving company laborer", "mover helper", "furniture mover",
    "piano mover", "white glove delivery specialist",
    "recycling worker", "material recovery associate",
    "composting worker", "environmental aide",
    "gaming dealer", "casino dealer", "slot technician",
    "gaming floor attendant", "cage cashier casino",
    "correctional officer", "detention officer", "prison guard",
    "juvenile corrections officer",
    "military recruiter", "national guard recruiter",
    "home inspector", "radon technician", "mold inspector",
    "energy auditor", "energy efficiency technician",
    "locksmith technician", "safe technician",
    "vending machine technician", "coin operated machine technician",
    "machine vending route driver", "vending route technician",
    "translation services coordinator", "multilingual customer service",
]

def _build_keyword_bank() -> List[str]:
    """Assemble all category sublists into one flat de-duplicated list."""
    all_categories = [
        _FOOD_SERVICE, _HOSPITALITY, _RETAIL, _WAREHOUSE_LOGISTICS,
        _DRIVER_DELIVERY, _CUSTOMER_SERVICE, _ADMIN_OFFICE,
        _HEALTHCARE_CLINICAL, _HEALTHCARE_SUPPORT, _SOCIAL_SERVICES,
        _SALES, _SKILLED_TRADES, _CONSTRUCTION, _MANUFACTURING,
        _MAINTENANCE_JANITORIAL, _SECURITY, _EDUCATION_CHILDCARE,
        _FINANCE_ACCOUNTING, _IT_TECH, _MARKETING_CREATIVE, _HR, _LEGAL,
        _AUTOMOTIVE, _BEAUTY_PERSONAL_CARE, _LANDSCAPING,
        _BANKING_FINANCE_FRONT, _GOVERNMENT_NONPROFIT, _MISC_CROSS_INDUSTRY,
    ]
    seen: set = set()
    result: List[str] = []
    for category in all_categories:
        for kw in category:
            kw = kw.strip().lower()
            if kw and kw not in seen:
                seen.add(kw)
                result.append(kw)
    return result


JOB_TITLE_KEYWORDS: List[str] = _build_keyword_bank()

# Optional negative-term hints applied ONLY when a domain preset is explicitly
# selected. In broad mode nothing here is used, so broad mode never rejects a
# job for being "the wrong industry". The authoritative per-industry term sets
# remain in ``industries/``; this is a small convenience mirror for callers that
# do not want to import the industries package.
DOMAIN_NEGATIVE_TERMS: Dict[str, List[str]] = {
    "food_service": [
        "registered nurse", "software engineer", "cdl", "forklift",
    ],
}


def list_domains() -> List[str]:
    """Domain keys that callers may use as an explicit preset.

    Sourced from the industries registry when available so the two stay in sync,
    with a static fallback if the registry cannot be imported.
    """
    try:
        from industries import list_industries

        return list(list_industries())
    except Exception:
        return ["food_service", "hospitality", "sales", "customer_service", "care_social", "retail_ops"]


def broad_queries(city: str = DEFAULT_CITY, postal: str = DEFAULT_POSTAL) -> List[str]:
    """Render the broad query templates for a location AND one query per keyword.

    Returns BOTH the existing location-only browse templates AND one query per
    keyword in ``JOB_TITLE_KEYWORDS`` in the form ``"{keyword} jobs {city}"``.
    Pure function — no I/O. Callers that need a capped sample should pass the
    full list to ``build_queries`` which applies the cap/rotation.
    """
    city = (city or DEFAULT_CITY).strip()
    postal = (postal or DEFAULT_POSTAL).strip()
    out: List[str] = []
    # Location-only broad templates (industry-neutral browse queries)
    for template in BROAD_QUERY_TEMPLATES:
        try:
            out.append(template.format(city=city, postal=postal).strip())
        except Exception:
            out.append(template)
    # One query per keyword in the full bank
    for keyword in JOB_TITLE_KEYWORDS:
        out.append(f"{keyword} jobs {city}")
    return out
