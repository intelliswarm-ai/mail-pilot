#!/usr/bin/env python3
"""
Simple startup script for Mail Pilot Interactive Web App
"""

import sys
import os

def main():
    print("🚀 Starting Mail Pilot Interactive Web App")
    print("=" * 45)
    
    # Add src directory to path (same pattern as main.py)
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    sys.path.insert(0, src_path)
    print(f"📂 Added to Python path: {src_path}")
    
    # Check credentials
    creds_path = os.path.join('..', 'credentials.json')
    if os.path.exists(creds_path):
        print("✅ Gmail credentials found - Production mode available")
    else:
        print("🎭 Demo mode - Using simulated email data")
    
    try:
        print("📦 Importing web application...")
        from src.web_app import app
        
        print("🌐 Starting Flask server...")
        print("   • URL: http://localhost:5000")
        print("   • Features: Real-time email processing")
        print("   • Press CTRL+C to stop")
        print("=" * 45)
        
        # Start the web application
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n🔧 TROUBLESHOOTING:")
        print("   1. Make sure you're in the mail-pilot directory")
        print("   2. Install missing packages: pip install flask requests")
        print("   3. Check that src/web_app.py exists")
        
    except KeyboardInterrupt:
        print("\n\n👋 Web application stopped by user")
        
    except Exception as e:
        print(f"\n❌ Startup error: {e}")

if __name__ == "__main__":
    main()