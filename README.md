# Mail Pilot 📧🤖

AI-powered email summary service that connects to your Gmail, analyzes unread messages using Ollama, and sends you intelligent summaries with voice narration.

## Features

- **Gmail Integration**: Securely connects to your Gmail using OAuth2
- **AI Summarization**: Uses Ollama with local LLMs to analyze and summarize emails
- **Smart NLP Clustering**: Automatically categorizes emails using machine learning algorithms
- **Intelligent Email Grouping**: Uses TF-IDF and K-means clustering to group similar emails
- **Smart Prioritization**: Categorizes emails by priority (High/Medium/Low)
- **Action Items Extraction**: Identifies tasks and follow-up items from emails
- **Voice Summaries**: Generates audio summaries using text-to-speech
- **Unlimited Email Processing**: Processes all available emails without artificial limits
- **Enhanced Content Analysis**: Analyzes up to 5000 characters per email for better accuracy
- **Interactive Menu System**: Choose timeframes and processing options interactively
- **Configurable Scheduling**: Runs every 6-24 hours automatically
- **Beautiful Email Reports**: Sends HTML and text summaries with category-specific reports
- **Privacy Focused**: All processing happens locally with open-source models

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Gmail API**:
   - Get credentials.json from Google Cloud Console
   - Place it in parent directory: `../credentials.json`
   - Run once to generate token.json automatically

3. **Install and start Ollama**:
   ```bash
   ollama pull mistral
   ollama serve
   ```

4. **Configure environment**:
   ```bash
   cp .env.example ../.env
   # Edit ../.env with your Gmail App Password and other settings
   ```

5. **Generate Gmail token** (first-time setup):
   ```bash
   # This will open a browser for Gmail authorization
   python main.py --once
   
   # Follow the browser prompts to authorize Gmail access
   # token.json will be created automatically in parent directory
   ```

6. **Run the service**:
   ```bash
   # Run once manually
   python main.py --once
   
   # Run with interactive menu (recommended for first-time users)
   python main.py --menu
   
   # Run scheduled service (every 6 hours)
   python main.py
   
   # Or use the web interface
   python web_app.py
   ```

## Example Output

The service generates comprehensive email summaries including:

- **Smart Categorization**: Automatically groups emails into categories like "Marketing", "Notifications", "Work", etc.
- **Category-Specific Reports**: Separate summaries for each email category
- **Overview**: Total emails, high priority count, action items per category
- **Individual Summaries**: AI-generated summary for each email
- **Priority Classification**: High/Medium/Low priority assignments
- **Action Items**: Extracted tasks and follow-ups
- **Response Indicators**: Emails that require your response
- **Voice Narration**: Audio file attached to summary emails
- **Interactive Timeframes**: Process emails from last 12h, 24h, 48h, or all unread

## Project Structure

```
mail-pilot/
├── src/
│   ├── gmail_client.py           # Gmail API integration with unlimited email support
│   ├── ollama_client.py          # Ollama/LLM integration
│   ├── email_processor.py        # Email analysis logic with NLP clustering
│   ├── email_categorizer.py      # Legacy categorization (fallback)
│   ├── email_nlp_categorizer.py  # Advanced NLP-based email clustering
│   ├── email_menu.py             # Interactive menu system
│   ├── email_sender.py           # SMTP email sending
│   ├── voice_generator.py        # Text-to-speech
│   ├── scheduler.py              # Scheduling system
│   ├── file_saver.py            # Enhanced file saving with category support
│   ├── config.py                # Configuration management
│   └── mail_pilot_service.py     # Main service orchestration
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies (includes ML libraries)
├── .env.example                 # Environment template
└── setup_instructions.md        # Detailed setup guide
```

## Configuration

Key environment variables in `.env`:

```env
# Gmail settings
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Ollama settings  
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Scheduling (hours)
SUMMARY_INTERVAL=6

# Voice features
VOICE_ENABLED=true
VOICE_LANGUAGE=en

# Note: This file should be placed as ../.env (parent directory)
```

## Usage

### Web Interface (Recommended)

Start the web application for an easy-to-use interface:

```bash
python web_app.py
```

Then open your browser to `http://localhost:5000` and follow the setup wizard:

1. **Connect Gmail**: One-click OAuth2 registration
2. **Configure Settings**: Web forms for all options
3. **Manual Processing**: Dashboard with real-time status

### Command Line Interface

```bash
# Run email summary once with automatic categorization
python main.py --once

# Run with interactive menu for timeframe and options selection
python main.py --menu

# Start scheduled service (runs every 6 hours by default)
python main.py

# Check service status including Ollama connection
python main.py --status

# Use custom config file
python main.py --config /path/to/.env
```

### Interactive Menu Features

When using `--menu`, you can select:

1. **Timeframe Options**:
   - Last 12 hours
   - Last 24 hours  
   - Last 48 hours
   - Last 3 days
   - Last 7 days
   - All unread emails

2. **Processing Options**:
   - Enable/disable automatic email clustering
   - Enable/disable voice summaries
   - Choose summary detail level (brief/detailed)

### NLP Clustering Features

The advanced email categorization system:

- Uses **TF-IDF vectorization** to extract email features
- Applies **K-means clustering** to group similar emails
- Automatically determines optimal number of categories (2-8)
- Generates meaningful category labels like "Marketing", "Notifications", "Work", etc.
- Creates separate reports for each category
- Supports unlimited email processing without caps

## Privacy & Security

- **Local Processing**: All AI analysis happens locally via Ollama
- **OAuth2 Authentication**: Secure Gmail access without storing passwords
- **App Passwords**: Uses Gmail app passwords, not your main account password
- **No Data Retention**: Emails are processed and not stored permanently
- **Open Source Models**: Uses transparent, auditable AI models

## Requirements

- Python 3.8+
- Ollama installed and running with a model (mistral recommended)
- Gmail account with 2FA enabled
- Gmail API credentials.json from Google Cloud Console
- Gmail App Password generated (not your regular password)
- Internet connection for Gmail API and voice generation
- **New**: scikit-learn, NLTK, and numpy for NLP clustering features
- **New**: Additional disk space for NLTK data downloads (punkt, stopwords, wordnet)

## Gmail Setup Details

### 1. Get Gmail API Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API
4. Create OAuth 2.0 Client ID credentials (Desktop Application)
5. Download as `credentials.json`
6. Place in parent directory: `../credentials.json`

### 2. Generate Gmail App Password
1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Security → 2-Step Verification → App passwords
3. Generate a new app password for "Mail"
4. Use this in your `.env` file (not your regular Gmail password)

### 3. First-Time Authorization
When you first run the service, it will:
- Open a browser window for Gmail authorization
- Ask you to sign in and grant permissions
- Automatically create `token.json` in the parent directory
- Store the authorization for future use

**File structure after setup:**
```
parent-directory/
├── credentials.json    # Gmail API credentials
├── token.json         # OAuth token (auto-generated)
├── .env               # Configuration file
└── mail-pilot/        # Project directory
    ├── .env.example   # Template for .env
    └── ...
```

## New in Latest Version

### 🚀 Major Updates:

- **NLP-Powered Email Clustering**: Replaces manual categorization with intelligent ML algorithms
- **Unlimited Email Processing**: Removed 100-email limit, now processes all available emails
- **Enhanced Content Analysis**: Increased email body analysis from 1000 to 5000 characters
- **Interactive Menu System**: Choose processing timeframes and options interactively
- **Advanced Category Reports**: Separate reports for each automatically detected category
- **Better Performance**: Optimized for large email volumes with progress tracking

### 🔬 Technical Improvements:

- TF-IDF feature extraction for email content analysis
- K-means clustering with automatic optimal cluster detection
- NLTK integration for text preprocessing and tokenization
- Smart category labeling based on email content patterns
- Pagination support for Gmail API to handle large inboxes

## Contributing

This project focuses on privacy-first email automation. Contributions welcome for:

- Additional LLM integrations
- Enhanced NLP clustering algorithms
- Better email content preprocessing
- Mobile notifications
- Multi-language support for clustering
- Custom clustering models

## License

MIT License - see LICENSE file for details.

---

**Note**: This is a defensive security tool designed to help users manage their email more effectively. All processing happens locally to protect your privacy." 
