# Mail Pilot Interactive Web App Setup Guide

## 🎯 WHAT'S BEEN FIXED

The web app now properly emulates the `python -m src.mail_pilot_service --menu` flow:

### ✅ **Corrected Issues:**
1. **Fixed import structure** - Now uses absolute imports instead of relative imports
2. **Fixed credentials path** - Now looks in `../credentials.json` like main.py does
3. **Proper service initialization** - Follows the same pattern as mail_pilot_service.py
4. **Real-time processing tracking** - Each email is tracked individually as it processes
5. **Proper query building** - Uses EmailMenu.calculate_date_query() like the CLI does

### ✅ **Enhanced Features:**
- **Real-time email-by-email display** - See each email as it's processed
- **Live progress tracking** - Stage indicators and individual email status
- **Processing log stream** - Terminal-style log with timestamps
- **Interactive controls** - Expand/collapse views, clear logs
- **Demo mode fallback** - Works even without credentials

---

## 🚀 HOW TO START THE INTERACTIVE WEB APP

### **Quick Start (Recommended):**
```bash
cd D:\Intelliswarm.ai\mail-pilot
python run_interactive_webapp.py
```

### **Alternative Methods:**
```bash
# Method 1: Using the enhanced startup script
python start_webapp.py

# Method 2: Direct Flask app
python -c "import sys, os; sys.path.insert(0, 'src'); from src.web_app import app; app.run(debug=True, port=5000)"

# Method 3: Module approach
python -m src.web_app
```

---

## 🎭 DEMO MODE vs PRODUCTION MODE

### **Demo Mode** (No credentials needed)
- ✅ Uses 8 realistic sample emails
- ✅ Simulates real processing delays
- ✅ All interactive features work
- ✅ Shows phishing detection
- ✅ Generates auto-replies

### **Production Mode** (With credentials)
- ✅ Connects to real Gmail account
- ✅ Processes actual unread emails
- ✅ Real categorization and analysis
- ✅ Requires `../credentials.json` and `../token.json`

---

## 🌐 INTERACTIVE FEATURES

When you click **"Start Processing"**, you'll see:

### **1. Real-Time Processing Panel**
```
🔧 Stage: Categorizing Emails          Progress: 60%
📊 Total: 8  Processed: 4  Current: 5  Remaining: 3

📧 Current Email:
Meeting request for project review
From: sarah@company.com              Status: Analyzing
```

### **2. Individual Email Tracking**
```
📧 Meeting request for project review
   From: sarah@company.com
   Status: Pending → Categorizing → Analyzed → Complete ✅
   Risk: Safe    Reply: Generated

📧 Urgent: Account verification required  
   From: suspicious@domain.tk
   Status: Analyzing → High Risk 🚨
```

### **3. Live Processing Log**
```
10:30:45 [INFO] Starting email processing pipeline
10:30:46 [INFO] Categorizing: Meeting request...
10:30:47 [WARN] ⚠️ HIGH risk email detected: Account verification...
10:30:48 [SUCCESS] Processing completed!
```

---

## 🧪 TESTING THE SETUP

### **Test Demo Services:**
```bash
python -c "
import sys, os
sys.path.insert(0, 'src')
from src.demo_services import DemoGmailClient
gmail = DemoGmailClient()
emails = gmail.get_unread_messages()
print(f'✅ Demo working: {len(emails)} emails')
"
```

### **Test Web App Processing:**
```bash
# Start the web app in one terminal
python run_interactive_webapp.py

# In another terminal, test processing
python test_webapp_processing.py
```

---

## 🔧 TROUBLESHOOTING

### **"Import Error" Issues:**
```bash
# Make sure you're in the right directory
cd D:\Intelliswarm.ai\mail-pilot

# Install Flask if missing
pip install flask

# Check Python path
python -c "import sys; print(sys.path)"
```

### **"Start Processing" Does Nothing:**
1. **Check browser console** for JavaScript errors
2. **Check server logs** in the terminal
3. **Test API directly:**
   ```bash
   curl -X POST http://localhost:5000/api/trigger-processing \
        -H "Content-Type: application/json" \
        -d '{"timeframe_hours": 24, "categorization_method": "enhanced"}'
   ```

### **"Processing Fails" Issues:**
- The web app now has proper error handling and fallbacks
- Check logs in the server terminal
- All failures should fall back to demo mode automatically

---

## 🎯 WHAT YOU'LL EXPERIENCE

1. **Start the web app** with any of the startup methods
2. **Open http://localhost:5000** in your browser
3. **Click "Start Processing"** - the interactive panel appears
4. **Watch real-time updates:**
   - Each email appears as it's processed
   - Status changes from Pending → Categorizing → Analyzed → Complete
   - Processing log streams live updates
   - Progress bars show stage completion
   - Statistics update every second

5. **See the results:**
   - Category overview with email counts
   - High priority emails highlighted
   - Security alerts for risky emails
   - Auto-reply suggestions for emails needing responses

---

## 🚀 NEXT STEPS

The web app now properly emulates the CLI flow (`python -m src.mail_pilot_service --menu`) with full interactive visualization. Try it out and you should see the real-time email-by-email processing working exactly as requested!

**The key fix:** The web app now follows the exact same initialization and processing pattern as your existing CLI tool, just with a beautiful interactive interface on top.