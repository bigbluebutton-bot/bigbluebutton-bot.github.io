from base64 import b64encode
import os
import time
import jwt
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Constants
GITHUB_API = "https://api.github.com"
APP_ID = os.environ['APP_ID']
INSTALLATION_ID = os.environ['INSTALLATION_ID']
PRIVATE_KEY = os.environ['PRIVATE_KEY']
ORG_NAME = os.environ['ORG_NAME']

def create_jwt():
    """Create a JWT (JSON Web Token) for GitHub App authentication."""
    private_key = serialization.load_pem_private_key(
        PRIVATE_KEY.encode(), 
        password=None, 
        backend=default_backend()
    )

    # JWT payload
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + (10 * 60),  # JWT expiration time (10 minutes)
        "iss": APP_ID
    }

    # Encode the JWT
    encoded_jwt = jwt.encode(payload, private_key, algorithm='RS256')
    return encoded_jwt 

def get_installation_token():
    """Obtain an installation access token for the GitHub App."""
    jwt_token = create_jwt()
    url = f"{GITHUB_API}/app/installations/{INSTALLATION_ID}/access_tokens"
    headers = {"Authorization": f"Bearer {jwt_token}"}
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()['token']

def get_repos(token):
    """Get the list of repositories in the organization."""
    url = f"{GITHUB_API}/orgs/{ORG_NAME}/repos"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def file_exists(repo_name, file_path, token):
    """Check if the file exists in the given repository."""
    url = f"{GITHUB_API}/repos/{ORG_NAME}/{repo_name}/contents/{file_path}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    return response.status_code == 200

def update_file(repo_name, file_path, content, commit_message, token):
    """Update the file in the given repository."""
    url = f"{GITHUB_API}/repos/{ORG_NAME}/{repo_name}/contents/{file_path}"
    headers = {"Authorization": f"token {token}"}

    # Get the SHA of the existing file
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    sha = response.json()['sha']

    # Update the file
    data = {
        "message": commit_message,
        "content": content,
        "sha": sha
    }
    response = requests.put(url, headers=headers, json=data)
    response.raise_for_status()

def main():
    from_file_path = 'index.html'
    to_file_path = 'docs/index.html'
    commit_message = '🤖 Update docs/index.html'
    
    # Obtain installation token
    token = get_installation_token()

    # Read the updated file content
    with open(from_file_path, "rb") as file:
        content = file.read().decode('utf-8')
        # base64 encode the content
        content = content.encode('utf-8')
        content = b64encode(content).decode('utf-8')

    for repo in get_repos(token):
        repo_name = repo['name']
        if file_exists(repo_name, to_file_path, token):
            print(f"Updating file in {repo_name}")
            update_file(repo_name, to_file_path, content, commit_message, token)

if __name__ == "__main__":
    main()
