from typing import TypeVar, Generic, Type, Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]):
        self._session = session
        self._model = model

    async def add(self, entity: T) -> T:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        stmt = select(self._model).where(self._model.id == entity_id)
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_all(self) -> List[T]:
        stmt = select(self._model)
        result = await self._session.execute(stmt)
        return result.unique().scalars().all()

    async def delete(self, entity: T) -> None:
        await self._session.delete(entity)
        await self._session.flush()

    async def update(self, entity: T) -> T:
        await self._session.flush()
        await self._session.refresh(entity)
        return entity
