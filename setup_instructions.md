# Mail Pilot Setup Instructions

## Prerequisites

1. **Python 3.8+** installed on your system
2. **Ollama** installed and running locally
3. **Gmail Account** with 2FA enabled
4. **App Password** generated for Gmail

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Gmail API Setup

#### Enable Gmail API:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API
4. Create credentials (OAuth 2.0 Client ID)
5. Download the credentials file as `credentials.json`

#### Set up OAuth:
1. Place `credentials.json` in the parent directory (one folder above the project for privacy)
2. Run the service once to complete OAuth flow
3. This will create `token.json` in the parent directory for future authentication

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your settings:
```env
# Gmail API Configuration (stored in parent directory for privacy)
GMAIL_CREDENTIALS_PATH=../credentials.json
GMAIL_TOKEN_PATH=../token.json

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Scheduling Configuration (hours)
SUMMARY_INTERVAL=6

# Voice Configuration
VOICE_ENABLED=true
VOICE_LANGUAGE=en
```

### 4. Generate Gmail App Password

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Security → 2-Step Verification → App passwords
3. Generate a new app password for "Mail"
4. Use this password in the `EMAIL_PASSWORD` field

### 5. Install and Configure Ollama

#### Install Ollama:
```bash
# On macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# On Windows - download from https://ollama.ai/download
```

#### Pull a model:
```bash
ollama pull llama3.1
# or
ollama pull llama2
# or any other model you prefer
```

#### Start Ollama service:
```bash
ollama serve
```

## Usage

### Run Once (Manual)
```bash
python main.py --once
```

### Run Scheduled Service
```bash
python main.py
```

### Check Status
```bash
python main.py --status
```

### Custom Configuration File
```bash
python main.py --config /path/to/custom/.env
```

## Configuration Options

### Scheduling Intervals
- Minimum: 1 hour
- Maximum: 24 hours
- Recommended: 6-12 hours

### Voice Settings
- Supported languages: en, es, fr, de, it, pt, ru, ja, ko, zh
- Voice files are automatically attached to summary emails
- Can be disabled by setting `VOICE_ENABLED=false`

### Ollama Models
Popular models to try:
- `llama3.1` (recommended)
- `llama2`
- `mistral`
- `codellama`

## Troubleshooting

### Gmail Authentication Issues
1. Ensure 2FA is enabled on your Google account
2. Use an App Password, not your regular password
3. Check that Gmail API is enabled in Google Cloud Console

### Ollama Connection Issues
1. Verify Ollama is running: `ollama list`
2. Check the URL in configuration matches Ollama's address
3. Ensure the model is pulled: `ollama pull llama3.1`

### Email Sending Issues
1. Verify SMTP settings for your email provider
2. Check firewall settings for SMTP ports
3. Ensure App Password is correctly generated

### Voice Generation Issues
1. Check internet connection (gTTS requires internet)
2. Verify language code is supported
3. Voice generation failures won't stop email summaries

## Running as a Service

### Linux (systemd)
Create `/etc/systemd/system/mail-pilot.service`:
```ini
[Unit]
Description=Mail Pilot Email Summary Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/mail-pilot
ExecStart=/usr/bin/python3 /path/to/mail-pilot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable mail-pilot
sudo systemctl start mail-pilot
```

### macOS (launchd)
Create `~/Library/LaunchAgents/com.mailpilot.service.plist`

### Windows
Use Task Scheduler or install as Windows service

## Security Notes

- Keep your `credentials.json` and `token.json` files secure
- Use App Passwords instead of your main Google password
- Consider running the service in a dedicated environment
- Regularly rotate your App Password

## Logs

Service logs are written to:
- `mail_pilot.log` in the project directory
- Console output when running manually

Log levels: DEBUG, INFO, WARNING, ERROR