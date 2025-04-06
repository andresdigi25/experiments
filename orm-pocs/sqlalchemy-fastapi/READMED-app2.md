✅ 1. Create a User with Posts

curl -X POST http://localhost:8000/users \
-H "Content-Type: application/json" \
-d '{
  "name": "Charlie",
  "email": "charlie@example.com",
  "posts": [
    { "title": "Intro", "content": "Hey folks!" },
    { "title": "Second Post", "content": "FastAPI is 💯" }
  ]
}'

✅ 2. Create a Post (for an existing user)

curl -X POST "http://localhost:8000/posts?user_id=1" \
-H "Content-Type: application/json" \
-d '{
  "title": "Post from curl",
  "content": "CLI-powered post"
}'

✅ 3. Get All Users (paginated)

curl "http://localhost:8000/users?page=1&per_page=5"

✅ 4. Get All Posts (with search and sorting)

curl "http://localhost:8000/posts?search=fastapi&sort_by=title&sort_order=asc"

✅ 5. Update a User

curl -X PUT http://localhost:8000/users/1 \
-H "Content-Type: application/json" \
-d '{
  "name": "Alice Updated",
  "email": "alice.updated@example.com",
  "posts": []
}'

✅ 6. Update a Post

curl -X PUT http://localhost:8000/posts/1 \
-H "Content-Type: application/json" \
-d '{
  "title": "Updated Title",
  "content": "Updated post content"
}'

✅ 7. Delete a User

curl -X DELETE http://localhost:8000/users/1

✅ 8. Delete a Post

curl -X DELETE http://localhost:8000/posts/1