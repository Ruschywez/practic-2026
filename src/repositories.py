from src.entities import User, Session, Link
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Union
from src.exceptions import NotFoundError
from datetime import date
"""
    User
"""
class UserRepository:
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
            print(f"User with id = {id} not found")
            raise NotFoundError
    
    @staticmethod
    async def get_by_login(login: str, asy: AsyncSession) -> User:
        try:
            query = select(User).where(User.login == login)
            result = await asy.execute(query)
            user = result.scalar_one() # login is unique key
            # can't return None. Will raise error if not found
            return user
        except NoResultFound:
            print(f"User with login = {login} is not found")
            raise NotFoundError
    
    @staticmethod
    async def create(login: str, password: str, asy: AsyncSession) -> User:
        try:
            await UserRepository.get_by_login(login, asy)
            raise ValueError(f"User with login '{login} already exists")
        except NotFoundError:
            pass
        new_user: User = User(login=login, password=password)
        asy.add(new_user)
        try:
            await asy.commit()
            await asy.refresh(new_user)
            return new_user
        except IntegrityError:
            await asy.rollback()
            raise ValueError(f"User with login '{login} already exists")
    
    @staticmethod
    async def update(user: User, asy: AsyncSession, **kwargs) -> User:
        allowed_keys = user.__table__.columns.keys()
        for key, value in kwargs.items():
            if key in allowed_keys:
                setattr(user, key, value)
            else:
                print(f"{key} is not allowed for user")
        try:
            await asy.commit()
            await asy.refresh(user)
            return user
        except Exception as e:
            await asy.rollback()
            raise e
    
    @staticmethod
    async def delete(user: User, asy: AsyncSession):
        asy.delete(user)
        await asy.commit()
"""
    Session
"""
class SessionRepository:
    @staticmethod
    async def get_all(asy: AsyncSession) -> List[Session]:
        query = select(Session)
        result = await asy.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_key(key: str, asy: AsyncSession) -> Session:
        try:
            session = await asy.get_one(Session, key)
            return session
        except NoResultFound:
            print(f"Session with key = {key} not found")
            raise NotFoundError
    
    @staticmethod
    async def get_user(key: str, asy: AsyncSession) -> User:
        try:
            session = await SessionRepository.get_by_key(key, asy)
            user: User = await UserRepository.get_by_id(session.user_id, asy)
            return user
        except NoResultFound:
            raise NotFoundError
    
    @staticmethod
    async def get_user_id(key: str, asy: AsyncSession) -> int:
        try:
            session = await SessionRepository.get_by_key(key, asy)
            return session.user_id
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
            user: Union[User, int],
            created_at: date,
            expires_at: date,
            asy: AsyncSession
            ) -> Session:
        if isinstance(user, User):
            user_id = user.id
        else:
            user_obj = await UserRepository.get_by_id(user, asy)
            user_id = user_obj.id
        new_session: Session = Session(key=key, user_id=user_id, created_at=created_at, expires_at=expires_at)
        try:
            asy.add(new_session)
            await asy.commit()
            await asy.refresh(new_session)
            return new_session
        except Exception as e:
            await asy.rollback()
            raise e

    @staticmethod
    async def update(session: Session, asy: AsyncSession, **kwargs) -> Session:
        allowed_keys = session.__table__.columns.keys()
        for key, value in kwargs.items():
            if key in allowed_keys:
                setattr(session, key, value)
            else:
                print(f"{key} is not allowed for session")
        try:
            await asy.commit()
            await asy.refresh(session)
            return session
        except Exception as e:
            await asy.rollback()
            raise e
    
    @staticmethod
    async def delete(session: Union[Session, str], asy: AsyncSession):
        if isinstance(session, Session):
            session_to_delete = session
        else:
            session_to_delete = SessionRepository.get_by_key(session)
        asy.delete(session_to_delete)
        await asy.commit()
"""
    Links
"""
class LinkRepository:
    @staticmethod
    async def get_by_key(key: str, asy: AsyncSession) -> List[Link]:
        query = select(Link).where(Link.key == key)
        result = await asy.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_key(key: str, asy: AsyncSession) -> List[Link]:
        owner_user: User = SessionRepository.get_user(key, Session)
        try:
            query = select(Link).where(Link.user_id == owner_user.id)
            result = await asy.execute(query)
            return list(result.scalars().all())
        except NoResultFound:
            print(f"Link by key {key} not found")
            raise NotFoundError
    
    @staticmethod
    async def get_by_user(user: Union[User, int], asy: AsyncSession) -> List[Link]:
        try:
            if isinstance(user, User):
                owner_user: User = user
            else:
                owner_user: User = UserRepository.get_by_id(user, asy)
            query = select(Link).where(Link.user_id == owner_user.id)
            result = await asy.execute(query)
            return list(result.scalars().all())
        except NoResultFound:
            print("Link by user {user} nnot found")
            raise NotFoundError
    
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
    async def get_by_owner_and_path(user: Union[User, int], path: str, asy: AsyncSession) -> List[Link]:
        if isinstance(user, User):
            owner_user: User = user
        else:
            owner_user: User = UserRepository.get_by_id(user)
        query = select(Link).where(Link.path == path & Link.user_id == owner_user.id)
        result = await asy.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def create(key: str, user: Union[User, int], path: str, asy: AsyncSession) -> Link:
        if isinstance(user, User):
            owner_user: User = user
        else:
            owner_user: User = UserRepository.get_by_id(user, asy)
        new_link = Link(key=key, user_id=owner_user.id, path=path)
        try:
            asy.add(new_link)
            await asy.commit()
            await asy.refresh(new_link)
            return new_link
        except Exception as e:
            await asy.rollback()
            raise e
    
    @staticmethod
    async def update(link: Link, asy: AsyncSession, **kwargs) -> Link:
        allowed_keys = link.__table__.columns.keys()
        for key, value in kwargs.items():
            if key in allowed_keys:
                setattr(link, key, value)
            else:
                print(f"{key} is not allowed for link")
        try:
            await asy.commit()
            await asy.refresh(link)
            return link
        except Exception as e:
            await asy.rollback()
            raise e
    
    @staticmethod
    async def delete(link: Union[Link, str], asy: AsyncSession):
        if isinstance(link, Link):
            link_to_delete = link
        else:
            link_to_delete = LinkRepository.get_by_key(link)
        asy.delete(link_to_delete)
        await asy.commit()