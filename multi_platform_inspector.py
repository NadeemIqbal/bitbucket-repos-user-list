#!/usr/bin/env python3
"""
Multi-Platform Repository Inspector
==================================

A unified script that inspects repositories across multiple platforms:
- Bitbucket Cloud
- GitHub
- GitLab
- Azure DevOps

This script will check all platforms where credentials are configured and
provide a comprehensive report of repositories where you have admin access.
"""

import os
import sys
import json
import csv
import argparse
import requests
import base64
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')


class PlatformInspector:
    """Base class for platform-specific repository inspection"""
    
    def __init__(self, name):
        self.name = name
        self.repositories = []
        self.errors = []
    
    def inspect(self):
        """Override this method in subclasses"""
        pass
    
    def print_results(self):
        """Print inspection results"""
        if not self.repositories:
            print(f"\n{self.name}: No repositories with admin access found.")
            return
        
        print(f"\n{self.name}:")
        print("=" * (len(self.name) + 1))
        
        for repo in self.repositories:
            print(f"\nRepository: {repo['name']}")
            if repo.get('users'):
                for user in repo['users']:
                    print(f"   {user['display_name']} ({user['username']}) - {user['permission']}")
            else:
                print("   No direct users found.")
        
        print(f"\nTotal repositories: {len(self.repositories)}")
    
    def get_export_data(self):
        """Get data in exportable format"""
        return {
            'platform': self.name,
            'repositories': self.repositories,
            'total_repositories': len(self.repositories),
            'errors': self.errors
        }


class BitbucketInspector(PlatformInspector):
    """Bitbucket Cloud repository inspector"""
    
    def __init__(self):
        super().__init__("Bitbucket Cloud")
        self.username = os.environ.get('BITBUCKET_USERNAME')
        self.password = os.environ.get('BITBUCKET_APP_PASSWORD')
        
        if not self.username or not self.password:
            self.errors.append("Missing BITBUCKET_USERNAME or BITBUCKET_APP_PASSWORD")
            return
    
    def inspect(self):
        if self.errors:
            return
        
        try:
            workspaces = self._get_workspaces()
            for workspace in workspaces:
                repos = self._get_admin_repos(workspace)
                for repo in repos:
                    users = self._get_repo_users(workspace, repo['slug'])
                    self.repositories.append({
                        'name': repo['full_name'],
                        'workspace': workspace,
                        'slug': repo['slug'],
                        'users': users
                    })
        except Exception as e:
            self.errors.append(f"Error during inspection: {str(e)}")
    
    def _get_workspaces(self):
        url = 'https://api.bitbucket.org/2.0/workspaces'
        workspaces = []
        
        while url:
            res = requests.get(url, auth=(self.username, self.password))
            if res.status_code != 200:
                raise Exception(f"Error fetching workspaces: {res.status_code}")
            
            data = res.json()
            workspaces.extend([ws['slug'] for ws in data.get('values', [])])
            url = data.get('next')
        
        return workspaces
    
    def _get_admin_repos(self, workspace):
        url = f'https://api.bitbucket.org/2.0/repositories/{workspace}'
        params = {'role': 'admin', 'pagelen': 50}
        repos = []
        
        while url:
            res = requests.get(url, auth=(self.username, self.password), params=params)
            if res.status_code != 200:
                raise Exception(f"Error fetching repos for {workspace}: {res.status_code}")
            
            data = res.json()
            for repo in data.get('values', []):
                repos.append({
                    'slug': repo['slug'],
                    'full_name': repo['full_name']
                })
            url = data.get('next')
        
        return repos
    
    def _get_repo_users(self, workspace, repo_slug):
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/permissions-config/users"
        users = []
        
        while url:
            res = requests.get(url, auth=(self.username, self.password))
            if res.status_code != 200:
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


class GitHubInspector(PlatformInspector):
    """GitHub repository inspector"""
    
    def __init__(self):
        super().__init__("GitHub")
        self.token = os.environ.get('GITHUB_TOKEN')
        
        if not self.token:
            self.errors.append("Missing GITHUB_TOKEN")
            return
    
    def inspect(self):
        if self.errors:
            return
        
        try:
            # Get personal repositories
            personal_repos = self._get_admin_repos()
            for repo in personal_repos:
                users = self._get_repo_collaborators(repo['owner'], repo['name'])
                self.repositories.append({
                    'name': repo['full_name'],
                    'owner': repo['owner'],
                    'type': 'personal',
                    'users': users
                })
            
            # Get organization repositories
            orgs = self._get_user_organizations()
            for org in orgs:
                org_repos = self._get_org_admin_repos(org)
                for repo in org_repos:
                    users = self._get_repo_collaborators(repo['owner'], repo['name'])
                    self.repositories.append({
                        'name': repo['full_name'],
                        'owner': repo['owner'],
                        'type': 'organization',
                        'organization': org,
                        'users': users
                    })
        except Exception as e:
            self.errors.append(f"Error during inspection: {str(e)}")
    
    def _get_user_organizations(self):
        url = 'https://api.github.com/user/orgs'
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        orgs = []
        
        while url:
            res = requests.get(url, headers=headers)
            if res.status_code != 200:
                raise Exception(f"Error fetching organizations: {res.status_code}")
            
            data = res.json()
            orgs.extend([org['login'] for org in data])
            
            if 'next' in res.links:
                url = res.links['next']['url']
            else:
                url = None
        
        return orgs
    
    def _get_admin_repos(self):
        url = 'https://api.github.com/user/repos'
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        params = {'type': 'all', 'sort': 'updated', 'per_page': 100}
        repos = []
        
        while url:
            res = requests.get(url, headers=headers, params=params)
            if res.status_code != 200:
                raise Exception(f"Error fetching repos: {res.status_code}")
            
            data = res.json()
            for repo in data:
                if repo.get('permissions', {}).get('admin', False):
                    repos.append({
                        'name': repo['name'],
                        'full_name': repo['full_name'],
                        'owner': repo['owner']['login']
                    })
            
            if 'next' in res.links:
                url = res.links['next']['url']
            else:
                url = None
        
        return repos
    
    def _get_org_admin_repos(self, org):
        url = f'https://api.github.com/orgs/{org}/repos'
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        params = {'type': 'all', 'per_page': 100}
        repos = []
        
        while url:
            res = requests.get(url, headers=headers, params=params)
            if res.status_code != 200:
                raise Exception(f"Error fetching org repos: {res.status_code}")
            
            data = res.json()
            for repo in data:
                if repo.get('permissions', {}).get('admin', False):
                    repos.append({
                        'name': repo['name'],
                        'full_name': repo['full_name'],
                        'owner': repo['owner']['login']
                    })
            
            if 'next' in res.links:
                url = res.links['next']['url']
            else:
                url = None
        
        return repos
    
    def _get_repo_collaborators(self, owner, repo_name):
        url = f'https://api.github.com/repos/{owner}/{repo_name}/collaborators'
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        params = {'per_page': 100}
        users = []
        
        while url:
            res = requests.get(url, headers=headers, params=params)
            if res.status_code != 200:
                break
            
            data = res.json()
            for user in data:
                users.append({
                    'username': user['login'],
                    'display_name': user.get('name', user['login']),
                    'permission': user.get('role_name', 'unknown')
                })
            
            if 'next' in res.links:
                url = res.links['next']['url']
            else:
                url = None
        
        return users


class GitLabInspector(PlatformInspector):
    """GitLab repository inspector"""
    
    def __init__(self):
        super().__init__("GitLab")
        self.token = os.environ.get('GITLAB_TOKEN')
        self.url = os.environ.get('GITLAB_URL', 'https://gitlab.com')
        
        if not self.token:
            self.errors.append("Missing GITLAB_TOKEN")
            return
    
    def inspect(self):
        if self.errors:
            return
        
        try:
            # Get personal projects
            personal_projects = self._get_user_projects()
            for project in personal_projects:
                users = self._get_project_members(project['id'])
                self.repositories.append({
                    'name': project['full_path'],
                    'id': project['id'],
                    'type': 'personal',
                    'users': users
                })
            
            # Get group projects
            groups = self._get_user_groups()
            for group in groups:
                group_projects = self._get_group_projects(group['id'])
                for project in group_projects:
                    users = self._get_project_members(project['id'])
                    self.repositories.append({
                        'name': project['full_path'],
                        'id': project['id'],
                        'type': 'group',
                        'group': group['name'],
                        'users': users
                    })
        except Exception as e:
            self.errors.append(f"Error during inspection: {str(e)}")
    
    def _get_user_groups(self):
        url = f'{self.url}/api/v4/groups'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        params = {'per_page': 100}
        groups = []
        
        while url:
            res = requests.get(url, headers=headers, params=params)
            if res.status_code != 200:
                raise Exception(f"Error fetching groups: {res.status_code}")
            
            data = res.json()
            for group in data:
                groups.append({
                    'id': group['id'],
                    'name': group['name'],
                    'path': group['path']
                })
            
            if 'next' in res.links:
                url = res.links['next']['url']
            else:
                url = None
        
        return groups
    
    def _get_user_projects(self):
        url = f'{self.url}/api/v4/projects'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        params = {'membership': True, 'per_page': 100}
        projects = []
        
        while url:
            res = requests.get(url, headers=headers, params=params)
            if res.status_code != 200:
                raise Exception(f"Error fetching projects: {res.status_code}")
            
            data = res.json()
            for project in data:
                if project.get('permissions', {}).get('project_access', {}).get('access_level', 0) >= 40:
                    projects.append({
                        'id': project['id'],
                        'name': project['name'],
                        'full_path': project['path_with_namespace']
                    })
            
            if 'next' in res.links:
                url = res.links['next']['url']
            else:
                url = None
        
        return projects
    
    def _get_group_projects(self, group_id):
        url = f'{self.url}/api/v4/groups/{group_id}/projects'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        params = {'per_page': 100}
        projects = []
        
        while url:
            res = requests.get(url, headers=headers, params=params)
            if res.status_code != 200:
                raise Exception(f"Error fetching group projects: {res.status_code}")
            
            data = res.json()
            for project in data:
                if project.get('permissions', {}).get('project_access', {}).get('access_level', 0) >= 40:
                    projects.append({
                        'id': project['id'],
                        'name': project['name'],
                        'full_path': project['path_with_namespace']
                    })
            
            if 'next' in res.links:
                url = res.links['next']['url']
            else:
                url = None
        
        return projects
    
    def _get_project_members(self, project_id):
        url = f'{self.url}/api/v4/projects/{project_id}/members'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        params = {'per_page': 100}
        users = []
        
        while url:
            res = requests.get(url, headers=headers, params=params)
            if res.status_code != 200:
                break
            
            data = res.json()
            for user in data:
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
                    'permission': permission
                })
            
            if 'next' in res.links:
                url = res.links['next']['url']
            else:
                url = None
        
        return users


class AzureDevOpsInspector(PlatformInspector):
    """Azure DevOps repository inspector"""
    
    def __init__(self):
        super().__init__("Azure DevOps")
        self.pat = os.environ.get('AZURE_DEVOPS_PAT')
        self.org = os.environ.get('AZURE_DEVOPS_ORG')
        
        if not self.pat or not self.org:
            self.errors.append("Missing AZURE_DEVOPS_PAT or AZURE_DEVOPS_ORG")
            return
    
    def inspect(self):
        if self.errors:
            return
        
        try:
            projects = self._get_projects()
            for project in projects:
                repos = self._get_repositories(project['id'])
                for repo in repos:
                    if self._check_user_permissions(project['id'], repo['id']):
                        users = self._get_repository_permissions(repo['id'])
                        self.repositories.append({
                            'name': f"{project['name']}/{repo['name']}",
                            'project': project['name'],
                            'repository': repo['name'],
                            'users': users
                        })
        except Exception as e:
            self.errors.append(f"Error during inspection: {str(e)}")
    
    def _get_authentication_header(self):
        credentials = f':{self.pat}'
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        return {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
    
    def _get_projects(self):
        url = f'https://dev.azure.com/{self.org}/_apis/projects'
        headers = self._get_authentication_header()
        params = {'api-version': '6.0', '$top': 100}
        projects = []
        
        while url:
            res = requests.get(url, headers=headers, params=params)
            if res.status_code != 200:
                raise Exception(f"Error fetching projects: {res.status_code}")
            
            data = res.json()
            for project in data.get('value', []):
                projects.append({
                    'id': project['id'],
                    'name': project['name']
                })
            
            if 'continuationToken' in data:
                params['continuationToken'] = data['continuationToken']
            else:
                url = None
        
        return projects
    
    def _get_repositories(self, project_id):
        url = f'https://dev.azure.com/{self.org}/{project_id}/_apis/git/repositories'
        headers = self._get_authentication_header()
        params = {'api-version': '6.0'}
        
        res = requests.get(url, headers=headers, params=params)
        if res.status_code != 200:
            raise Exception(f"Error fetching repositories: {res.status_code}")
        
        data = res.json()
        repos = []
        for repo in data.get('value', []):
            repos.append({
                'id': repo['id'],
                'name': repo['name']
            })
        
        return repos
    
    def _check_user_permissions(self, project_id, repo_id):
        url = f'https://dev.azure.com/{self.org}/_apis/git/repositories/{repo_id}/permissions'
        headers = self._get_authentication_header()
        params = {'api-version': '6.0'}
        
        res = requests.get(url, headers=headers, params=params)
        if res.status_code != 200:
            return False
        
        data = res.json()
        for permission in data.get('value', []):
            if permission.get('identityType') == 'user' and permission.get('permission') in ['Administer', 'Manage']:
                return True
        
        return False
    
    def _get_repository_permissions(self, repo_id):
        url = f'https://dev.azure.com/{self.org}/_apis/git/repositories/{repo_id}/permissions'
        headers = self._get_authentication_header()
        params = {'api-version': '6.0'}
        users = []
        
        res = requests.get(url, headers=headers, params=params)
        if res.status_code != 200:
            return users
        
        data = res.json()
        for permission in data.get('value', []):
            if permission.get('identityType') == 'user':
                identity = permission.get('identity', {})
                users.append({
                    'username': identity.get('displayName', identity.get('uniqueName', 'Unknown')),
                    'display_name': identity.get('displayName', identity.get('uniqueName', 'Unknown')),
                    'permission': permission.get('permission', 'unknown')
                })
        
        return users


def export_to_csv(data, filename):
    """Export data to CSV format"""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['platform', 'repository', 'username', 'display_name', 'permission']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for platform_data in data:
            platform = platform_data['platform']
            for repo in platform_data['repositories']:
                if repo.get('users'):
                    for user in repo['users']:
                        writer.writerow({
                            'platform': platform,
                            'repository': repo['name'],
                            'username': user['username'],
                            'display_name': user['display_name'],
                            'permission': user['permission']
                        })
                else:
                    # Write empty row for repositories with no users
                    writer.writerow({
                        'platform': platform,
                        'repository': repo['name'],
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


def main():
    """Main function to run all platform inspectors"""
    parser = argparse.ArgumentParser(description='Multi-Platform Repository Inspector')
    parser.add_argument('--csv', help='Export results to CSV file')
    parser.add_argument('--json', help='Export results to JSON file')
    parser.add_argument('--quiet', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("Multi-Platform Repository Inspector")
        print("=" * 40)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    # Initialize inspectors for all platforms
    inspectors = [
        BitbucketInspector(),
        GitHubInspector(),
        GitLabInspector(),
        AzureDevOpsInspector()
    ]
    
    # Run inspections for platforms with valid credentials
    valid_inspectors = [inspector for inspector in inspectors if not inspector.errors]
    
    if not valid_inspectors:
        if not args.quiet:
            print("No platforms configured. Please check your .env file.")
            print("\nRequired environment variables:")
            print("- Bitbucket: BITBUCKET_USERNAME, BITBUCKET_APP_PASSWORD")
            print("- GitHub: GITHUB_TOKEN")
            print("- GitLab: GITLAB_TOKEN")
            print("- Azure DevOps: AZURE_DEVOPS_PAT, AZURE_DEVOPS_ORG")
        return
    
    if not args.quiet:
        print(f"Found {len(valid_inspectors)} platform(s) with valid credentials.")
        print()
    
    # Run inspections
    total_repositories = 0
    export_data = []
    
    for inspector in valid_inspectors:
        if not args.quiet:
            print(f"Inspecting {inspector.name}...")
        
        inspector.inspect()
        
        if not args.quiet:
            inspector.print_results()
            if inspector.errors:
                print(f"Errors: {', '.join(inspector.errors)}")
            print()
        
        total_repositories += len(inspector.repositories)
        export_data.append(inspector.get_export_data())
    
    # Summary
    if not args.quiet:
        print("=" * 40)
        print("SUMMARY")
        print("=" * 40)
        print(f"Total repositories with admin access: {total_repositories}")
        print(f"Platforms checked: {len(valid_inspectors)}")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Export data if requested
    if args.csv:
        export_to_csv(export_data, args.csv)
    
    if args.json:
        export_to_json(export_data, args.json)


if __name__ == '__main__':
    main() 