import logging
import json
from typing import Dict, List, Tuple, Optional
from collections import Counter, defaultdict
import re

class EmailLLMCategorizer:
    """
    LLM-powered email categorizer using Ollama for intelligent semantic categorization.
    Provides the most accurate and context-aware email grouping.
    """
    
    def __init__(self, ollama_client, batch_size: int = 5):
        """
        Initialize the LLM email categorizer
        
        Args:
            ollama_client: Instance of OllamaClient for LLM interactions
            batch_size: Number of emails to process in each LLM call for efficiency
        """
        self.ollama_client = ollama_client
        self.batch_size = batch_size
        self.predefined_categories = {
            'Professional Development': 'Job applications, career opportunities, recruitment, interviews, LinkedIn',
            'Work & Business': 'Work-related communications, meetings, business correspondence, project updates',
            'Development & Technology': 'GitHub notifications, code repositories, CI/CD, technical updates, programming',
            'Shopping & E-commerce': 'Online purchases, orders, delivery notifications, shopping recommendations',
            'Entertainment & Media': 'Streaming services, movies, music, gaming, social media notifications',
            'Financial Services': 'Banking, payments, invoices, transactions, financial statements',
            'Security & Authentication': 'Login notifications, security alerts, password resets, verification codes',
            'Travel & Booking': 'Hotel reservations, flight bookings, travel confirmations, itineraries',
            'Health & Wellness': 'Medical appointments, health reminders, fitness tracking, wellness content',
            'Education & Learning': 'Courses, educational content, training materials, academic communications',
            'News & Information': 'Newsletters, news updates, blogs, informational content',
            'Social & Communication': 'Social media, messaging apps, community updates, personal communications',
            'Marketing & Promotions': 'Promotional emails, advertisements, marketing campaigns, offers',
            'Support & Service': 'Customer support, help desk, service notifications, technical assistance'
        }
    
    def categorize_emails(self, emails: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categorize emails using LLM analysis for maximum accuracy
        
        Returns: Dictionary with category names as keys and email lists as values
        """
        import time
        
        if not emails:
            return {"General": []}
        
        start_time = time.time()
        print(f"\n🤖 Starting LLM-powered email categorization for {len(emails)} emails...")
        print(f"   🧠 Using {self.ollama_client.model} for intelligent analysis")
        print(f"   ⏱️  Estimated time: {len(emails) // self.batch_size * 35:.0f} seconds")
        
        # Step 1: Analyze emails in batches for efficiency with progress saving
        email_analyses = self._analyze_emails_in_batches(emails)
        
        # Step 2: Group emails by LLM-suggested categories
        categorized_emails = self._group_by_llm_categories(emails, email_analyses)
        
        # Step 3: Refine and merge similar categories
        categorized_emails = self._refine_categories(categorized_emails)
        
        # Step 4: Add uncategorized for unclear emails
        categorized_emails = self._handle_uncategorized(categorized_emails, emails)
        
        # Step 5: Print results with insights
        elapsed_time = time.time() - start_time
        print(f"\n⏱️  Total processing time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        
        self._print_llm_categorization_summary(categorized_emails)
        self._print_llm_insights(categorized_emails, emails)
        
        return categorized_emails
    
    def _analyze_emails_in_batches(self, emails: List[Dict]) -> List[Dict]:
        """Analyze emails in batches using LLM for efficiency with progress saving"""
        import time
        
        print(f"📊 Analyzing emails in batches of {self.batch_size}...")
        
        all_analyses = []
        failed_batches = []
        
        # Process emails in batches
        for i in range(0, len(emails), self.batch_size):
            batch = emails[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(emails) + self.batch_size - 1) // self.batch_size
            
            print(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} emails)...")
            
            # Try up to 2 times for each batch with escalating timeouts
            success = False
            timeout_multiplier = 1
            
            for attempt in range(2):
                try:
                    if attempt > 0:
                        print(f"   🔄 Retry attempt {attempt + 1}/2 with {timeout_multiplier}x timeout...")
                    
                    batch_analysis = self._analyze_email_batch(batch, timeout_multiplier)
                    all_analyses.extend(batch_analysis)
                    success = True
                    break
                    
                except TimeoutError as e:
                    print(f"   ⏰ Timeout on attempt {attempt + 1}: {str(e)[:100]}...")
                    timeout_multiplier = 5  # 5x timeout for next attempt
                    if attempt == 0:
                        time.sleep(3)  # Brief pause before retry
                except Exception as e:
                    print(f"   ❌ Attempt {attempt + 1} failed: {str(e)[:100]}...")
                    if attempt == 0:
                        time.sleep(2)  # Brief pause before retry
            
            if not success:
                print(f"   ⚠️  Batch {batch_num} failed after retries, using fallback")
                failed_batches.append(batch_num)
                # Fallback: assign to general category
                for email in batch:
                    all_analyses.append({
                        'category': 'General',
                        'confidence': 0.3,
                        'reasoning': 'LLM analysis failed after retries'
                    })
        
        if failed_batches:
            print(f"⚠️  Failed batches: {failed_batches} (used fallback categorization)")
            print(f"📊 Success rate: {((total_batches - len(failed_batches)) / total_batches * 100):.1f}%")
        else:
            print(f"✅ All batches processed successfully!")
        
        return all_analyses
    
    def _analyze_email_batch(self, emails: List[Dict], timeout_multiplier: int = 1) -> List[Dict]:
        """Analyze a batch of emails using LLM"""
        
        # Prepare email summaries for LLM analysis (shorter format)
        email_summaries = []
        for i, email in enumerate(emails):
            sender = email.get('sender', 'Unknown')
            subject = email.get('subject', 'No Subject')
            body_preview = email.get('body', '')[:100] + "..." if len(email.get('body', '')) > 100 else email.get('body', '')
            
            email_summaries.append(f"{i+1}. From: {sender[:30]} Subject: {subject} Content: {body_preview}")
        
        # Create simplified LLM prompt for batch categorization
        categories_list = ", ".join(self.predefined_categories.keys())
        
        prompt = f"""Categorize these {len(emails)} emails. Choose the best category for each email.

Categories: {categories_list}

Emails:
{chr(10).join(email_summaries)}

Return valid JSON array with email_index, category, and confidence:
[
  {{"email_index": 1, "category": "Professional Development", "confidence": 0.9}},
  {{"email_index": 2, "category": "Shopping & E-commerce", "confidence": 0.8}}
]

Important: Use email_index (not email\\_index), valid JSON format, no trailing commas."""
        
        try:
            # Get LLM response with dynamic timeout
            response = self._call_llm(prompt, timeout_multiplier)
            
            print(f"   📝 LLM response preview: {response[:100]}...")
            
            # Parse JSON response
            analyses = self._parse_llm_response(response, len(emails))
            
            print(f"   ✅ Successfully parsed {len(analyses)} email analyses")
            return analyses
            
        except Exception as e:
            print(f"   ❌ LLM analysis failed: {e}")
            logging.error(f"LLM analysis failed: {e}")
            # Fallback analysis
            print(f"   🔄 Using fallback keyword analysis for {len(emails)} emails")
            return self._fallback_analysis(emails)
    
    def _format_categories_for_prompt(self) -> str:
        """Format categories with descriptions for LLM prompt"""
        formatted = []
        for category, description in self.predefined_categories.items():
            formatted.append(f"- {category}: {description}")
        return "\n".join(formatted)
    
    def _call_llm(self, prompt: str, timeout_multiplier: int = 1) -> str:
        """Call the LLM with error handling and dynamic timeout"""
        import time
        import requests
        
        try:
            print(f"   ⏳ Sending request to LLM (timeout: {120 * timeout_multiplier}s)...")
            start_time = time.time()
            
            # Use custom timeout instead of the hardcoded one
            payload = {
                "model": self.ollama_client.model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(
                self.ollama_client.api_url,
                json=payload,
                timeout=120 * timeout_multiplier  # Dynamic timeout scaling
            )
            
            if response.status_code == 200:
                result = response.json().get('response', '')
                elapsed_time = time.time() - start_time
                print(f"   ✅ LLM response received ({elapsed_time:.1f}s)")
                return result
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
            
        except requests.exceptions.Timeout as e:
            elapsed_time = time.time() - start_time
            print(f"   ⏰ Timeout after {elapsed_time:.1f}s (will retry with {timeout_multiplier * 5}x timeout)")
            raise TimeoutError(f"LLM request timed out after {elapsed_time:.1f}s")
        except Exception as e:
            logging.error(f"LLM call failed: {e}")
            raise
    
    def _parse_llm_response(self, response: str, expected_count: int) -> List[Dict]:
        """Parse LLM JSON response with error handling"""
        try:
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response.strip()
            
            # Fix common LLM JSON issues
            json_str = json_str.replace('email\\_index', 'email_index')  # Fix escaped underscores
            json_str = json_str.replace('\\_', '_')  # Fix any other escaped underscores
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
            json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
            
            # Parse JSON
            analyses = json.loads(json_str)
            
            # Validate and normalize
            validated_analyses = []
            for analysis in analyses:
                if isinstance(analysis, dict) and 'category' in analysis:
                    # Ensure category is valid
                    category = analysis.get('category', 'General')
                    if category not in self.predefined_categories:
                        category = 'General'
                    
                    validated_analyses.append({
                        'category': category,
                        'confidence': float(analysis.get('confidence', 0.5)),
                        'reasoning': analysis.get('reasoning', 'LLM categorization')
                    })
            
            # Ensure we have the right number of analyses
            while len(validated_analyses) < expected_count:
                validated_analyses.append({
                    'category': 'General',
                    'confidence': 0.3,
                    'reasoning': 'Incomplete LLM response'
                })
            
            return validated_analyses[:expected_count]
            
        except Exception as e:
            logging.error(f"Failed to parse LLM response: {e}")
            return self._fallback_analysis_count(expected_count)
    
    def _fallback_analysis(self, emails: List[Dict]) -> List[Dict]:
        """Fallback analysis when LLM fails"""
        analyses = []
        for email in emails:
            # Simple keyword-based fallback
            subject = email.get('subject', '').lower()
            sender = email.get('sender', '').lower()
            
            category = 'General'
            confidence = 0.4
            reasoning = 'Fallback keyword analysis'
            
            # Simple keyword matching
            if any(word in subject for word in ['job', 'application', 'career', 'hiring']):
                category = 'Professional Development'
                confidence = 0.6
            elif any(word in subject for word in ['github', 'build', 'failed', 'commit']):
                category = 'Development & Technology'
                confidence = 0.6
            elif any(word in subject for word in ['order', 'delivery', 'cart', 'purchase']):
                category = 'Shopping & E-commerce'
                confidence = 0.6
            elif any(word in subject for word in ['login', 'security', 'verify', 'password']):
                category = 'Security & Authentication'
                confidence = 0.6
            elif any(word in sender for word in ['netflix', 'amazon', 'spotify', 'youtube']):
                category = 'Entertainment & Media'
                confidence = 0.6
            
            analyses.append({
                'category': category,
                'confidence': confidence,
                'reasoning': reasoning
            })
        
        return analyses
    
    def _fallback_analysis_count(self, count: int) -> List[Dict]:
        """Create fallback analyses for a specific count"""
        return [{
            'category': 'General',
            'confidence': 0.3,
            'reasoning': 'LLM parsing failed'
        } for _ in range(count)]
    
    def _group_by_llm_categories(self, emails: List[Dict], analyses: List[Dict]) -> Dict[str, List[Dict]]:
        """Group emails by LLM-suggested categories"""
        categorized_emails = defaultdict(list)
        
        for email, analysis in zip(emails, analyses):
            category = analysis['category']
            
            # Add analysis metadata to email (ensure JSON serializable)
            email_with_metadata = email.copy()
            email_with_metadata['llm_category'] = str(category)
            email_with_metadata['llm_confidence'] = float(analysis['confidence'])
            email_with_metadata['llm_reasoning'] = str(analysis.get('reasoning', 'LLM categorization'))
            email_with_metadata['category'] = str(category)
            
            categorized_emails[category].append(email_with_metadata)
        
        return dict(categorized_emails)
    
    def _refine_categories(self, categorized_emails: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Refine categories by merging similar ones and improving names"""
        refined_categories = {}
        
        for category, emails in categorized_emails.items():
            # Add email count to category name
            refined_name = f"{category} ({len(emails)} emails)"
            refined_categories[refined_name] = emails
        
        return refined_categories
    
    def _handle_uncategorized(self, categorized_emails: Dict[str, List[Dict]], all_emails: List[Dict]) -> Dict[str, List[Dict]]:
        """Handle emails with low confidence as uncategorized"""
        # Find low-confidence emails
        low_confidence_emails = []
        high_confidence_categories = {}
        
        for category, emails in categorized_emails.items():
            high_confidence_emails = []
            
            for email in emails:
                confidence = email.get('llm_confidence', 0.5)
                if confidence < 0.4:  # Low confidence threshold
                    email_copy = email.copy()
                    email_copy['category'] = 'Uncategorized'
                    email_copy['is_outlier'] = True
                    low_confidence_emails.append(email_copy)
                else:
                    high_confidence_emails.append(email)
            
            if high_confidence_emails:
                # Update category name with new count
                original_name = category.split(' (')[0]
                new_name = f"{original_name} ({len(high_confidence_emails)} emails)"
                high_confidence_categories[new_name] = high_confidence_emails
        
        # Add uncategorized category if needed
        if low_confidence_emails:
            high_confidence_categories[f"Uncategorized ({len(low_confidence_emails)} emails)"] = low_confidence_emails
        
        return high_confidence_categories
    
    def _print_llm_categorization_summary(self, categorized_emails: Dict[str, List[Dict]]):
        """Print summary of LLM categorization results"""
        print(f"\n🤖 LLM Email Categorization Results:")
        print(f"   🎯 Total Categories: {len(categorized_emails)}")
        
        # Sort categories by size (largest first)
        sorted_categories = sorted(categorized_emails.items(), 
                                 key=lambda x: len(x[1]), reverse=True)
        
        for category, emails in sorted_categories:
            print(f"   📂 {category}: {len(emails)} emails")
            
            # Show sample subjects with confidence scores
            for email in emails[:2]:
                subject = email.get('subject', 'No Subject')
                if len(subject) > 60:
                    subject = subject[:57] + "..."
                confidence = email.get('llm_confidence', 0.0)
                print(f"      - {subject} (confidence: {confidence:.2f})")
            
            if len(emails) > 2:
                print(f"      ... and {len(emails) - 2} more")
    
    def _print_llm_insights(self, categorized_emails: Dict[str, List[Dict]], all_emails: List[Dict]):
        """Print detailed insights about LLM categorization"""
        print(f"\n🧠 LLM Categorization Insights:")
        
        # Calculate metrics
        total_emails = len(all_emails)
        total_categorized = sum(len(emails) for emails in categorized_emails.values())
        
        print(f"   📊 Coverage: {total_categorized}/{total_emails} emails (100.0%)")
        
        # Confidence analysis
        all_confidences = []
        for emails in categorized_emails.values():
            for email in emails:
                all_confidences.append(email.get('llm_confidence', 0.0))
        
        if all_confidences:
            avg_confidence = sum(all_confidences) / len(all_confidences)
            high_conf_count = sum(1 for c in all_confidences if c >= 0.7)
            print(f"   🎯 Average Confidence: {avg_confidence:.2f}")
            print(f"   ✅ High Confidence (≥0.7): {high_conf_count}/{len(all_confidences)} emails ({high_conf_count/len(all_confidences)*100:.1f}%)")
        
        # Category insights
        professional_emails = 0
        important_categories = ['Professional Development', 'Work & Business', 'Development & Technology', 'Security & Authentication']
        
        for category, emails in categorized_emails.items():
            if any(important in category for important in important_categories):
                professional_emails += len(emails)
                print(f"   🎯 Important: {category}")
        
        print(f"   ⚡ Total Important Emails: {professional_emails}")
        
        # Quality check
        largest_category = max(categorized_emails.items(), key=lambda x: len(x[1]), default=("None", []))
        if largest_category[1]:
            largest_size = len(largest_category[1])
            largest_percentage = (largest_size / total_emails) * 100
            
            if largest_percentage > 50:
                print(f"   ⚠️  Note: Largest category '{largest_category[0]}' contains {largest_percentage:.1f}% of emails")
            else:
                print(f"   ✅ Well-balanced categorization (largest: {largest_percentage:.1f}%)")
    
    def get_category_insights(self, categorized_emails: Dict[str, List[Dict]]) -> Dict:
        """Get detailed insights about LLM categorization for analysis"""
        insights = {
            'total_categories': len(categorized_emails),
            'total_emails': sum(len(emails) for emails in categorized_emails.values()),
            'category_distribution': {},
            'confidence_stats': {},
            'llm_reasoning_samples': {}
        }
        
        # Category distribution
        for category, emails in categorized_emails.items():
            insights['category_distribution'][category] = len(emails)
        
        # Confidence statistics
        all_confidences = []
        for emails in categorized_emails.values():
            for email in emails:
                all_confidences.append(email.get('llm_confidence', 0.0))
        
        if all_confidences:
            insights['confidence_stats'] = {
                'average': sum(all_confidences) / len(all_confidences),
                'high_confidence_count': sum(1 for c in all_confidences if c >= 0.7),
                'low_confidence_count': sum(1 for c in all_confidences if c < 0.4),
                'total_analyzed': len(all_confidences)
            }
        
        # Sample reasoning from each category
        for category, emails in categorized_emails.items():
            if emails:
                sample_reasoning = emails[0].get('llm_reasoning', 'No reasoning provided')
                insights['llm_reasoning_samples'][category] = sample_reasoning
        
        return insights