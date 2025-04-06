# flask_app.py
import logging
import base64
import json

from ollama import chat
from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow

from marshmallow import fields
from marshmallow_jsonschema import JSONSchema

app = Flask(__name__)
ma = Marshmallow(app)


# Define Marshmallow Schemas with explicit field definitions
class QABaseSchema(ma.Schema):
    question = fields.String(required=True)
    answer = fields.String(required=True)


class QAAnalyticsSchema(ma.Schema):
    question = fields.String(required=True)
    answer = fields.String(required=True)
    thoughts = fields.String(required=True)
    topic = fields.String(required=True)


class QuestionPayloadSchema(ma.Schema):
    question = fields.String(required=True)
    encoded_image = fields.String(required=True)


qa_base_schema = QABaseSchema()
qa_analytics_schema = QAAnalyticsSchema()
question_payload_schema = QuestionPayloadSchema()

# Convert QAAnalyticsSchema to a JSON Schema using marshmallow-jsonschema
qa_analytics_json_schema = JSONSchema().dump(QAAnalyticsSchema())


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def ollama_llm_response(question: str, encoded_image: str):
    return chat(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Answer this question: {question}", "images": [encoded_image]},
        ],
        model="gemma3:latest",
        format=qa_analytics_json_schema, 
    )


# Setup Logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename="response.log", level=logging.INFO)


def log_response(response_data):
    logger.info(f"Question = {response_data.get('question')}")
    logger.info(f"Answer = {response_data.get('answer')}")
    logger.info(f"Thoughts = {response_data.get('thoughts')}")
    logger.info(f"Topic = {response_data.get('topic')}")


@app.route("/api/question", methods=["POST"])
def api_question():
    payload = request.get_json()
    errors = question_payload_schema.validate(payload)
    if errors:
        return jsonify(errors), 400

    question = payload.get("question")
    encoded_image = payload.get("encoded_image")
    response = ollama_llm_response(question, encoded_image)

    # Retrieve the content from the response
    response_content = response.get("message", {}).get("content", {})

    # If response_content is a string, attempt to parse it as JSON.
    if isinstance(response_content, str):
        try:
            response_content = json.loads(response_content)
        except json.JSONDecodeError as e:
            return jsonify({"error": "Failed to parse LLM response as JSON", "detail": str(e)}), 500

    # Load the response using the analytics schema
    qa_instance = qa_analytics_schema.load(response_content)
    log_response(qa_instance)

    return qa_base_schema.dump(qa_instance)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=True)