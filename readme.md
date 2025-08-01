# Bitbucket Admin Repository Inspector

A Python script that fetches all Bitbucket Cloud repositories where you are an admin, across all workspaces you belong to. It also lists users with direct permissions on each repository, along with their roles (`admin`, `write`, or `read`).

## Problem Statement

Managing access permissions across multiple Bitbucket repositories can be extremely time-consuming and error-prone. When you have tens or hundreds of repositories, manually checking which users have access to which repositories and at what permission level becomes a daunting task.

**Common challenges:**
- Manually navigating through each repository's settings
- Checking individual user permissions one by one
- No centralized view of all repository access
- Time-consuming audit processes
- Risk of missing users or repositories during manual checks

This tool automates the entire process, providing you with a comprehensive overview of all repositories where you have admin access and the users who have direct permissions on each one.

## Features

- Lists all Bitbucket workspaces you have access to
- Fetches all repositories where you have `admin` role
- Displays users with direct access to each repository
- Shows their permission level (admin, write, read)
- Uses environment variables for secure authentication
- Handles pagination for large datasets
- Provides detailed error reporting

## Prerequisites

- Python 3.6 or higher
- Bitbucket Cloud account with admin access to repositories
- Bitbucket App Password (not your regular password)

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

Then edit the `.env` file with your actual Bitbucket credentials:

```env
BITBUCKET_USERNAME=your_bitbucket_username
BITBUCKET_APP_PASSWORD=your_bitbucket_app_password
```

### 3. Generate Bitbucket App Password

1. Go to Bitbucket Cloud settings
2. Navigate to "App passwords" under "Access management"
3. Create a new app password with the following permissions:
   - Repositories: Read
   - Workspace membership: Read
4. Copy the generated password to your `.env` file

## Usage

Run the script from the command line:

```bash
python bitbucket_repos_user_list.py
```

## Output

The script will display:
- All workspaces you have access to
- All repositories where you are an admin
- Users with direct permissions on each repository
- Their permission levels (admin, write, read)

Example output:
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

## How It Works

1. **Authentication**: Uses HTTP Basic Auth with your username and app password
2. **Workspace Discovery**: Fetches all workspaces you belong to using the Bitbucket API
3. **Repository Filtering**: For each workspace, finds repositories where you have admin role
4. **Permission Analysis**: For each admin repository, retrieves users with direct permissions
5. **Pagination Handling**: Automatically handles large datasets using Bitbucket's pagination

## API Endpoints Used

- `GET /2.0/workspaces` - List all workspaces
- `GET /2.0/repositories/{workspace}` - List repositories with role filter
- `GET /2.0/repositories/{workspace}/{repo_slug}/permissions-config/users` - Get user permissions

## Error Handling

The script includes error handling for:
- Missing environment variables
- Authentication failures
- API rate limiting
- Network connectivity issues
- Invalid workspace or repository access

## Security Notes

- Never commit your `.env` file to version control
- Use app passwords instead of your main account password
- App passwords can be revoked if compromised
- The script only reads data, it cannot modify permissions

## Troubleshooting

### Common Issues

1. **Authentication Error**: Verify your username and app password in the `.env` file
2. **No Repositories Found**: Ensure you have admin access to repositories
3. **Permission Denied**: Check that your app password has the required permissions
4. **Rate Limiting**: The script handles pagination automatically, but may hit rate limits with large datasets

### Debug Mode

To see detailed API responses, you can modify the script to print response details:

```python
print(f"Response: {res.status_code} - {res.text}")
```

## Dependencies

- `requests`: HTTP library for API calls
- `python-dotenv`: Environment variable management

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues and enhancement requests.

