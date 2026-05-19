from pathlib import Path
from datetime import date
from typing import List, Optional
import secrets
import os
from src.const import ENV_PATH, EXPIRATION_TIME
from src.entities import User, Session, Link
from src.repositories import UserRepository, SessionRepository, LinkRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.exceptions import InvalidSession, WrongPasswordError
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
        session = 
