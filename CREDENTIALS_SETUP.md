# Gmail Credentials Setup

## File Structure

For security and privacy, Gmail credentials should be stored **one folder above** the project directory:

```
parent-directory/
├── credentials.json     ← Place Gmail API credentials here
├── token.json          ← Auto-generated OAuth token (after first run)
├── .env                ← Configuration file (copied from .env.example)
└── mail-pilot/         ← Project directory
    ├── src/
    ├── templates/
    ├── .env.example    ← Template file
    └── ...
```

## Setup Steps

### 1. Download Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable the Gmail API
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Choose **Desktop Application** as application type
6. Download the JSON file
7. **Rename it to `credentials.json`**
8. **Move it to the parent directory** (one folder above mail-pilot)

### 2. Create Configuration File

Copy the template to the parent directory and update it:

```bash
cp .env.example ../.env
```

Your `../.env` file should contain:

```env
# Gmail API Configuration (stored in parent directory for privacy)
GMAIL_CREDENTIALS_PATH=../credentials.json
GMAIL_TOKEN_PATH=../token.json

# Email Configuration
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Other settings...
```

### 3. First Run Authentication

When you first run the service:

1. It will open a browser for Gmail authorization
2. Sign in with your Gmail account
3. Grant permissions to read emails
4. `token.json` will be created automatically in the parent directory

## Security Benefits

**Why store sensitive files in parent directory:**

✅ **Git Safety**: All sensitive files are outside the project repository  
✅ **Accidental Commits**: Won't be included in version control  
✅ **Deployment Separation**: Keeps secrets and config separate from code  
✅ **Multi-Project Usage**: Can be shared across multiple instances  
✅ **Environment Isolation**: Different .env files for dev/staging/prod  

## File Permissions (Recommended)

Set restrictive permissions on credential files:

```bash
# Make all sensitive files readable only by owner
chmod 600 ../credentials.json
chmod 600 ../token.json
chmod 600 ../.env
```

## Troubleshooting

**File not found errors:**
- Verify `credentials.json` and `.env` are in the parent directory
- Check the paths in your `../.env` file
- Ensure files are named exactly `credentials.json` and `.env`

**Permission errors:**
- Check file permissions
- Ensure the directory is readable
- Run with appropriate user permissions

**OAuth errors:**
- Delete `token.json` and re-authenticate
- Check OAuth client configuration in Google Cloud Console
- Verify redirect URIs are configured correctly

## Multiple Environments

For different environments (dev/staging/prod), you can use different credential files:

```env
# Development
GMAIL_CREDENTIALS_PATH=../credentials-dev.json
GMAIL_TOKEN_PATH=../token-dev.json

# Production
GMAIL_CREDENTIALS_PATH=../credentials-prod.json
GMAIL_TOKEN_PATH=../token-prod.json
```

## Web UI Behavior

The web interface will:
- Check for `credentials.json` in the parent directory
- Show an error if not found
- Guide users through the setup process
- Create temporary copies for OAuth flow
- Clean up temporary files on logout