Trigger a Validation Error

Send an invalid payload, like missing the email field:

curl -X POST http://localhost:8000/users \
-H "Content-Type: application/json" \
-d '{
  "name": "Invalid User"
}'

✅ You should get a 422 response like:

{
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "timestamp": "2025-03-24T20:00:00Z",
  "errors": [
    {
      "type": "missing",
      "loc": ["body", "email"],
      "msg": "Field required",
      ...
    }
  ],
  "body": { "name": "Invalid User" }
}

And a warning log will be written to app.log.
💥 2. Trigger an Internal Server Error

Modify a request to reference a non-existent user:

curl -X PUT http://localhost:8000/users/999 \
-H "Content-Type: application/json" \
-d '{
  "name": "Does Not Exist",
  "email": "nope@example.com",
  "posts": []
}'

Since user 999 doesn’t exist, you’ll get:

{
  "detail": "User not found"
}

But if you trigger any uncaught Python exception (like a typo or a failed DB call), it will return:

{
  "error_code": "INTERNAL_SERVER_ERROR",
  "message": "Internal server error",
  "timestamp": "2025-03-24T20:00:00Z"
}
