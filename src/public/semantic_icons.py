from __future__ import annotations

"""Semantic icon policy for public ISI pages.

The public website must never choose an icon only from a broad visual kind such as
"network" or "indicator-grid".  Icons are selected from the actual domain concept
(item key/domain/label) so repeated lists remain visually meaningful.
"""

SECTION_ITEM_ICONS: dict[tuple[str, str], str] = {
    # ISI / home
    ("institutional_method", "research"): "research",
    ("institutional_method", "develop"): "methodology",
    ("institutional_method", "apply"): "public-policy",
    ("knowledge_architecture", "isi"): "institution",
    ("knowledge_architecture", "simpa"): "social-policy",
    ("knowledge_architecture", "ordo"): "destination",
    ("knowledge_architecture", "shared"): "shared-layer",
    ("evidence_chain", "source"): "source",
    ("evidence_chain", "method"): "methodology",
    ("evidence_chain", "indicator"): "indicator",
    ("evidence_chain", "analysis"): "analytics",
    ("evidence_chain", "responsibility"): "human-responsibility",

    # SIMPA ecosystem
    ("ecosystem", "csr"): "social-work",
    ("ecosystem", "jls"): "municipality",
    ("ecosystem", "providers"): "service-provider",
    ("ecosystem", "education"): "education",
    ("ecosystem", "health"): "health",
    ("ecosystem", "employment"): "employment",
    ("ecosystem", "civil"): "civil-society",

    # SIMPA data domains
    ("data_domains", "needs"): "needs",
    ("data_domains", "poverty"): "poverty",
    ("data_domains", "family"): "family",
    ("data_domains", "crisis"): "crisis",
    ("data_domains", "older"): "older-person",
    ("data_domains", "services"): "service-access",
    ("data_domains", "capacity"): "capacity",
    ("data_domains", "cooperation"): "cooperation",
    ("data_domains", "outcomes"): "outcomes",

    # SIMPA indicators
    ("indicators", "entry_rate"): "user-entry",
    ("indicators", "duration"): "duration",
    ("indicators", "repeat"): "repeat",
    ("indicators", "territorial"): "territory",
    ("indicators", "family_vulnerability"): "family-risk",
    ("indicators", "child"): "child-wellbeing",
    ("indicators", "access"): "access-index",
    ("indicators", "intersector"): "intersector",

    # SIMPA decision questions
    ("decision_questions", "q1"): "vulnerable-groups",
    ("decision_questions", "q2"): "service-gap",
    ("decision_questions", "q3"): "outcome-check",
    ("decision_questions", "q4"): "budget-impact",

    # SIMPA implementation
    ("implementation", "p0"): "priorities",
    ("implementation", "p1"): "system-analysis",
    ("implementation", "p2"): "data-model",
    ("implementation", "p3"): "quality",
    ("implementation", "p4"): "indicator",
    ("implementation", "p5"): "prediction",
    ("implementation", "p6"): "decision",
    ("implementation", "p7"): "training",
    ("implementation", "p8"): "improve",

    # SIMPA responsible data
    ("responsible_data", "control"): "institution-control",
    ("responsible_data", "min"): "minimize-data",
    ("responsible_data", "access"): "access-control",
    ("responsible_data", "pseudo"): "pseudonym",
    ("responsible_data", "audit"): "audit",
    ("responsible_data", "human"): "professional",

    # ORDO destination system
    ("destination_system", "nature"): "nature",
    ("destination_system", "heritage"): "heritage",
    ("destination_system", "offer"): "tourism",
    ("destination_system", "economy"): "economy",
    ("destination_system", "labour"): "employment",
    ("destination_system", "space"): "infrastructure",
    ("destination_system", "environment"): "sustainability",
    ("destination_system", "community"): "community",

    # ORDO five pillars
    ("five_pillars", "data"): "database",
    ("five_pillars", "knowledge"): "book",
    ("five_pillars", "analytics"): "analytics",
    ("five_pillars", "ai"): "ai",
    ("five_pillars", "human"): "human-experience",

    # ORDO architecture
    ("architecture", "goal"): "goal",
    ("architecture", "sources"): "source-integration",
    ("architecture", "indicators"): "indicator",
    ("architecture", "model"): "model",
    ("architecture", "predict"): "prediction",
    ("architecture", "synthesis"): "synthesis",
    ("architecture", "decision"): "decision",

    # ORDO development potentials
    ("potentials", "producers"): "producer",
    ("potentials", "crafts"): "crafts",
    ("potentials", "creative"): "creative",
    ("potentials", "entrepreneurship"): "entrepreneurship",
    ("potentials", "youth"): "youth",
    ("potentials", "education"): "education",

    # ORDO scenario outcomes
    ("scenario_outcomes", "competitiveness"): "competitiveness",
    ("scenario_outcomes", "sustainability"): "sustainability",
    ("scenario_outcomes", "inclusion"): "inclusion",
    ("scenario_outcomes", "employment"): "employment",
    ("scenario_outcomes", "quality"): "quality-life",

    # ORDO human + AI learning
    ("human_ai_learning", "observe"): "observe",
    ("human_ai_learning", "learn"): "learn",
    ("human_ai_learning", "refine"): "refine",
    ("human_ai_learning", "decide"): "decision",
}

KEYWORD_ICONS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("obraz", "education", "school"), "education"),
    (("zdrav", "health", "medical"), "health"),
    (("zapošlj", "zaposl", "employment", "labour", "labor"), "employment"),
    (("siroma", "poverty", "deprivation"), "poverty"),
    (("porod", "family", "deca", "child"), "family"),
    (("nasil", "kriz", "violence", "crisis"), "crisis"),
    (("starije", "invalid", "older", "disab"), "older-person"),
    (("uslug", "service"), "service-access"),
    (("kapac", "capacity"), "capacity"),
    (("sarad", "cooperation", "partner"), "cooperation"),
    (("rezultat", "efekt", "outcome", "result"), "outcomes"),
    (("teritor", "region", "opšt", "opst", "municip"), "territory"),
    (("budž", "budz", "budget"), "budget-impact"),
    (("rizik", "risk", "ranjiv", "vulnerab"), "family-risk"),
    (("indik", "indicator"), "indicator"),
    (("analiz", "analytics"), "analytics"),
    (("model",), "model"),
    (("podat", "data"), "database"),
    (("znanj", "knowledge"), "book"),
    (("odluk", "decision"), "decision"),
    (("održ", "odrz", "sustain"), "sustainability"),
    (("kultur", "heritage"), "heritage"),
    (("turist", "tourism"), "tourism"),
    (("privred", "economy", "economic"), "economy"),
    (("infrastr", "space"), "infrastructure"),
    (("zajednic", "community", "civil"), "community"),
    (("istraž", "istraz", "research"), "research"),
    (("metodol", "method"), "methodology"),
    (("struč", "struc", "professional"), "professional"),
)

KIND_FALLBACKS = {
    "source": "source",
    "indicator": "indicator",
    "question": "question",
    "principle": "shield",
    "step": "process-step",
    "domain": "domain",
    "outcome": "outcomes",
}


def semantic_icon(
    section_key: str = "",
    item_key: str = "",
    domain_code: str = "",
    label: str = "",
    kind: str = "",
) -> str:
    exact = SECTION_ITEM_ICONS.get((section_key or "", item_key or ""))
    if exact:
        return exact

    haystack = " ".join((domain_code or "", label or "", item_key or "")).casefold()
    for needles, icon in KEYWORD_ICONS:
        if any(needle in haystack for needle in needles):
            return icon
    return KIND_FALLBACKS.get(kind or "", "domain")


def document_icon(document_type: str = "") -> str:
    value = (document_type or "").casefold()
    if "strateg" in value:
        return "strategy"
    if "akcioni" in value or "plan" in value:
        return "priorities"
    if "smernic" in value or "okvir" in value:
        return "guideline"
    if "analiz" in value:
        return "analytics"
    if "izvešt" in value or "izvest" in value or "report" in value:
        return "report"
    if "propis" in value or "zakon" in value:
        return "public-policy"
    return "file"


def activity_icon(activity_kind: str = "") -> str:
    value = (activity_kind or "").casefold()
    if "konfer" in value:
        return "conference"
    if "radion" in value:
        return "workshop"
    if "dijalog" in value:
        return "dialogue"
    if "obuk" in value or "training" in value:
        return "training"
    if "publik" in value:
        return "publication"
    return "calendar"
