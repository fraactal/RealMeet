from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.whatsapp import WhatsAppConsent, WhatsAppTemplate, WhatsAppWebhookEvent
from app.whatsapp.enums import WhatsAppConsentPurpose, WhatsAppWebhookEventType, WhatsAppWebhookProcessingStatus


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


class WhatsAppWebhookEventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, event: WhatsAppWebhookEvent) -> WhatsAppWebhookEvent:
        self.db.add(event)
        self.db.flush()
        return event

    def get(self, event_id: int) -> WhatsAppWebhookEvent | None:
        return self.db.get(WhatsAppWebhookEvent, event_id)

    def get_by_event_key(self, event_key: str) -> WhatsAppWebhookEvent | None:
        return self.db.scalar(select(WhatsAppWebhookEvent).where(WhatsAppWebhookEvent.event_key == event_key))

    def list_recent(
        self,
        *,
        integration_id: int | None = None,
        event_type: WhatsAppWebhookEventType | None = None,
        processing_status: WhatsAppWebhookProcessingStatus | None = None,
        duplicate: bool | None = None,
        limit: int = 100,
    ) -> Sequence[WhatsAppWebhookEvent]:
        query = select(WhatsAppWebhookEvent)
        conditions = []
        if integration_id is not None:
            conditions.append(WhatsAppWebhookEvent.integration_id == integration_id)
        if event_type is not None:
            conditions.append(WhatsAppWebhookEvent.event_type == event_type)
        if processing_status is not None:
            conditions.append(WhatsAppWebhookEvent.processing_status == processing_status)
        if duplicate is not None:
            conditions.append(WhatsAppWebhookEvent.duplicate.is_(duplicate))
        if conditions:
            query = query.where(*conditions)
        return self.db.scalars(query.order_by(WhatsAppWebhookEvent.received_at.desc(), WhatsAppWebhookEvent.id.desc()).limit(limit)).all()
