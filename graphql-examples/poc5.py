



import requests 
  
url = "https://api.github.com/graphql"
GITHUB_TOKEN = ""
  
body = """ 
query GetRepositoryWithIssues {
  repository(owner: "facebook", name: "react"){
    id
    nameWithOwner
    description
    url
    issues(last: 2) {
      totalCount
      nodes{
        title
        createdAt
        author {
          login
        }
       
      }
    }
  }
}

"""
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json",
}

response = requests.post(url=url, json={"query": body}, headers=headers) 
print("response status code: ", response.status_code) 
if response.status_code == 200: 
    print("response : ", response.content) 