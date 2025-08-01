import os
import sys
import json
import csv
import argparse
import requests
import base64
from dotenv import load_dotenv

# Load .env
load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

PAT = os.environ.get('AZURE_DEVOPS_PAT')
ORGANIZATION = os.environ.get('AZURE_DEVOPS_ORG')

if not PAT or not ORGANIZATION:
    print("Set AZURE_DEVOPS_PAT and AZURE_DEVOPS_ORG in your .env file.")
    exit(1)


def get_authentication_header():
    """Create authentication header for Azure DevOps API"""
    credentials = f':{PAT}'
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    return {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json'
    }


def get_projects():
    """Fetch all projects in the organization"""
    url = f'https://dev.azure.com/{ORGANIZATION}/_apis/projects'
    headers = get_authentication_header()
    params = {
        'api-version': '6.0',
        '$top': 100
    }
    projects = []

    while url:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code != 200:
            print(f"Error fetching projects: {res.status_code} - {res.text}")
            break

        data = res.json()
        for project in data.get('value', []):
            projects.append({
                'id': project['id'],
                'name': project['name'],
                'description': project.get('description', ''),
                'state': project['state']
            })

        # Azure DevOps uses continuation token for pagination
        if 'continuationToken' in data:
            params['continuationToken'] = data['continuationToken']
        else:
            url = None

    return projects


def get_repositories(project_id):
    """Fetch all repositories in a project"""
    url = f'https://dev.azure.com/{ORGANIZATION}/{project_id}/_apis/git/repositories'
    headers = get_authentication_header()
    params = {
        'api-version': '6.0'
    }
    repos = []

    res = requests.get(url, headers=headers, params=params)
    if res.status_code != 200:
        print(f"Error fetching repositories for project {project_id}: {res.status_code} - {res.text}")
        return repos

    data = res.json()
    for repo in data.get('value', []):
        repos.append({
            'id': repo['id'],
            'name': repo['name'],
            'project': repo['project']['name'],
            'default_branch': repo.get('defaultBranch', ''),
            'web_url': repo['webUrl']
        })

    return repos


def get_repository_permissions(repo_id):
    """Fetch users with permissions on a repository"""
    url = f'https://dev.azure.com/{ORGANIZATION}/_apis/git/repositories/{repo_id}/permissions'
    headers = get_authentication_header()
    params = {
        'api-version': '6.0'
    }
    users = []

    res = requests.get(url, headers=headers, params=params)
    if res.status_code != 200:
        print(f"Error fetching repository permissions: {res.status_code} - {res.text}")
        return users

    data = res.json()
    for permission in data.get('value', []):
        # Filter for user permissions (not group permissions)
        if permission.get('identityType') == 'user':
            identity = permission.get('identity', {})
            users.append({
                'username': identity.get('displayName', identity.get('uniqueName', 'Unknown')),
                'email': identity.get('uniqueName', ''),
                'permission': permission.get('permission', 'unknown')
            })

    return users


def get_project_members(project_id):
    """Fetch all members of a project"""
    url = f'https://dev.azure.com/{ORGANIZATION}/_apis/projects/{project_id}/teams'
    headers = get_authentication_header()
    params = {
        'api-version': '6.0'
    }
    members = []

    # First get all teams in the project
    res = requests.get(url, headers=headers, params=params)
    if res.status_code != 200:
        print(f"Error fetching teams for project {project_id}: {res.status_code} - {res.text}")
        return members

    teams_data = res.json()
    
    # For each team, get members
    for team in teams_data.get('value', []):
        team_id = team['id']
        members_url = f'https://dev.azure.com/{ORGANIZATION}/_apis/projects/{project_id}/teams/{team_id}/members'
        
        members_res = requests.get(members_url, headers=headers, params=params)
        if members_res.status_code == 200:
            team_members = members_res.json()
            for member in team_members.get('value', []):
                identity = member.get('identity', {})
                members.append({
                    'username': identity.get('displayName', identity.get('uniqueName', 'Unknown')),
                    'email': identity.get('uniqueName', ''),
                    'team': team['name'],
                    'permission': 'team_member'  # Azure DevOps permissions are more complex
                })

    return members


def check_user_permissions(project_id, repo_id):
    """Check if current user has admin permissions on repository"""
    url = f'https://dev.azure.com/{ORGANIZATION}/_apis/git/repositories/{repo_id}/permissions'
    headers = get_authentication_header()
    params = {
        'api-version': '6.0'
    }

    res = requests.get(url, headers=headers, params=params)
    if res.status_code != 200:
        return False

    data = res.json()
    for permission in data.get('value', []):
        # Check if current user has admin permissions
        if permission.get('identityType') == 'user' and permission.get('permission') in ['Administer', 'Manage']:
            return True

    return False


def export_to_csv(data, filename):
    """Export data to CSV format"""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['project', 'repository', 'username', 'email', 'permission']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for repo in data:
            if repo.get('users'):
                for user in repo['users']:
                    writer.writerow({
                        'project': repo['project'],
                        'repository': repo['repository'],
                        'username': user['username'],
                        'email': user.get('email', ''),
                        'permission': user['permission']
                    })
            else:
                # Write empty row for repositories with no users
                writer.writerow({
                    'project': repo['project'],
                    'repository': repo['repository'],
                    'username': '',
                    'email': '',
                    'permission': ''
                })
    
    print(f"Data exported to {filename}")


def export_to_json(data, filename):
    """Export data to JSON format"""
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"Data exported to {filename}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Azure DevOps Repository Permission Inspector')
    parser.add_argument('--csv', help='Export results to CSV file')
    parser.add_argument('--json', help='Export results to JSON file')
    parser.add_argument('--quiet', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("Fetching Azure DevOps repositories where you have admin access...")
    
    all_repo_data = []
    
    # Get all projects
    if not args.quiet:
        print("Fetching projects...")
    projects = get_projects()
    
    for project in projects:
        if not args.quiet:
            print(f"\nProject: {project['name']}")
        repos = get_repositories(project['id'])
        
        for repo in repos:
            if not args.quiet:
                print(f"Repository: {repo['name']}")
            
            # Check if user has admin permissions
            if check_user_permissions(project['id'], repo['id']):
                if not args.quiet:
                    print("  ✓ You have admin access")
                
                # Get repository permissions
                users = get_repository_permissions(repo['id'])
                if not args.quiet:
                    if not users:
                        print("   No direct user permissions found.")
                    else:
                        for u in users:
                            print(f"   {u['username']} ({u['email']}) - {u['permission']}")
                
                repo_data = {
                    'project': project['name'],
                    'repository': repo['name'],
                    'project_id': project['id'],
                    'repo_id': repo['id'],
                    'default_branch': repo['default_branch'],
                    'web_url': repo['web_url'],
                    'users': users
                }
                all_repo_data.append(repo_data)
            else:
                if not args.quiet:
                    print("  ✗ No admin access")

    if not args.quiet:
        print(f"\nFinished. Total repositories with admin access: {len(all_repo_data)}")
    
    # Export data if requested
    if args.csv:
        export_to_csv(all_repo_data, args.csv)
    
    if args.json:
        export_to_json(all_repo_data, args.json) 