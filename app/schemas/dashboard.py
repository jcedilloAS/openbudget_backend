from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import List, Optional


# --- 1. Financial Summary (KPIs) ---

class FinancialSummary(BaseModel):
    """Overall financial KPIs."""
    total_initial_budget: Decimal
    total_commited: Decimal
    total_spent: Decimal
    total_available: Decimal
    execution_percentage: Decimal
    commitment_percentage: Decimal

    model_config = ConfigDict(from_attributes=True)


# --- 2. Project Status ---

class StatusCount(BaseModel):
    status: str
    count: int


class ProjectStatusSummary(BaseModel):
    """Projects grouped by status."""
    statuses: List[StatusCount]
    total: int


class ProjectRanked(BaseModel):
    """A project with its ranking metric."""
    id: int
    project_code: str
    name: str
    initial_budget: Decimal
    commited: Decimal
    spent: Decimal
    available_balance: Decimal
    execution_percentage: Decimal
    status: str

    model_config = ConfigDict(from_attributes=True)


class OvercommittedProject(BaseModel):
    id: int
    project_code: str
    name: str
    initial_budget: Decimal
    commited: Decimal
    spent: Decimal
    overcommit_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class MonthCount(BaseModel):
    year: int
    month: int
    count: int


class ProjectsDashboard(BaseModel):
    by_status: ProjectStatusSummary
    top_budget: List[ProjectRanked]
    top_execution: List[ProjectRanked]
    overcommitted: List[OvercommittedProject]
    creation_trend: List[MonthCount]


# --- 3. Requisitions ---

class RequisitionStatusAmount(BaseModel):
    status: str
    count: int
    total_amount: Decimal


class TopRequester(BaseModel):
    user_id: int
    username: str
    name: str
    count: int


class AgingBucket(BaseModel):
    over_3_days: int
    over_7_days: int
    over_15_days: int


class RequisitionsDashboard(BaseModel):
    by_status: List[RequisitionStatusAmount]
    avg_approval_hours: Optional[Decimal]
    approval_rate: Optional[Decimal]
    top_requesters: List[TopRequester]
    aging: AgingBucket


# --- 4. Budget Distribution ---

class ProjectBudgetBar(BaseModel):
    id: int
    project_code: str
    name: str
    commited: Decimal
    spent: Decimal
    available_balance: Decimal

    model_config = ConfigDict(from_attributes=True)


class MonthlySpend(BaseModel):
    year: int
    month: int
    total_spent: Decimal


class BudgetForecastPoint(BaseModel):
    year: int
    month: int
    projected_spent: Decimal
    projected_available: Decimal


class BudgetDistribution(BaseModel):
    by_project: List[ProjectBudgetBar]
    monthly_trend: List[MonthlySpend]
    forecast: List[BudgetForecastPoint]


# --- Full Dashboard ---

class DashboardResponse(BaseModel):
    financial_summary: FinancialSummary
    projects: ProjectsDashboard
    requisitions: RequisitionsDashboard
    budget_distribution: BudgetDistribution
