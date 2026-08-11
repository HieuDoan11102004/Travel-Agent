from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Base(DeclarativeBase):
    pass


class ItineraryDB(Base):
    __tablename__ = "itineraries"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    destination: Mapped[str] = mapped_column(String(100), nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    people: Mapped[int] = mapped_column(Integer, nullable=False)
    budget: Mapped[int] = mapped_column(Integer, nullable=False)
    preferences_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class SearchHistoryDB(Base):
    __tablename__ = "search_history"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    results_count: Mapped[int] = mapped_column(Integer, default=0)
    response_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PostgresClient:
    """Async PostgreSQL client for persistent storage."""

    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        await self.engine.dispose()

    async def create_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.async_session() as session:
            yield session

    async def save_itinerary(self, data: dict) -> str:
        async with self.async_session() as session:
            itinerary = ItineraryDB(**data)
            session.add(itinerary)
            await session.commit()
            return itinerary.id

    async def get_itinerary(self, itinerary_id: str) -> dict | None:
        async with self.async_session() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(ItineraryDB).where(ItineraryDB.id == itinerary_id)
            )
            itinerary = result.scalar_one_or_none()
            if itinerary:
                return {
                    "id": itinerary.id,
                    "user_input": itinerary.user_input,
                    "destination": itinerary.destination,
                    "days": itinerary.days,
                    "people": itinerary.people,
                    "budget": itinerary.budget,
                    "preferences_json": itinerary.preferences_json,
                    "result_json": itinerary.result_json,
                    "status": itinerary.status,
                    "created_at": itinerary.created_at.isoformat(),
                    "updated_at": itinerary.updated_at.isoformat(),
                }
            return None

    async def update_itinerary_result(self, itinerary_id: str, result_json: dict) -> None:
        async with self.async_session() as session:
            from sqlalchemy import select, update

            await session.execute(
                update(ItineraryDB)
                .where(ItineraryDB.id == itinerary_id)
                .values(result_json=result_json, status="completed")
            )
            await session.commit()

    async def save_search(self, query: str, results_count: int, response_time_ms: int) -> None:
        async with self.async_session() as session:
            search = SearchHistoryDB(
                query=query,
                results_count=results_count,
                response_time_ms=response_time_ms,
            )
            session.add(search)
            await session.commit()
