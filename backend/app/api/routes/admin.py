from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.session import get_db
from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.automation.schemas import (
    WebhookDeliveryRead,
    WebhookSubscriptionCreate,
    WebhookSubscriptionRead,
    WebhookSubscriptionUpdate,
    WebhookTestResult,
)
from app.automation.service import WebhookDeliveryService
from app.automation.examples import get_automation_example_detail, list_automation_examples
from app.automation.n8n import N8nWorkflowService
from app.automation.n8n_schemas import N8nWorkflowCreate, N8nWorkflowRead, N8nWorkflowUpdate
from app.integrations.exceptions import (
    IntegrationConfigurationError,
    IntegrationDisabledError,
    IntegrationError,
    IntegrationExecutionInProgressError,
    IntegrationNotFoundError,
    IntegrationOperationUnsupportedError,
    IntegrationProviderUnsupportedError,
)
from app.integrations.google_oauth import GoogleOAuthService
from app.models.audit_log import AuditLog
from app.models.appointment import Appointment, AppointmentStatus
from app.models.integration import Integration
from app.models.category import Category
from app.models.professional_profile import ProfessionalProfile, ProfessionalSpecialty
from app.models.specialty import Specialty
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminAppointmentListResponse,
    AdminAppointmentStatusUpdate,
    AdminProfessionalDetail,
    AdminProfessionalListItem,
    AdminProfessionalListResponse,
    AdminProfessionalUpdate,
    AdminUserDetail,
    AdminUserListItem,
    AdminUserListResponse,
    AdminUserUpdate,
    PageMeta,
)
from app.schemas.appointments import AppointmentAdminRead, AppointmentHistoryRead, AppointmentMeetingRead, AppointmentStatusUpdate
from app.schemas.categories import CategoryAdminRead, CategoryCreate, CategoryUpdate
from app.schemas.integrations import (
    GoogleMeetMeetingCancel,
    GoogleMeetMeetingCreate,
    GoogleMeetMeetingRead,
    GoogleOAuthAuthorizationUrlRead,
    GoogleOAuthCallbackRead,
    GoogleOAuthDisconnectRead,
    GoogleOAuthStatusRead,
    IntegrationExecutionRead,
    IntegrationListResponse,
    IntegrationOperationResultRead,
    IntegrationPageMeta,
    IntegrationRead,
    IntegrationTestRequest,
    IntegrationCreate,
    IntegrationUpdate,
)
from app.schemas.specialties import SpecialtyAdminRead, SpecialtyCreate, SpecialtyUpdate
from app.services.catalog import CatalogService
from app.services.appointments import AppointmentService
from app.services.integrations import IntegrationService
from app.services.google_meet import GoogleMeetService
from app.services.meeting_provisioning import MeetingProvisioningService
from app.notifications.service import AppointmentNotificationService
from app.integrations.meeting_contracts import MeetingAttendee, MeetingCreateRequest
from app.whatsapp.exceptions import WhatsAppError, WhatsAppNotFoundError, WhatsAppValidationError
from app.whatsapp.schemas import (
    AppointmentNotificationRead,
    WhatsAppConsentAdminCorrection,
    WhatsAppConsentRead,
    WhatsAppConsentSummary,
    WhatsAppIntegrationStatusRead,
    WhatsAppHealthCheckRead,
    WhatsAppMessageRead,
    WhatsAppMessageSendRead,
    WhatsAppMessageSendRequest,
    WhatsAppNotificationPolicyRead,
    WhatsAppNotificationPolicyUpdate,
    WhatsAppTemplateCreate,
    WhatsAppTemplateRead,
    WhatsAppTemplateSyncRead,
    WhatsAppTemplateUpdate,
    WhatsAppValidationRead,
    WhatsAppWebhookEventRead,
    WhatsAppWebhookStatusRead,
)
from app.whatsapp.enums import WhatsAppWebhookEventType, WhatsAppWebhookProcessingStatus
from app.whatsapp.messaging import WhatsAppMessagingService, serialize_message
from app.whatsapp.services import WhatsAppConsentService, WhatsAppTemplateService, WhatsAppWebhookService, serialize_webhook_event

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/integrations", response_model=IntegrationListResponse)
def list_integrations(
    integration_type: IntegrationType | None = Query(default=None),
    provider: IntegrationProvider | None = Query(default=None),
    enabled: bool | None = Query(default=None),
    integration_status: IntegrationStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> IntegrationListResponse:
    items, total = IntegrationService(db).list_integrations(
        integration_type=integration_type,
        provider=provider,
        enabled=enabled,
        status=integration_status,
        page=page,
        page_size=page_size,
    )
    return IntegrationListResponse(
        items=[IntegrationRead.model_validate(item) for item in items],
        meta=_integration_page_meta(page, page_size, total),
    )


@router.get("/webhook-subscriptions", response_model=list[WebhookSubscriptionRead])
def list_webhook_subscriptions(db: Session = Depends(get_db)) -> list[WebhookSubscriptionRead]:
    return [WebhookSubscriptionRead.model_validate(item) for item in WebhookDeliveryService(db).list_subscriptions()]


@router.post("/webhook-subscriptions", response_model=WebhookSubscriptionRead)
def create_webhook_subscription(
    payload: WebhookSubscriptionCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WebhookSubscriptionRead:
    item = WebhookDeliveryService(db).create_subscription(payload, admin_user)
    return WebhookSubscriptionRead.model_validate(item)


@router.get("/webhook-subscriptions/{subscription_id}", response_model=WebhookSubscriptionRead)
def get_webhook_subscription(subscription_id: int, db: Session = Depends(get_db)) -> WebhookSubscriptionRead:
    return WebhookSubscriptionRead.model_validate(WebhookDeliveryService(db).get_subscription(subscription_id))


@router.patch("/webhook-subscriptions/{subscription_id}", response_model=WebhookSubscriptionRead)
def update_webhook_subscription(
    subscription_id: int,
    payload: WebhookSubscriptionUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WebhookSubscriptionRead:
    item = WebhookDeliveryService(db).update_subscription(subscription_id, payload, admin_user)
    return WebhookSubscriptionRead.model_validate(item)


@router.post("/webhook-subscriptions/{subscription_id}/enable", response_model=WebhookSubscriptionRead)
def enable_webhook_subscription(
    subscription_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WebhookSubscriptionRead:
    item = WebhookDeliveryService(db).set_enabled(subscription_id, True, admin_user)
    return WebhookSubscriptionRead.model_validate(item)


@router.post("/webhook-subscriptions/{subscription_id}/disable", response_model=WebhookSubscriptionRead)
def disable_webhook_subscription(
    subscription_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WebhookSubscriptionRead:
    item = WebhookDeliveryService(db).set_enabled(subscription_id, False, admin_user)
    return WebhookSubscriptionRead.model_validate(item)


@router.post("/webhook-subscriptions/{subscription_id}/test", response_model=WebhookTestResult)
def test_webhook_subscription(
    subscription_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WebhookTestResult:
    delivery = WebhookDeliveryService(db).test_subscription(subscription_id, admin_user)
    return WebhookTestResult(
        success=delivery.status == "succeeded",
        delivery_id=delivery.id,
        status=delivery.status,
        message="Webhook test entregado." if delivery.status == "succeeded" else "Webhook test no entregado.",
    )


@router.get("/webhook-deliveries", response_model=list[WebhookDeliveryRead])
def list_webhook_deliveries(
    subscription_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[WebhookDeliveryRead]:
    return [WebhookDeliveryRead.model_validate(item) for item in WebhookDeliveryService(db).list_deliveries(subscription_id=subscription_id, limit=limit)]


@router.post("/webhook-deliveries/{delivery_id}/retry", response_model=WebhookDeliveryRead)
def retry_webhook_delivery(
    delivery_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WebhookDeliveryRead:
    return WebhookDeliveryRead.model_validate(WebhookDeliveryService(db).retry_delivery(delivery_id, admin_user))


@router.get("/automation/examples")
def list_automation_connector_examples() -> list[dict]:
    return list_automation_examples()


@router.get("/automation/examples/{example_key}")
def get_automation_connector_example(example_key: str) -> dict:
    return get_automation_example_detail(example_key)


@router.get("/integrations/{integration_id}/n8n/workflows", response_model=list[N8nWorkflowRead])
def list_n8n_workflows(integration_id: int, db: Session = Depends(get_db)) -> list[N8nWorkflowRead]:
    return [N8nWorkflowRead.model_validate(item) for item in N8nWorkflowService(db).list_workflows(integration_id)]


@router.post("/integrations/{integration_id}/n8n/workflows", response_model=N8nWorkflowRead)
def create_n8n_workflow(
    integration_id: int,
    payload: N8nWorkflowCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> N8nWorkflowRead:
    return N8nWorkflowRead.model_validate(N8nWorkflowService(db).create_workflow(integration_id, payload, admin_user))


@router.get("/integrations/{integration_id}/n8n/workflows/{workflow_id}", response_model=N8nWorkflowRead)
def get_n8n_workflow(integration_id: int, workflow_id: int, db: Session = Depends(get_db)) -> N8nWorkflowRead:
    return N8nWorkflowRead.model_validate(N8nWorkflowService(db).get_workflow(integration_id, workflow_id))


@router.patch("/integrations/{integration_id}/n8n/workflows/{workflow_id}", response_model=N8nWorkflowRead)
def update_n8n_workflow(
    integration_id: int,
    workflow_id: int,
    payload: N8nWorkflowUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> N8nWorkflowRead:
    return N8nWorkflowRead.model_validate(N8nWorkflowService(db).update_workflow(integration_id, workflow_id, payload, admin_user))


@router.post("/integrations/{integration_id}/n8n/workflows/{workflow_id}/enable", response_model=N8nWorkflowRead)
def enable_n8n_workflow(
    integration_id: int,
    workflow_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> N8nWorkflowRead:
    return N8nWorkflowRead.model_validate(N8nWorkflowService(db).set_enabled(integration_id, workflow_id, True, admin_user))


@router.post("/integrations/{integration_id}/n8n/workflows/{workflow_id}/disable", response_model=N8nWorkflowRead)
def disable_n8n_workflow(
    integration_id: int,
    workflow_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> N8nWorkflowRead:
    return N8nWorkflowRead.model_validate(N8nWorkflowService(db).set_enabled(integration_id, workflow_id, False, admin_user))


@router.post("/integrations/{integration_id}/n8n/workflows/{workflow_id}/test", response_model=WebhookDeliveryRead)
def test_n8n_workflow(
    integration_id: int,
    workflow_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WebhookDeliveryRead:
    return WebhookDeliveryRead.model_validate(N8nWorkflowService(db).test_workflow(integration_id, workflow_id, admin_user))


@router.get("/integrations/{integration_id}/n8n/workflows/{workflow_id}/deliveries", response_model=list[WebhookDeliveryRead])
def list_n8n_workflow_deliveries(
    integration_id: int,
    workflow_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[WebhookDeliveryRead]:
    return [WebhookDeliveryRead.model_validate(item) for item in N8nWorkflowService(db).list_deliveries(integration_id, workflow_id, limit=limit)]


@router.post("/integrations", response_model=IntegrationRead)
def create_integration(
    payload: IntegrationCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> IntegrationRead:
    try:
        item = IntegrationService(db).create_integration(payload, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return IntegrationRead.model_validate(item)


@router.get("/integrations/{integration_id}", response_model=IntegrationRead)
def get_integration(integration_id: int, db: Session = Depends(get_db)) -> IntegrationRead:
    try:
        item = IntegrationService(db).get_integration(integration_id)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return IntegrationRead.model_validate(item)


@router.patch("/integrations/{integration_id}", response_model=IntegrationRead)
def update_integration(
    integration_id: int,
    payload: IntegrationUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> IntegrationRead:
    try:
        item = IntegrationService(db).update_integration(integration_id, payload, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return IntegrationRead.model_validate(item)


@router.post("/integrations/{integration_id}/validate", response_model=IntegrationOperationResultRead)
def validate_integration(
    integration_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> IntegrationOperationResultRead:
    try:
        result = IntegrationService(db).validate_configuration(integration_id, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return _operation_result(result)


@router.post("/integrations/{integration_id}/enable", response_model=IntegrationRead)
def enable_integration(
    integration_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> IntegrationRead:
    try:
        item = IntegrationService(db).enable_integration(integration_id, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return IntegrationRead.model_validate(item)


@router.post("/integrations/{integration_id}/disable", response_model=IntegrationRead)
def disable_integration(
    integration_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> IntegrationRead:
    try:
        item = IntegrationService(db).disable_integration(integration_id, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return IntegrationRead.model_validate(item)


@router.post("/integrations/{integration_id}/health-check", response_model=IntegrationOperationResultRead)
def health_check_integration(
    integration_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> IntegrationOperationResultRead:
    try:
        result = IntegrationService(db).health_check(integration_id, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return _operation_result(result)


@router.post("/integrations/{integration_id}/test", response_model=IntegrationOperationResultRead)
def test_integration(
    integration_id: int,
    payload: IntegrationTestRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> IntegrationOperationResultRead:
    try:
        result = IntegrationService(db).test_integration(integration_id, admin_user, idempotency_key=payload.idempotency_key)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return _operation_result(result)


@router.get("/integrations/{integration_id}/executions", response_model=list[IntegrationExecutionRead])
def list_integration_executions(
    integration_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[IntegrationExecutionRead]:
    try:
        items = IntegrationService(db).list_executions(integration_id, limit=limit)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return [IntegrationExecutionRead.model_validate(item) for item in items]


@router.get("/integrations/{integration_id}/whatsapp/status", response_model=WhatsAppIntegrationStatusRead)
def get_whatsapp_status(integration_id: int, db: Session = Depends(get_db)) -> WhatsAppIntegrationStatusRead:
    try:
        integration = IntegrationService(db).get_integration(integration_id)
        return WhatsAppIntegrationStatusRead(**WhatsAppTemplateService(db).status(integration))
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc


@router.post("/integrations/{integration_id}/whatsapp/validate", response_model=WhatsAppValidationRead)
def validate_whatsapp_config(
    integration_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WhatsAppValidationRead:
    try:
        integration = IntegrationService(db).get_integration(integration_id)
        return WhatsAppValidationRead(**WhatsAppTemplateService(db).validate_local_configuration(integration, admin_user))
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc


@router.get("/integrations/{integration_id}/whatsapp/templates", response_model=list[WhatsAppTemplateRead])
def list_whatsapp_templates(integration_id: int, db: Session = Depends(get_db)) -> list[WhatsAppTemplateRead]:
    try:
        integration = IntegrationService(db).get_integration(integration_id)
        items = WhatsAppTemplateService(db).list_templates(integration)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc
    return [WhatsAppTemplateRead.model_validate(item) for item in items]


@router.post("/integrations/{integration_id}/whatsapp/templates", response_model=WhatsAppTemplateRead)
def create_whatsapp_template(
    integration_id: int,
    payload: WhatsAppTemplateCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WhatsAppTemplateRead:
    try:
        integration = IntegrationService(db).get_integration(integration_id)
        item = WhatsAppTemplateService(db).create_template(integration, payload, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc
    return WhatsAppTemplateRead.model_validate(item)


@router.post("/integrations/{integration_id}/whatsapp/templates/sync", response_model=WhatsAppTemplateSyncRead)
def sync_whatsapp_templates(
    integration_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WhatsAppTemplateSyncRead:
    try:
        integration = IntegrationService(db).get_integration(integration_id)
        return WhatsAppMessagingService(db).sync_templates(integration, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc


@router.get("/integrations/{integration_id}/whatsapp/templates/{template_id}", response_model=WhatsAppTemplateRead)
def get_whatsapp_template(integration_id: int, template_id: int, db: Session = Depends(get_db)) -> WhatsAppTemplateRead:
    try:
        integration = IntegrationService(db).get_integration(integration_id)
        item = WhatsAppTemplateService(db).get_template(integration, template_id)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc
    return WhatsAppTemplateRead.model_validate(item)


@router.patch("/integrations/{integration_id}/whatsapp/templates/{template_id}", response_model=WhatsAppTemplateRead)
def update_whatsapp_template(
    integration_id: int,
    template_id: int,
    payload: WhatsAppTemplateUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WhatsAppTemplateRead:
    try:
        integration = IntegrationService(db).get_integration(integration_id)
        item = WhatsAppTemplateService(db).update_template(integration, template_id, payload, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc
    return WhatsAppTemplateRead.model_validate(item)


@router.post("/integrations/{integration_id}/whatsapp/health-check", response_model=WhatsAppHealthCheckRead)
def health_check_whatsapp(
    integration_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WhatsAppHealthCheckRead:
    try:
        integration = IntegrationService(db).get_integration(integration_id)
        result = WhatsAppMessagingService(db).health_check(integration, admin_user)
        return WhatsAppHealthCheckRead(success=result.success, code=result.code, message=result.message, metadata=result.metadata)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc


@router.get("/integrations/{integration_id}/whatsapp/messages", response_model=list[WhatsAppMessageRead])
def list_whatsapp_messages(
    integration_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[WhatsAppMessageRead]:
    try:
        integration = IntegrationService(db).get_integration(integration_id)
        items = WhatsAppMessagingService(db).list_messages(integration, limit=limit)
        return [serialize_message(item) for item in items]
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc


@router.post("/integrations/{integration_id}/whatsapp/messages", response_model=WhatsAppMessageSendRead)
def send_whatsapp_message(
    integration_id: int,
    payload: WhatsAppMessageSendRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WhatsAppMessageSendRead:
    try:
        integration = IntegrationService(db).get_integration(integration_id)
        return WhatsAppMessagingService(db).send_template(integration, payload, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc


@router.get("/integrations/{integration_id}/whatsapp/messages/{message_id}", response_model=WhatsAppMessageRead)
def get_whatsapp_message(integration_id: int, message_id: int, db: Session = Depends(get_db)) -> WhatsAppMessageRead:
    try:
        integration = IntegrationService(db).get_integration(integration_id)
        return serialize_message(WhatsAppMessagingService(db).get_message(integration, message_id))
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc


@router.post("/integrations/{integration_id}/whatsapp/messages/{message_id}/retry", response_model=WhatsAppMessageSendRead)
def retry_whatsapp_message(
    integration_id: int,
    message_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WhatsAppMessageSendRead:
    try:
        integration = IntegrationService(db).get_integration(integration_id)
        return WhatsAppMessagingService(db).retry_message(integration, message_id, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc


@router.get("/integrations/{integration_id}/whatsapp/notification-policy", response_model=WhatsAppNotificationPolicyRead)
def get_whatsapp_notification_policy(integration_id: int, db: Session = Depends(get_db)) -> WhatsAppNotificationPolicyRead:
    integration = _integration(db, integration_id)
    config = integration.config or {}
    return _notification_policy_read(integration.id, config)


@router.patch("/integrations/{integration_id}/whatsapp/notification-policy", response_model=WhatsAppNotificationPolicyRead)
def update_whatsapp_notification_policy(
    integration_id: int,
    payload: WhatsAppNotificationPolicyUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> WhatsAppNotificationPolicyRead:
    integration = _integration(db, integration_id)
    if integration.provider != IntegrationProvider.whatsapp_cloud:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La politica solo aplica a WhatsApp Cloud")
    config = dict(integration.config or {})
    config.update(
        {
            "notification_policy": payload.notification_policy,
            "fallback_channel": payload.fallback_channel,
            "reminder_enabled": payload.reminder_enabled,
            "reminder_minutes_before": payload.reminder_minutes_before,
            "default_language": payload.default_language,
            "template_mapping": {key.value: value for key, value in payload.template_mapping.items() if value},
        }
    )
    integration.config = config
    _audit(
        db,
        admin_user.id,
        "whatsapp_notification_policy_updated",
        "Integration",
        str(integration.id),
        {"integration_id": integration.id, "provider": "whatsapp_cloud", "notification_policy": payload.notification_policy},
    )
    db.commit()
    return _notification_policy_read(integration.id, config)


@router.get("/appointment-notifications", response_model=list[AppointmentNotificationRead])
def list_appointment_notifications(
    appointment_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[AppointmentNotificationRead]:
    items = AppointmentNotificationService(db).list_notifications(appointment_id=appointment_id, limit=limit, offset=offset)
    return [AppointmentNotificationRead.model_validate(item) for item in items]


@router.get("/appointment-notifications/{notification_id}", response_model=AppointmentNotificationRead)
def get_appointment_notification(notification_id: int, db: Session = Depends(get_db)) -> AppointmentNotificationRead:
    item = AppointmentNotificationService(db).get_notification(notification_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificacion no encontrada")
    return AppointmentNotificationRead.model_validate(item)


@router.post("/appointment-notifications/{notification_id}/retry", response_model=AppointmentNotificationRead)
def retry_appointment_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> AppointmentNotificationRead:
    try:
        return AppointmentNotificationRead.model_validate(AppointmentNotificationService(db).retry(notification_id, admin_user))
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc


@router.post("/appointment-notifications/{notification_id}/reconcile", response_model=AppointmentNotificationRead)
def reconcile_appointment_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> AppointmentNotificationRead:
    try:
        return AppointmentNotificationRead.model_validate(AppointmentNotificationService(db).reconcile(notification_id, admin_user))
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc


@router.post("/appointment-notifications/{notification_id}/cancel", response_model=AppointmentNotificationRead)
def cancel_appointment_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> AppointmentNotificationRead:
    try:
        return AppointmentNotificationRead.model_validate(AppointmentNotificationService(db).cancel_pending(notification_id, admin_user))
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc


@router.get("/integrations/{integration_id}/whatsapp/webhook-events", response_model=list[WhatsAppWebhookEventRead])
def list_whatsapp_webhook_events(
    integration_id: int,
    event_type: WhatsAppWebhookEventType | None = Query(default=None),
    processing_status: WhatsAppWebhookProcessingStatus | None = Query(default=None),
    duplicate: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[WhatsAppWebhookEventRead]:
    try:
        integration = IntegrationService(db).get_integration(integration_id)
        WhatsAppTemplateService(db).status(integration)
        items = WhatsAppWebhookService(db).list_events(
            integration_id=integration_id,
            event_type=event_type,
            processing_status=processing_status,
            duplicate=duplicate,
            limit=limit,
        )
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc
    return [WhatsAppWebhookEventRead(**serialize_webhook_event(item)) for item in items]


@router.get("/integrations/{integration_id}/whatsapp/webhook-events/{event_id}", response_model=WhatsAppWebhookEventRead)
def get_whatsapp_webhook_event(integration_id: int, event_id: int, db: Session = Depends(get_db)) -> WhatsAppWebhookEventRead:
    try:
        integration = IntegrationService(db).get_integration(integration_id)
        WhatsAppTemplateService(db).status(integration)
        item = WhatsAppWebhookService(db).get_event(integration_id=integration_id, event_id=event_id)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc
    return WhatsAppWebhookEventRead(**serialize_webhook_event(item))


@router.get("/integrations/{integration_id}/whatsapp/webhook-status", response_model=WhatsAppWebhookStatusRead)
def get_whatsapp_webhook_status(integration_id: int, db: Session = Depends(get_db)) -> WhatsAppWebhookStatusRead:
    try:
        integration = IntegrationService(db).get_integration(integration_id)
        WhatsAppTemplateService(db).status(integration)
        return WhatsAppWebhookStatusRead(**WhatsAppWebhookService(db).webhook_status(integration_id))
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc


@router.get("/whatsapp/consents", response_model=list[WhatsAppConsentSummary])
def list_whatsapp_consents(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[WhatsAppConsentSummary]:
    items = WhatsAppConsentService(db).list_admin_summary(limit=limit, offset=offset)
    return [WhatsAppConsentSummary.model_validate(item) for item in items]


@router.post("/whatsapp/consents/corrections", response_model=WhatsAppConsentRead)
def correct_whatsapp_consent(
    payload: WhatsAppConsentAdminCorrection,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WhatsAppConsentRead:
    try:
        item = WhatsAppConsentService(db).admin_correction(admin_user, payload)
    except WhatsAppError as exc:
        raise _whatsapp_http_error(exc) from exc
    return WhatsAppConsentRead.model_validate(item)


@router.post("/integrations/{integration_id}/oauth/google/authorize", response_model=GoogleOAuthAuthorizationUrlRead)
def authorize_google_oauth(
    integration_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GoogleOAuthAuthorizationUrlRead:
    try:
        authorization_url, expires_at = GoogleOAuthService(db).authorization_url(integration_id, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return GoogleOAuthAuthorizationUrlRead(authorization_url=authorization_url, state_expires_at=expires_at)


@router.get("/integrations/oauth/google/callback", response_model=GoogleOAuthCallbackRead)
def google_oauth_callback(code: str | None = None, state: str | None = None, db: Session = Depends(get_db)) -> GoogleOAuthCallbackRead:
    if not code or not state:
        return GoogleOAuthCallbackRead(
            success=False,
            status="error",
            message="No pudimos completar la autorizacion.",
            redirect_url="/dashboard/admin/integrations?google_oauth=error",
        )
    try:
        GoogleOAuthService(db).callback(code=code, state=state)
    except IntegrationError:
        return GoogleOAuthCallbackRead(
            success=False,
            status="error",
            message="No pudimos completar la autorizacion.",
            redirect_url="/dashboard/admin/integrations?google_oauth=error",
        )
    return GoogleOAuthCallbackRead(
        success=True,
        status="connected",
        message="Cuenta Google conectada correctamente.",
        redirect_url="/dashboard/admin/integrations?google_oauth=connected",
    )


@router.get("/integrations/{integration_id}/oauth/status", response_model=GoogleOAuthStatusRead)
def google_oauth_status(
    integration_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GoogleOAuthStatusRead:
    try:
        status_data = GoogleOAuthService(db).status(integration_id)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return GoogleOAuthStatusRead(**status_data)


@router.post("/integrations/{integration_id}/oauth/refresh", response_model=GoogleOAuthStatusRead)
def refresh_google_oauth(
    integration_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GoogleOAuthStatusRead:
    try:
        GoogleOAuthService(db).refresh(integration_id, admin_user)
        status_data = GoogleOAuthService(db).status(integration_id)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return GoogleOAuthStatusRead(**status_data)


@router.post("/integrations/{integration_id}/oauth/disconnect", response_model=GoogleOAuthDisconnectRead)
def disconnect_google_oauth(
    integration_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GoogleOAuthDisconnectRead:
    try:
        GoogleOAuthService(db).disconnect(integration_id, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return GoogleOAuthDisconnectRead(success=True, status="revoked", message="Cuenta Google desconectada.")


@router.post("/integrations/{integration_id}/meetings", response_model=GoogleMeetMeetingRead)
def create_google_meet_meeting(
    integration_id: int,
    payload: GoogleMeetMeetingCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GoogleMeetMeetingRead:
    try:
        result = GoogleMeetService(db).create_meeting(
            integration_id,
            MeetingCreateRequest(
                title=payload.title,
                description=payload.description or "Reunion programada mediante RealMeet.",
                start_at=payload.start_at,
                end_at=payload.end_at,
                timezone=payload.timezone,
                attendees=[MeetingAttendee(email=item) for item in payload.attendees],
                idempotency_key=payload.idempotency_key,
                send_updates=payload.send_updates,
                entity_type="admin_test",
                entity_id=payload.idempotency_key,
            ),
            admin_user,
        )
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return GoogleMeetMeetingRead(**result.__dict__)


@router.get("/integrations/{integration_id}/meetings/{external_event_id}", response_model=GoogleMeetMeetingRead)
def get_google_meet_meeting(
    integration_id: int,
    external_event_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GoogleMeetMeetingRead:
    try:
        result = GoogleMeetService(db).get_meeting(integration_id, external_event_id, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return GoogleMeetMeetingRead(**result.__dict__)


@router.delete("/integrations/{integration_id}/meetings/{external_event_id}", response_model=GoogleMeetMeetingRead)
def cancel_google_meet_meeting(
    integration_id: int,
    external_event_id: str,
    payload: GoogleMeetMeetingCancel,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GoogleMeetMeetingRead:
    try:
        result = GoogleMeetService(db).cancel_meeting(integration_id, external_event_id, admin_user, idempotency_key=payload.idempotency_key, send_updates=payload.send_updates)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return GoogleMeetMeetingRead(**result.__dict__)


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    search: str | None = Query(default=None),
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AdminUserListResponse:
    query = select(User)
    count_query = select(func.count(User.id))
    conditions = []
    if search:
        term = f"%{search.strip()}%"
        conditions.append(or_(User.email.ilike(term), User.first_name.ilike(term), User.last_name.ilike(term)))
    if role:
        conditions.append(User.role == role)
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    if conditions:
        query = query.where(*conditions)
        count_query = count_query.where(*conditions)
    total = db.scalar(count_query) or 0
    items = list(db.scalars(query.offset((page - 1) * page_size).limit(page_size).order_by(User.created_at.desc(), User.id.desc())))
    return AdminUserListResponse(
        items=[_serialize_user_item(item) for item in items],
        meta=_page_meta(page, page_size, total),
    )


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def get_user(user_id: int, db: Session = Depends(get_db)) -> AdminUserDetail:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _serialize_user_detail(user)


@router.patch("/users/{user_id}", response_model=AdminUserDetail)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminUserDetail:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(user, key, value)
    _audit(db, admin_user.id, "admin_user_updated", "User", str(user.id), {"fields": sorted(changes.keys())})
    db.commit()
    db.refresh(user)
    return _serialize_user_detail(user)


@router.get("/professionals", response_model=AdminProfessionalListResponse)
def list_professionals(
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    is_public: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AdminProfessionalListResponse:
    query = select(ProfessionalProfile).join(User, ProfessionalProfile.user_id == User.id)
    count_query = select(func.count(ProfessionalProfile.id)).join(User, ProfessionalProfile.user_id == User.id)
    conditions = []
    if search:
        term = f"%{search.strip()}%"
        conditions.append(or_(User.email.ilike(term), User.first_name.ilike(term), User.last_name.ilike(term), ProfessionalProfile.title.ilike(term)))
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    if is_public is not None:
        conditions.append(ProfessionalProfile.is_public == is_public)
    if conditions:
        query = query.where(*conditions)
        count_query = count_query.where(*conditions)
    total = db.scalar(count_query) or 0
    items = list(db.scalars(query.offset((page - 1) * page_size).limit(page_size).order_by(ProfessionalProfile.created_at.desc())))
    return AdminProfessionalListResponse(
        items=[_serialize_professional_item(item) for item in items],
        meta=_page_meta(page, page_size, total),
    )


@router.get("/professionals/{professional_id}", response_model=AdminProfessionalDetail)
def get_professional(professional_id: int, db: Session = Depends(get_db)) -> AdminProfessionalDetail:
    professional = db.get(ProfessionalProfile, professional_id)
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    return _serialize_professional_detail(db, professional)


@router.get("/categories", response_model=list[CategoryAdminRead])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryAdminRead]:
    items = CatalogService(db).list_categories(active_only=False)
    return [CategoryAdminRead.model_validate(item) for item in items]


@router.post("/categories", response_model=CategoryAdminRead)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> CategoryAdminRead:
    item = CatalogService(db).create_category(payload)
    return CategoryAdminRead.model_validate(item)


@router.patch("/categories/{category_id}", response_model=CategoryAdminRead)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)) -> CategoryAdminRead:
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    item = CatalogService(db).update_category(category, payload)
    return CategoryAdminRead.model_validate(item)


@router.get("/specialties", response_model=list[SpecialtyAdminRead])
def list_specialties(category_id: int | None = Query(default=None), db: Session = Depends(get_db)) -> list[SpecialtyAdminRead]:
    items = CatalogService(db).list_specialties(category_id=category_id, active_only=False)
    return [SpecialtyAdminRead.model_validate(item) for item in items]


@router.post("/specialties", response_model=SpecialtyAdminRead)
def create_specialty(payload: SpecialtyCreate, db: Session = Depends(get_db)) -> SpecialtyAdminRead:
    item = CatalogService(db).create_specialty(payload)
    return SpecialtyAdminRead.model_validate(item)


@router.patch("/specialties/{specialty_id}", response_model=SpecialtyAdminRead)
def update_specialty(specialty_id: int, payload: SpecialtyUpdate, db: Session = Depends(get_db)) -> SpecialtyAdminRead:
    specialty = db.get(Specialty, specialty_id)
    if not specialty:
        raise HTTPException(status_code=404, detail="Specialty not found")
    item = CatalogService(db).update_specialty(specialty, payload)
    return SpecialtyAdminRead.model_validate(item)


@router.patch("/professionals/{professional_id}", response_model=AdminProfessionalDetail)
def patch_professional(
    professional_id: int,
    payload: AdminProfessionalUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminProfessionalDetail:
    professional = db.get(ProfessionalProfile, professional_id)
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    changes = payload.model_dump(exclude_unset=True)
    user_is_active = changes.pop("user_is_active", None)
    for key, value in changes.items():
        setattr(professional, key, value)
    if user_is_active is not None:
        professional.user.is_active = user_is_active
    _audit(
        db,
        admin_user.id,
        "admin_professional_updated",
        "ProfessionalProfile",
        str(professional.id),
        {"fields": sorted([*changes.keys(), *([] if user_is_active is None else ["user_is_active"])])},
    )
    db.commit()
    db.refresh(professional)
    return _serialize_professional_detail(db, professional)


@router.get("/appointments", response_model=AdminAppointmentListResponse)
def list_appointments(
    status: AppointmentStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AdminAppointmentListResponse:
    service = AppointmentService(db)
    query = select(Appointment)
    count_query = select(func.count(Appointment.id))
    conditions = []
    if status:
        conditions.append(Appointment.status == status)
    if search:
        term = f"%{search.strip()}%"
        query = query.join(ProfessionalProfile, Appointment.professional_id == ProfessionalProfile.id).join(User, ProfessionalProfile.user_id == User.id)
        count_query = count_query.join(ProfessionalProfile, Appointment.professional_id == ProfessionalProfile.id).join(User, ProfessionalProfile.user_id == User.id)
        conditions.append(or_(User.email.ilike(term), User.first_name.ilike(term), User.last_name.ilike(term)))
    if conditions:
        query = query.where(*conditions)
        count_query = count_query.where(*conditions)
    total = db.scalar(count_query) or 0
    items = list(db.scalars(query.offset((page - 1) * page_size).limit(page_size).order_by(Appointment.start_datetime.desc())))
    return AdminAppointmentListResponse(
        items=[_serialize_admin_appointment(item, service) for item in items],
        meta=_page_meta(page, page_size, total),
    )


@router.get("/appointments/{appointment_id}", response_model=AppointmentAdminRead)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)) -> AppointmentAdminRead:
    service = AppointmentService(db)
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return _serialize_admin_appointment(appointment, service)


@router.patch("/appointments/{appointment_id}/status", response_model=AppointmentAdminRead)
def update_appointment_status(
    appointment_id: int,
    payload: AdminAppointmentStatusUpdate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AppointmentAdminRead:
    service = AppointmentService(db)
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    item = service.transition(appointment, user, payload.status, AppointmentStatusUpdate(reason=payload.reason))
    _audit(db, user.id, "admin_appointment_status_updated", "Appointment", str(appointment.id), {"status": payload.status.value})
    db.commit()
    db.refresh(item)
    return _serialize_admin_appointment(item, service)


@router.post("/appointments/{appointment_id}/meeting/retry-create", response_model=AppointmentAdminRead)
def retry_appointment_meeting_create(
    appointment_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AppointmentAdminRead:
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    MeetingProvisioningService(db).retry_create(appointment_id, user)
    db.refresh(appointment)
    return _serialize_admin_appointment(appointment, AppointmentService(db))


@router.post("/appointments/{appointment_id}/meeting/retry-cancel", response_model=AppointmentAdminRead)
def retry_appointment_meeting_cancel(
    appointment_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AppointmentAdminRead:
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    MeetingProvisioningService(db).retry_cancel(appointment_id, user)
    db.refresh(appointment)
    return _serialize_admin_appointment(appointment, AppointmentService(db))


@router.post("/appointments/{appointment_id}/meeting/reconcile", response_model=AppointmentAdminRead)
def reconcile_appointment_meeting(
    appointment_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AppointmentAdminRead:
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    MeetingProvisioningService(db).reconcile(appointment_id, user)
    db.refresh(appointment)
    return _serialize_admin_appointment(appointment, AppointmentService(db))


def _integration_page_meta(page: int, page_size: int, total: int) -> IntegrationPageMeta:
    total_pages = max((total + page_size - 1) // page_size, 1)
    return IntegrationPageMeta(page=page, page_size=page_size, total=total, total_pages=total_pages)


def _operation_result(result) -> IntegrationOperationResultRead:
    return IntegrationOperationResultRead(
        success=result.success,
        code=result.code,
        message=result.message,
        skipped=result.skipped,
        metadata=result.metadata,
        execution_id=result.execution_id,
        duration_ms=result.duration_ms,
    )


def _integration_http_error(exc: IntegrationError) -> HTTPException:
    if isinstance(exc, IntegrationNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, IntegrationConfigurationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    if isinstance(exc, (IntegrationProviderUnsupportedError, IntegrationDisabledError, IntegrationExecutionInProgressError, IntegrationOperationUnsupportedError)):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    if getattr(exc, "code", "").startswith("google_oauth"):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Integration operation failed")


def _whatsapp_http_error(exc: WhatsAppError) -> HTTPException:
    if isinstance(exc, WhatsAppNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, WhatsAppValidationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="WhatsApp operation failed")


def _integration(db: Session, integration_id: int) -> Integration:
    integration = db.get(Integration, integration_id)
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    return integration


def _notification_policy_read(integration_id: int, config: dict) -> WhatsAppNotificationPolicyRead:
    mapping = config.get("template_mapping") if isinstance(config.get("template_mapping"), dict) else {}
    return WhatsAppNotificationPolicyRead(
        integration_id=integration_id,
        notification_policy=str(config.get("notification_policy") or "email_only"),
        fallback_channel=str(config.get("fallback_channel") or "email"),
        reminder_enabled=bool(config.get("reminder_enabled", True)),
        reminder_minutes_before=int(config.get("reminder_minutes_before") or 1440),
        default_language=str(config.get("default_language") or "es_CL"),
        template_mapping={str(key): int(value) for key, value in mapping.items() if str(value).isdigit() or isinstance(value, int)},
    )


def _serialize_user_item(user: User) -> AdminUserListItem:
    return AdminUserListItem(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _serialize_user_detail(user: User) -> AdminUserDetail:
    return AdminUserDetail(**_serialize_user_item(user).model_dump(), phone=user.phone, updated_at=user.updated_at)


def _serialize_professional_item(professional: ProfessionalProfile) -> AdminProfessionalListItem:
    return AdminProfessionalListItem(
        id=professional.id,
        user_id=professional.user_id,
        email=professional.user.email,
        full_name=f"{professional.user.first_name} {professional.user.last_name}",
        title=professional.title,
        category_id=professional.category_id,
        consultation_mode=professional.consultation_mode,
        is_public=professional.is_public,
        is_verified=professional.is_verified,
        user_is_active=professional.user.is_active,
        created_at=professional.created_at,
    )


def _serialize_professional_detail(db: Session, professional: ProfessionalProfile) -> AdminProfessionalDetail:
    specialties = list(
        db.scalars(
            select(Specialty.name)
            .join(ProfessionalSpecialty, ProfessionalSpecialty.specialty_id == Specialty.id)
            .where(ProfessionalSpecialty.professional_id == professional.id)
            .order_by(Specialty.name.asc())
        )
    )
    return AdminProfessionalDetail(
        **_serialize_professional_item(professional).model_dump(),
        bio=professional.bio,
        years_experience=professional.years_experience,
        session_duration_minutes=professional.session_duration_minutes,
        price=professional.price,
        city=professional.city,
        country=professional.country,
        specialties=specialties,
    )


def _page_meta(page: int, page_size: int, total: int) -> PageMeta:
    total_pages = max((total + page_size - 1) // page_size, 1)
    return PageMeta(page=page, page_size=page_size, total=total, total_pages=total_pages)


def _audit(db: Session, user_id: int, action: str, entity_name: str, entity_id: str, metadata: dict) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity_name=entity_name,
            entity_id=entity_id,
            metadata_json=metadata,
            created_at=datetime.now(UTC),
        )
    )


def _serialize_admin_appointment(appointment: Appointment, service: AppointmentService) -> AppointmentAdminRead:
    meeting = _serialize_meeting(appointment, is_admin=True)
    return AppointmentAdminRead(
        id=appointment.id,
        professional_id=appointment.professional_id,
        client_id=appointment.client_id,
        category_id=appointment.category_id,
        specialty_id=appointment.specialty_id,
        start_datetime=appointment.start_datetime,
        end_datetime=appointment.end_datetime,
        status=appointment.status,
        consultation_mode=appointment.consultation_mode,
        meeting_provider=appointment.meeting_provider.value if appointment.meeting_provider else None,
        meeting_url=meeting.join_url if meeting else None,
        meeting=meeting,
        cancellation_reason=appointment.cancellation_reason,
        client_notes=appointment.client_notes,
        history=[AppointmentHistoryRead.model_validate(item) for item in service.list_history(appointment.id)],
    )


def _serialize_meeting(appointment: Appointment, *, is_admin: bool = False) -> AppointmentMeetingRead | None:
    link = getattr(appointment, "meeting_link", None)
    if link:
        join_url = link.meeting_url if link.status.value in {"ready", "fallback_ready"} and appointment.status != AppointmentStatus.cancelled else None
        return AppointmentMeetingRead(
            provider=link.provider.value if link.provider else None,
            join_url=join_url,
            status=link.status.value,
            fallback_used=link.fallback_used,
            message=_meeting_message(link.status.value, link.fallback_used),
            error_code=link.error_code if is_admin else None,
            error_message=link.error_message if is_admin else None,
        )
    if not appointment.meeting_provider:
        return None
    is_cancelled = appointment.status == AppointmentStatus.cancelled
    return AppointmentMeetingRead(
        provider=appointment.meeting_provider.value,
        join_url=None if is_cancelled else appointment.meeting_url,
        status="inactive" if is_cancelled else "active",
        message="Reunion lista." if not is_cancelled else "Reunion cancelada.",
    )


def _meeting_message(status_value: str, fallback_used: bool) -> str:
    if status_value == "ready":
        return "Reunion lista."
    if status_value == "fallback_ready":
        return "Reunion simulada para entorno de prueba." if fallback_used else "Reunion lista."
    if status_value in {"pending", "provisioning"}:
        return "El enlace de reunion todavia esta siendo preparado."
    if status_value == "failed":
        return "No pudimos preparar el enlace todavia."
    if status_value == "cancelled":
        return "Reunion cancelada."
    if status_value == "not_required":
        return "No se requiere reunion automatica."
    return "Estado de reunion no disponible."
