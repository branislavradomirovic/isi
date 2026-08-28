from __future__ import annotations

DIMENSION_CATALOG = (
    {"code": "SOCIAL_NEEDS", "name_sr": "Socijalne potrebe stanovništva", "sort_order": 10},
    {"code": "POVERTY", "name_sr": "Siromaštvo i materijalna ugroženost", "sort_order": 20},
    {"code": "FAMILY_CHILDREN_YOUTH", "name_sr": "Porodica, deca i mladi", "sort_order": 30},
    {"code": "VIOLENCE_CRISIS", "name_sr": "Nasilje i krizne situacije", "sort_order": 40},
    {"code": "OLDER_DISABLED", "name_sr": "Starije osobe i osobe sa invaliditetom", "sort_order": 50},
    {"code": "SERVICE_ACCESS", "name_sr": "Dostupnost socijalnih usluga", "sort_order": 60},
    {"code": "SYSTEM_CAPACITY", "name_sr": "Kapaciteti lokalnog sistema", "sort_order": 70},
    {"code": "INTERSECTORAL_COOPERATION", "name_sr": "Međusektorska saradnja", "sort_order": 80},
    {"code": "OUTCOMES_EFFECTS", "name_sr": "Rezultati i efekti usluga", "sort_order": 90},
)

SOURCE_TYPE_CATALOG = (
    {"code": "LOCAL_GOVERNMENT", "name_sr": "Jedinica lokalne samouprave"},
    {"code": "SOCIAL_WORK_CENTER", "name_sr": "Centar za socijalni rad"},
    {"code": "SOCIAL_SERVICE_PROVIDER", "name_sr": "Pružalac usluga socijalne zaštite"},
    {"code": "EDUCATION", "name_sr": "Obrazovanje"},
    {"code": "HEALTH", "name_sr": "Zdravstvo"},
    {"code": "EMPLOYMENT", "name_sr": "Zapošljavanje"},
    {"code": "HOUSING", "name_sr": "Stanovanje"},
    {"code": "CIVIL_SOCIETY", "name_sr": "Civilno društvo"},
    {"code": "DEMOGRAPHY", "name_sr": "Demografija i statistika"},
)

# These are conceptual registry entries from the SIMPA source material. ISI-08 does not
# claim validated formulas. Formulas and model-backed calculations belong to later work.
INDICATOR_CATALOG = (
    {"code": "new_client_entry_rate", "name_sr": "Stopa ulaska novih korisnika u sistem socijalne zaštite", "dimension_code": "SOCIAL_NEEDS", "unit_hint": "rate"},
    {"code": "average_support_duration", "name_sr": "Prosečno trajanje korišćenja pojedinih prava i usluga", "dimension_code": "SOCIAL_NEEDS", "unit_hint": "duration"},
    {"code": "repeat_intervention_rate", "name_sr": "Učestalost ponovljenih intervencija", "dimension_code": "OUTCOMES_EFFECTS", "unit_hint": "rate"},
    {"code": "long_term_assistance_dependency_risk", "name_sr": "Rizik od dugotrajne zavisnosti od socijalne pomoći", "dimension_code": "POVERTY", "unit_hint": "risk_index"},
    {"code": "territorial_social_risk_concentration", "name_sr": "Teritorijalna koncentracija socijalnih rizika", "dimension_code": "SOCIAL_NEEDS", "unit_hint": "index"},
    {"code": "family_vulnerability_index", "name_sr": "Indeks porodične ranjivosti", "dimension_code": "FAMILY_CHILDREN_YOUTH", "unit_hint": "index"},
    {"code": "child_wellbeing_risk_index", "name_sr": "Indeks dečje dobrobiti i ugroženosti", "dimension_code": "FAMILY_CHILDREN_YOUTH", "unit_hint": "index"},
    {"code": "older_people_social_inclusion_index", "name_sr": "Indeks socijalne uključenosti starijih osoba", "dimension_code": "OLDER_DISABLED", "unit_hint": "index"},
    {"code": "social_service_access_index", "name_sr": "Indeks dostupnosti socijalnih usluga", "dimension_code": "SERVICE_ACCESS", "unit_hint": "index"},
    {"code": "preventive_crisis_intervention_ratio", "name_sr": "Odnos preventivnih i kriznih intervencija", "dimension_code": "OUTCOMES_EFFECTS", "unit_hint": "ratio"},
    {"code": "local_social_service_coverage", "name_sr": "Obuhvat stanovništva lokalnim uslugama socijalne zaštite", "dimension_code": "SERVICE_ACCESS", "unit_hint": "rate"},
    {"code": "community_service_development_index", "name_sr": "Indeks razvijenosti usluga u zajednici", "dimension_code": "SERVICE_ACCESS", "unit_hint": "index"},
    {"code": "intersectoral_cooperation_index", "name_sr": "Indeks međusektorske saradnje", "dimension_code": "INTERSECTORAL_COOPERATION", "unit_hint": "index"},
    {"code": "vulnerable_group_social_inclusion_index", "name_sr": "Indeks socijalne inkluzije posebno osetljivih grupa", "dimension_code": "OUTCOMES_EFFECTS", "unit_hint": "index"},
    {"code": "investment_social_effect_ratio", "name_sr": "Odnos ulaganja lokalne samouprave i ostvarenih društvenih efekata", "dimension_code": "SYSTEM_CAPACITY", "unit_hint": "ratio"},
)

__all__ = ["DIMENSION_CATALOG", "SOURCE_TYPE_CATALOG", "INDICATOR_CATALOG"]
