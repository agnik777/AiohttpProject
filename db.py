import os
import datetime

from sqlalchemy.ext.asyncio import (AsyncSession, create_async_engine,
                                    AsyncAttrs, async_sessionmaker)
from sqlalchemy.orm import (DeclarativeBase, mapped_column, MappedColumn,
                            relationship)
from sqlalchemy import Integer, String, Text, DateTime, func, ForeignKey


POSTGRES_USER = os.getenv("POSTGRES_USER", "agnik")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "12345")
POSTGRES_DB = os.getenv("POSTGRES_DB", "aiohttp")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5431")

POSTGRES_DSN = (
    f"postgresql+asyncpg://"
    f"{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


engine = create_async_engine(POSTGRES_DSN)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase, AsyncAttrs):
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)

    @property
    def id_dict(self):
        return {"id": self.id}


class User(Base):
    __tablename__ = 'users'
    name: MappedColumn[str] = mapped_column(String(20))
    email: MappedColumn[str] = mapped_column(String, unique=True)
    password: MappedColumn[str] = mapped_column(String)
    registration_time: MappedColumn[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    announcements = relationship("Announcement",
                                 back_populates="user",
                                 cascade="all, delete-orphan")

    @property
    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "registration_time": self.registration_time.isoformat()
        }


class Announcement(Base):
    __tablename__ = 'announcements'
    title: MappedColumn[str] = mapped_column(String(100))
    description: MappedColumn[str] = mapped_column(Text)
    owner: MappedColumn[int] = mapped_column(Integer, ForeignKey(
        'users.id', ondelete='CASCADE'))
    creation_time: MappedColumn[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    user = relationship("User", back_populates="announcements")

    @property
    def dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "owner": self.owner,
            "creation_time": self.creation_time.isoformat()
        }


async def init_orm():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_orm():
    await engine.dispose()
