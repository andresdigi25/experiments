import uuid
from pydantic import BaseModel, ConfigDict, Field


class Ingredient(BaseModel):
    """Ingredient model."""

    model_config = ConfigDict(from_attributes=True)

    pk: uuid.UUID
    name: str


class IngredientPayload(BaseModel):
    """Ingredient payload model."""

    name: str = Field(min_length=1, max_length=127)


# Demonstration script
class IngredientObject:
    def __init__(self, pk, name):
        self.pk = pk
        self.name = name


def main():
    ingredient_obj = IngredientObject(pk=uuid.uuid4(), name="Dragon Scale")

    # Create Ingredient instance from an object with attributes
    ingredient = Ingredient.model_validate(ingredient_obj)
    print("Ingredient from object:", ingredient)

    # Convert Ingredient instance back to dict
    ingredient_dict = ingredient.model_dump()
    print("Ingredient as dict:", ingredient_dict)


if __name__ == "__main__":
    main()