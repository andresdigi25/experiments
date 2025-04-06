import typer
import bcrypt
import uuid
import json
from datetime import datetime
from sqlmodel import Field, SQLModel, create_engine, Session, select, Relationship
from jose import jwt

app = typer.Typer()

# Database
engine = create_engine("sqlite:///db.sqlite", echo=False)

# Secret for JWT
SECRET_KEY = "super-secret"
ALGORITHM = "HS256"

# -------------------------
# Models
# -------------------------

class UserBase(SQLModel):
    email: str = Field(index=True, unique=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)

class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner")

class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)

class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id")
    owner: User = Relationship(back_populates="items")

# -------------------------
# Utility Functions
# -------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def generate_token(user_id: uuid.UUID) -> str:
    return jwt.encode({"sub": str(user_id)}, SECRET_KEY, algorithm=ALGORITHM)

def get_user_by_email(email: str, session: Session) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()

def log_action(action: str, data: dict = {}):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "data": data
    }
    with open("audit.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

# -------------------------
# Commands
# -------------------------

@app.command()
def create_db():
    SQLModel.metadata.create_all(engine)
    typer.echo("✅ Database created.")

@app.command()
def add_user(
    email: str = typer.Option(...),
    password: str = typer.Option(...),
    full_name: str = typer.Option("")
):
    with Session(engine) as session:
        if get_user_by_email(email, session):
            typer.echo("❌ Email already exists.")
            raise typer.Exit()

        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password)
        )
        session.add(user)
        session.commit()
        log_action("add_user", {"email": email, "full_name": full_name})
        typer.echo(f"✅ User {email} added.")

@app.command()
def update_user(
    email: str = typer.Option(...),
    new_name: str = typer.Option(None),
    new_email: str = typer.Option(None)
):
    with Session(engine) as session:
        user = get_user_by_email(email, session)
        if not user:
            typer.echo("❌ User not found.")
            raise typer.Exit()
        if new_name:
            user.full_name = new_name
        if new_email:
            user.email = new_email
        session.add(user)
        session.commit()
        log_action("update_user", {"email": email, "new_name": new_name, "new_email": new_email})
        typer.echo("✅ User updated.")

@app.command()
def delete_user(email: str = typer.Option(...)):
    with Session(engine) as session:
        user = get_user_by_email(email, session)
        if not user:
            typer.echo("❌ User not found.")
            raise typer.Exit()
        session.delete(user)
        session.commit()
        log_action("delete_user", {"email": email})
        typer.echo("🗑️ User deleted.")

@app.command()
def list_users(
    json_output: bool = typer.Option(False),
    name_filter: str = typer.Option(None)
):
    with Session(engine) as session:
        query = select(User)
        if name_filter:
            query = query.where(User.full_name.contains(name_filter))
        users = session.exec(query).all()

        if json_output:
            typer.echo(json.dumps([user.dict() for user in users], indent=2))
        else:
            for user in users:
                typer.echo(f"{user.id} | {user.email} | {user.full_name}")

@app.command()
def reset_password(
    email: str = typer.Option(...),
    new_password: str = typer.Option(...)
):
    with Session(engine) as session:
        user = get_user_by_email(email, session)
        if not user:
            typer.echo("❌ User not found.")
            raise typer.Exit()
        user.hashed_password = hash_password(new_password)
        session.add(user)
        session.commit()
        log_action("reset_password", {"email": email})
        typer.echo("🔒 Password reset successful.")

@app.command()
def login(
    email: str = typer.Option(...),
    password: str = typer.Option(...)
):
    with Session(engine) as session:
        user = get_user_by_email(email, session)
        if not user or not verify_password(password, user.hashed_password):
            typer.echo("❌ Invalid credentials.")
            raise typer.Exit()
        token = generate_token(user.id)
        log_action("login", {"email": email})
        typer.echo(f"✅ Token: {token}")

@app.command()
def add_item(
    title: str = typer.Option(...),
    owner_email: str = typer.Option(...)
):
    with Session(engine) as session:
        user = get_user_by_email(owner_email, session)
        if not user:
            typer.echo("❌ User not found.")
            raise typer.Exit()
        item = Item(title=title, owner_id=user.id)
        session.add(item)
        session.commit()
        log_action("add_item", {"title": title, "owner_email": owner_email})
        typer.echo(f"✅ Item '{title}' added to {owner_email}.")

@app.command()
def list_items(
    json_output: bool = typer.Option(False),
    title_filter: str = typer.Option(None)
):
    with Session(engine) as session:
        query = select(Item)
        if title_filter:
            query = query.where(Item.title.contains(title_filter))
        items = session.exec(query).all()

        if json_output:
            typer.echo(json.dumps([item.dict() for item in items], indent=2))
        else:
            for item in items:
                typer.echo(f"{item.id} | {item.title} | Owner: {item.owner_id}")

@app.command()
def update_item(
    item_id: uuid.UUID = typer.Option(...),
    new_title: str = typer.Option(None)
):
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if not item:
            typer.echo("❌ Item not found.")
            raise typer.Exit()
        if new_title:
            item.title = new_title
        session.add(item)
        session.commit()
        log_action("update_item", {"item_id": str(item_id), "new_title": new_title})
        typer.echo("✅ Item updated.")

@app.command()
def delete_item(item_id: uuid.UUID = typer.Option(...)):
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if not item:
            typer.echo("❌ Item not found.")
            raise typer.Exit()
        session.delete(item)
        session.commit()
        log_action("delete_item", {"item_id": str(item_id)})
        typer.echo("🗑️ Item deleted.")

@app.command()
def view_logs(lines: int = typer.Option(10)):
    try:
        with open("audit.log") as f:
            all_lines = f.readlines()
            for line in all_lines[-lines:]:
                typer.echo(line.strip())
    except FileNotFoundError:
        typer.echo("⚠️ No audit logs found.")

if __name__ == "__main__":
    app()

'''
python sqlmodel-poc4.py create-db

# Users
python sqlmodel-poc4.py add-user --email test@me.com --password pass123 --full-name "Test User"
python sqlmodel-poc4.py list-users
python sqlmodel-poc4.py update-user --email test@me.com --full-name "Updated Name"
python sqlmodel-poc4.py delete-user --email test@me.com
python sqlmodel-poc4.py reset-password --email test@me.com --new-password newpass
python sqlmodel-poc4.py login --email test@me.com --password newpass

# Items
python sqlmodel-poc4.py add-item --title "Notebook" --owner-email test@me.com
python sqlmodel-poc4.py list-items
python sqlmodel-poc4.py update-item --title "Notebook" --new-title "Notebook V2"
python sqlmodel-poc4.py delete-item --title "Notebook"

python sqlmodel-poc4.py view-logs --lines 5

'''