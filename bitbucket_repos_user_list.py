import os
import sys
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load .env
load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

USERNAME = os.environ.get('BITBUCKET_USERNAME')
APP_PASSWORD = os.environ.get('BITBUCKET_APP_PASSWORD')

if not USERNAME or not APP_PASSWORD:
    print("Set BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD in your .env file.")
    exit(1)


def get_workspaces():
    url = 'https://api.bitbucket.org/2.0/workspaces'
    workspaces = []

    while url:
        res = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
        if res.status_code != 200:
            print(f"Error fetching workspaces: {res.status_code} - {res.text}")
            break

        data = res.json()
        for ws in data.get('values', []):
            workspaces.append(ws['slug'])

        url = data.get('next')

    return workspaces


def get_admin_repos(workspace):
    url = f'https://api.bitbucket.org/2.0/repositories/{workspace}'
    params = {
        'role': 'admin',
        'pagelen': 50
    }
    repos = []

    while url:
        res = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), params=params)
        if res.status_code != 200:
            print(f"Error fetching repos for {workspace}: {res.status_code} - {res.text}")
            break

        data = res.json()
        for repo in data.get('values', []):
            repos.append({
                'slug': repo['slug'],
                'full_name': repo['full_name'],
                'workspace': workspace
            })

        url = data.get('next')

    return repos


def get_repo_users(workspace, repo_slug):
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/permissions-config/users"
    users = []

    while url:
        res = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
        if res.status_code != 200:
            print(f"Error fetching users for repo {repo_slug}: {res.status_code} - {res.text}")
            break

        data = res.json()
        for entry in data.get('values', []):
            user_info = entry.get('user', {})
            users.append({
                'username': user_info.get('username'),
                'display_name': user_info.get('display_name'),
                'permission': entry.get('permission')
            })

        url = data.get('next')

    return users


if __name__ == '__main__':
    print("Fetching workspaces...")
    workspaces = get_workspaces()

    all_repo_data = []

    for ws in workspaces:
        print(f"\nWorkspace: {ws}")
        repos = get_admin_repos(ws)
        for repo in repos:
            print(f"Repo: {repo['full_name']}")
            users = get_repo_users(ws, repo['slug'])
            if not users:
                print("   No direct user permissions found.")
            else:
                for u in users:
                    print(f"   {u['display_name']} ({u['username']}) - {u['permission']}")
            all_repo_data.append({
                'repo': repo['full_name'],
                'users': users
            })

    print("\nFinished. Total repositories checked:", len(all_repo_data))
