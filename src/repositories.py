from src.entities import User, Session, Link
from sqlalchemy import select, delete, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from src.exceptions import UserNotFoundError

class UserRepository:
    async def get_all(self, session: AsyncSession) -> List[User]:
        query = select(User)
        result = await session.execute(query)
        return list(result.scalars().all())
    async def get_by_id(self, id: int, session: AsyncSession) -> Optional[User]:
        try:
            user = await session.get_one(User, id)
            return user
        except NoResultFound:
            print(f"User with id = {id} not found")
            raise UserNotFoundError
    async def get_by_login(self, login: str, session: AsyncSession) -> User:
        try:
            query = select(User).where(User.login == login)
            result = await session.execute(query)
            user = result.scalar_one() # login is unique key
            # can't return None. Will raise error if not found
            return user
        except NoResultFound:
            print(f"User with login = {login} is not found")
            raise UserNotFoundError
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
    async def update(self, user: User, session: AsyncSession, **kwargs) -> User:
        allowed_keys = user.__table__.columns.keys()
        for key, value in kwargs.items():
            if key in allowed_keys:
                setattr(user, key, value)
            else:
                print(f"{key} is not allowed for user")
        try:
            await session.commit()
            await session.refresh(user)
            return user
        except Exception as e:
            await session.rollback()
            raise e
