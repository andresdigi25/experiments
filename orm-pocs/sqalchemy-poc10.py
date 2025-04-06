import asyncio
import math
import json
from typing import Any

from sqlalchemy import String, Integer, ForeignKey, select, func
from sqlalchemy.ext.asyncio import (
    AsyncEngine, create_async_engine, AsyncSession
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column,
    relationship, selectinload, sessionmaker
)

# ----------------------------
# Async Engine & Session
# ----------------------------
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ----------------------------
# Declarative Base
# ----------------------------
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
    posts: Mapped[list["Post"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    author: Mapped["User"] = relationship(back_populates="posts")

# ----------------------------
# Async Pagination Utility
# ----------------------------
async def paginate(
    session: AsyncSession,
    stmt,
    page: int = 1,
    per_page: int = 10
) -> dict[str, Any]:
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await session.scalar(count_stmt)
    total_pages = math.ceil(total / per_page) if total else 1

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
                "posts": [
                    {"id": p.id, "title": p.title}
                    for p in getattr(r, "posts", [])
                ] if hasattr(r, "posts") else None
            }
            for r in rows
        ]
    }

# ----------------------------
# Async Main Program
# ----------------------------
async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Insert sample data
        user1 = User(name="Alice", email="alice@example.com", posts=[
            Post(title="Post 1", content="Hello World"),
            Post(title="Post 2", content="Another one"),
        ])
        user2 = User(name="Bob", email="bob@example.com", posts=[
            Post(title="Post 3", content="Bob's post"),
            Post(title="Post 4", content="Bob's second post"),
            Post(title="Post 5", content="Bob's third post"),
        ])
        session.add_all([user1, user2])
        await session.commit()

    # Paginate posts for user_id=2
    async with AsyncSessionLocal() as session:
        print("\n--- Paginate Posts for user_id=2 (Page 1, 2 per page) ---")
        stmt = select(Post).where(Post.user_id == 2).order_by(Post.id)
        result = await paginate(session, stmt, page=1, per_page=2)
        print(json.dumps(result, indent=2))

    # Paginate users with posts
    async with AsyncSessionLocal() as session:
        print("\n--- Paginate Users with their Posts (Page 1, 1 per page) ---")
        stmt = select(User).options(selectinload(User.posts)).order_by(User.id)
        result = await paginate(session, stmt, page=1, per_page=1)
        print(json.dumps(result, indent=2))

# ----------------------------
# Run the async program
# ----------------------------
if __name__ == "__main__":
    asyncio.run(main())
