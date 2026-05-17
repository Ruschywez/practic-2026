from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.const import DB_URL

engine = create_async_engine(DB_URL, echo=True)
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)