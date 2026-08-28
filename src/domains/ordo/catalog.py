from __future__ import annotations

PILLAR_CATALOG = (
    {"code": "DATA", "name_sr": "Podaci", "sort_order": 10},
    {"code": "KNOWLEDGE", "name_sr": "Znanje", "sort_order": 20},
    {"code": "ANALYTICS", "name_sr": "Analitika", "sort_order": 30},
    {"code": "AI", "name_sr": "Veštačka inteligencija", "sort_order": 40},
    {"code": "HUMAN_EXPERIENCE", "name_sr": "Ljudsko iskustvo", "sort_order": 50},
)

DIMENSION_CATALOG = (
    {"code": "NATURAL_RESOURCES", "name_sr": "Prirodni resursi", "sort_order": 10},
    {"code": "CULTURAL_HERITAGE", "name_sr": "Kulturno nasleđe", "sort_order": 20},
    {"code": "LOCAL_ECONOMY", "name_sr": "Lokalna ekonomija i preduzetništvo", "sort_order": 30},
    {"code": "LABOR_MARKET", "name_sr": "Tržište rada i kompetencije", "sort_order": 40},
    {"code": "INFRASTRUCTURE_MOBILITY", "name_sr": "Infrastruktura i mobilnost", "sort_order": 50},
    {"code": "SUSTAINABILITY", "name_sr": "Održivost i upravljanje resursima", "sort_order": 60},
    {"code": "COMMUNITY_IDENTITY", "name_sr": "Zajednica i identitet destinacije", "sort_order": 70},
    {"code": "KNOWLEDGE_INNOVATION", "name_sr": "Znanje, podaci i inovacije", "sort_order": 80},
    {"code": "VISITOR_EXPERIENCE", "name_sr": "Iskustvo posetilaca i dostupnost ponude", "sort_order": 90},
)

SOURCE_TYPE_CATALOG = (
    {"code": "LOCAL_GOVERNMENT", "name_sr": "Lokalna samouprava"},
    {"code": "TOURISM_ORGANIZATION", "name_sr": "Turistička organizacija"},
    {"code": "OFFICIAL_STATISTICS", "name_sr": "Zvanična statistika"},
    {"code": "HERITAGE_INSTITUTION", "name_sr": "Institucija kulture / zaštite nasleđa"},
    {"code": "PROTECTED_AREA", "name_sr": "Upravljač zaštićenog područja"},
    {"code": "BUSINESS_REGISTRY", "name_sr": "Poslovni registri i privreda"},
    {"code": "INFRASTRUCTURE_OPERATOR", "name_sr": "Infrastrukturni operator"},
    {"code": "MOBILITY_TRANSPORT", "name_sr": "Saobraćaj i mobilnost"},
    {"code": "CIVIL_SOCIETY_COMMUNITY", "name_sr": "Civilno društvo i zajednica"},
    {"code": "SURVEY_RESEARCH", "name_sr": "Istraživanja i ankete"},
    {"code": "GIS_SPATIAL", "name_sr": "GIS i prostorni podaci"},
    {"code": "OTHER_VERIFIED", "name_sr": "Drugi verifikovani izvor"},
)

# Conceptual registry only. No formula is claimed as validated in ISI-10.
INDICATOR_CATALOG = (
    {"code": "destination_data_completeness", "name_sr": "Kompletnost podataka o destinaciji", "dimension_code": "KNOWLEDGE_INNOVATION", "pillar_code": "DATA", "unit_hint": "coverage"},
    {"code": "resource_inventory_coverage", "name_sr": "Obuhvat inventara resursa i atrakcija", "dimension_code": "NATURAL_RESOURCES", "pillar_code": "DATA", "unit_hint": "coverage"},
    {"code": "heritage_asset_activation", "name_sr": "Aktivacija i dostupnost kulturnog nasleđa", "dimension_code": "CULTURAL_HERITAGE", "pillar_code": "HUMAN_EXPERIENCE", "unit_hint": "index"},
    {"code": "natural_resource_accessibility", "name_sr": "Dostupnost prirodnih resursa za održivo korišćenje", "dimension_code": "NATURAL_RESOURCES", "pillar_code": "HUMAN_EXPERIENCE", "unit_hint": "index"},
    {"code": "local_business_linkage", "name_sr": "Povezanost turističke ponude sa lokalnom privredom", "dimension_code": "LOCAL_ECONOMY", "pillar_code": "KNOWLEDGE", "unit_hint": "index"},
    {"code": "local_value_chain_participation", "name_sr": "Učešće lokalnih aktera u lancu vrednosti destinacije", "dimension_code": "LOCAL_ECONOMY", "pillar_code": "KNOWLEDGE", "unit_hint": "ratio"},
    {"code": "workforce_capacity_readiness", "name_sr": "Spremnost radne snage i kompetencija", "dimension_code": "LABOR_MARKET", "pillar_code": "KNOWLEDGE", "unit_hint": "index"},
    {"code": "entrepreneurship_ecosystem_readiness", "name_sr": "Spremnost preduzetničkog ekosistema", "dimension_code": "LOCAL_ECONOMY", "pillar_code": "KNOWLEDGE", "unit_hint": "index"},
    {"code": "transport_accessibility", "name_sr": "Saobraćajna dostupnost destinacije", "dimension_code": "INFRASTRUCTURE_MOBILITY", "pillar_code": "HUMAN_EXPERIENCE", "unit_hint": "index"},
    {"code": "visitor_infrastructure_readiness", "name_sr": "Spremnost infrastrukture za iskustvo posetilaca", "dimension_code": "INFRASTRUCTURE_MOBILITY", "pillar_code": "HUMAN_EXPERIENCE", "unit_hint": "index"},
    {"code": "sustainability_management_readiness", "name_sr": "Spremnost upravljanja održivošću destinacije", "dimension_code": "SUSTAINABILITY", "pillar_code": "ANALYTICS", "unit_hint": "index"},
    {"code": "community_participation_readiness", "name_sr": "Spremnost zajednice za učešće u razvoju destinacije", "dimension_code": "COMMUNITY_IDENTITY", "pillar_code": "HUMAN_EXPERIENCE", "unit_hint": "index"},
    {"code": "destination_identity_coherence", "name_sr": "Koherentnost identiteta i pozicioniranja destinacije", "dimension_code": "COMMUNITY_IDENTITY", "pillar_code": "KNOWLEDGE", "unit_hint": "index"},
    {"code": "knowledge_governance_maturity", "name_sr": "Zrelost upravljanja podacima i znanjem", "dimension_code": "KNOWLEDGE_INNOVATION", "pillar_code": "DATA", "unit_hint": "maturity"},
    {"code": "visitor_experience_readiness", "name_sr": "Spremnost integrisanog iskustva posetilaca", "dimension_code": "VISITOR_EXPERIENCE", "pillar_code": "HUMAN_EXPERIENCE", "unit_hint": "index"},
)
