from pydantic import BaseModel, EmailStr, Field

from models import User

def main():
    user_data_1 = {
        "nickname": "john_doe",
        "email": "john@example.com",
        "password": "securepassword",
        "is_read_only": True
    }

    user_data_2 = {
        "nickname": "jane_doe",
        "email": "jane@example.com",
        "password": "anothersecurepassword"
    }

    user_1 = User(**user_data_1)
    user_2 = User(**user_data_2)

    print(user_1)
    print(user_2)

if __name__ == "__main__":
    main()