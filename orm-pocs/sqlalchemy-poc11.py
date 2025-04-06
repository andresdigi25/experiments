import asyncio
import math
import json
from typing import Any
from datetime import datetime, timedelta

from sqlalchemy import (
    String, Integer, ForeignKey, DateTime,
    select, func, or_, desc, asc
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine, create_async_engine, AsyncSession
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column,
    relationship, selectinload, sessionmaker
)

# ----------------------------
# Async Engine & Base Setup
# ----------------------------
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

# ----------------------------
# ORM Models
# ----------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    posts: Mapped[list["Post"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    author: Mapped["User"] = relationship(back_populates="posts")

# ----------------------------
# Pagination Utility
# ----------------------------
async def paginate(
    session: AsyncSession,
    stmt,
    page: int = 1,
    per_page: int = 10
) -> dict[str, Any]:
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await session.scalar(count_stmt)
    total_pages = max(1, math.ceil(total / per_page)) if total else 1

    result = await session.execute(
        stmt.limit(per_page).offset((page - 1) * per_page)
    )
    rows = result.scalars().all()

    return {
        "meta": {
            "page": page,
            "per_page": per_page,
            "total_items": total,
            "total_pages": total_pages,
        },
        "data": [
            {
                "id": r.id,
                "title": getattr(r, "title", None),
                "content": getattr(r, "content", None),
                "user_id": getattr(r, "user_id", None),
                "name": getattr(r, "name", None),
                "email": getattr(r, "email", None),
                "created_at": getattr(r, "created_at", None).isoformat() if hasattr(r, "created_at") else None,
                "posts": [
                    {"id": p.id, "title": p.title}
                    for p in getattr(r, "posts", [])
                ] if hasattr(r, "posts") else None
            }
            for r in rows
        ]
    }

# ----------------------------
# Query Builder: Post
# ----------------------------
def build_post_query(
    search: str = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    created_at_gte: datetime = None,
    created_at_lte: datetime = None
):
    stmt = select(Post)

    if search:
        stmt = stmt.where(
            or_(
                Post.title.ilike(f"%{search}%"),
                Post.content.ilike(f"%{search}%")
            )
        )

    if created_at_gte:
        stmt = stmt.where(Post.created_at >= created_at_gte)
    if created_at_lte:
        stmt = stmt.where(Post.created_at <= created_at_lte)

    sort_column = getattr(Post, sort_by, Post.created_at)
    stmt = stmt.order_by(asc(sort_column) if sort_order == "asc" else desc(sort_column))

    return stmt

# ----------------------------
# Query Builder: User
# ----------------------------
def build_user_query(
    search: str = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    created_at_gte: datetime = None,
    created_at_lte: datetime = None
):
    stmt = select(User).options(selectinload(User.posts))

    if search:
        stmt = stmt.where(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )

    if created_at_gte:
        stmt = stmt.where(User.created_at >= created_at_gte)
    if created_at_lte:
        stmt = stmt.where(User.created_at <= created_at_lte)

    sort_column = getattr(User, sort_by, User.created_at)
    stmt = stmt.order_by(asc(sort_column) if sort_order == "asc" else desc(sort_column))

    return stmt

# ----------------------------
# Main async runner
# ----------------------------
async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    now = datetime.utcnow()
    earlier = now - timedelta(days=3)

    async with AsyncSessionLocal() as session:
        user1 = User(
            name="Alice", email="alice@example.com", created_at=earlier,
            posts=[
                Post(title="First Post", content="Hello World", created_at=earlier),
                Post(title="Second Post", content="Another one", created_at=now),
            ]
        )
        user2 = User(
            name="Bob", email="bob@example.com", posts=[
                Post(title="Bob's Post", content="Bob's content", created_at=now),
                Post(title="Zebra", content="Last post", created_at=now),
            ]
        )
        session.add_all([user1, user2])
        await session.commit()

    # Example: Search and sort posts
    async with AsyncSessionLocal() as session:
        print("\n--- Paginate Posts with Search & Date Range ---")
        stmt = build_post_query(
            search="post",
            sort_by="title",
            sort_order="asc",
            created_at_gte=now - timedelta(days=1)
        )
        result = await paginate(session, stmt, page=1, per_page=5)
        print(json.dumps(result, indent=2))

    # Example: Search and sort users
    async with AsyncSessionLocal() as session:
        print("\n--- Paginate Users with Filters ---")
        stmt = build_user_query(
            search="bob",
            sort_by="name",
            sort_order="desc"
        )
        result = await paginate(session, stmt, page=1, per_page=5)
        print(json.dumps(result, indent=2))

# ----------------------------
# Run it
# ----------------------------
if __name__ == "__main__":
    asyncio.run(main())
