# file: sqlalchemy_core_example.py

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Text, ForeignKey, insert, select, join
)

# 1. Setup engine and metadata
engine = create_engine("sqlite:///core_complex.db", echo=True)
metadata = MetaData()

# 2. Define tables
users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(50), nullable=False),
    Column("email", String(100), nullable=False, unique=True),
)

posts = Table(
    "posts", metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(100), nullable=False),
    Column("content", Text, nullable=False),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
)

# 3. Create tables
metadata.create_all(engine)

# 4. Insert data
def insert_data():
    with engine.begin() as conn:
        conn.execute(insert(users), [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
        ])

        conn.execute(insert(posts), [
            {"title": "Post 1", "content": "Hello world!", "user_id": 1},
            {"title": "Post 2", "content": "SQLAlchemy Core is cool.", "user_id": 1},
            {"title": "Post 3", "content": "Hi from Bob.", "user_id": 2},
        ])

# 5. Query all users
def get_all_users():
    with engine.connect() as conn:
        result = conn.execute(select(users))
        print("\n📋 All Users:")
        for row in result:
            print(row)

# 6. Query user by ID
def get_user_by_id(user_id: int):
    with engine.connect() as conn:
        stmt = select(users).where(users.c.id == user_id)
        result = conn.execute(stmt).first()
        print(f"\n🔍 User with ID {user_id}:", result)

# 7. Query posts and their authors (JOIN)
def get_all_posts_with_authors():
    with engine.connect() as conn:
        stmt = select(
            posts.c.id,
            posts.c.title,
            posts.c.content,
            users.c.name.label("author")
        ).select_from(
            join(posts, users, posts.c.user_id == users.c.id)
        )

        print("\n📝 Posts with Authors:")
        for row in conn.execute(stmt):
            print(f"{row.title} by {row.author}: {row.content}")

# 8. Query posts by user ID
def get_posts_by_user(user_id: int):
    with engine.connect() as conn:
        stmt = select(posts).where(posts.c.user_id == user_id)
        result = conn.execute(stmt).all()
        print(f"\n📚 Posts by User {user_id}:")
        for row in result:
            print(row)

# 9. Run everything
if __name__ == "__main__":
    insert_data()
    get_all_users()
    get_user_by_id(1)
    get_posts_by_user(1)
    get_all_posts_with_authors()
