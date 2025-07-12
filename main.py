#!/usr/bin/env python3

"""
Mail Pilot - AI Email Summary Service
Main entry point for the application
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.mail_pilot_service import main

if __name__ == '__main__':
    main()