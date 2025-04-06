import uuid
from models import Ingredient, IngredientPayload, Potion, PotionPayload

def main():
    # Create Ingredient instances from dicts
    ingredient_dict1 = {"pk": uuid.uuid4(), "name": "Dragon Scale"}
    ingredient_dict2 = {"pk": uuid.uuid4(), "name": "Phoenix Feather"}
    ingredient1 = Ingredient(**ingredient_dict1)
    ingredient2 = Ingredient(**ingredient_dict2)

    # Create IngredientPayload instances from dicts
    ingredient_payload_dict1 = {"name": "Unicorn Horn"}
    ingredient_payload_dict2 = {"name": "Mermaid Tears"}
    ingredient_payload1 = IngredientPayload(**ingredient_payload_dict1)
    ingredient_payload2 = IngredientPayload(**ingredient_payload_dict2)

    # Create Potion instance from dict
    potion_dict = {
        "pk": uuid.uuid4(),
        "name": "Elixir of Life",
        "ingredients": [ingredient1, ingredient2]
    }
    potion = Potion(**potion_dict)

    # Create PotionPayload instance from dict
    potion_payload_dict = {
        "name": "Potion of Strength",
        "ingredients": [ingredient1.pk, ingredient2.pk]
    }
    potion_payload = PotionPayload(**potion_payload_dict)

    # Print the created instances
    print("Ingredient 1:", ingredient1)
    print("Ingredient 2:", ingredient2)
    print("Ingredient Payload 1:", ingredient_payload1)
    print("Ingredient Payload 2:", ingredient_payload2)
    print("Potion:", potion)
    print("Potion Payload:", potion_payload)
    print("-------------------------------------------------------------")

    # Convert objects back to dicts and print them
    print("Ingredient 1 as dict:", ingredient1.model_dump())
    print("Ingredient 2 as dict:", ingredient2.model_dump())
    print("Ingredient Payload 1 as dict:", ingredient_payload1.model_dump())
    print("Ingredient Payload 2 as dict:", ingredient_payload2.model_dump())
    print("Potion as dict:", potion.model_dump())
    print("Potion Payload as dict:", potion_payload.model_dump())

if __name__ == "__main__":
    main()