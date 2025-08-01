# Multi-Platform Repository Permission Inspector

A collection of Python scripts that fetch all repositories where you have admin access across multiple repository management platforms, along with users who have direct permissions on each repository.

## Supported Platforms

- **Bitbucket Cloud** - Atlassian's Git hosting service
- **GitHub** - Microsoft's code hosting platform  
- **GitLab** - Complete DevOps platform
- **Azure DevOps** - Microsoft's enterprise development platform

## Problem Statement

Managing access permissions across multiple repositories and platforms can be extremely time-consuming and error-prone. When you have tens or hundreds of repositories across different platforms, manually checking which users have access to which repositories and at what permission level becomes a daunting task.

**Common challenges:**
- Manually navigating through each repository's settings across different platforms
- Checking individual user permissions one by one
- No centralized view of all repository access across platforms
- Time-consuming audit processes
- Risk of missing users or repositories during manual checks

These tools automate the entire process, providing you with a comprehensive overview of all repositories where you have admin access and the users who have direct permissions on each one.

## Features

### All Platforms
- Lists all repositories/projects where you have admin/maintainer role
- Displays users with direct access to each repository
- Shows their permission level (admin, write, read, etc.)
- Uses environment variables for secure authentication
- Handles pagination for large datasets
- Provides detailed error reporting

### Platform-Specific Features

#### Bitbucket
- Lists all Bitbucket workspaces you have access to
- Fetches repositories where you have `admin` role
- Shows permission levels: admin, write, read

#### GitHub
- Lists personal repositories and organization repositories
- Fetches repositories where you have `admin` permissions
- Shows collaborator roles: admin, maintain, write, triage, read

#### GitLab
- Lists personal projects and group projects
- Fetches projects where you have `maintainer` or `owner` access
- Shows access levels: owner, maintainer, developer, reporter, guest

#### Azure DevOps
- Lists all projects in your organization
- Fetches repositories where you have admin permissions
- Shows user permissions and team memberships

## Prerequisites

- Python 3.6 or higher
- Admin/maintainer access to repositories on the platforms you want to inspect
- Appropriate authentication tokens for each platform

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Environment File

Copy the example environment file and configure your credentials:

```bash
cp env.example .env
```

Then edit the `.env` file with your actual credentials for each platform:

```env
# Bitbucket credentials
BITBUCKET_USERNAME=your_bitbucket_username
BITBUCKET_APP_PASSWORD=your_bitbucket_app_password

# GitHub credentials
GITHUB_USERNAME=your_github_username
GITHUB_TOKEN=your_github_personal_access_token

# GitLab credentials
GITLAB_TOKEN=your_gitlab_personal_access_token
GITLAB_URL=https://gitlab.com  # Change to your GitLab instance URL if self-hosted

# Azure DevOps credentials
AZURE_DEVOPS_PAT=your_azure_devops_personal_access_token
AZURE_DEVOPS_ORG=your_azure_devops_organization_name
```

### 3. Generate Authentication Tokens

#### Bitbucket
1. Go to Bitbucket Cloud settings
2. Navigate to "App passwords" under "Access management"
3. Create a new app password with the following permissions:
   - Repositories: Read
   - Workspace membership: Read
4. Copy the generated password to your `.env` file

#### GitHub
1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a new token with the following scopes:
   - `repo` (Full control of private repositories)
   - `read:org` (Read organization data)
3. Copy the token to your `.env` file

#### GitLab
1. Go to GitLab User Settings > Access Tokens
2. Create a new token with the following scopes:
   - `read_api` (Read API)
   - `read_user` (Read user information)
3. Copy the token to your `.env` file

#### Azure DevOps
1. Go to Azure DevOps User Settings > Personal access tokens
2. Create a new token with the following scopes:
   - `vso.code` (Read code)
   - `vso.project` (Read project information)
   - `vso.security_manage` (Manage security)
3. Copy the token to your `.env` file

## Usage

### Individual Platform Scripts

Run the appropriate script for each platform:

```bash
# Bitbucket
python bitbucket_repos_user_list.py

# GitHub
python github_repos_user_list.py

# GitLab
python gitlab_repos_user_list.py

# Azure DevOps
python azure_devops_repos_user_list.py
```

### Export Options

All scripts support CSV and JSON export:

```bash
# Export to CSV
python github_repos_user_list.py --csv github_repos.csv

# Export to JSON
python gitlab_repos_user_list.py --json gitlab_projects.json

# Export both formats
python bitbucket_repos_user_list.py --csv bitbucket_repos.csv --json bitbucket_repos.json

# Quiet mode (suppress console output)
python azure_devops_repos_user_list.py --quiet --csv azure_repos.csv
```

### Multi-Platform Unified Script

```bash
# Run all platforms
python multi_platform_inspector.py

# Export to CSV
python multi_platform_inspector.py --csv all_repos.csv

# Export to JSON
python multi_platform_inspector.py --json all_repos.json

# Quiet mode with export
python multi_platform_inspector.py --quiet --csv all_repos.csv --json all_repos.json
```

## Output Examples

### Individual Platform Scripts

#### Bitbucket Output
```bash
$ python bitbucket_repos_user_list.py
```
```
Fetching workspaces...

Workspace: my-workspace
Repo: my-workspace/my-project
   John Doe (john.doe) - admin
   Jane Smith (jane.smith) - write
   Bob Wilson (bob.wilson) - read

Workspace: another-workspace
Repo: another-workspace/legacy-project
   No direct user permissions found.

Finished. Total repositories checked: 2
```

#### GitHub Output
```bash
$ python github_repos_user_list.py
```
```
Fetching GitHub repositories where you have admin access...

=== Personal Repositories ===
Repo: username/my-project
   John Doe (john.doe) - admin
   Jane Smith (jane.smith) - write

Repo: username/private-repo
   No direct collaborators found.

=== Organization Repositories ===
Organization: my-org
Repo: my-org/team-project
   Alice Johnson (alice.johnson) - maintain
   Bob Wilson (bob.wilson) - write

Organization: another-org
Repo: another-org/shared-lib
   Charlie Brown (charlie.brown) - admin
   Diana Prince (diana.prince) - triage

Finished. Total repositories checked: 4
```

#### GitLab Output
```bash
$ python gitlab_repos_user_list.py
```
```
Fetching GitLab projects where you have maintainer/owner access...

=== Personal Projects ===
Project: username/my-project
   John Doe (john.doe) - maintainer
   Jane Smith (jane.smith) - developer

Project: username/private-project
   No direct members found.

=== Group Projects ===
Group: My Team (my-team)
Project: my-team/team-project
   Alice Johnson (alice.johnson) - owner
   Bob Wilson (bob.wilson) - developer

Group: DevOps (devops)
Project: devops/ci-cd-pipeline
   Charlie Brown (charlie.brown) - maintainer
   Diana Prince (diana.prince) - reporter

Finished. Total projects checked: 4
```

#### Azure DevOps Output
```bash
$ python azure_devops_repos_user_list.py
```
```
Fetching Azure DevOps repositories where you have admin access...

Project: MyProject
Repository: my-repo
  ✓ You have admin access
   John Doe (john.doe@company.com) - Administer
   Jane Smith (jane.smith@company.com) - Contribute

Repository: shared-lib
  ✓ You have admin access
   No direct user permissions found.

Project: LegacyProject
Repository: old-repo
  ✗ No admin access

Finished. Total repositories with admin access: 2
```

### Multi-Platform Unified Script

#### Complete Output Example
```bash
$ python multi_platform_inspector.py
```
```
Multi-Platform Repository Permission Inspector
========================================
Started at: 2024-01-15 10:30:00

Found 3 platform(s) with valid credentials.

Inspecting GitHub...
GitHub:
==========
Repository: username/my-project
   John Doe (john.doe) - admin
   Jane Smith (jane.smith) - write

Repository: my-org/team-project
   Alice Johnson (alice.johnson) - maintain
   Bob Wilson (bob.wilson) - write

Total repositories: 2

Inspecting GitLab...
GitLab:
========
Repository: username/my-project
   John Doe (john.doe) - maintainer
   Jane Smith (jane.smith) - developer

Repository: my-team/team-project
   Alice Johnson (alice.johnson) - owner
   Bob Wilson (bob.wilson) - developer

Total repositories: 2

Inspecting Azure DevOps...
Azure DevOps:
=============
Repository: MyProject/my-repo
   John Doe (john.doe@company.com) - Administer
   Jane Smith (jane.smith@company.com) - Contribute

Total repositories: 1

========================================
SUMMARY
========================================
Total repositories with admin access: 5
Platforms checked: 3
Completed at: 2024-01-15 10:30:45
```

#### Error Handling Examples

**Missing Credentials:**
```bash
$ python multi_platform_inspector.py
```
```
Multi-Platform Repository Permission Inspector
========================================
Started at: 2024-01-15 10:30:00

No platforms configured. Please check your .env file.

Required environment variables:
- Bitbucket: BITBUCKET_USERNAME, BITBUCKET_APP_PASSWORD
- GitHub: GITHUB_TOKEN
- GitLab: GITLAB_TOKEN
- Azure DevOps: AZURE_DEVOPS_PAT, AZURE_DEVOPS_ORG
```

**Authentication Error:**
```
Inspecting GitHub...
Errors: Error during inspection: Error fetching organizations: 401
```

**No Admin Access:**
```
Inspecting GitLab...
GitLab:
========
No repositories with admin access found.
```

### Export Formats

#### CSV Export

CSV files contain one row per user-repository relationship:

```csv
platform,repository,username,display_name,permission
GitHub,username/my-project,john.doe,John Doe,admin
GitHub,username/my-project,jane.smith,Jane Smith,write
GitLab,username/my-project,john.doe,John Doe,maintainer
```

#### JSON Export

JSON files contain structured data with full repository and user information:

```json
[
  {
    "platform": "GitHub",
    "repositories": [
      {
        "name": "username/my-project",
        "type": "personal",
        "owner": "username",
        "users": [
          {
            "username": "john.doe",
            "display_name": "John Doe",
            "permission": "admin"
          }
        ]
      }
    ]
  }
]
```

### Expected Data Structure

Each script returns data in a consistent format:

```python
# Repository/Project Structure
{
    'name': 'owner/repo-name',
    'users': [
        {
            'username': 'john.doe',
            'display_name': 'John Doe',
            'permission': 'admin'  # or 'write', 'read', 'maintainer', etc.
        }
    ]
}
```

### Permission Level Mapping

| Platform | Permission Levels |
|----------|------------------|
| **Bitbucket** | `admin`, `write`, `read` |
| **GitHub** | `admin`, `maintain`, `write`, `triage`, `read` |
| **GitLab** | `owner`, `maintainer`, `developer`, `reporter`, `guest` |
| **Azure DevOps** | `Administer`, `Contribute`, `Read`, `Manage` |

## API Endpoints Used

### Bitbucket
- `GET /2.0/workspaces` - List all workspaces
- `GET /2.0/repositories/{workspace}` - List repositories with role filter
- `GET /2.0/repositories/{workspace}/{repo_slug}/permissions-config/users` - Get user permissions

### GitHub
- `GET /user/orgs` - List user organizations
- `GET /user/repos` - List user repositories
- `GET /orgs/{org}/repos` - List organization repositories
- `GET /repos/{owner}/{repo}/collaborators` - Get repository collaborators

### GitLab
- `GET /api/v4/groups` - List user groups
- `GET /api/v4/projects` - List user projects
- `GET /api/v4/groups/{id}/projects` - List group projects
- `GET /api/v4/projects/{id}/members` - Get project members

### Azure DevOps
- `GET /_apis/projects` - List organization projects
- `GET /_apis/git/repositories` - List project repositories
- `GET /_apis/git/repositories/{id}/permissions` - Get repository permissions

## Error Handling

All scripts include error handling for:
- Missing environment variables
- Authentication failures
- API rate limiting
- Network connectivity issues
- Invalid repository or project access

## Security Notes

- Never commit your `.env` file to version control
- Use personal access tokens instead of passwords
- Tokens can be revoked if compromised
- The scripts only read data, they cannot modify permissions
- Store tokens securely and rotate them regularly

## Troubleshooting

### Common Issues

1. **Authentication Error**: Verify your credentials in the `.env` file
2. **No Repositories Found**: Ensure you have admin/maintainer access to repositories
3. **Permission Denied**: Check that your tokens have the required scopes
4. **Rate Limiting**: The scripts handle pagination automatically, but may hit rate limits with large datasets

### Platform-Specific Issues

#### Bitbucket
- Ensure your app password has the correct permissions
- Check that you're using the correct username (not email)

#### GitHub
- Verify your personal access token has the required scopes
- For organization repositories, ensure you're a member of the organization

#### GitLab
- For self-hosted GitLab, update the `GITLAB_URL` in your `.env` file
- Ensure your token has the correct scopes

#### Azure DevOps
- Verify your organization name is correct
- Ensure your PAT has the required scopes

## Dependencies

- `requests`: HTTP library for API calls
- `python-dotenv`: Environment variable management

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues and enhancement requests for additional platforms or features. 