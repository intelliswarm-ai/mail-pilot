#!/usr/bin/env python3
"""
Startup script for Mail Pilot Backend API Server
Exposes mail_pilot_service progress tracking via REST API
"""

import sys
import os
import logging

def main():
    print("🚀 Starting Mail Pilot Backend API Server")
    print("=" * 50)
    
    # Add src directory to path
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    sys.path.insert(0, src_path)
    print(f"📂 Added to Python path: {src_path}")
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Check credentials
    creds_path = os.path.join('..', 'credentials.json')
    if os.path.exists(creds_path):
        print("✅ Gmail credentials found - Production mode available")
    else:
        print("🎭 Demo mode - Using simulated email data")
    
    try:
        print("📦 Importing Mail Pilot Service...")
        from src.mail_pilot_service import MailPilotService
        
        print("🔧 Initializing service...")
        print(f"📄 Using config file: ../.env")
        
        # Debug: Check if .env file exists
        env_path = '../.env'
        if os.path.exists(env_path):
            print(f"✅ Found .env file at {env_path}")
        else:
            print(f"❌ .env file not found at {env_path}")
        
        service = MailPilotService(config_file='../.env')
        
        if not service.initialize():
            print("❌ Failed to initialize Mail Pilot Service")
            print("   This is normal if Ollama is not running")
            print("   The API will still work for progress tracking")
        else:
            print("✅ Mail Pilot Service initialized successfully")
        
        print("\n🌐 Starting API server...")
        print("   • URL: http://localhost:5001")
        print("   • Endpoints:")
        print("     - GET  /api/processing-status")
        print("     - POST /api/trigger-processing") 
        print("     - POST /api/stop-processing")
        print("     - GET  /api/service-status")
        print("   • Press CTRL+C to stop")
        print("=" * 50)
        
        # Start the API server
        service.start_api_server(host='0.0.0.0', port=5001)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n🔧 TROUBLESHOOTING:")
        print("   1. Make sure you're in the mail-pilot directory")
        print("   2. Install missing packages: pip install flask flask-cors requests")
        print("   3. Check that src/mail_pilot_service.py exists")
        
    except KeyboardInterrupt:
        print("\n\n👋 Backend API server stopped by user")
        
    except Exception as e:
        print(f"\n❌ Startup error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()