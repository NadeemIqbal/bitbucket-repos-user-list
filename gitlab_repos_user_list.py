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

TOKEN = os.environ.get('GITLAB_TOKEN')
GITLAB_URL = os.environ.get('GITLAB_URL', 'https://gitlab.com')

if not TOKEN:
    print("Set GITLAB_TOKEN in your .env file.")
    exit(1)


def get_user_groups():
    """Fetch all groups the user belongs to"""
    url = f'{GITLAB_URL}/api/v4/groups'
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }
    params = {
        'per_page': 100
    }
    groups = []

    while url:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code != 200:
            print(f"Error fetching groups: {res.status_code} - {res.text}")
            break

        data = res.json()
        for group in data:
            groups.append({
                'id': group['id'],
                'name': group['name'],
                'path': group['path']
            })

        # GitLab uses Link header for pagination
        if 'next' in res.links:
            url = res.links['next']['url']
        else:
            url = None

    return groups


def get_user_projects():
    """Fetch all projects where user has maintainer or owner access"""
    url = f'{GITLAB_URL}/api/v4/projects'
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }
    params = {
        'membership': True,  # Only projects where user is a member
        'per_page': 100
    }
    projects = []

    while url:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code != 200:
            print(f"Error fetching projects: {res.status_code} - {res.text}")
            break

        data = res.json()
        for project in data:
            # Check if user has maintainer or owner access
            if project.get('permissions', {}).get('project_access', {}).get('access_level', 0) >= 40:  # Maintainer = 40
                projects.append({
                    'id': project['id'],
                    'name': project['name'],
                    'path': project['path'],
                    'full_path': project['path_with_namespace'],
                    'visibility': project['visibility'],
                    'web_url': project['web_url']
                })

        # GitLab uses Link header for pagination
        if 'next' in res.links:
            url = res.links['next']['url']
        else:
            url = None

    return projects


def get_group_projects(group_id):
    """Fetch projects in group where user has maintainer access"""
    url = f'{GITLAB_URL}/api/v4/groups/{group_id}/projects'
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }
    params = {
        'per_page': 100
    }
    projects = []

    while url:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code != 200:
            print(f"Error fetching group projects: {res.status_code} - {res.text}")
            break

        data = res.json()
        for project in data:
            # Check if user has maintainer or owner access
            if project.get('permissions', {}).get('project_access', {}).get('access_level', 0) >= 40:  # Maintainer = 40
                projects.append({
                    'id': project['id'],
                    'name': project['name'],
                    'path': project['path'],
                    'full_path': project['path_with_namespace'],
                    'visibility': project['visibility'],
                    'web_url': project['web_url']
                })

        # GitLab uses Link header for pagination
        if 'next' in res.links:
            url = res.links['next']['url']
        else:
            url = None

    return projects


def get_project_members(project_id):
    """Fetch users with direct access to project"""
    url = f'{GITLAB_URL}/api/v4/projects/{project_id}/members'
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }
    params = {
        'per_page': 100
    }
    users = []

    while url:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code != 200:
            print(f"Error fetching project members: {res.status_code} - {res.text}")
            break

        data = res.json()
        for user in data:
            # Map access levels to readable names
            access_level = user.get('access_level', 0)
            if access_level == 50:
                permission = 'owner'
            elif access_level == 40:
                permission = 'maintainer'
            elif access_level == 30:
                permission = 'developer'
            elif access_level == 20:
                permission = 'reporter'
            elif access_level == 10:
                permission = 'guest'
            else:
                permission = 'unknown'

            users.append({
                'username': user['username'],
                'display_name': user.get('name', user['username']),
                'permission': permission,
                'access_level': access_level
            })

        # GitLab uses Link header for pagination
        if 'next' in res.links:
            url = res.links['next']['url']
        else:
            url = None

    return users


def export_to_csv(data, filename):
    """Export data to CSV format"""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['project', 'type', 'group', 'username', 'display_name', 'permission', 'access_level']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for project in data:
            if project.get('users'):
                for user in project['users']:
                    writer.writerow({
                        'project': project['full_path'],
                        'type': project.get('type', 'personal'),
                        'group': project.get('group', ''),
                        'username': user['username'],
                        'display_name': user['display_name'],
                        'permission': user['permission'],
                        'access_level': user.get('access_level', '')
                    })
            else:
                # Write empty row for projects with no users
                writer.writerow({
                    'project': project['full_path'],
                    'type': project.get('type', 'personal'),
                    'group': project.get('group', ''),
                    'username': '',
                    'display_name': '',
                    'permission': '',
                    'access_level': ''
                })
    
    print(f"Data exported to {filename}")


def export_to_json(data, filename):
    """Export data to JSON format"""
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"Data exported to {filename}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GitLab Repository Permission Inspector')
    parser.add_argument('--csv', help='Export results to CSV file')
    parser.add_argument('--json', help='Export results to JSON file')
    parser.add_argument('--quiet', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("Fetching GitLab projects where you have maintainer/owner access...")
    
    all_repo_data = []
    
    # Get user's projects
    if not args.quiet:
        print("\n=== Personal Projects ===")
    personal_projects = get_user_projects()
    for project in personal_projects:
        if not args.quiet:
            print(f"Project: {project['full_path']}")
        users = get_project_members(project['id'])
        if not args.quiet:
            if not users:
                print("   No direct members found.")
            else:
                for u in users:
                    print(f"   {u['display_name']} ({u['username']}) - {u['permission']}")
        
        project_data = {
            'id': project['id'],
            'name': project['name'],
            'full_path': project['full_path'],
            'type': 'personal',
            'visibility': project['visibility'],
            'web_url': project['web_url'],
            'users': users
        }
        all_repo_data.append(project_data)
    
    # Get group projects
    if not args.quiet:
        print("\n=== Group Projects ===")
    groups = get_user_groups()
    
    for group in groups:
        if not args.quiet:
            print(f"\nGroup: {group['name']} ({group['path']})")
        group_projects = get_group_projects(group['id'])
        for project in group_projects:
            if not args.quiet:
                print(f"Project: {project['full_path']}")
            users = get_project_members(project['id'])
            if not args.quiet:
                if not users:
                    print("   No direct members found.")
                else:
                    for u in users:
                        print(f"   {u['display_name']} ({u['username']}) - {u['permission']}")
            
            project_data = {
                'id': project['id'],
                'name': project['name'],
                'full_path': project['full_path'],
                'type': 'group',
                'group': group['name'],
                'visibility': project['visibility'],
                'web_url': project['web_url'],
                'users': users
            }
            all_repo_data.append(project_data)

    if not args.quiet:
        print(f"\nFinished. Total projects checked: {len(all_repo_data)}")
    
    # Export data if requested
    if args.csv:
        export_to_csv(all_repo_data, args.csv)
    
    if args.json:
        export_to_json(all_repo_data, args.json) 