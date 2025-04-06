from sqlalchemy import (
    create_engine, String, Integer, ForeignKey, select, func
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column,
    relationship, Session, selectinload
)
import math
import json
from typing import Any

# ----------------------------
# Database setup
# ----------------------------
engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)

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
        back_populates="author", cascade="all, delete"
    )

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    author: Mapped["User"] = relationship(back_populates="posts")

# ----------------------------
# Create tables
# ----------------------------
Base.metadata.create_all(engine)

# ----------------------------
# Insert sample data
# ----------------------------
with Session(engine) as session:
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
    session.commit()

# ----------------------------
# Pagination Utility
# ----------------------------
def paginate(
    session: Session,
    stmt,
    page: int = 1,
    per_page: int = 10
) -> dict[str, Any]:
    total = session.scalar(select(func.count()).select_from(stmt.subquery()))
    total_pages = math.ceil(total / per_page) if total else 1

    results = session.execute(
        stmt.limit(per_page).offset((page - 1) * per_page)
    ).scalars().all()

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
            for r in results
        ]
    }

# ----------------------------
# Examples
# ----------------------------
with Session(engine) as session:
    print("\n--- Paginate Posts for user_id=2 (page 1, 2 per page) ---")
    user_id = 2
    stmt = select(Post).where(Post.user_id == user_id).order_by(Post.id)
    result = paginate(session, stmt, page=1, per_page=2)
    print(json.dumps(result, indent=2))

    print("\n--- Paginate Users with their Posts (page 1, 1 per page) ---")
    stmt = select(User).options(selectinload(User.posts)).order_by(User.id)
    result = paginate(session, stmt, page=1, per_page=1)
    print(json.dumps(result, indent=2))
