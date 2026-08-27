from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.public_content.sections import PublicPageSection, PublicPageSectionItem, PublicPageSectionItemTranslation, PublicPageSectionTranslation


@dataclass(frozen=True)
class PublicSectionItemView:
    key: str
    kind: str
    domain_code: str
    label: str
    value: str
    description: str
    featured: bool


@dataclass(frozen=True)
class PublicSectionView:
    key: str
    product_scope: str
    domain_code: str
    visual_kind: str
    theme: str
    eyebrow: str
    title: str
    lead: str
    body_html: str
    items: tuple[PublicSectionItemView, ...]


def list_page_sections(session: Session, *, page_id, locale: str, include_drafts: bool = False) -> list[PublicSectionView]:
    stmt = (
        select(PublicPageSection, PublicPageSectionTranslation)
        .join(PublicPageSectionTranslation, PublicPageSectionTranslation.section_id == PublicPageSection.id)
        .where(PublicPageSection.page_id == page_id, PublicPageSectionTranslation.locale == locale)
        .order_by(PublicPageSection.sort_order.asc())
    )
    if not include_drafts:
        stmt = stmt.where(PublicPageSection.status == "published")
    sections=[]
    for section, tr in session.execute(stmt).all():
        item_stmt = (
            select(PublicPageSectionItem, PublicPageSectionItemTranslation)
            .join(PublicPageSectionItemTranslation, PublicPageSectionItemTranslation.item_id == PublicPageSectionItem.id)
            .where(PublicPageSectionItem.section_id == section.id, PublicPageSectionItemTranslation.locale == locale)
            .order_by(PublicPageSectionItem.sort_order.asc())
        )
        items=tuple(PublicSectionItemView(key=i.item_key,kind=i.item_kind,domain_code=i.domain_code,label=t.label,value=t.value,description=t.description,featured=i.is_featured) for i,t in session.execute(item_stmt).all())
        sections.append(PublicSectionView(key=section.section_key,product_scope=section.product_scope,domain_code=section.domain_code,visual_kind=section.visual_kind,theme=section.theme,eyebrow=tr.eyebrow,title=tr.title,lead=tr.lead,body_html=tr.body_html,items=items))
    return sections
