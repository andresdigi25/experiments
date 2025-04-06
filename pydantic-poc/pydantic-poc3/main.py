import uuid
from models import Ingredient, IngredientPayload, Potion, PotionPayload

def main():
    # Create Ingredient instances
    ingredient1 = Ingredient(pk=uuid.uuid4(), name="Dragon Scale")
    ingredient2 = Ingredient(pk=uuid.uuid4(), name="Phoenix Feather")

    # Create IngredientPayload instances
    ingredient_payload1 = IngredientPayload(name="Unicorn Horn")
    ingredient_payload2 = IngredientPayload(name="Mermaid Tears")

    # Create Potion instance
    potion = Potion(
        pk=uuid.uuid4(),
        name="Elixir of Life",
        ingredients=[ingredient1, ingredient2]
    )

    # Create PotionPayload instance
    potion_payload = PotionPayload(
        name="Potion of Strength",
        ingredients=[ingredient1.pk, ingredient2.pk]
    )

    # Print the created instances
    print("Ingredient 1:", ingredient1)
    print("Ingredient 2:", ingredient2)
    print("Ingredient Payload 1:", ingredient_payload1)
    print("Ingredient Payload 2:", ingredient_payload2)
    print("Potion:", potion)
    print("Potion Payload:", potion_payload)

if __name__ == "__main__":
    main()