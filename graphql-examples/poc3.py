import requests

# Replace these with your values
GITHUB_TOKEN = ""
USERNAME = "manivix"

# GitHub GraphQL API URL
url = "https://api.github.integrichain.net/graphql"

# GraphQL query to fetch contributions (commits, pull requests, issues)
query = """
{
  user(login: "%s") {
    contributionsCollection(from: "2023-01-01T00:00:00Z", to: "2023-12-31T23:59:59Z") {
      commitContributionsByRepository {
        repository {
          name
        }
        contributions(first: 5) {
          totalCount
          nodes {
            commitCount
          }
        }
      }
      pullRequestContributionsByRepository {
        repository {
          name
        }
        contributions(first: 5) {
          totalCount
        }
      }
      issueContributionsByRepository {
        repository {
          name
        }
        contributions(first: 5) {
          totalCount
        }
      }
    }
  }
}
""" % USERNAME

# Set up the headers with authorization token
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json",
}

# Send the GraphQL query to GitHub API
def get_contributions():
    response = requests.post(url, json={"query": query}, headers=headers, verify=False)
    return response.json()

# Call the function and print the results
contributions = get_contributions()
print("Contributions data:", contributions)