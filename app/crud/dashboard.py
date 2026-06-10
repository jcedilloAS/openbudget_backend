from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Optional

from app.models.project import Project
from app.models.requisition import Requisition
from app.models.user import User
from app.models.user_project import UserProject
from app.schemas.dashboard import (
    FinancialSummary,
    StatusCount, ProjectStatusSummary, ProjectRanked, OvercommittedProject, MonthCount,
    ProjectsDashboard,
    RequisitionStatusAmount, TopRequester, AgingBucket, RequisitionsDashboard,
    ProjectBudgetBar, MonthlySpend, BudgetForecastPoint, BudgetDistribution,
    DashboardResponse,
)


class CRUDDashboard:

    # ------------------------------------------------------------------ #
    #  Scope helpers
    # ------------------------------------------------------------------ #
    def _project_filter(self, query, user_id: Optional[int]):
        """Restrict the query to projects where the user is a member."""
        if user_id is None:
            return query
        return query.join(UserProject, UserProject.project_id == Project.id).filter(
            UserProject.user_id == user_id
        )

    def _requisition_filter(self, query, user_id: Optional[int]):
        """Restrict the query to requisitions created by the user."""
        if user_id is None:
            return query
        return query.filter(Requisition.created_by == user_id)

    # ------------------------------------------------------------------ #
    #  1. Financial Summary
    # ------------------------------------------------------------------ #
    def get_financial_summary(self, db: Session, user_id: Optional[int] = None) -> FinancialSummary:
        base = db.query(
            func.coalesce(func.sum(Project.initial_budget), 0).label("budget"),
            func.coalesce(func.sum(Project.commited), 0).label("commited"),
            func.coalesce(func.sum(Project.spent), 0).label("spent"),
            func.coalesce(func.sum(Project.available_balance), 0).label("available"),
        )
        row = self._project_filter(base, user_id).first()

        budget = Decimal(str(row.budget))
        commited = Decimal(str(row.commited))
        spent = Decimal(str(row.spent))
        available = Decimal(str(row.available))

        exec_pct = (spent / budget * 100).quantize(Decimal("0.01")) if budget else Decimal("0.00")
        commit_pct = ((commited + spent) / budget * 100).quantize(Decimal("0.01")) if budget else Decimal("0.00")

        return FinancialSummary(
            total_initial_budget=budget,
            total_commited=commited,
            total_spent=spent,
            total_available=available,
            execution_percentage=exec_pct,
            commitment_percentage=commit_pct,
        )

    # ------------------------------------------------------------------ #
    #  2. Projects Dashboard
    # ------------------------------------------------------------------ #
    def get_projects_dashboard(self, db: Session, user_id: Optional[int] = None) -> ProjectsDashboard:
        # --- by status ---
        rows = (
            self._project_filter(
                db.query(Project.status, func.count(Project.id)),
                user_id,
            )
            .group_by(Project.status)
            .all()
        )
        statuses = [StatusCount(status=s, count=c) for s, c in rows]
        total = sum(s.count for s in statuses)

        # --- top 5 budget ---
        top_budget_rows = (
            self._project_filter(db.query(Project), user_id)
            .order_by(Project.initial_budget.desc())
            .limit(5)
            .all()
        )
        top_budget = [self._project_ranked(p) for p in top_budget_rows]

        # --- top 5 execution % ---
        top_exec_rows = (
            self._project_filter(db.query(Project), user_id)
            .filter(Project.initial_budget > 0)
            .order_by((Project.spent / Project.initial_budget).desc())
            .limit(5)
            .all()
        )
        top_execution = [self._project_ranked(p) for p in top_exec_rows]

        # --- overcommitted ---
        oc_rows = (
            self._project_filter(db.query(Project), user_id)
            .filter((Project.commited + Project.spent) > Project.initial_budget)
            .all()
        )
        overcommitted = [
            OvercommittedProject(
                id=p.id,
                project_code=p.project_code,
                name=p.name,
                initial_budget=p.initial_budget,
                commited=p.commited,
                spent=p.spent,
                overcommit_amount=(p.commited + p.spent) - p.initial_budget,
            )
            for p in oc_rows
        ]

        # --- creation trend (last 12 months) ---
        twelve_months_ago = datetime.now() - timedelta(days=365)
        trend_rows = (
            self._project_filter(
                db.query(
                    extract("year", Project.created_at).label("year"),
                    extract("month", Project.created_at).label("month"),
                    func.count(Project.id).label("count"),
                ),
                user_id,
            )
            .filter(Project.created_at >= twelve_months_ago)
            .group_by("year", "month")
            .order_by("year", "month")
            .all()
        )
        creation_trend = [MonthCount(year=int(r.year), month=int(r.month), count=r.count) for r in trend_rows]

        return ProjectsDashboard(
            by_status=ProjectStatusSummary(statuses=statuses, total=total),
            top_budget=top_budget,
            top_execution=top_execution,
            overcommitted=overcommitted,
            creation_trend=creation_trend,
        )

    # ------------------------------------------------------------------ #
    #  3. Requisitions Dashboard
    # ------------------------------------------------------------------ #
    def get_requisitions_dashboard(self, db: Session, user_id: Optional[int] = None) -> RequisitionsDashboard:
        # --- by status with amounts ---
        rows = (
            self._requisition_filter(
                db.query(
                    Requisition.status,
                    func.count(Requisition.id),
                    func.coalesce(func.sum(Requisition.total_amount), 0),
                ),
                user_id,
            )
            .group_by(Requisition.status)
            .all()
        )
        by_status = [
            RequisitionStatusAmount(status=s, count=c, total_amount=Decimal(str(t)))
            for s, c, t in rows
        ]

        # --- avg approval time (hours) ---
        avg_row = (
            self._requisition_filter(
                db.query(
                    func.avg(
                        extract("epoch", Requisition.approved_at) - extract("epoch", Requisition.created_at)
                    )
                ),
                user_id,
            )
            .filter(Requisition.status == "approved", Requisition.approved_at.isnot(None))
            .scalar()
        )
        avg_approval_hours = (
            (Decimal(str(avg_row)) / Decimal("3600")).quantize(Decimal("0.01"))
            if avg_row
            else None
        )

        # --- approval rate ---
        processed = (
            self._requisition_filter(db.query(func.count(Requisition.id)), user_id)
            .filter(Requisition.status.in_(["approved", "rejected"]))
            .scalar()
        )
        approved_count = (
            self._requisition_filter(db.query(func.count(Requisition.id)), user_id)
            .filter(Requisition.status == "approved")
            .scalar()
        )
        approval_rate = (
            (Decimal(str(approved_count)) / Decimal(str(processed)) * 100).quantize(Decimal("0.01"))
            if processed
            else None
        )

        # --- top 5 requesters ---
        req_rows = (
            self._requisition_filter(
                db.query(
                    Requisition.created_by,
                    User.username,
                    User.name,
                    func.count(Requisition.id).label("cnt"),
                ),
                user_id,
            )
            .join(User, User.id == Requisition.created_by)
            .group_by(Requisition.created_by, User.username, User.name)
            .order_by(func.count(Requisition.id).desc())
            .limit(5)
            .all()
        )
        top_requesters = [
            TopRequester(user_id=r.created_by, username=r.username, name=r.name, count=r.cnt)
            for r in req_rows
        ]

        # --- aging buckets (submitted requisitions) ---
        now = datetime.now()
        over_3 = (
            self._requisition_filter(db.query(func.count(Requisition.id)), user_id)
            .filter(Requisition.status == "submitted", Requisition.created_at <= now - timedelta(days=3))
            .scalar()
        )
        over_7 = (
            self._requisition_filter(db.query(func.count(Requisition.id)), user_id)
            .filter(Requisition.status == "submitted", Requisition.created_at <= now - timedelta(days=7))
            .scalar()
        )
        over_15 = (
            self._requisition_filter(db.query(func.count(Requisition.id)), user_id)
            .filter(Requisition.status == "submitted", Requisition.created_at <= now - timedelta(days=15))
            .scalar()
        )

        return RequisitionsDashboard(
            by_status=by_status,
            avg_approval_hours=avg_approval_hours,
            approval_rate=approval_rate,
            top_requesters=top_requesters,
            aging=AgingBucket(over_3_days=over_3, over_7_days=over_7, over_15_days=over_15),
        )

    # ------------------------------------------------------------------ #
    #  4. Budget Distribution
    # ------------------------------------------------------------------ #
    def get_budget_distribution(self, db: Session, user_id: Optional[int] = None) -> BudgetDistribution:
        # --- bar chart: committed vs spent vs available per project ---
        projects = (
            self._project_filter(db.query(Project), user_id)
            .order_by(Project.initial_budget.desc())
            .all()
        )
        by_project = [
            ProjectBudgetBar(
                id=p.id,
                project_code=p.project_code,
                name=p.name,
                commited=p.commited,
                spent=p.spent,
                available_balance=p.available_balance,
            )
            for p in projects
        ]

        # --- monthly spend trend (last 12 months from approved requisitions) ---
        twelve_months_ago = datetime.now() - timedelta(days=365)
        trend_rows = (
            self._requisition_filter(
                db.query(
                    extract("year", Requisition.approved_at).label("year"),
                    extract("month", Requisition.approved_at).label("month"),
                    func.coalesce(func.sum(Requisition.total_amount), 0).label("total"),
                ),
                user_id,
            )
            .filter(
                Requisition.status == "approved",
                Requisition.approved_at.isnot(None),
                Requisition.approved_at >= twelve_months_ago,
            )
            .group_by("year", "month")
            .order_by("year", "month")
            .all()
        )
        monthly_trend = [
            MonthlySpend(year=int(r.year), month=int(r.month), total_spent=Decimal(str(r.total)))
            for r in trend_rows
        ]

        # --- forecast: linear projection for next 3 months ---
        forecast = self._compute_forecast(db, monthly_trend, user_id)

        return BudgetDistribution(
            by_project=by_project,
            monthly_trend=monthly_trend,
            forecast=forecast,
        )

    # ------------------------------------------------------------------ #
    #  Full dashboard
    # ------------------------------------------------------------------ #
    def get_full_dashboard(self, db: Session, user_id: Optional[int] = None) -> DashboardResponse:
        return DashboardResponse(
            financial_summary=self.get_financial_summary(db, user_id=user_id),
            projects=self.get_projects_dashboard(db, user_id=user_id),
            requisitions=self.get_requisitions_dashboard(db, user_id=user_id),
            budget_distribution=self.get_budget_distribution(db, user_id=user_id),
        )

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _project_ranked(p) -> ProjectRanked:
        budget = Decimal(str(p.initial_budget)) if p.initial_budget else Decimal("0")
        spent = Decimal(str(p.spent)) if p.spent else Decimal("0")
        exec_pct = (spent / budget * 100).quantize(Decimal("0.01")) if budget else Decimal("0.00")
        return ProjectRanked(
            id=p.id,
            project_code=p.project_code,
            name=p.name,
            initial_budget=p.initial_budget,
            commited=p.commited,
            spent=p.spent,
            available_balance=p.available_balance,
            execution_percentage=exec_pct,
            status=p.status,
        )

    def _compute_forecast(
        self,
        db: Session,
        monthly_trend: List[MonthlySpend],
        user_id: Optional[int] = None,
    ) -> List[BudgetForecastPoint]:
        if len(monthly_trend) < 2:
            return []

        # Simple linear regression on last 6 data-points
        recent = monthly_trend[-6:]
        n = len(recent)
        xs = list(range(n))
        ys = [float(m.total_spent) for m in recent]
        x_mean = sum(xs) / n
        y_mean = sum(ys) / n
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
        denominator = sum((x - x_mean) ** 2 for x in xs)
        slope = numerator / denominator if denominator else 0
        intercept = y_mean - slope * x_mean

        # Total available budget (scoped to user's projects when applicable)
        total_available_row = self._project_filter(
            db.query(func.coalesce(func.sum(Project.available_balance), 0)),
            user_id,
        ).scalar()
        remaining = Decimal(str(total_available_row))

        # Project next 3 months
        last = recent[-1]
        year, month = last.year, last.month
        cumulative_spent = Decimal("0")
        forecast = []
        for i in range(1, 4):
            month += 1
            if month > 12:
                month = 1
                year += 1
            projected = max(Decimal(str(slope * (n - 1 + i) + intercept)).quantize(Decimal("0.01")), Decimal("0"))
            cumulative_spent += projected
            forecast.append(BudgetForecastPoint(
                year=year,
                month=month,
                projected_spent=projected,
                projected_available=remaining - cumulative_spent,
            ))

        return forecast


dashboard = CRUDDashboard()
