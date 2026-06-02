from pathlib import Path
from datetime import date
from typing import List, Dict, Union
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from src.const import EXPIRATION_TIME, CONTAINER_PATH, CHUNK_SIZE
from src.entities import User, Session, Link
from src.repositories import UserRepository, SessionRepository, LinkRepository
from src.db_connect import async_session_factory
from src.exceptions import WrongPasswordError, ConflictError, SessionError, NotFoundError
import bcrypt
import asyncio
from datetime import datetime

"""
    there is two types of methods:
    1) tools - have 'asy' as an input arg
    2) transactions - don't have 'asy' as an input arg. This methods creating them
"""

class SessionService:
    @staticmethod
    async def is_session_key_valid(key: str, asy: AsyncSession) -> bool:
        session: Session = await SessionRepository.get_by_key(key, asy)
        return session.expires_at >= date.today()
    
    @staticmethod
    def is_session_valid(session: Session) -> bool:
        return session.expires_at >= date.today()
    
    @staticmethod
    async def check_session_key_valid(key: str, asy: AsyncSession):
        session: Session = await SessionRepository.get_by_key(key, asy)
        if session.expires_at < date.today():
            raise SessionError("Session expired")
    
    @staticmethod
    def check_session_valid(session: Session):
        if session.expires_at < date.today():
            raise SessionError("Session expired")
    
    @staticmethod
    async def get_user(key: str, asy: AsyncSession) -> User:
        await SessionService.check_session_key_valid(key, asy)
        return await SessionRepository.get_user(key, asy)
    
    @staticmethod
    async def get_user_id(key: str, asy: AsyncSession) -> int:
        await SessionService.check_session_key_valid(key, asy)
        return await SessionRepository.get_user_id(key, asy)
    
    @staticmethod
    async def get_session(key: str, asy: AsyncSession) -> Session:
        session: Session = await SessionRepository.get_by_key(key, asy)
        SessionService.check_session_valid(session)
        return session
    
    @staticmethod
    async def authentification(login: str, password: str) -> str:
        async with async_session_factory() as asy:
            user: User = await UserRepository.get_by_login(login, asy)
            if not bcrypt.checkpw(password.encode(), str(user.password).encode()):
                raise WrongPasswordError()
            session: Session = await SessionRepository.create(
                key=secrets.token_urlsafe(192),
                user=user.id,
                created_at=date.today(),
                expires_at=date.today() + EXPIRATION_TIME,
                asy=asy
            )
            return session.key
    
    @staticmethod
    async def extension(key: str):
        async with async_session_factory() as asy:
            session: Session = await SessionService.get_session(key, asy)
            await SessionRepository.update(session, asy, expires_at=date.today + EXPIRATION_TIME)
    
    @staticmethod
    async def logout(key: str):
        async with async_session_factory() as asy:
            session: Session = SessionService.get_session(key, asy)
            return await SessionRepository.delete(session, asy)
class UserService:
    @staticmethod
    async def register(login: str, password: str) -> User:
        async with async_session_factory() as asy:
            if await UserRepository.is_login_exists(login, asy):
                raise ConflictError("User with this login already exists")
            hash_password: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            user: User = await UserRepository.create(login=login, password=hash_password, asy=asy)
            FileService.create_users_directory(user.login)
            return user
    
    @staticmethod
    async def update_profile(key: str, **kwargs):
        async with async_session_factory() as asy:
            user: User = await SessionService.get_user(key, asy)
            await UserRepository.update(user, asy, **kwargs)
    
    @staticmethod
    async def delete_profile(key: str):
        async with async_session_factory() as asy:
            user = await SessionService.get_user(key, asy)
            FileService.remove_users_directory(user.login)
            await UserRepository.delete(user, asy)
    
    @staticmethod
    async def get_profile_info(key: str) -> dict:
        async with async_session_factory() as asy:
            user = await SessionService.get_user(key, asy)
            return {"login": user.login}
class FileService:
    @staticmethod
    async def is_owner(key: str, full_path: Union[str, Path], asy: AsyncSession) -> bool:
        user: User = await SessionService.get_user(key, asy) # can raise
        if isinstance(full_path, Path):
            full_path = str(full_path)
        expected_prefix = str(CONTAINER_PATH / user.login)
        return str(Path(full_path).resolve()).startswith(expected_prefix + os.sep)
    
    @staticmethod
    async def get_full_path(key:  str, path: Union[str, Path], asy: AsyncSession):
        # container_path (const: CONTAINER_PATH) / owner (login) / local_path (path)
        user: User = await SessionService.get_user(key, asy)
        full_path = CONTAINER_PATH / user.login / path
        return full_path
    
    @staticmethod
    async def is_path_exists(full_path: str) -> bool:
        return Path(full_path.exists())
    
    @staticmethod
    async def upload_file(file_path: str):
        # Need to take full path!
        loop = asyncio.get_event_loop()
        def open_file():
            return open(file_path, "rb")
        file = await loop.run_in_executor(None, open_file)
        try:
            while True:
                def read_chunk():
                    return file.read(CHUNK_SIZE)
                chunk = await loop.run_in_executor(None, read_chunk)
                if not chunk:
                    break
                yield chunk
        finally:
            await loop.run_in_executor(None, file.close)
    
    @staticmethod
    async def save_file(file: upload_file, destination: Union[str, Path]):
        # Need to take full path!ты 
        loop = asyncio.get_event_loop()
        def open_dest():
            return open(destination, "wb")
        dest_file = await loop.run_in_executor(None, open_dest)
        try:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                def write_chunk():
                    dest_file.write(chunk)
                await loop.run_in_executor(None, write_chunk)
        finally:
            await loop.run_in_executor(None, dest_file.close)
    
    @staticmethod
    async def check_file_info(full_path: Union[str, Path]) -> Dict:
        def _sync_check():
            path_obj = Path(full_path)
            data = {
                "name": path_obj.name,
                "size_bytes": path_obj.stat().st_size,
                "last_modified": datetime.fromtimestamp(path_obj.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
            }
            return data
        return await asyncio.to_thread(_sync_check)
    
    @staticmethod
    async def check_directory(full_path: Union[str, Path]) -> List[Dict]:
        def _sync_check():
            out = []
            path_obj = Path(full_path)
            for item in path_obj.iterdir():
                data = {
                    "name": item.name,
                    "size_bytes": item.stat().st_size,
                    "last_modified": datetime.fromtimestamp(item.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                }
                out.append(data)
            return out
        return await asyncio.to_thread(_sync_check)
    
    @staticmethod
    async def remove_file(full_path: Union[str, Path]):
        obj_path = Path(full_path)
        obj_path.unlink()
    
    @staticmethod
    async def create_users_directory(login: str):
        dir_path = CONTAINER_PATH / login
        await asyncio.to_thread(
            dir_path.mkdir,
            parents=True,
            exist_ok=True
        )
    
    @staticmethod
    async def remove_users_directory(login: str):
        full_path: Path = CONTAINER_PATH / login
        await asyncio.to_thread(full_path.rmtree())
    
class LinkService:
    @staticmethod
    async def create_link(session_key: str, path: Union[str, Path]) -> str:
        async with async_session_factory() as asy:
            user: User = await SessionService.get_user(session_key, asy)
            new_link: Link = await LinkRepository.create(
                key=secrets.token_urlsafe(192),
                user=user,
                path=str(path),
                asy=asy
            )
            return new_link.key
    
    @staticmethod
    async def delete_link(session: Union[str, Session], link: Union[Link, str]):
        async with async_session_factory() as asy:
            session_user: User = await SessionService.get_user(session, asy)
            link_user: User = await LinkRepository.get_owner(link, asy)
            if UserRepository.is_same(session_user, link_user):
                await LinkRepository.delete(link, asy)
    
    @staticmethod
    async def get_file_info_by_link(link: Union[str, Link]) -> Dict:
        async with async_session_factory() as asy:
            path_obj: Path = await LinkService.get_full_path(link, asy)
            def _sync_check():
                data = {
                        "name": path_obj.name,
                        "size_bytes": path_obj.stat().st_size,
                        "last_modified": datetime.fromtimestamp(path_obj.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    }
                return data
            return await asyncio.to_thread(_sync_check)
    
    @staticmethod
    async def get_file_stream_by_link(link: Union[str, Link]):
        async with async_session_factory() as asy:
            # Need to take full path!
            file_path: Path = await LinkService.get_full_path(link, asy)
            loop = asyncio.get_event_loop()
            def open_file():
                return open(file_path, "rb")
            file = await loop.run_in_executor(None, open_file)
            try:
                while True:
                    def read_chunk():
                        return file.read(CHUNK_SIZE)
                    chunk = await loop.run_in_executor(None, read_chunk)
                    if not chunk:
                        break
                    yield chunk
            finally:
                await loop.run_in_executor(None, file.close)
    
    @staticmethod
    async def get_full_path(link: Union[str, Link], asy: AsyncSession):
        # container_path (const: CONTAINER_PATH) / owner (login) / local_path (path)
        owner: User = await LinkRepository.get_owner(link, asy)
        if isinstance(link, str):
            link = await LinkRepository.get_by_key(link, asy)
        full_path = CONTAINER_PATH / owner.login / link.path
        return full_path