# Mail Pilot Web UI Setup and Usage

## Overview

The Mail Pilot Web UI provides a user-friendly interface for Gmail registration, service configuration, and manual email processing. Users can seamlessly connect their Gmail account and trigger email summaries through a modern web interface.

## Features

- **Seamless Gmail OAuth2 Registration**: One-click Gmail account connection
- **Interactive Configuration**: Web forms for all service settings
- **Manual Email Processing**: Button to trigger email summaries on-demand
- **Real-time Status Updates**: Live progress tracking and status indicators
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Session Management**: Secure browser session handling

## Installation and Setup

### 1. Install Web Dependencies

The web UI requires additional Flask dependencies:

```bash
pip install -r requirements.txt
```

### 2. Start the Web Application

```bash
python web_app.py
```

The application will be available at: `http://localhost:5000`

### 3. Access the Web Interface

1. Open your browser to `http://localhost:5000`
2. Follow the registration flow to connect Gmail
3. Configure service settings
4. Use the dashboard to manually process emails

## Web Application Structure

```
web_app.py              # Main Flask application
templates/              # HTML templates
├── base.html          # Base template with navigation
├── index.html         # Landing page
├── register.html      # Gmail registration flow
├── setup.html         # Service configuration
├── dashboard.html     # Main dashboard
└── error.html         # Error pages
static/
├── css/
│   └── custom.css     # Custom styling
└── js/
    └── app.js         # JavaScript functionality
```

## Usage Flow

### 1. Gmail Registration

**URL**: `/register`

- **Prerequisites Check**: Interactive checklist for setup requirements
- **OAuth2 Flow**: Secure Gmail authorization
- **Account Verification**: Confirms successful connection

**Requirements**:
- Gmail account with 2FA enabled
- Gmail App Password generated
- Gmail API credentials.json file
- Ollama running with a model

### 2. Service Configuration

**URL**: `/setup`

Configure the following settings:

**Email Settings**:
- Gmail App Password (required)
- SMTP server and port
- Email address (auto-populated)

**Ollama Settings**:
- Ollama URL (default: http://localhost:11434)
- AI model selection (llama3.1, llama2, mistral, etc.)
- Connection testing

**Voice Settings**:
- Enable/disable voice summaries
- Language selection (10+ languages supported)

### 3. Dashboard

**URL**: `/dashboard`

Main interface features:

**Manual Processing**:
- "Process Emails Now" button
- Real-time progress tracking
- Status indicators

**Status Information**:
- Processing state (Ready/Processing/Error)
- Last run timestamp
- Processing results summary

**Results Display**:
- Total emails processed
- High priority count
- Action items found
- Success/error status

## API Endpoints

### Authentication Required Endpoints

All API endpoints require an active session (user must be registered).

**POST** `/api/process-emails`
- Triggers manual email processing
- Returns: Processing status

**GET** `/api/status`
- Returns current processing status
- Includes last run results

**GET** `/api/test-ollama`
- Tests Ollama service connection
- Returns connection status and model info

### Public Endpoints

**GET** `/`
- Landing page (redirects to dashboard if registered)

**GET** `/register`
- Gmail registration page

**GET** `/oauth/gmail`
- Initiates Gmail OAuth2 flow

**GET** `/logout`
- Clears session and temporary files

## Configuration

### Environment Variables

The web app uses the same environment variables as the CLI version:

```env
# Gmail Configuration
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Voice Configuration
VOICE_ENABLED=true
VOICE_LANGUAGE=en
```

### Session Configuration

Sessions are stored in the filesystem and automatically expire. Configuration includes:

- **SESSION_TYPE**: filesystem
- **SESSION_PERMANENT**: false
- **SESSION_USE_SIGNER**: true (for security)

## Security Features

### OAuth2 Implementation

- **Secure Flow**: Uses Google's official OAuth2 implementation
- **Temporary Credentials**: Creates isolated credential files per session
- **No Password Storage**: Never stores or transmits Gmail passwords
- **Session Isolation**: Each user session has separate credential files

### Session Management

- **Auto-Expiry**: Sessions automatically expire
- **Secure Cookies**: Signed session cookies
- **Cleanup**: Temporary files removed on logout
- **CSRF Protection**: Built-in Flask CSRF protection

## Development

### Running in Development Mode

```bash
# Enable debug mode
python web_app.py
```

Debug mode includes:
- Auto-reload on file changes
- Detailed error messages
- Development server

### Production Deployment

For production deployment:

```bash
# Use a production WSGI server
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

### Customization

**Styling**: Modify `static/css/custom.css`
**Functionality**: Extend `static/js/app.js`
**Templates**: Customize HTML in `templates/`

## Troubleshooting

### Common Issues

**Gmail OAuth Fails**:
- Verify `credentials.json` exists in project root
- Check Google Cloud Console API settings
- Ensure Gmail API is enabled

**Ollama Connection Issues**:
- Verify Ollama is running: `ollama list`
- Check URL in configuration
- Test with: `curl http://localhost:11434/api/tags`

**Session Issues**:
- Clear browser cookies
- Check filesystem permissions for session storage
- Restart the web application

**Processing Failures**:
- Check Ollama model is pulled: `ollama pull llama3.1`
- Verify Gmail App Password is correct
- Check email configuration settings

### Logging

Web application logs include:

- **Console Output**: Real-time application logs
- **Browser Console**: JavaScript errors and status updates
- **Flask Logs**: HTTP requests and application events

## Browser Support

**Supported Browsers**:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Required Features**:
- JavaScript enabled
- Cookies enabled
- Modern CSS support (Grid, Flexbox)

## Mobile Support

The web UI is fully responsive and works on:

- **Mobile Phones**: iOS Safari, Chrome Mobile
- **Tablets**: iPad Safari, Android Chrome
- **Touch Interfaces**: Full touch support for all interactions

## API Integration

The web UI can be extended to integrate with external services:

- **Webhooks**: Add webhook endpoints for external triggers
- **APIs**: Expose additional REST endpoints
- **Real-time Updates**: WebSocket support for live updates

## Performance

**Optimization Features**:
- **Lazy Loading**: Components load as needed
- **Debounced Requests**: Prevents excessive API calls
- **Caching**: Static assets cached by browser
- **Minimal Dependencies**: Only essential libraries loaded

**Resource Usage**:
- **Memory**: ~50MB base Flask application
- **CPU**: Low usage except during email processing
- **Network**: Minimal except during OAuth and API calls