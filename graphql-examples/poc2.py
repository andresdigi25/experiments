



import requests 
  
url = "https://api.github.integrichain.net/graphql"
GITHUB_TOKEN = ""
  
body = """ 
 {
  user(login: "cardeaf") {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
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

response = requests.post(url=url, json={"query": body}, headers=headers, verify=False) 
print("response status code: ", response.status_code) 
if response.status_code == 200: 
    print("response : ", response.content) 