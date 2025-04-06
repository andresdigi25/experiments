import uuid
import bcrypt
import json
import secrets

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
engine = create_engine("sqlite:///db.sqlite", echo=False)


def get_user_by_email(session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()


@app.command()
def create_db():
    SQLModel.metadata.create_all(engine)
    typer.echo("✅ Database tables created.")


@app.command()
def add_user(
    email: str = typer.Option(...),
    password: str = typer.Option(...),
    full_name: str = typer.Option("")
):
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(email=email, full_name=full_name, hashed_password=hashed_password)

    with Session(engine) as session:
        if get_user_by_email(session, email):
            typer.echo("❌ User already exists.")
            raise typer.Exit()

        session.add(user)
        session.commit()
        typer.echo(f"✅ User created: {email}")


@app.command()
def update_user(
    email: str = typer.Option(...),
    new_email: str = typer.Option(None),
    full_name: str = typer.Option(None)
):
    with Session(engine) as session:
        user = get_user_by_email(session, email)
        if not user:
            typer.echo("❌ User not found.")
            raise typer.Exit()

        if new_email:
            user.email = new_email
        if full_name:
            user.full_name = full_name

        session.add(user)
        session.commit()
        typer.echo(f"✅ User updated: {user.email}")


@app.command()
def delete_user(email: str = typer.Option(...)):
    with Session(engine) as session:
        user = get_user_by_email(session, email)
        if not user:
            typer.echo("❌ User not found.")
            raise typer.Exit()

        session.delete(user)
        session.commit()
        typer.echo(f"🗑️ User deleted: {email}")


@app.command()
def list_users(json_output: bool = typer.Option(False)):
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        if json_output:
            typer.echo(json.dumps([u.dict() for u in users], indent=2, default=str))
        else:
            for u in users:
                typer.echo(f"- {u.email} | {u.full_name}")


@app.command()
def search_users(query: str = typer.Option(...)):
    with Session(engine) as session:
        results = session.exec(
            select(User).where(User.email.contains(query))
        ).all()
        for user in results:
            typer.echo(f"- {user.email} | {user.full_name}")


@app.command()
def reset_password(email: str = typer.Option(...), new_password: str = typer.Option(...)):
    with Session(engine) as session:
        user = get_user_by_email(session, email)
        if not user:
            typer.echo("❌ User not found.")
            raise typer.Exit()
        user.hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        session.add(user)
        session.commit()
        typer.echo(f"🔒 Password reset for {email}")


@app.command()
def login(email: str = typer.Option(...), password: str = typer.Option(...)):
    with Session(engine) as session:
        user = get_user_by_email(session, email)
        if not user:
            typer.echo("❌ User not found.")
            raise typer.Exit()

        if bcrypt.checkpw(password.encode(), user.hashed_password.encode()):
            token = secrets.token_hex(16)
            typer.echo(f"✅ Login successful. Fake token: {token}")
        else:
            typer.echo("❌ Invalid password.")


@app.command()
def add_item(
    title: str = typer.Option(...),
    owner_email: str = typer.Option(...)
):
    with Session(engine) as session:
        user = get_user_by_email(session, owner_email)
        if not user:
            typer.echo("❌ User not found.")
            raise typer.Exit()

        item = Item(title=title, owner_id=user.id)
        session.add(item)
        session.commit()
        typer.echo(f"✅ Item '{title}' added to user '{owner_email}'")


@app.command()
def list_items(json_output: bool = typer.Option(False)):
    with Session(engine) as session:
        items = session.exec(select(Item)).all()
        if json_output:
            typer.echo(json.dumps([i.dict() for i in items], indent=2, default=str))
        else:
            for item in items:
                typer.echo(f"- {item.title} | Owner: {item.owner_id}")


@app.command()
def delete_item(title: str = typer.Option(...)):
    with Session(engine) as session:
        item = session.exec(select(Item).where(Item.title == title)).first()
        if not item:
            typer.echo("❌ Item not found.")
            raise typer.Exit()
        session.delete(item)
        session.commit()
        typer.echo(f"🗑️ Item deleted: {title}")


@app.command()
def update_item(
    title: str = typer.Option(...),
    new_title: str = typer.Option(None)
):
    with Session(engine) as session:
        item = session.exec(select(Item).where(Item.title == title)).first()
        if not item:
            typer.echo("❌ Item not found.")
            raise typer.Exit()
        if new_title:
            item.title = new_title
        session.add(item)
        session.commit()
        typer.echo(f"✅ Item updated to: {item.title}")


@app.command()
def search_items(query: str = typer.Option(...)):
    with Session(engine) as session:
        items = session.exec(select(Item).where(Item.title.contains(query))).all()
        for i in items:
            typer.echo(f"- {i.title} | Owner: {i.owner_id}")


if __name__ == "__main__":
    app()
'''
python sqlmodel-poc3.py create-db

# Users
python sqlmodel-poc3.py add-user --email test@me.com --password pass123 --full-name "Test User"
python sqlmodel-poc3.py list-users
python sqlmodel-poc3.py update-user --email test@me.com --full-name "Updated Name"
python sqlmodel-poc3.py delete-user --email test@me.com
python sqlmodel-poc3.py reset-password --email test@me.com --new-password newpass
python sqlmodel-poc3.py login --email test@me.com --password newpass

# Items
python sqlmodel-poc3.py add-item --title "Notebook" --owner-email test@me.com
python sqlmodel-poc3.py list-items
python sqlmodel-poc3.py update-item --title "Notebook" --new-title "Notebook V2"
python sqlmodel-poc3.py delete-item --title "Notebook"

# Filters & JSON output
python sqlmodel-poc3.py list-users --json-output
python sqlmodel-poc3.py search-users --query me.com
'''