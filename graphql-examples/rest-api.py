import requests

# Replace these with your values
GITHUB_TOKEN = ""
REPO_OWNER = "cardeaf"
REPO_NAME = "delivery-services"
USERNAME = "cardeaf"

# Set up the headers with authorization token
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

# Fetch commits by the user
def get_commits():
    url = f"https://api.github.integrichain.net/repos/{REPO_OWNER}/{REPO_NAME}/commits"
    params = {"author": USERNAME}
    response = requests.get(url, headers=headers, params=params,verify=False)
    return response.json()

# Fetch pull requests by the user
def get_pull_requests():
    url = f"https://api.github.integrichain.net/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
    params = {"state": "all", "creator": USERNAME}
    response = requests.get(url, headers=headers, params=params, verify=False)
    return response.json()

# Fetch issues created by the user
def get_issues():
    url = f"https://api.github.integrichain.net/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    params = {"creator": USERNAME}
    response = requests.get(url, headers=headers, params=params, verify=False)
    return response.json()

# Call the functions and print the results
commits = get_commits()
pull_requests = get_pull_requests()
issues = get_issues()

print(f"Commits by {USERNAME}:", commits)
print(f"Pull requests by {USERNAME}:", pull_requests)
print(f"Issues created by {USERNAME}:", issues)