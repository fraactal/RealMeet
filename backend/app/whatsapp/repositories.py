from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.whatsapp import WhatsAppConsent, WhatsAppTemplate
from app.whatsapp.enums import WhatsAppConsentPurpose


class WhatsAppConsentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, consent_id: int) -> WhatsAppConsent | None:
        return self.db.get(WhatsAppConsent, consent_id)

    def get_by_user_phone_purpose(self, user_id: int, phone_hash: str, purpose: WhatsAppConsentPurpose) -> WhatsAppConsent | None:
        return self.db.scalar(
            select(WhatsAppConsent).where(
                WhatsAppConsent.user_id == user_id,
                WhatsAppConsent.phone_hash == phone_hash,
                WhatsAppConsent.purpose == purpose,
            )
        )

    def list_for_user(self, user_id: int) -> Sequence[WhatsAppConsent]:
        return self.db.scalars(
            select(WhatsAppConsent)
            .where(WhatsAppConsent.user_id == user_id)
            .order_by(WhatsAppConsent.updated_at.desc(), WhatsAppConsent.id.desc())
        ).all()

    def list_admin(self, *, limit: int = 100, offset: int = 0) -> Sequence[WhatsAppConsent]:
        return self.db.scalars(
            select(WhatsAppConsent)
            .order_by(WhatsAppConsent.updated_at.desc(), WhatsAppConsent.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()


class WhatsAppTemplateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, template: WhatsAppTemplate) -> WhatsAppTemplate:
        self.db.add(template)
        self.db.flush()
        return template

    def get(self, template_id: int) -> WhatsAppTemplate | None:
        return self.db.get(WhatsAppTemplate, template_id)

    def list_by_integration(self, integration_id: int) -> Sequence[WhatsAppTemplate]:
        return self.db.scalars(
            select(WhatsAppTemplate)
            .where(WhatsAppTemplate.integration_id == integration_id)
            .order_by(WhatsAppTemplate.created_at.desc(), WhatsAppTemplate.id.desc())
        ).all()

    def get_by_name_language(self, integration_id: int, name: str, language: str) -> WhatsAppTemplate | None:
        return self.db.scalar(
            select(WhatsAppTemplate).where(
                WhatsAppTemplate.integration_id == integration_id,
                WhatsAppTemplate.name == name,
                WhatsAppTemplate.language == language,
            )
        )
