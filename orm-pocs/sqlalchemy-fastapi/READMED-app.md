Assuming you're running on http://localhost:8000
🔹 List Users (default pagination)

curl "http://localhost:8000/users"

🔹 List Users with Filters

curl "http://localhost:8000/users?search=alice&sort_by=name&sort_order=asc&page=1&per_page=5"

🔹 List Users Created After a Date

curl "http://localhost:8000/users?created_at_gte=2024-01-01T00:00:00"

🔹 List Posts (default pagination)

curl "http://localhost:8000/posts"

🔹 List Posts with Search

curl "http://localhost:8000/posts?search=hello&sort_by=title&sort_order=desc&page=1&per_page=3"

🔹 List Posts in Date Range

curl "http://localhost:8000/posts?created_at_gte=2024-01-01T00:00:00&created_at_lte=2025-01-01T00:00:00"


others 
curl -X 'GET' \
  'http://localhost:8000/posts?page=1&per_page=10&sort_by=created_at&sort_order=desc' \
  -H 'accept: application/json'