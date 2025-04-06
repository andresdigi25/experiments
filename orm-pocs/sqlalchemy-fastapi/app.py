# app.py
import math
from typing import Optional, Any
from datetime import datetime
from fastapi import FastAPI, Query
from sqlalchemy import (
    String, Integer, ForeignKey, DateTime, select, func, or_, desc, asc
)
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column,
    relationship, selectinload, sessionmaker
)

# FastAPI app
app = FastAPI()

# ----------------------------
# Database Setup
# ----------------------------
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

# ----------------------------
# Models
# ----------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    posts: Mapped[list["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    author: Mapped["User"] = relationship(back_populates="posts")

# ----------------------------
# Utility: Pagination + Format
# ----------------------------
async def paginate(session: AsyncSession, stmt, page: int = 1, per_page: int = 10) -> dict[str, Any]:
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await session.scalar(count_stmt)
    total_pages = max(1, math.ceil(total / per_page)) if total else 1

    result = await session.execute(stmt.limit(per_page).offset((page - 1) * per_page))
    rows = result.scalars().all()

    def serialize(obj):
        return {
            "id": obj.id,
            "name": getattr(obj, "name", None),
            "email": getattr(obj, "email", None),
            "title": getattr(obj, "title", None),
            "content": getattr(obj, "content", None),
            "user_id": getattr(obj, "user_id", None),
            "created_at": obj.created_at.isoformat() if obj.created_at else None,
            "posts": [
                {"id": p.id, "title": p.title} for p in getattr(obj, "posts", [])
            ] if hasattr(obj, "posts") else None
        }

    return {
        "meta": {
            "page": page,
            "per_page": per_page,
            "total_items": total,
            "total_pages": total_pages,
        },
        "data": [serialize(r) for r in rows]
    }

# ----------------------------
# Query Builders
# ----------------------------
def build_user_query(search: Optional[str], sort_by: str, sort_order: str,
                     created_at_gte: Optional[datetime], created_at_lte: Optional[datetime]):
    stmt = select(User).options(selectinload(User.posts))

    if search:
        stmt = stmt.where(or_(User.name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%")))

    if created_at_gte:
        stmt = stmt.where(User.created_at >= created_at_gte)
    if created_at_lte:
        stmt = stmt.where(User.created_at <= created_at_lte)

    column = getattr(User, sort_by, User.created_at)
    stmt = stmt.order_by(asc(column) if sort_order == "asc" else desc(column))
    return stmt

def build_post_query(search: Optional[str], sort_by: str, sort_order: str,
                     created_at_gte: Optional[datetime], created_at_lte: Optional[datetime]):
    stmt = select(Post)

    if search:
        stmt = stmt.where(or_(Post.title.ilike(f"%{search}%"), Post.content.ilike(f"%{search}%")))

    if created_at_gte:
        stmt = stmt.where(Post.created_at >= created_at_gte)
    if created_at_lte:
        stmt = stmt.where(Post.created_at <= created_at_lte)

    column = getattr(Post, sort_by, Post.created_at)
    stmt = stmt.order_by(asc(column) if sort_order == "asc" else desc(column))
    return stmt

# ----------------------------
# Endpoints
# ----------------------------
from datetime import timedelta

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Add test data
    async with async_session() as session:
        now = datetime.utcnow()
        earlier = now - timedelta(days=3)

        user1 = User(
            name="Alice", email="alice@example.com", created_at=earlier,
            posts=[
                Post(title="Hello World", content="My first post!", created_at=earlier),
                Post(title="Another Day", content="FastAPI is awesome", created_at=now),
            ]
        )

        user2 = User(
            name="Bob", email="bob@example.com", created_at=now,
            posts=[
                Post(title="Bob’s Thoughts", content="I like databases", created_at=now),
                Post(title="Zebra", content="Sorting test post", created_at=now),
            ]
        )

        session.add_all([user1, user2])
        await session.commit()


@app.get("/users")
async def get_users(
    page: int = 1,
    per_page: int = 10,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", enum=["id", "name", "email", "created_at"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    created_at_gte: Optional[datetime] = None,
    created_at_lte: Optional[datetime] = None
):
    async with async_session() as session:
        stmt = build_user_query(search, sort_by, sort_order, created_at_gte, created_at_lte)
        return await paginate(session, stmt, page, per_page)

@app.get("/posts")
async def get_posts(
    page: int = 1,
    per_page: int = 10,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", enum=["id", "title", "created_at"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    created_at_gte: Optional[datetime] = None,
    created_at_lte: Optional[datetime] = None
):
    async with async_session() as session:
        stmt = build_post_query(search, sort_by, sort_order, created_at_gte, created_at_lte)
        return await paginate(session, stmt, page, per_page)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
