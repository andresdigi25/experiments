import uuid
import bcrypt

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel,Session,create_engine,select
import typer



# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)




app = typer.Typer()

# SQLite DB (can be replaced with PostgreSQL, MySQL, etc.)
engine = create_engine("sqlite:///db.sqlite", echo=False)


@app.command()
def create_db():
    """Create database tables."""
    SQLModel.metadata.create_all(engine)
    typer.echo("✅ Database created.")


@app.command()
def add_user(
    email: str = typer.Option(..., help="Email of the user"),
    password: str = typer.Option(..., help="Password for the user"),
    full_name: str = typer.Option("", help="Full name of the user")
):
    """Add a new user."""
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hashed_password
    )
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing:
            typer.echo("❌ User with this email already exists.")
            raise typer.Exit()
        session.add(user)
        session.commit()
        typer.echo(f"✅ User created: {email}")


@app.command()
def list_users():
    """List all users."""
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        if not users:
            typer.echo("ℹ️ No users found.")
        for user in users:
            typer.echo(f"- ID: {user.id} | Email: {user.email} | Name: {user.full_name}")


@app.command()
def add_item(
    title: str = typer.Option(..., help="Title of the item"),
    owner_email: str = typer.Option(..., help="Email of the item's owner")
):
    """Add a new item to a user."""
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == owner_email)).first()
        if not user:
            typer.echo("❌ User not found.")
            raise typer.Exit()

        item = Item(title=title, owner_id=user.id)
        session.add(item)
        session.commit()
        typer.echo(f"✅ Item '{title}' created for {owner_email}")


@app.command()
def list_items():
    """List all items."""
    with Session(engine) as session:
        items = session.exec(select(Item)).all()
        if not items:
            typer.echo("ℹ️ No items found.")
        for item in items:
            typer.echo(f"- ID: {item.id} | Title: {item.title} | Owner ID: {item.owner_id}")


if __name__ == "__main__":
    app()
'''
python sqlmodel-poc2.py create-db
python sqlmodel-poc2.py add-user --email test@example.com --password secret123 --full-name "Test User"
python sqlmodel-poc2.py list-users
python sqlmodel-poc2.py add-item --title "My First Item" --owner-email test@example.com
python sqlmodel-poc2.py list-items
'''