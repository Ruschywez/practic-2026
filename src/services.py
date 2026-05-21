from pathlib import Path
from datetime import date
from typing import List, Optional, Dict, Union
import secrets
import os
from src.const import ENV_PATH, EXPIRATION_TIME, CONTAINER_PATH, CHUNK_SIZE
from src.entities import User, Session, Link
from src.repositories import UserRepository, SessionRepository, LinkRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.exceptions import InvalidSession, WrongPasswordError, ConflictError
import bcrypt
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import shutil
from datetime import datetime

class SessionService:
    @staticmethod
    async def is_session_key_valid(key: str, asy: AsyncSession) -> bool:
        session: Session = SessionRepository.get_by_key(key, asy)
        return session.expires_at >= date.today()
    @staticmethod
    async def get_user(key: str, asy: AsyncSession) -> User:
        if await SessionService.is_session_key_valid(key, asy):
            return await SessionRepository.get_user(key, asy)
        else:
            raise InvalidSession
    @staticmethod
    async def get_user_id(key: str, asy: AsyncSession) -> int:
        if await SessionService.is_session_key_valid(key, asy):
            return await SessionRepository.get_user_id(key, asy)
        else:
            raise InvalidSession
    @staticmethod
    async def get_session(key: str, asy: AsyncSession) -> Session:
        session: Session = SessionRepository.get_by_key(key, asy)
        if session.expires_at >= date.today():
            raise InvalidSession
        else:
            return session
    @staticmethod
    async def authentification(login: str, password: str, asy: AsyncSession) -> str:
        user: User = await UserRepository.get_by_login(login, asy)
        if not bcrypt.checkpw(password.encode(), str(user.password).encode()):
            raise WrongPasswordError()
        session: Session = await SessionRepository.create(
            key=secrets.token_urlsafe(192),
            user=user.id,
            created_at=date.today(),
            expires_at=date.today + EXPIRATION_TIME,
            asy=asy
        )
        return session.key
    @staticmethod
    async def extension(key: str, asy: AsyncSession):
        session: Session = await SessionService.get_session(key, asy)
        await SessionRepository.update(session, asy, expires_at=date.today + EXPIRATION_TIME)
    @staticmethod
    async def logout(key: str, asy: AsyncSession):
        return await SessionRepository.delete(key, asy)
class UserService:
    @staticmethod
    async def register(login: str, password: str, asy: AsyncSession) -> User:
        try:
            _ = await UserRepository.get_by_login(login, asy)
            raise ConflictError("User with this login already exists")
        except Exception:
            pass
        hash_password: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user: User = await UserRepository.create(login=login, password=hash_password, asy=asy)
        return user
    @staticmethod
    async def update_profile(key: str, asy: AsyncSession, **kwargs):
        user: User = await SessionService.get_user(key, asy)
        await UserRepository.update(user, asy, **kwargs)
    @staticmethod
    async def delete(key: str, asy: AsyncSession):
        user = await SessionService.get_user(key, asy)
        await UserRepository.delete(user, asy)
    @staticmethod
    async def get_info(key: str, asy: AsyncSession) -> dict:
        user = await SessionService.get_user(key, asy)
        return {
            "login": user.login,
        }
class FileService:
    @staticmethod
    async def is_owner(key: str, full_path: Union[str, Path], asy: AsyncSession) -> bool:
        user: User = SessionService.get_user(key, asy) # can raise
        if isinstance(full_path, Path):
            full_path = str(full_path)
        return True if user.login in full_path else False
    @staticmethod
    async def get_full_path(key:  str, path: Union[str, Path], asy: AsyncSession):
        # container_path (const: CONTAINER_PATH) / owner (login) / local_path (path)
        user: User = SessionService.get_user(key, asy)
        full_path = CONTAINER_PATH / user.login / path
        return full_path
    @staticmethod
    async def is_path_exists(full_path: str) -> bool:
        return Path.exists()
    @staticmethod
    async def upload_file(file_path: str, chunk_size: int = CHUNK_SIZE):
        # Need to take full path!
        loop = asyncio.get_event_loop()
        def open_file():
            return open(file_path, "rb")
        file = await loop.run_in_executor(None, open_file)
        try:
            while True:
                def read_chunk():
                    return file.read(chunk_size)
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
        obj_path.unlink
    @staticmethod
    async def create_users_directory(login: str):
        dir_path = CONTAINER_PATH / login
        await asyncio.to_thread(
            dir_path.mkdir,
            parents=True,
            exist_ok=True
        )
    @staticmethod
    async def change_users_directory(new_login: str, old_login: str):
        new_path = CONTAINER_PATH / new_login
        old_path = CONTAINER_PATH / old_login
        await asyncio.to_thread(old_path.rename, new_path)
    @staticmethod
    async def remove_users_directory(login: str):
        full_path = CONTAINER_PATH / login
        await asyncio.to_thread(full_path.unlink)
class LinkService:
    @staticmethod
    async def create_link(session_key: str, link_key: str) -> str:
        pass
    @staticmethod
    async def delete_link(key: str, link_id):
        pass
    @staticmethod
    async def check_directory(key: str) -> List[dict]