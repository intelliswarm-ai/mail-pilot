#!/usr/bin/env python3
"""
Mail Pilot Web Application Startup Script
Provides an easy way to start the web application with proper initialization
"""

import os
import sys
import logging
from datetime import datetime

def setup_logging():
    """Setup logging for the web application"""
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/webapp.log'),
            logging.StreamHandler()
        ]
    )

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    required_packages = ['flask', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package}")
    
    if missing_packages:
        print(f"\n❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_configuration():
    """Check configuration and determine mode"""
    print("\n🔧 Checking configuration...")
    
    # Check for credentials (look in parent directory like main.py does)
    has_credentials = os.path.exists('../credentials.json')
    has_token = os.path.exists('../token.json')
    
    if has_credentials and has_token:
        print("  ✅ Gmail credentials found - Production mode available")
        mode = "production"
    elif has_credentials:
        print("  ⚠️  Gmail credentials found but token missing - First-time setup needed")
        mode = "setup"
    else:
        print("  ℹ️  No Gmail credentials found - Demo mode will be used")
        mode = "demo"
    
    # Check Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("  ✅ Ollama service detected")
            ollama_available = True
        else:
            print("  ⚠️  Ollama service not responding")
            ollama_available = False
    except:
        print("  ⚠️  Ollama service not available - Demo LLM will be used")
        ollama_available = False
    
    return mode, ollama_available

def print_banner():
    """Print startup banner"""
    print("=" * 60)
    print("🚀 Mail Pilot - Interactive Email Processing Web App")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def print_startup_info(mode, ollama_available):
    """Print startup information"""
    print("\n📋 STARTUP INFORMATION:")
    print("-" * 30)
    
    if mode == "demo":
        print("🎭 Mode: DEMO")
        print("   • Using simulated email data")
        print("   • 8 sample emails with realistic content")
        print("   • All features available for testing")
        print("   • No real Gmail connection required")
    elif mode == "setup":
        print("🔧 Mode: SETUP REQUIRED")
        print("   • Gmail credentials found")
        print("   • Run initial OAuth flow needed")
        print("   • Demo mode available as fallback")
    else:
        print("🏭 Mode: PRODUCTION")
        print("   • Real Gmail connection available")
        print("   • Live email processing enabled")
    
    if ollama_available:
        print("🤖 LLM: Ollama (localhost:11434)")
    else:
        print("🤖 LLM: Demo simulation")
    
    print()

def print_features():
    """Print available features"""
    print("✨ INTERACTIVE FEATURES:")
    print("-" * 25)
    print("  📧 Real-time email-by-email processing display")
    print("  📊 Live progress tracking with stage indicators")
    print("  🎯 Individual email status updates")
    print("  📝 Processing log with timestamped events")
    print("  🔍 Current email being processed highlighting")
    print("  📈 Email statistics (total/processed/current/remaining)")
    print("  📋 Expandable email progress list")
    print("  🎨 Color-coded status badges")
    print("  🛡️  Real-time phishing risk detection")
    print("  💬 Auto-reply generation progress tracking")
    print()

def print_urls():
    """Print access URLs"""
    print("🌐 ACCESS URLS:")
    print("-" * 15)
    print("  🏠 Main Dashboard:  http://localhost:5000")
    print("  📊 Status Page:     http://localhost:5000/status")
    print("  🏷️  Categories:      http://localhost:5000/categories")
    print("  🔗 API Status:      http://localhost:5000/api/processing-status")
    print()

def start_webapp():
    """Start the web application"""
    print("🚀 Starting Mail Pilot Web Application...")
    print("   • Flask server starting on port 5000")
    print("   • Debug mode enabled")
    print("   • Real-time processing interface active")
    print()
    print("⏹️  Press CTRL+C to stop the server")
    print("=" * 60)
    print()
    
    # Set up paths like main.py does
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    # Import and start the enhanced web app
    try:
        from src.web_app import app
        
        # Start the Flask app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Trying alternative import method...")
        
        # Fallback: try importing from current directory
        try:
            from web_app import app
            app.run(debug=True, host='0.0.0.0', port=5000)
        except ImportError as fallback_error:
            print(f"❌ Fallback import failed: {fallback_error}")
            print("\n🔧 TROUBLESHOOTING:")
            print("   1. Make sure you're in the mail-pilot directory")
            print("   2. Check that src/web_app.py exists")
            print("   3. Try: python -m src.web_app")
            sys.exit(1)

if __name__ == "__main__":
    print_banner()
    
    # Setup logging
    setup_logging()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check configuration
    mode, ollama_available = check_configuration()
    
    # Print information
    print_startup_info(mode, ollama_available)
    print_features()
    print_urls()
    
    # Start the application
    try:
        start_webapp()
    except KeyboardInterrupt:
        print("\n\n👋 Mail Pilot web application stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start web application: {e}")
        sys.exit(1)