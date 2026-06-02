from src.entities import User, Session, Link
from sqlalchemy import select, exists
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Union
from src.exceptions import NotFoundError, SessionError, ConflictError
from datetime import date
"""
    User
"""
class UserRepository:
    allowed_keys = User.__table__.columns.keys()
    @staticmethod
    async def is_login_exists(login: str, asy: AsyncSession) -> bool:
        query = select(exists().where(User.login == login))
        result = await asy.execute(query)
        return result.scalar_one()
        
    @staticmethod
    async def get_all(asy: AsyncSession) -> List[User]:
        query = select(User)
        result = await asy.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_id(id: int, asy: AsyncSession) -> User:
        try:
            user = await asy.get_one(User, id)
            return user
        except NoResultFound:
            raise NotFoundError(f"User with id = {id} not found")
    
    @staticmethod
    async def get_by_login(login: str, asy: AsyncSession) -> User:
        try:
            query = select(User).where(User.login == login)
            result = await asy.execute(query)
            user: User = result.scalar_one() # login is unique key
            # can't return None. Will raise error if not found
            return user
        except NoResultFound:
            raise NotFoundError(f"User with login = {login} is not found")
    
    @staticmethod
    async def create(login: str, password: str, asy: AsyncSession):
        # need to commit and roll back if exception
        conflict_exception = ConflictError(f"User with login '{login}' already exists")
        if await UserRepository.is_login_exists(login, asy):
            raise conflict_exception
        new_user: User = User(login=login, password=password)
        asy.add(new_user)
    
    @staticmethod
    async def update(user: User, asy: AsyncSession, **kwargs) -> User:
        # need to commit and roll back if exception
        for key, value in kwargs.items():
            if key in UserRepository.allowed_keys:
                setattr(user, key, value)
            else:
                raise ValueError(f"{key} is not allowed for user")
    
    @staticmethod
    async def delete(user: User, asy: AsyncSession):
        asy.delete(user)
        
"""
    Session
"""
class SessionRepository:
    allowed_keys = Session.__table__.columns.keys()
    @staticmethod
    def is_active(session: Session):
        return session.expires_at >= date.today()
    
    @staticmethod
    async def get_all(asy: AsyncSession) -> List[Session]:
        query = select(Session)
        result = await asy.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_key(key: str, asy: AsyncSession) -> Session:
        try:
            return await asy.get_one(Session, key)
        except NoResultFound:
            print(f"Session with key = {key} not found")
            raise NotFoundError
    
    @staticmethod
    async def get_user(session: Session, asy: AsyncSession) -> User:
        try:
            user: User = await UserRepository.get_by_id(session.user_id, asy)
            return user
        except NoResultFound:
            raise NotFoundError
    
    @staticmethod
    async def get_expired(asy: AsyncSession) -> List[Session]:
        query = select(Session).where(Session.expires_at < date.today())
        result = await asy.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_active(asy: AsyncSession) -> List[Session]:
        query = select(Session).where(Session.expires_at >= date.today())
        result = await asy.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def create(
            key: str,
            user: User,
            created_at: date,
            expires_at: date,
            asy: AsyncSession
            ):
        new_session: Session = Session(key=key, user_id=user.id, created_at=created_at, expires_at=expires_at)
        asy.add(new_session)

    @staticmethod
    async def update(session: Session, asy: AsyncSession, **kwargs) -> Session:
        for key, value in kwargs.items():
            if key in SessionRepository.allowed_keys:
                setattr(session, key, value)
            else:
                raise ValueError(f"{key} is not allowed for session")
    
    @staticmethod
    async def delete(session: Session, asy: AsyncSession):
        asy.delete(session)
        
"""
    Links
"""
class LinkRepository:
    allowed_keys = Link.__table__.columns.keys()
    @staticmethod
    async def get_by_key(key: str, asy: AsyncSession) -> Link:
        try:
            link = await asy.get_one(Link, key)
            return link
        except NoResultFound:
            raise NotFoundError(f"Link with key = {key} not found")
    
    @staticmethod
    async def get_by_session_key(key: str, asy: AsyncSession) -> List[Link]:
        owner_user: User = await SessionRepository.get_user(key, asy)
        try:
            query = select(Link).where(Link.user_id == owner_user.id)
            result = await asy.execute(query)
            return list(result.scalars().all())
        except NoResultFound:
            print(f"Link by key {key} not found")
            raise NotFoundError
    
    @staticmethod
    async def get_owner(link: Link, asy: AsyncSession) -> User:
        return await UserRepository.get_by_id(link.user_id, asy)
    
    @staticmethod
    async def get_by_user(user: User, asy: AsyncSession) -> List[Link]:
        try:
            query = select(Link).where(Link.user_id == user.id)
            result = await asy.execute(query)
            return list(result.scalars().all())
        except NoResultFound:
            raise NotFoundError("Link by user {user} nnot found")
    
    @staticmethod
    async def get_all(asy: AsyncSession) -> List[Link]:
        query = select(Link)
        result = await asy.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_path(path: str, asy: AsyncSession) -> List[Link]:
        query = select(Link).where(Link.path == path)
        result = await asy.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_owner_and_path(user: User, path: str, asy: AsyncSession) -> List[Link]:
        query = select(Link).where((Link.path == path) & (Link.user_id == user.id))
        result = await asy.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def create(key: str, user: User, path: str, asy: AsyncSession): 
        new_link = Link(key=key, user_id=user.id, path=path)
        asy.add(new_link)
    
    @staticmethod
    async def update(link: Link, asy: AsyncSession, **kwargs) -> Link:
        for key, value in kwargs.items():
            if key in LinkRepository.allowed_keys:
                setattr(link, key, value)
            else:
                raise ValueError(f"{key} is not allowed for link")
    
    @staticmethod
    async def delete(link: Link, asy: AsyncSession):
        asy.delete(link)
        