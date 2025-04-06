import uuid
from sqlalchemy import Column, ForeignKey, Table, create_engine, orm
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session


class Base(orm.DeclarativeBase):
    """Base database model."""
    pk: orm.Mapped[uuid.UUID] = orm.mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )


potion_ingredient_association = Table(
    "potion_ingredient",
    Base.metadata,
    Column("potion_id", UUID(as_uuid=True), ForeignKey("potion.pk")),
    Column("ingredient_id", UUID(as_uuid=True), ForeignKey("ingredient.pk")),
)


class Ingredient(Base):
    """Ingredient database model."""
    __tablename__ = "ingredient"
    name: orm.Mapped[str]
    
    def __repr__(self):
        return f"Ingredient(name='{self.name}')"


class Potion(Base):
    """Potion database model."""
    __tablename__ = "potion"
    name: orm.Mapped[str]
    ingredients: orm.Mapped[list["Ingredient"]] = orm.relationship(
        secondary=potion_ingredient_association,
        backref="potions",
        lazy="selectin",
    )
    
    def __repr__(self):
        return f"Potion(name='{self.name}')"


def main():
    # Create an in-memory SQLite database for demonstration
    # For a real application, you would use PostgreSQL with something like:
    # engine = create_engine("postgresql://user:password@localhost/dbname")
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create a session
    with Session(engine) as session:
        # Create ingredients
        mint = Ingredient(name="Mint")
        toadstool = Ingredient(name="Toadstool")
        dragon_scale = Ingredient(name="Dragon Scale")
        unicorn_hair = Ingredient(name="Unicorn Hair")
        mandrake_root = Ingredient(name="Mandrake Root")
        
        # Add ingredients to session
        session.add_all([mint, toadstool, dragon_scale, unicorn_hair, mandrake_root])
        
        # Create potions with ingredients
        healing_potion = Potion(
            name="Healing Potion", 
            ingredients=[mint, unicorn_hair]
        )
        
        invisibility_potion = Potion(
            name="Invisibility Potion", 
            ingredients=[toadstool, dragon_scale]
        )
        
        strength_potion = Potion(
            name="Strength Potion",
            ingredients=[dragon_scale, mandrake_root, mint]
        )
        
        # Add potions to session
        session.add_all([healing_potion, invisibility_potion, strength_potion])
        
        # Commit to save everything to the database
        session.commit()
        
        print("\n===== DEMONSTRATION OF RELATIONSHIPS =====\n")
        
        # Demonstration 1: List all potions and their ingredients
        print("All Potions and their Ingredients:")
        potions = session.query(Potion).all()
        for potion in potions:
            print(f"\n{potion.name}:")
            for ingredient in potion.ingredients:
                print(f"  - {ingredient.name}")
        
        print("\n" + "-" * 40 + "\n")
        
        # Demonstration 2: Find all potions that contain a specific ingredient
        mint = session.query(Ingredient).filter_by(name="Mint").first()
        dragon_scale = session.query(Ingredient).filter_by(name="Dragon Scale").first()
        
        print(f"Potions containing {mint.name}:")
        for potion in mint.potions:
            print(f"  - {potion.name}")
            
        print(f"\nPotions containing {dragon_scale.name}:")
        for potion in dragon_scale.potions:
            print(f"  - {potion.name}")
        
        print("\n" + "-" * 40 + "\n")
        
        # Demonstration 3: Adding an ingredient to an existing potion
        phoenix_feather = Ingredient(name="Phoenix Feather")
        session.add(phoenix_feather)
        
        # Add Phoenix Feather to Healing Potion
        healing_potion.ingredients.append(phoenix_feather)
        session.commit()
        
        print("Updated Healing Potion ingredients:")
        healing_potion = session.query(Potion).filter_by(name="Healing Potion").first()
        for ingredient in healing_potion.ingredients:
            print(f"  - {ingredient.name}")
        
        print("\n" + "-" * 40 + "\n")
        
        # Demonstration 4: Check which potions the new ingredient is in
        print(f"Potions containing {phoenix_feather.name}:")
        for potion in phoenix_feather.potions:
            print(f"  - {potion.name}")


if __name__ == "__main__":
    main()