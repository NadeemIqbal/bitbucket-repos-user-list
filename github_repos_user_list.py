import os
import sys
import json
import csv
import argparse
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load .env
load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

USERNAME = os.environ.get('GITHUB_USERNAME')
TOKEN = os.environ.get('GITHUB_TOKEN')

if not USERNAME or not TOKEN:
    print("Set GITHUB_USERNAME and GITHUB_TOKEN in your .env file.")
    exit(1)


def get_user_organizations():
    """Fetch all organizations the user belongs to"""
    url = 'https://api.github.com/user/orgs'
    headers = {
        'Authorization': f'token {TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    orgs = []

    while url:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"Error fetching organizations: {res.status_code} - {res.text}")
            break

        data = res.json()
        for org in data:
            orgs.append(org['login'])

        # GitHub uses Link header for pagination
        if 'next' in res.links:
            url = res.links['next']['url']
        else:
            url = None

    return orgs


def get_admin_repos():
    """Fetch all repositories where user has admin access"""
    url = 'https://api.github.com/user/repos'
    headers = {
        'Authorization': f'token {TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    params = {
        'type': 'all',  # all, owner, public, private, member
        'sort': 'updated',
        'per_page': 100
    }
    repos = []

    while url:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code != 200:
            print(f"Error fetching repos: {res.status_code} - {res.text}")
            break

        data = res.json()
        for repo in data:
            # Check if user has admin permissions
            if repo.get('permissions', {}).get('admin', False):
                repos.append({
                    'name': repo['name'],
                    'full_name': repo['full_name'],
                    'owner': repo['owner']['login'],
                    'private': repo['private'],
                    'html_url': repo['html_url']
                })

        # GitHub uses Link header for pagination
        if 'next' in res.links:
            url = res.links['next']['url']
        else:
            url = None

    return repos


def get_org_admin_repos(org):
    """Fetch repositories in organization where user has admin access"""
    url = f'https://api.github.com/orgs/{org}/repos'
    headers = {
        'Authorization': f'token {TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    params = {
        'type': 'all',
        'per_page': 100
    }
    repos = []

    while url:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code != 200:
            print(f"Error fetching repos for org {org}: {res.status_code} - {res.text}")
            break

        data = res.json()
        for repo in data:
            # Check if user has admin permissions
            if repo.get('permissions', {}).get('admin', False):
                repos.append({
                    'name': repo['name'],
                    'full_name': repo['full_name'],
                    'owner': repo['owner']['login'],
                    'private': repo['private'],
                    'html_url': repo['html_url']
                })

        # GitHub uses Link header for pagination
        if 'next' in res.links:
            url = res.links['next']['url']
        else:
            url = None

    return repos


def get_repo_collaborators(owner, repo_name):
    """Fetch users with direct access to repository"""
    url = f'https://api.github.com/repos/{owner}/{repo_name}/collaborators'
    headers = {
        'Authorization': f'token {TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    params = {
        'per_page': 100
    }
    users = []

    while url:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code != 200:
            print(f"Error fetching collaborators for {owner}/{repo_name}: {res.status_code} - {res.text}")
            break

        data = res.json()
        for user in data:
            users.append({
                'username': user['login'],
                'display_name': user.get('name', user['login']),
                'permission': user.get('role_name', 'unknown')
            })

        # GitHub uses Link header for pagination
        if 'next' in res.links:
            url = res.links['next']['url']
        else:
            url = None

    return users


def export_to_csv(data, filename):
    """Export data to CSV format"""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['repository', 'type', 'owner', 'username', 'display_name', 'permission']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for repo in data:
            if repo.get('users'):
                for user in repo['users']:
                    writer.writerow({
                        'repository': repo['full_name'],
                        'type': repo.get('type', 'personal'),
                        'owner': repo.get('owner', ''),
                        'username': user['username'],
                        'display_name': user['display_name'],
                        'permission': user['permission']
                    })
            else:
                # Write empty row for repositories with no users
                writer.writerow({
                    'repository': repo['full_name'],
                    'type': repo.get('type', 'personal'),
                    'owner': repo.get('owner', ''),
                    'username': '',
                    'display_name': '',
                    'permission': ''
                })
    
    print(f"Data exported to {filename}")


def export_to_json(data, filename):
    """Export data to JSON format"""
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"Data exported to {filename}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GitHub Repository Permission Inspector')
    parser.add_argument('--csv', help='Export results to CSV file')
    parser.add_argument('--json', help='Export results to JSON file')
    parser.add_argument('--quiet', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("Fetching GitHub repositories where you have admin access...")
    
    all_repo_data = []
    
    # Get user's own repositories
    if not args.quiet:
        print("\n=== Personal Repositories ===")
    personal_repos = get_admin_repos()
    for repo in personal_repos:
        if not args.quiet:
            print(f"Repo: {repo['full_name']}")
        users = get_repo_collaborators(repo['owner'], repo['name'])
        if not args.quiet:
            if not users:
                print("   No direct collaborators found.")
            else:
                for u in users:
                    print(f"   {u['display_name']} ({u['username']}) - {u['permission']}")
        
        repo_data = {
            'full_name': repo['full_name'],
            'name': repo['name'],
            'owner': repo['owner'],
            'type': 'personal',
            'private': repo['private'],
            'html_url': repo['html_url'],
            'users': users
        }
        all_repo_data.append(repo_data)
    
    # Get organization repositories
    if not args.quiet:
        print("\n=== Organization Repositories ===")
    orgs = get_user_organizations()
    
    for org in orgs:
        if not args.quiet:
            print(f"\nOrganization: {org}")
        org_repos = get_org_admin_repos(org)
        for repo in org_repos:
            if not args.quiet:
                print(f"Repo: {repo['full_name']}")
            users = get_repo_collaborators(repo['owner'], repo['name'])
            if not args.quiet:
                if not users:
                    print("   No direct collaborators found.")
                else:
                    for u in users:
                        print(f"   {u['display_name']} ({u['username']}) - {u['permission']}")
            
            repo_data = {
                'full_name': repo['full_name'],
                'name': repo['name'],
                'owner': repo['owner'],
                'type': 'organization',
                'organization': org,
                'private': repo['private'],
                'html_url': repo['html_url'],
                'users': users
            }
            all_repo_data.append(repo_data)

    if not args.quiet:
        print(f"\nFinished. Total repositories checked: {len(all_repo_data)}")
    
    # Export data if requested
    if args.csv:
        export_to_csv(all_repo_data, args.csv)
    
    if args.json:
        export_to_json(all_repo_data, args.json) 