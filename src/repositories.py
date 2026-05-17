from src.entities import User, Session, Link
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

class UserRepository:
    async def get_all(self, session: AsyncSession) -> List[User]:
        query = select(User)
        result = await session.execute(query)
        return list(result.scalars().all())
    async def add_user(self, login: str, password: str, session: AsyncSession) -> User:
        new_user: User = User(login=login, password=password)
        try:
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user
        except KeyboardInterrupt:
            await session.rollback()
            raise ValueError(f"Account with this login is already exists")