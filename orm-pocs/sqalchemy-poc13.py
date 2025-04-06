import uuid
from sqlalchemy import Column, ForeignKey, Table, orm
from sqlalchemy.dialects.postgresql import UUID
from typing import List

# Define the declarative base
class Base(orm.DeclarativeBase):
    """Base model class."""
    pk: orm.Mapped[uuid.UUID] = orm.mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

# Define the association table (still needed for the relationship definition)
potion_ingredient_association = Table(
    "potion_ingredient",
    Base.metadata,
    Column("potion_id", UUID(as_uuid=True), ForeignKey("potion.pk")),
    Column("ingredient_id", UUID(as_uuid=True), ForeignKey("ingredient.pk")),
)

class Ingredient(Base):
    """Ingredient model."""
    __tablename__ = "ingredient"
    name: orm.Mapped[str]
    
    def __repr__(self):
        return f"Ingredient(name='{self.name}')"

class Potion(Base):
    """Potion model."""
    __tablename__ = "potion"
    name: orm.Mapped[str]
    ingredients: orm.Mapped[List["Ingredient"]] = orm.relationship(
        secondary=potion_ingredient_association,
        backref="potions",
        lazy="selectin",
    )
    
    def __repr__(self):
        return f"Potion(name='{self.name}')"

def main():
    # Create ingredients as plain Python objects
    mint = Ingredient(name="Mint")
    toadstool = Ingredient(name="Toadstool")
    dragon_scale = Ingredient(name="Dragon Scale")
    
    # Create potions with ingredients
    healing_potion = Potion(name="Healing Potion", ingredients=[mint, dragon_scale])
    invisibility_potion = Potion(name="Invisibility Potion", ingredients=[toadstool, mint])
    
    # Using the relationship from Potion to Ingredient
    print("Healing Potion ingredients:")
    for ingredient in healing_potion.ingredients:
        print(f"- {ingredient.name}")
    
    print("\nInvisibility Potion ingredients:")
    for ingredient in invisibility_potion.ingredients:
        print(f"- {ingredient.name}")
    
    # Using the backref relationship from Ingredient to Potion
    print(f"\nPotions containing {mint.name}:")
    for potion in mint.potions:
        print(f"- {potion.name}")
    
    # Adding a new ingredient to an existing potion
    unicorn_hair = Ingredient(name="Unicorn Hair")
    healing_potion.ingredients.append(unicorn_hair)
    
    print("\nUpdated Healing Potion ingredients:")
    for ingredient in healing_potion.ingredients:
        print(f"- {ingredient.name}")
    
    # The backref relationship is automatically updated
    print(f"\nPotions containing {unicorn_hair.name}:")
    for potion in unicorn_hair.potions:
        print(f"- {potion.name}")

if __name__ == "__main__":
    main()