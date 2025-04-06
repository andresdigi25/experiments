import base64
import json 

from ollama import chat
from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow

from marshmallow import fields
from marshmallow_jsonschema import JSONSchema

app = Flask(__name__)
ma = Marshmallow(app)


class QABaseSchema(ma.Schema):
    # Schema for basic QA with question and answer fields
    question = fields.String(required=True)
    answer = fields.String(required=True)


class QAAnalyticsSchema(ma.Schema):
    # Schema for QA with additional analytics fields
    question = fields.String(required=True)
    answer = fields.String(required=True)
    thoughts = fields.String(required=True)
    topic = fields.String(required=True)


qa_base_schema = QABaseSchema()
qa_analytics_schema = QAAnalyticsSchema()

qa_analytics_json_schema = JSONSchema().dump(QAAnalyticsSchema())


def encode_image_to_base64(image_path: str) -> str:
    """
    Encodes an image to a base64 string.
    
    :param image_path: Path to the image file
    :return: Base64 encoded string of the image
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def ollama_llm_response(question: str, encoded_image: str):
    """
    Sends a question and an encoded image to the LLM and returns the response.
    
    :param question: The question to ask the LLM
    :param encoded_image: Base64 encoded image string
    :return: Response from the LLM
    """
    return chat(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Answer this question: {question}", "images": [encoded_image]},
        ],
        model="gemma3:latest",
        format=qa_analytics_json_schema,  
    )

if __name__ == "__main__":  
    # Main block to test the functions
    question = "What is in this image"  
    image_path = "receipt.png"  
    encoded_image = encode_image_to_base64(image_path)  
    response = ollama_llm_response(question, encoded_image)  
    response_content = response.get("message", {}).get("content", {})
    response_content = json.loads(response_content)
    qa_instance = qa_analytics_schema.load(response_content)
    print(qa_instance)