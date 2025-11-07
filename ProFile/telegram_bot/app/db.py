
from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Text, UniqueConstraint
from .config import settings

engine = create_async_engine(settings.db_url, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    boards: Mapped[list[Board]] = relationship(back_populates="user", cascade="all, delete-orphan")
    items: Mapped[list[Item]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Board(Base):
    __tablename__ = "boards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    user: Mapped[User] = relationship(back_populates="boards")
    items: Mapped[list[Item]] = relationship(back_populates="board", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_board_user_name"),)

class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    kind: Mapped[str] = mapped_column(String(32))  # link/photo/document/video/other
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tg_file_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    user: Mapped[User] = relationship(back_populates="items")
    board: Mapped[Board] = relationship(back_populates="items")
    __table_args__ = (UniqueConstraint("user_id", "title", name="uq_item_user_title"),)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_or_create_user(session: AsyncSession, tg_user_id: int) -> User:
    from sqlalchemy import select
    res = await session.execute(select(User).where(User.tg_user_id == tg_user_id))
    user = res.scalar_one_or_none()
    if user:
        return user
    user = User(tg_user_id=tg_user_id)
    session.add(user)
    await session.flush()
    # default board
    b = Board(user_id=user.id, name="Моя доска")
    session.add(b)
    await session.commit()
    return user

async def get_board_by_name(session: AsyncSession, user_id: int, name: str) -> Optional[Board]:
    from sqlalchemy import select, func
    res = await session.execute(
        select(Board).where(Board.user_id == user_id, func.lower(Board.name) == func.lower(name))
    )
    return res.scalar_one_or_none()

async def ensure_board(session: AsyncSession, user_id: int, name: str) -> Board:
    b = await get_board_by_name(session, user_id, name)
    if b: return b
    b = Board(user_id=user_id, name=name)
    session.add(b)
    await session.commit()
    await session.refresh(b)
    return b
