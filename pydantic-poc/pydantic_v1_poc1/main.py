from models import User

def main():
    user_data = {
        "nickname": "john_doe",
        "email": "john@example.com",
        "password": "securepassword",
        "is_read_only": False
    }

    user = User(**user_data)
    print('pydatic v1')
    print(user)

if __name__ == "__main__":
    main()