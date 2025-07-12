import sys
from datetime import datetime, timedelta
from typing import Tuple

class EmailMenu:
    def __init__(self):
        self.timeframe_options = {
            '1': {'hours': 12, 'label': '12 hours'},
            '2': {'hours': 24, 'label': '24 hours'},
            '3': {'hours': 48, 'label': '48 hours'},
            '4': {'hours': 72, 'label': '3 days'},
            '5': {'hours': 168, 'label': '7 days'},
            '6': {'hours': 0, 'label': 'All unread emails'}
        }
    
    def show_timeframe_menu(self) -> int:
        """Show timeframe selection menu and return selected hours (0 = all unread)"""
        print("\n" + "="*60)
        print("📧 MAIL PILOT - EMAIL TIMEFRAME SELECTION")
        print("="*60)
        print("\nSelect the timeframe for email processing:")
        print()
        
        for key, option in self.timeframe_options.items():
            if option['hours'] == 0:
                print(f"  {key}. {option['label']} (default unread behavior)")
            else:
                print(f"  {key}. Last {option['label']}")
        
        print("\n  q. Quit")
        print("-" * 40)
        
        while True:
            choice = input("Enter your choice (1-6 or q): ").strip().lower()
            
            if choice == 'q':
                print("👋 Goodbye!")
                sys.exit(0)
            
            if choice in self.timeframe_options:
                selected = self.timeframe_options[choice]
                print(f"\n✅ Selected: {selected['label']}")
                return selected['hours']
            
            print("❌ Invalid choice. Please enter 1-6 or q.")
    
    def show_processing_options(self) -> dict:
        """Show email processing options menu"""
        print("\n" + "="*60)
        print("🔧 EMAIL PROCESSING OPTIONS")
        print("="*60)
        print("\nSelect processing preferences:")
        print()
        
        # Email categorization
        print("📂 Email Categorization:")
        print("  1. Process all emails together")
        print("  2. Use intelligent NLP clustering (recommended)")
        print("      • TF-IDF vectorization + adaptive clustering")
        print("      • Creates categories like Professional, GitHub, Shopping, etc.")
        print("      • Fast and efficient processing")
        print("  3. Use hybrid categorization (best of both worlds)")
        print("      • Fast clustering with Enhanced NLP")
        print("      • Intelligent category naming with LLM")
        print("      • Optimal balance of speed and accuracy")
        print()
        
        categorize = self._get_choice("Select categorization method (1-3): ", ['1', '2', '3'])
        categorize_emails = categorize in ['2', '3']
        categorization_method = 'enhanced' if categorize == '2' else ('llm' if categorize == '3' else 'none')
        
        if categorize_emails:
            if categorization_method == 'llm':
                print("\n✅ Hybrid categorization enabled")
                print("   📊 Fast clustering using Enhanced NLP algorithms")
                print("   🧠 Intelligent category naming using Ollama LLM") 
                print("   🚀 Optimal combination of speed and accuracy")
            else:
                print("\n✅ NLP-based email clustering enabled") 
                print("   🤖 Emails will be automatically grouped using machine learning")
                print("   📊 Separate reports will be generated for each detected category")
                print("   🏷️  Categories are determined by email content similarity")
        else:
            print("\n✅ Processing all emails together (no clustering)")
        
        # Voice generation
        print("\n🎵 Voice Summary:")
        print("  1. Enable voice summaries")
        print("  2. Disable voice summaries")
        print()
        
        voice = self._get_choice("Generate voice summaries? (1-2): ", ['1', '2'])
        voice_enabled = voice == '1'
        
        # Summary detail level
        print("\n📝 Summary Detail Level:")
        print("  1. Brief summaries (faster)")
        print("  2. Detailed summaries (slower)")
        print()
        
        detail = self._get_choice("Summary detail level? (1-2): ", ['1', '2'])
        detailed_summaries = detail == '2'
        
        options = {
            'categorize_emails': categorize_emails,
            'categorization_method': categorization_method,
            'voice_enabled': voice_enabled,
            'detailed_summaries': detailed_summaries
        }
        
        print("\n" + "="*60)
        print("📋 PROCESSING CONFIGURATION SUMMARY")
        print("="*60)
        if categorize_emails:
            if categorization_method == 'llm':
                print("📂 Email Clustering: Hybrid (Enhanced NLP + LLM)")
                print("🚀 AI Features: Fast clustering + intelligent naming")
            else:
                print("📂 Email Clustering: NLP-based (ML)")
                print("🤖 ML Features: TF-IDF vectorization + adaptive clustering")
        else:
            print("📂 Email Clustering: Disabled (all together)")
        
        print(f"🎵 Voice Summaries: {'Enabled' if voice_enabled else 'Disabled'}")
        print(f"📝 Detail Level: {'Detailed' if detailed_summaries else 'Brief'}")
        print("="*60)
        
        input("\nPress Enter to start processing...")
        return options
    
    def _get_choice(self, prompt: str, valid_choices: list) -> str:
        """Get a valid choice from user"""
        while True:
            choice = input(prompt).strip()
            if choice in valid_choices:
                return choice
            print(f"❌ Invalid choice. Please enter one of: {', '.join(valid_choices)}")
    
    def calculate_date_query(self, hours: int) -> str:
        """Calculate Gmail search query for timeframe"""
        if hours == 0:
            return "is:unread"
        
        # Calculate the date for the timeframe
        cutoff_date = datetime.now() - timedelta(hours=hours)
        date_str = cutoff_date.strftime("%Y/%m/%d")
        
        return f"after:{date_str}"
    
    def get_timeframe_description(self, hours: int) -> str:
        """Get human-readable description of timeframe"""
        if hours == 0:
            return "all unread emails"
        elif hours == 12:
            return "emails from last 12 hours"
        elif hours == 24:
            return "emails from last 24 hours"
        elif hours == 48:
            return "emails from last 48 hours"
        elif hours == 72:
            return "emails from last 3 days"
        elif hours == 168:
            return "emails from last 7 days"
        else:
            days = hours // 24
            if days > 0:
                return f"emails from last {days} days"
            else:
                return f"emails from last {hours} hours"