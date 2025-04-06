# test_flask.py
import base64
from flask_app import app


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def test_api_question():
    client = app.test_client()
    question = "What is in this image"
    encoded_image = encode_image_to_base64("equation.png")
    payload = {"question": question, "encoded_image": encoded_image}
    response = client.post("/api/question", json=payload)
    print(response)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.get_json())


if __name__ == "__main__":
    test_api_question()