from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any
from datetime import datetime, timedelta
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
import logging
import math

# ----------------------------
# Logging Configuration
# ----------------------------
from logging.handlers import RotatingFileHandler

log_handler = RotatingFileHandler("app3.log", maxBytes=1000000, backupCount=3)
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
logger.addHandler(console_handler)

# ----------------------------
# FastAPI App
# ----------------------------
app = FastAPI(title="Async CRUD API with Filters & Pagination")

# Enable CORS if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Database Setup
# ----------------------------
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    posts: Mapped[List["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")

class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    author: Mapped["User"] = relationship(back_populates="posts")

# ----------------------------
# Schemas
# ----------------------------
class PostCreate(BaseModel):
    title: str
    content: str
    created_at: Optional[datetime] = None

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    created_at: Optional[datetime] = None
    posts: Optional[List[PostCreate]] = []

class PostOut(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    user_id: int
    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    posts: List[PostOut] = []
    class Config:
        from_attributes = True

import uuid

# ----------------------------
# Exception Handling
# ----------------------------
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    trace_id = str(uuid.uuid4())
    logger.warning(f"[TRACE_ID: {trace_id}] Validation error: {exc.errors()}")
    error_response = {
        "error_code": "VALIDATION_ERROR",
        "message": "Request validation failed",
        "timestamp": datetime.utcnow().isoformat(),
        "trace_id": trace_id,
        "errors": exc.errors(),
        "body": exc.body
    }
    return JSONResponse(status_code=422, content=error_response)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    trace_id = str(uuid.uuid4())
    logger.error(f"[TRACE_ID: {trace_id}] Unhandled error: {exc}")
    error_response = {
        "error_code": "INTERNAL_SERVER_ERROR",
        "message": "Internal server error",
        "timestamp": datetime.utcnow().isoformat()
    }
    return JSONResponse(status_code=500, content=error_response)

# ----------------------------
# Startup and Seed Data
# ----------------------------
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        now = datetime.utcnow()
        earlier = now - timedelta(days=3)
        user1 = User(name="Alice", email="alice@example.com", created_at=earlier,
                     posts=[Post(title="Hello World", content="My first post!", created_at=earlier)])
        user2 = User(name="Bob", email="bob@example.com", posts=[Post(title="FastAPI", content="Loving it", created_at=now)])
        session.add_all([user1, user2])
        await session.commit()

# ----------------------------
# Utility: Pagination
# ----------------------------
async def paginate(session: AsyncSession, stmt, page: int = 1, per_page: int = 10):
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    total_pages = max(1, math.ceil(total / per_page))
    result = await session.execute(stmt.limit(per_page).offset((page - 1) * per_page))
    return {
        "meta": {"page": page, "per_page": per_page, "total": total, "total_pages": total_pages},
        "data": [row for row in result.scalars().all()]
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
    col = getattr(User, sort_by, User.created_at)
    stmt = stmt.order_by(asc(col) if sort_order == "asc" else desc(col))
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
    col = getattr(Post, sort_by, Post.created_at)
    stmt = stmt.order_by(asc(col) if sort_order == "asc" else desc(col))
    return stmt

# ----------------------------
# CRUD Endpoints
# ----------------------------
@app.post("/users", response_model=UserOut, status_code=201)
async def create_user(user: UserCreate):
    async with async_session() as session:
        new_user = User(name=user.name, email=user.email, created_at=user.created_at or datetime.utcnow())
        for p in user.posts:
            new_user.posts.append(Post(title=p.title, content=p.content, created_at=p.created_at or datetime.utcnow()))
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        await session.refresh(new_user, attribute_names=["posts"])
        return UserOut.from_orm(new_user)

@app.post("/posts", response_model=PostOut, status_code=201)
async def create_post(post: PostCreate, user_id: int):
    async with async_session() as session:
        new_post = Post(title=post.title, content=post.content, created_at=post.created_at or datetime.utcnow(), user_id=user_id)
        session.add(new_post)
        await session.commit()
        await session.refresh(new_post)
        return PostOut.from_orm(new_post)

@app.put("/users/{id}", response_model=UserOut)
async def update_user(id: int, user: UserCreate):
    async with async_session() as session:
        db_user = await session.get(User, id, options=[selectinload(User.posts)])
        if not db_user:
            trace_id = str(uuid.uuid4())
            logger.warning(f"[TRACE_ID: {trace_id}] User with id {id} not found")
            raise HTTPException(status_code=404, detail=f"User not found. Trace ID: {trace_id}")
        db_user.name = user.name
        db_user.email = user.email
        db_user.created_at = user.created_at or db_user.created_at
        await session.commit()
        await session.refresh(db_user)
        await session.refresh(db_user, attribute_names=["posts"])
        return UserOut.from_orm(db_user)

@app.put("/posts/{id}", response_model=PostOut)
async def update_post(id: int, post: PostCreate):
    async with async_session() as session:
        db_post = await session.get(Post, id)
        if not db_post:
            trace_id = str(uuid.uuid4())
            logger.warning(f"[TRACE_ID: {trace_id}] Post with id {id} not found")
            raise HTTPException(status_code=404, detail=f"Post not found. Trace ID: {trace_id}")
        db_post.title = post.title
        db_post.content = post.content
        db_post.created_at = post.created_at or db_post.created_at
        await session.commit()
        await session.refresh(db_post)
        return PostOut.from_orm(db_post)

@app.delete("/users/{id}", status_code=204)
async def delete_user(id: int):
    async with async_session() as session:
        user = await session.get(User, id)
        if not user:
            trace_id = str(uuid.uuid4())
            logger.warning(f"[TRACE_ID: {trace_id}] User with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail=f"User not found. Trace ID: {trace_id}")
        await session.delete(user)
        await session.commit()

@app.delete("/posts/{id}", status_code=204)
async def delete_post(id: int):
    async with async_session() as session:
        post = await session.get(Post, id)
        if not post:
            trace_id = str(uuid.uuid4())
            logger.warning(f"[TRACE_ID: {trace_id}] Post with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail=f"Post not found. Trace ID: {trace_id}")
        await session.delete(post)
        await session.commit()

@app.get("/users", response_model=List[UserOut])
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
        result = await paginate(session, stmt, page, per_page)
        return [UserOut.from_orm(user) for user in result["data"]]

@app.get("/posts", response_model=List[PostOut])
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
        result = await paginate(session, stmt, page, per_page)
        return [PostOut.from_orm(post) for post in result["data"]]

# ----------------------------
# Run the App
# ----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app3:app", host="127.0.0.1", port=8000, reload=True)
