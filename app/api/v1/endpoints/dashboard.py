from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.dashboard import dashboard
from app.schemas.dashboard import (
    DashboardResponse,
    FinancialSummary,
    ProjectsDashboard,
    RequisitionsDashboard,
    BudgetDistribution,
)

router = APIRouter()


@router.get("/", response_model=DashboardResponse, summary="Get full dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("projects", "list")),
):
    """Returns the complete dashboard: financial KPIs, project status, requisitions, and budget distribution."""
    return dashboard.get_full_dashboard(db)


@router.get("/financial-summary", response_model=FinancialSummary, summary="Financial KPIs")
def get_financial_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("projects", "list")),
):
    """Presupuesto total, comprometido, gastado, disponible, % ejecución y % compromiso."""
    return dashboard.get_financial_summary(db)


@router.get("/projects", response_model=ProjectsDashboard, summary="Projects dashboard")
def get_projects_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("projects", "list")),
):
    """Estado de proyectos, top budget, top ejecución, sobre-compromisos, tendencia de creación."""
    return dashboard.get_projects_dashboard(db)


@router.get("/requisitions", response_model=RequisitionsDashboard, summary="Requisitions dashboard")
def get_requisitions_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "list")),
):
    """Requisiciones por status, tiempo promedio aprobación, tasa, top solicitantes, aging."""
    return dashboard.get_requisitions_dashboard(db)


@router.get("/budget-distribution", response_model=BudgetDistribution, summary="Budget distribution")
def get_budget_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("projects", "list")),
):
    """Distribución presupuestal por proyecto, tendencia mensual, y forecast 3 meses."""
    return dashboard.get_budget_distribution(db)
