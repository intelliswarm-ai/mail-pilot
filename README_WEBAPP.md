# Mail Pilot Web Application

A comprehensive web interface for intelligent email management with AI-powered categorization, phishing detection, and auto-reply generation.

## Features

### Core Functionality
- **AI-Powered Email Categorization**: Three methods available:
  - Fast processing (no categorization)
  - Enhanced NLP clustering (TF-IDF + adaptive clustering)
  - Hybrid AI categorization (clustering + LLM naming)

- **Intelligent Email Processing**:
  - Automatic email summaries using AI
  - Action item extraction and categorization
  - Priority level assignment
  - Response requirement detection

- **Security & Safety**:
  - Advanced phishing detection with risk scoring
  - Rule-based + LLM analysis for comprehensive threat assessment
  - Risk indicators and safety recommendations
  - Visual alerts for high-risk emails

- **Auto-Reply Generation**:
  - Context-aware reply suggestions
  - Multiple tone options (professional, friendly, formal, helpful)
  - Side-by-side interface for review and editing
  - Template-based fallbacks for reliability

### Web Interface Features
- **Responsive Dashboard**: Real-time processing status and results overview
- **Email Categories View**: Filterable and searchable email organization
- **Detailed Email View**: Comprehensive email analysis and metadata
- **Reply Interface**: Split-screen original/reply editing with approval workflow
- **Progress Tracking**: Real-time processing updates with progress indicators

## Installation & Setup

### Prerequisites
- Python 3.8+
- Gmail API credentials
- Ollama with Mistral model for LLM features

### Quick Start

1. **Install Dependencies**:
   ```bash
   pip install flask requests
   ```

2. **Start the Web Server**:
   ```bash
   cd /path/to/mail-pilot
   python -m src.web_app
   ```

3. **Access the Interface**:
   - Open browser to `http://localhost:5000`
   - Configure email processing options
   - Start processing emails

## API Endpoints

### Processing Control
- `POST /api/trigger-processing` - Start email processing
- `GET /api/processing-status` - Get current processing status
- `GET /api/results` - Retrieve processing results
- `POST /api/trigger-cli` - Run CLI version

### Email Management
- `GET /email-details/<email_id>` - View detailed email information
- `GET /reply-interface/<email_id>` - Access reply interface
- `POST /api/update-reply` - Update suggested reply
- `POST /api/approve-reply` - Approve/send reply

### Views
- `GET /` - Main dashboard
- `GET /dashboard` - Dashboard with results
- `GET /categories` - Category-organized view

## Configuration Options

### Processing Parameters
- **Timeframe**: 12h, 24h, 48h, 3d, 7d, or all unread
- **Categorization Method**: 
  - `none` - Fast processing
  - `enhanced` - NLP clustering
  - `llm` - Hybrid AI categorization
- **Features**:
  - Phishing detection (enabled by default)
  - Auto-reply suggestions (optional)

### Security Settings
- **Phishing Detection**: Configurable risk thresholds
- **LLM Timeouts**: Progressive timeout handling (60s → 300s → 1500s)
- **API Rate Limiting**: Built-in retry mechanisms

## File Structure

```
src/
├── web_app.py                 # Flask application main file
├── templates/                 # Jinja2 templates
│   ├── base.html             # Base template with common layout
│   ├── dashboard.html        # Main dashboard interface
│   ├── email_details.html    # Detailed email view
│   ├── reply_interface.html  # Split-screen reply editor
│   └── categories.html       # Category-organized email view
├── static/                   # Static assets
│   ├── css/
│   │   └── mail-pilot.css    # Custom styles
│   └── js/
│       └── mail-pilot.js     # JavaScript utilities
├── auto_reply_generator.py   # AI-powered reply generation
├── phishing_detector.py      # Security analysis
└── [other email processing modules]
```

## Usage Examples

### Basic Email Processing
1. Navigate to dashboard
2. Select timeframe (e.g., "Last 24 hours")
3. Choose "Enhanced NLP Clustering"
4. Enable phishing detection
5. Click "Start Processing"
6. Monitor progress and view results

### Reply Management
1. Click "Reply" button on any email requiring response
2. Review original email (left panel)
3. Edit suggested reply (right panel)
4. Validate using built-in quality checks
5. Approve or send immediately

### Security Analysis
- High-risk emails automatically flagged
- Detailed risk indicators and explanations
- Color-coded threat levels (safe/low/medium/high)
- Actionable security recommendations

## Advanced Features

### Real-Time Processing
- WebSocket-like polling for status updates
- Progressive loading with user feedback
- Background processing prevents UI blocking

### Data Export
- JSON export of email data and analysis
- Category statistics and metrics
- Individual email content and metadata

### Keyboard Shortcuts
- `Ctrl/Cmd + /` - Show help and shortcuts
- `Esc` - Close open modals
- `Ctrl/Cmd + R` - Refresh (with processing confirmation)

## Troubleshooting

### Common Issues

1. **Service Initialization Failed**:
   - Check Gmail API credentials
   - Verify Ollama is running on localhost:11434
   - Ensure Mistral model is available

2. **Processing Stuck**:
   - Check logs in `logs/webapp.log`
   - Verify LLM service connectivity
   - Review timeout settings

3. **Missing Results**:
   - Confirm processing completed successfully
   - Check for errors in browser console
   - Verify API endpoints responding

### Performance Optimization
- Use "Enhanced NLP" for faster processing
- Enable LLM features only when needed
- Process smaller timeframes for quicker results

## Security Considerations

- Never commit API credentials
- Review auto-generated replies before sending
- Trust but verify phishing detection results
- Use HTTPS in production environments

## Development

### Adding New Features
1. Create new templates in `src/templates/`
2. Add routes in `web_app.py`
3. Implement backend logic in dedicated modules
4. Update static assets as needed

### Styling Guidelines
- Follow Bootstrap 5 conventions
- Use CSS custom properties for theming
- Maintain responsive design principles
- Include accessibility features

## Support

For issues and feature requests:
- Check existing GitHub issues
- Review troubleshooting guide
- Consult application logs
- Submit detailed bug reports

---

**Note**: This web interface provides a user-friendly way to access all Mail Pilot features. For programmatic access or integration with other systems, consider using the CLI interface or developing custom API integrations.