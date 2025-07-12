import logging
import json
from typing import Dict, List, Tuple, Optional
from collections import Counter, defaultdict
import re
import time

class EmailHybridCategorizer:
    """
    Hybrid email categorizer: Uses Enhanced NLP clustering + LLM naming
    - Fast clustering with Enhanced Categorizer (method 2)
    - Intelligent category naming with LLM (method 3)
    - Best of both worlds: speed + accuracy
    """
    
    def __init__(self, enhanced_categorizer, ollama_client):
        """
        Initialize the hybrid email categorizer
        
        Args:
            enhanced_categorizer: Instance of EmailEnhancedCategorizer for clustering
            ollama_client: Instance of OllamaClient for intelligent naming
        """
        self.enhanced_categorizer = enhanced_categorizer
        self.ollama_client = ollama_client
        
    def categorize_emails(self, emails: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categorize emails using hybrid approach: fast clustering + LLM naming
        
        Returns: Dictionary with LLM-generated category names as keys and email lists as values
        """
        if not emails:
            return {"General": []}
        
        start_time = time.time()
        print(f"\n🚀 Starting hybrid email categorization for {len(emails)} emails...")
        print(f"   📊 Phase 1: Fast clustering with Enhanced NLP")
        print(f"   🧠 Phase 2: Intelligent naming with LLM")
        
        # Phase 1: Use Enhanced Categorizer for fast, accurate clustering
        print(f"\n📊 Phase 1: Clustering emails...")
        clustered_emails = self.enhanced_categorizer.categorize_emails(emails)
        
        clustering_time = time.time() - start_time
        print(f"✅ Clustering completed in {clustering_time:.1f} seconds")
        
        # Phase 2: Use LLM to generate intelligent category names
        print(f"\n🧠 Phase 2: Generating intelligent category names...")
        llm_named_categories = self._generate_llm_category_names(clustered_emails)
        
        total_time = time.time() - start_time
        print(f"\n⏱️  Total processing time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"   📊 Clustering: {clustering_time:.1f}s | 🧠 LLM Naming: {total_time - clustering_time:.1f}s")
        
        # Print results
        self._print_hybrid_categorization_summary(llm_named_categories)
        
        return llm_named_categories
    
    def _generate_llm_category_names(self, clustered_emails: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Generate intelligent category names using LLM for each cluster"""
        llm_named_categories = {}
        total_clusters = len(clustered_emails)
        
        print(f"🏷️  Generating names for {total_clusters} clusters...")
        
        for i, (original_category, emails) in enumerate(clustered_emails.items(), 1):
            cluster_size = len(emails)
            print(f"\n🔄 Processing cluster {i}/{total_clusters}: {original_category} ({cluster_size} emails)")
            
            try:
                # Generate intelligent name for this cluster
                intelligent_name = self._get_llm_category_name(emails, original_category, cluster_size)
                llm_named_categories[intelligent_name] = emails
                
                print(f"   ✅ Generated name: '{intelligent_name}'")
                
            except Exception as e:
                print(f"   ⚠️  LLM naming failed for cluster {i}: {str(e)[:100]}...")
                print(f"   🔄 Using original name: '{original_category}'")
                llm_named_categories[original_category] = emails
        
        return llm_named_categories
    
    def _get_llm_category_name(self, emails: List[Dict], original_category: str, cluster_size: int) -> str:
        """Get intelligent category name from LLM with timeout handling"""
        
        # Prepare cluster analysis for LLM
        sample_emails = emails[:5]  # Use first 5 emails as representatives
        cluster_summary = self._create_cluster_summary(sample_emails, cluster_size)
        
        # Create LLM prompt for naming
        prompt = f"""Analyze this email cluster and suggest a clear, descriptive category name.

Cluster Info:
- Size: {cluster_size} emails
- Current name: {original_category}

Sample emails from cluster:
{cluster_summary}

Rules:
1. Create a clear, professional category name (2-4 words)
2. Focus on the main theme/purpose of these emails
3. Use categories like: Professional Development, Work Communications, Shopping & E-commerce, 
   Entertainment & Media, Financial Services, Security & Authentication, Travel & Booking,
   News & Updates, Social & Networking, Support & Service, Development & Technology
4. If emails don't fit standard categories, create a descriptive custom name

Return ONLY the category name, nothing else.
Example: "Professional Development" or "GitHub Notifications" or "Travel Bookings"
"""
        
        # Call LLM with progressive timeout handling
        return self._call_llm_with_timeout_retry(prompt, original_category, cluster_size)
    
    def _create_cluster_summary(self, sample_emails: List[Dict], total_size: int) -> str:
        """Create a concise summary of the cluster for LLM analysis"""
        summaries = []
        
        for i, email in enumerate(sample_emails, 1):
            sender = email.get('sender', 'Unknown')[:50]
            subject = email.get('subject', 'No Subject')[:80]
            body_preview = email.get('body', '')[:100]
            
            summaries.append(f"{i}. From: {sender}\n   Subject: {subject}\n   Preview: {body_preview}...")
        
        if total_size > len(sample_emails):
            summaries.append(f"... and {total_size - len(sample_emails)} more similar emails")
        
        return "\n\n".join(summaries)
    
    def _call_llm_with_timeout_retry(self, prompt: str, fallback_name: str, cluster_size: int) -> str:
        """Call LLM with progressive timeout increases until success"""
        import requests
        
        timeout_multiplier = 1
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                current_timeout = 60 * timeout_multiplier  # Start with 60s, then 300s, then 1500s
                
                if attempt > 0:
                    print(f"   🔄 Retry attempt {attempt + 1}/{max_attempts} (timeout: {current_timeout}s)...")
                else:
                    print(f"   ⏳ Requesting category name (timeout: {current_timeout}s)...")
                
                start_time = time.time()
                
                # Direct API call with custom timeout
                payload = {
                    "model": self.ollama_client.model,
                    "prompt": prompt,
                    "stream": False
                }
                
                response = requests.post(
                    self.ollama_client.api_url,
                    json=payload,
                    timeout=current_timeout
                )
                
                if response.status_code == 200:
                    result = response.json().get('response', '').strip()
                    elapsed_time = time.time() - start_time
                    print(f"   ✅ Response received ({elapsed_time:.1f}s)")
                    
                    # Clean and validate the response
                    clean_name = self._clean_category_name(result, fallback_name, cluster_size)
                    return clean_name
                else:
                    raise Exception(f"Ollama API error: {response.status_code}")
            
            except requests.exceptions.Timeout:
                elapsed_time = time.time() - start_time
                print(f"   ⏰ Timeout after {elapsed_time:.1f}s")
                timeout_multiplier *= 5  # 5x increase: 60s -> 300s -> 1500s
                
                if attempt == max_attempts - 1:
                    print(f"   ⚠️  All timeout attempts failed, using fallback name")
                    break
                else:
                    time.sleep(2)  # Brief pause before retry
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}...")
                if attempt == max_attempts - 1:
                    break
                time.sleep(1)
        
        # Fallback: use enhanced original name
        return self._enhance_fallback_name(fallback_name, cluster_size)
    
    def _clean_category_name(self, llm_response: str, fallback_name: str, cluster_size: int) -> str:
        """Clean and validate LLM-generated category name"""
        if not llm_response:
            return self._enhance_fallback_name(fallback_name, cluster_size)
        
        # Remove quotes and extra text
        clean_name = llm_response.strip().strip('"\'')
        
        # Remove any explanatory text (keep only the category name)
        lines = clean_name.split('\n')
        clean_name = lines[0].strip()
        
        # Remove common prefixes
        prefixes_to_remove = ['Category: ', 'Name: ', 'Suggestion: ', 'Category Name: ']
        for prefix in prefixes_to_remove:
            if clean_name.startswith(prefix):
                clean_name = clean_name[len(prefix):].strip()
        
        # Validate length and content
        if len(clean_name) < 3 or len(clean_name) > 50:
            return self._enhance_fallback_name(fallback_name, cluster_size)
        
        # Check if it looks like a reasonable category name
        if not re.match(r'^[A-Za-z0-9\s&\-\/\(\)]+$', clean_name):
            return self._enhance_fallback_name(fallback_name, cluster_size)
        
        # Add email count to the name
        return f"{clean_name} ({cluster_size} emails)"
    
    def _enhance_fallback_name(self, original_name: str, cluster_size: int) -> str:
        """Enhance the fallback name when LLM fails"""
        # Remove existing email count if present
        base_name = re.sub(r'\s*\(\d+\s*emails?\)', '', original_name)
        
        # Improve common generic names
        improvements = {
            'General': 'Mixed Communications',
            'Miscellaneous': 'Various Topics',
            'Uncategorized': 'Unclassified Emails',
            'Email Group': 'Email Cluster',
            'Cluster': 'Email Group'
        }
        
        for old, new in improvements.items():
            if old in base_name:
                base_name = base_name.replace(old, new)
        
        return f"{base_name} ({cluster_size} emails)"
    
    def _print_hybrid_categorization_summary(self, categorized_emails: Dict[str, List[Dict]]):
        """Print summary of hybrid categorization results"""
        print(f"\n🚀 Hybrid Email Categorization Results:")
        print(f"   🎯 Total Categories: {len(categorized_emails)}")
        print(f"   📊 Clustering Method: Enhanced NLP (TF-IDF + Adaptive)")
        print(f"   🧠 Naming Method: LLM-powered (Ollama)")
        
        # Sort categories by size (largest first)
        sorted_categories = sorted(categorized_emails.items(), 
                                 key=lambda x: len(x[1]), reverse=True)
        
        for category, emails in sorted_categories:
            print(f"   📂 {category}")
            
            # Show sample subjects
            for email in emails[:2]:
                subject = email.get('subject', 'No Subject')
                if len(subject) > 60:
                    subject = subject[:57] + "..."
                print(f"      - {subject}")
            
            if len(emails) > 2:
                print(f"      ... and {len(emails) - 2} more")
    
    def get_categorization_insights(self, categorized_emails: Dict[str, List[Dict]]) -> Dict:
        """Get detailed insights about hybrid categorization"""
        insights = {
            'method': 'Hybrid (Enhanced NLP + LLM)',
            'clustering_algorithm': 'TF-IDF + Adaptive Clustering', 
            'naming_algorithm': 'LLM Semantic Analysis',
            'total_categories': len(categorized_emails),
            'total_emails': sum(len(emails) for emails in categorized_emails.values()),
            'category_distribution': {},
            'processing_efficiency': 'High (fast clustering + targeted LLM calls)'
        }
        
        # Category distribution
        for category, emails in categorized_emails.items():
            insights['category_distribution'][category] = len(emails)
        
        # Analyze category quality
        category_sizes = list(insights['category_distribution'].values())
        if category_sizes:
            insights['avg_category_size'] = sum(category_sizes) / len(category_sizes)
            insights['largest_category_size'] = max(category_sizes)
            insights['smallest_category_size'] = min(category_sizes)
        
        return insights