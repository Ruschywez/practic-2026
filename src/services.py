from pathlib import Path
from datetime import date
from typing import List, Optional
import secrets
import os
from src.const import ENV_PATH, EXPIRATION_TIME
from src.entities import User, Session, Link
from src.repositories import UserRepository, SessionRepository, LinkRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.exceptions import InvalidSession, WrongPasswordError, ConflictError
import bcrypt

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
