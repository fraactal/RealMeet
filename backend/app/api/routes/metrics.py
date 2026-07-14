from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import UserRole
from app.schemas.metrics import AdminMetrics, ProfessionalMetrics
from app.services.metrics import MetricsService

router = APIRouter()


@router.get("/professional/metrics", response_model=ProfessionalMetrics, dependencies=[Depends(require_roles(UserRole.professional))])
def professional_metrics(user=Depends(get_current_user), db: Session = Depends(get_db)) -> ProfessionalMetrics:
    return ProfessionalMetrics(**MetricsService(db).professional_metrics(user))


@router.get("/admin/metrics", response_model=AdminMetrics, dependencies=[Depends(require_roles(UserRole.admin))])
def admin_metrics(db: Session = Depends(get_db)) -> AdminMetrics:
    return AdminMetrics(**MetricsService(db).admin_metrics())
