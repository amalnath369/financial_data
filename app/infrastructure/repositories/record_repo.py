from __future__ import annotations
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.record import FinancialRecord
from app.domain.enums.enum import RecordType
from app.domain.repositories.record_repo import (
    AbstractRecordRepository, RecordFilters,
    DashboardSummary, CategoryTotal, TrendPoint,
)
from app.infrastructure.database.models.record import FinancialRecordModel
from app.infrastructure.database.models.category import CategoryModel
from app.infrastructure.repositories.mappers import map_record


class SQLAlchemyRecordRepository(AbstractRecordRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> FinancialRecord | None:
        result = await self._session.execute(
            select(FinancialRecordModel)
            .options(selectinload(FinancialRecordModel.category))
            .where(
                FinancialRecordModel.id == id,
                FinancialRecordModel.is_deleted == False,
            )
        )
        m = result.scalar_one_or_none()
        return map_record(m) if m else None

    async def get_by_id_with_category(self, id: uuid.UUID) -> FinancialRecord | None:
        return await self.get_by_id(id)

    async def get_all(
        self, filters: RecordFilters
    ) -> tuple[list[FinancialRecord], int]:
        stmt = (
            select(FinancialRecordModel)
            .options(selectinload(FinancialRecordModel.category))
            .where(FinancialRecordModel.is_deleted == False)
        )

        # dynamic filter chaining — still 1 query
        if filters.user_id:
            stmt = stmt.where(FinancialRecordModel.user_id == filters.user_id)
        if filters.record_type:
            stmt = stmt.where(FinancialRecordModel.record_type == filters.record_type)
        if filters.category_id:
            stmt = stmt.where(FinancialRecordModel.category_id == filters.category_id)
        if filters.date_from:
            stmt = stmt.where(FinancialRecordModel.record_date >= filters.date_from)
        if filters.date_to:
            stmt = stmt.where(FinancialRecordModel.record_date <= filters.date_to)
        if filters.min_amount:
            stmt = stmt.where(FinancialRecordModel.amount >= filters.min_amount)
        if filters.max_amount:
            stmt = stmt.where(FinancialRecordModel.amount <= filters.max_amount)
        if filters.search:
            # PostgreSQL full-text search via GIN index
            stmt = stmt.where(
                FinancialRecordModel.search_vector.op("@@")(
                    func.plainto_tsquery("english", filters.search)
                )
            )

        # count before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self._session.scalar(count_stmt)

        # paginate
        stmt = (
            stmt
            .order_by(FinancialRecordModel.record_date.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
        result = await self._session.execute(stmt)
        records = [map_record(m) for m in result.scalars().all()]
        return records, total or 0

    async def get_dashboard_summary(
        self,
        user_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> DashboardSummary:
        # single aggregation query — no Python summing
        stmt = select(
            func.coalesce(
                func.sum(FinancialRecordModel.amount).filter(
                    FinancialRecordModel.record_type == RecordType.INCOME
                ), 0
            ).label("total_income"),
            func.coalesce(
                func.sum(FinancialRecordModel.amount).filter(
                    FinancialRecordModel.record_type == RecordType.EXPENSE
                ), 0
            ).label("total_expense"),
            func.count(FinancialRecordModel.id).label("total_records"),
        ).where(FinancialRecordModel.is_deleted == False)

        if user_id:
            stmt = stmt.where(FinancialRecordModel.user_id == user_id)
        if date_from:
            stmt = stmt.where(FinancialRecordModel.record_date >= date_from)
        if date_to:
            stmt = stmt.where(FinancialRecordModel.record_date <= date_to)

        row = (await self._session.execute(stmt)).one()
        income = Decimal(str(row.total_income))
        expense = Decimal(str(row.total_expense))

        return DashboardSummary(
            total_income=income,
            total_expense=expense,
            net_balance=income - expense,
            total_records=row.total_records,
        )

    async def get_category_totals(
        self,
        user_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[CategoryTotal]:
        # single GROUP BY query — no N+1
        stmt = (
            select(
                FinancialRecordModel.category_id,
                CategoryModel.name.label("category_name"),
                FinancialRecordModel.record_type,
                func.sum(FinancialRecordModel.amount).label("total"),
                func.count(FinancialRecordModel.id).label("count"),
            )
            .join(CategoryModel, FinancialRecordModel.category_id == CategoryModel.id)
            .where(FinancialRecordModel.is_deleted == False)
            .group_by(
                FinancialRecordModel.category_id,
                CategoryModel.name,
                FinancialRecordModel.record_type,
            )
            .order_by(text("total DESC"))
        )

        if user_id:
            stmt = stmt.where(FinancialRecordModel.user_id == user_id)
        if date_from:
            stmt = stmt.where(FinancialRecordModel.record_date >= date_from)
        if date_to:
            stmt = stmt.where(FinancialRecordModel.record_date <= date_to)

        result = await self._session.execute(stmt)
        return [
            CategoryTotal(
                category_id=row.category_id,
                category_name=row.category_name,
                record_type=row.record_type,
                total=Decimal(str(row.total)),
                count=row.count,
            )
            for row in result.all()
        ]

    async def get_trends(
        self,
        period: str,
        user_id: uuid.UUID | None = None,
        limit: int = 12,
    ) -> list[TrendPoint]:
        # date_trunc determines monthly vs weekly
        trunc = "month" if period == "monthly" else "week"
        period_expr = func.date_trunc(trunc, FinancialRecordModel.record_date)

        stmt = (
            select(
                period_expr.label("period"),
                FinancialRecordModel.record_type,
                func.sum(FinancialRecordModel.amount).label("total"),
                func.count(FinancialRecordModel.id).label("count"),
            )
            .where(FinancialRecordModel.is_deleted == False)
            .group_by(period_expr, FinancialRecordModel.record_type)
            .order_by(text("period DESC"))
            .limit(limit)
        )

        if user_id:
            stmt = stmt.where(FinancialRecordModel.user_id == user_id)

        result = await self._session.execute(stmt)
        return [
            TrendPoint(
                period=row.period.strftime(
                    "%Y-%m" if period == "monthly" else "%Y-W%W"
                ),
                record_type=row.record_type,
                total=Decimal(str(row.total)),
                count=row.count,
            )
            for row in result.all()
        ]

    async def get_recent(
        self,
        user_id: uuid.UUID | None = None,
        limit: int = 10,
    ) -> list[FinancialRecord]:
        stmt = (
            select(FinancialRecordModel)
            .options(selectinload(FinancialRecordModel.category))
            .where(FinancialRecordModel.is_deleted == False)
            .order_by(FinancialRecordModel.record_date.desc())
            .limit(limit)
        )
        if user_id:
            stmt = stmt.where(FinancialRecordModel.user_id == user_id)

        result = await self._session.execute(stmt)
        return [map_record(m) for m in result.scalars().all()]

    async def add(self, record: FinancialRecord) -> FinancialRecord:
        m = FinancialRecordModel(
            id=record.id,
            user_id=record.user_id,
            amount=record.amount.to_decimal(),
            record_type=record.record_type,
            category_id=record.category_id,
            record_date=record.record_date,
            notes=record.notes,
        )
        self._session.add(m)
        await self._session.flush()
        return record

    async def update(self, record: FinancialRecord) -> FinancialRecord:
        result = await self._session.execute(
            select(FinancialRecordModel).where(FinancialRecordModel.id == record.id)
        )
        m = result.scalar_one()
        m.amount = record.amount.to_decimal()
        m.record_type = record.record_type
        m.category_id = record.category_id
        m.record_date = record.record_date
        m.notes = record.notes
        m.is_deleted = record.is_deleted
        m.deleted_at = record.deleted_at
        m.deleted_by = record.deleted_by
        await self._session.flush()
        return record

    async def delete(self, record: FinancialRecord) -> None:
        result = await self._session.execute(
            select(FinancialRecordModel).where(FinancialRecordModel.id == record.id)
        )
        m = result.scalar_one()
        await self._session.delete(m)
        await self._session.flush()