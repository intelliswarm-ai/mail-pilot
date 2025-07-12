import logging
import re
from typing import Dict, List, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import silhouette_score
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

class EmailEnhancedCategorizer:
    """
    Enhanced email categorizer using TF-IDF + advanced clustering algorithms
    with dynamic category discovery and semantic category naming.
    """
    
    def __init__(self, min_cluster_size: int = 3):
        """
        Initialize the enhanced email categorizer
        
        Args:
            min_cluster_size: Minimum emails required to form a cluster
        """
        self.min_cluster_size = min_cluster_size
        self.vectorizer = None
        self.embeddings = None
        self.clusterer = None
        self.reducer = None
        self.cluster_labels = {}
        self.lemmatizer = WordNetLemmatizer()
        
        # Download required NLTK data
        self._ensure_nltk_data()
    
    def _ensure_nltk_data(self):
        """Download required NLTK data if not present"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            print("📦 Downloading NLTK punkt tokenizer...")
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            print("📦 Downloading NLTK stopwords...")
            nltk.download('stopwords', quiet=True)
        
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            print("📦 Downloading NLTK WordNet...")
            nltk.download('wordnet', quiet=True)
    
    def categorize_emails(self, emails: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categorize emails using enhanced TF-IDF and adaptive clustering
        
        Returns: Dictionary with category names as keys and email lists as values
        """
        if len(emails) < self.min_cluster_size:
            logging.info(f"Too few emails ({len(emails)}) for clustering")
            return {"General": emails}
        
        print(f"\n🧠 Starting enhanced email categorization for {len(emails)} emails...")
        
        # Step 1: Create rich text representations
        processed_texts = self._create_text_representations(emails)
        
        # Step 2: Generate enhanced TF-IDF features
        print("📊 Creating enhanced TF-IDF feature matrix...")
        self.vectorizer = TfidfVectorizer(
            max_features=2000,  # Increased features
            stop_words='english',
            ngram_range=(1, 3),  # Include trigrams
            min_df=1,
            max_df=0.8,
            sublinear_tf=True,  # Apply sublinear scaling
            use_idf=True
        )
        
        try:
            tfidf_matrix = self.vectorizer.fit_transform(processed_texts)
            print(f"✅ Created {tfidf_matrix.shape[0]}x{tfidf_matrix.shape[1]} TF-IDF matrix")
        except Exception as e:
            logging.error(f"Failed to create TF-IDF matrix: {e}")
            return {"General": emails}
        
        # Step 3: Reduce dimensionality if needed
        if tfidf_matrix.shape[1] > 100:
            print("🔄 Reducing dimensionality with PCA...")
            n_components = min(100, len(emails) - 1, tfidf_matrix.shape[1])
            self.reducer = PCA(n_components=n_components, random_state=42)
            reduced_features = self.reducer.fit_transform(tfidf_matrix.toarray())
            print(f"✅ Reduced to {reduced_features.shape[1]} dimensions")
        else:
            reduced_features = tfidf_matrix.toarray()
        
        # Step 4: Adaptive clustering
        print("🎯 Discovering email clusters with adaptive clustering...")
        cluster_assignments = self._adaptive_clustering(reduced_features, emails)
        n_clusters = len(set(cluster_assignments)) - (1 if -1 in cluster_assignments else 0)
        n_noise = list(cluster_assignments).count(-1)
        
        print(f"✅ Discovered {n_clusters} meaningful categories ({n_noise} outliers)")
        
        # Step 5: Generate semantic category names
        category_names = self._generate_semantic_category_names(
            emails, processed_texts, cluster_assignments, tfidf_matrix
        )
        
        # Step 6: Group emails by categories
        categorized_emails = self._group_emails_by_category(
            emails, cluster_assignments, category_names
        )
        
        # Step 7: Post-process to merge similar categories and add uncategorized
        categorized_emails = self._post_process_categories(categorized_emails)
        categorized_emails = self._add_uncategorized_category(categorized_emails, emails)
        
        # Step 8: Print results with diagnostics
        self._print_categorization_summary(categorized_emails)
        self._print_categorization_diagnostics(categorized_emails, emails)
        
        return categorized_emails
    
    def _create_text_representations(self, emails: List[Dict]) -> List[str]:
        """Create rich text representations for feature extraction"""
        processed_texts = []
        
        print("🔄 Creating enhanced text representations...")
        for email in emails:
            # Extract and clean different components
            subject = self._clean_text(email.get('subject', ''))
            body = self._clean_text(email.get('body', ''))
            sender_info = self._extract_sender_features(email.get('sender', ''))
            
            # Create weighted representation with enhanced features
            # Subject gets triple weight, body normal weight, sender features added
            text_repr = f"{subject} {subject} {subject} {body} {sender_info}"
            processed_texts.append(text_repr)
        
        return processed_texts
    
    def _clean_text(self, text: str) -> str:
        """Enhanced text cleaning for better feature extraction"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove HTML and email artifacts
        text = re.sub(r'<[^>]+>', ' ', text)  # HTML tags
        text = re.sub(r'&[a-z]+;', ' ', text)  # HTML entities
        text = re.sub(r'http[s]?://\S+', ' ', text)  # URLs
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', ' ', text)  # Emails
        
        # Remove technical noise but preserve important terms
        noise_patterns = [
            r'\bzwnj\b', r'\bnull\b', r'\bwidth\b', r'\bheight\b', r'\bpx\b',
            r'\brgb\b', r'\bhex\b', r'\bstyle\b', r'\bfont\b', r'\bcolor\b',
            r'\bunsubscribe\b', r'\bview\s+browser\b'
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # Keep alphanumeric and spaces, preserve important punctuation
        text = re.sub(r'[^\w\s-]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Tokenize and process
        try:
            tokens = word_tokenize(text)
            stop_words = set(stopwords.words('english'))
            
            # Enhanced stop words for email context
            email_stop_words = {
                'email', 'message', 'mail', 'sent', 'received', 'inbox', 'subject',
                'dear', 'hello', 'hi', 'regards', 'sincerely', 'thanks', 'thank',
                'please', 'best', 'kind', 'click', 'here', 'now', 'today'
            }
            
            all_stop_words = stop_words.union(email_stop_words)
            
            # Advanced token filtering
            processed_tokens = []
            for token in tokens:
                if (len(token) > 2 and 
                    token not in all_stop_words and 
                    token.isalpha() and
                    not token.startswith(('http', 'www', 'com', 'org'))):
                    # Apply lemmatization
                    lemmatized = self.lemmatizer.lemmatize(token)
                    processed_tokens.append(lemmatized)
            
            return ' '.join(processed_tokens)
        except Exception as e:
            logging.warning(f"Text preprocessing failed: {e}")
            return text
    
    def _extract_sender_features(self, sender: str) -> str:
        """Extract meaningful features from sender information"""
        if not sender or '@' not in sender:
            return ""
        
        try:
            domain = sender.split('@')[1].lower()
            
            # Extract domain-based features
            domain_features = []
            
            # Common service providers
            service_mapping = {
                'github.com': 'github development',
                'linkedin.com': 'professional networking',
                'amazon.com': 'ecommerce amazon',
                'netflix.com': 'streaming entertainment',
                'spotify.com': 'music streaming',
                'youtube.com': 'video entertainment',
                'facebook.com': 'social media',
                'twitter.com': 'social media',
                'instagram.com': 'social media',
                'paypal.com': 'financial payment',
                'stripe.com': 'financial payment',
                'google.com': 'technology services',
                'microsoft.com': 'technology services',
                'apple.com': 'technology services',
                'slack.com': 'communication work',
                'zoom.us': 'communication meeting'
            }
            
            # Check for known services
            for service_domain, features in service_mapping.items():
                if service_domain in domain:
                    domain_features.append(features)
                    break
            
            # Extract generic domain parts
            domain_clean = domain.replace('.com', '').replace('.org', '').replace('.net', '')
            domain_clean = domain_clean.replace('.co.uk', '').replace('.io', '')
            domain_parts = re.split(r'[.-]', domain_clean)
            
            meaningful_parts = [part for part in domain_parts if len(part) > 2]
            domain_features.extend(meaningful_parts)
            
            return ' '.join(domain_features)
        except:
            return ""
    
    def _adaptive_clustering(self, features: np.ndarray, emails: List[Dict]) -> np.ndarray:
        """
        Adaptive clustering that selects optimal method and parameters
        """
        n_samples = len(emails)
        
        # For very small datasets
        if n_samples < 10:
            print("📊 Using simple KMeans for very small dataset")
            n_clusters = min(3, max(2, n_samples // 2))
            clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            return clusterer.fit_predict(features)
        
        # For small datasets
        if n_samples < 20:
            print("📊 Using Agglomerative Clustering for small dataset")
            n_clusters = min(max(2, n_samples // self.min_cluster_size), 6)
            clusterer = AgglomerativeClustering(
                n_clusters=n_clusters,
                linkage='ward'
            )
            return clusterer.fit_predict(features)
        
        # For larger datasets, try multiple approaches
        best_assignments = None
        best_score = -1
        best_method = None
        
        # Normalize features for distance-based clustering
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Try DBSCAN with different eps values - allow some outliers
        eps_values = [0.3, 0.5, 0.7, 1.0]
        for eps in eps_values:
            try:
                clusterer = DBSCAN(eps=eps, min_samples=self.min_cluster_size)
                assignments = clusterer.fit_predict(features_scaled)
                
                n_clusters = len(set(assignments)) - (1 if -1 in assignments else 0)
                n_noise = list(assignments).count(-1)
                
                # Allow some outliers (up to 30%) but ensure reasonable clustering
                if n_clusters < 2 or n_noise > len(emails) * 0.6:
                    continue
                
                # Calculate silhouette score
                if n_clusters > 1:
                    non_noise_mask = assignments != -1
                    if np.sum(non_noise_mask) > 1:
                        score = silhouette_score(features_scaled[non_noise_mask], assignments[non_noise_mask])
                        
                        if score > best_score:
                            best_score = score
                            best_assignments = assignments
                            best_method = f"DBSCAN(eps={eps})"
            except:
                continue
        
        # Try Agglomerative clustering with more conservative cluster counts
        max_clusters = min(8, n_samples // (self.min_cluster_size * 2))  # More conservative
        for n_clusters in range(2, max_clusters + 1):
            try:
                clusterer = AgglomerativeClustering(
                    n_clusters=n_clusters,
                    linkage='ward'
                )
                assignments = clusterer.fit_predict(features)
                
                score = silhouette_score(features, assignments)
                
                # Penalize if any cluster is too large (> 40% of data)
                cluster_sizes = [np.sum(assignments == i) for i in range(n_clusters)]
                max_cluster_size = max(cluster_sizes)
                if max_cluster_size > n_samples * 0.4:
                    score *= 0.5  # Penalty for imbalanced clustering
                
                if score > best_score:
                    best_score = score
                    best_assignments = assignments
                    best_method = f"Agglomerative(n_clusters={n_clusters})"
            except:
                continue
        
        # Try KMeans with balance penalty
        max_clusters_kmeans = min(6, n_samples // (self.min_cluster_size * 2))
        for n_clusters in range(2, max_clusters_kmeans + 1):
            try:
                clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                assignments = clusterer.fit_predict(features)
                
                score = silhouette_score(features, assignments)
                
                # Penalize if any cluster is too large (> 40% of data)
                cluster_sizes = [np.sum(assignments == i) for i in range(n_clusters)]
                max_cluster_size = max(cluster_sizes)
                if max_cluster_size > n_samples * 0.4:
                    score *= 0.5  # Penalty for imbalanced clustering
                
                if score > best_score:
                    best_score = score
                    best_assignments = assignments
                    best_method = f"KMeans(n_clusters={n_clusters})"
            except:
                continue
        
        if best_assignments is not None:
            print(f"✅ Selected {best_method} with silhouette score: {best_score:.3f}")
            return best_assignments
        
        # Final fallback
        print("⚠️  Using fallback clustering method")
        n_clusters = min(4, max(2, n_samples // self.min_cluster_size))
        clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        return clusterer.fit_predict(features)
    
    def _generate_semantic_category_names(self, emails: List[Dict], texts: List[str], 
                                        cluster_assignments: np.ndarray, tfidf_matrix) -> Dict[int, str]:
        """Generate meaningful category names using multiple strategies"""
        category_names = {}
        unique_clusters = set(cluster_assignments)
        feature_names = self.vectorizer.get_feature_names_out()
        
        for cluster_id in unique_clusters:
            if cluster_id == -1:  # Noise cluster
                category_names[cluster_id] = "Miscellaneous"
                continue
            
            # Get emails and texts in this cluster
            cluster_mask = cluster_assignments == cluster_id
            cluster_emails = [emails[i] for i in range(len(emails)) if cluster_mask[i]]
            cluster_texts = [texts[i] for i in range(len(texts)) if cluster_mask[i]]
            
            # Get TF-IDF features for this cluster
            cluster_tfidf = tfidf_matrix[cluster_mask]
            
            # Strategy 1: Domain-based analysis
            category_name = self._analyze_cluster_domains(cluster_emails, cluster_id)
            
            # Strategy 2: TF-IDF semantic analysis
            if not category_name or category_name.startswith("Cluster"):
                category_name = self._analyze_cluster_tfidf_semantics(
                    cluster_tfidf, feature_names, cluster_emails, cluster_id
                )
            
            # Strategy 3: Keyword frequency analysis
            if not category_name or category_name.startswith("Cluster"):
                category_name = self._analyze_cluster_keywords(cluster_texts, cluster_id)
            
            category_names[cluster_id] = category_name
        
        return category_names
    
    def _analyze_cluster_tfidf_semantics(self, cluster_tfidf, feature_names: np.ndarray, 
                                       cluster_emails: List[Dict], cluster_id: int) -> str:
        """Analyze cluster using TF-IDF features and semantic patterns"""
        
        # Calculate mean TF-IDF scores for this cluster
        mean_scores = np.mean(cluster_tfidf, axis=0).A1
        
        # Get top features
        top_indices = np.argsort(mean_scores)[-20:][::-1]
        top_features = [feature_names[i] for i in top_indices if mean_scores[i] > 0]
        
        if not top_features:
            return f"Cluster {cluster_id}"
        
        # Enhanced semantic categories with more specific patterns and priority scoring
        semantic_patterns = {
            'Professional Development': {
                'keywords': [
                    'job', 'jobs', 'apply', 'position', 'career', 'hiring', 'candidate', 
                    'developer', 'engineer', 'work', 'employment', 'resume', 'interview',
                    'application', 'opportunity', 'recruitment', 'professional', 'quantitative',
                    'full', 'stack', 'frontend', 'backend', 'senior', 'role', 'glassdoor',
                    'jobleads', 'eFinancialCareers', 'scientist', 'typescript', 'react'
                ],
                'priority': 10  # High priority - job emails are very important
            },
            'GitHub & Development': {
                'keywords': [
                    'github', 'repository', 'commit', 'pull', 'merge', 'build', 'failed', 
                    'ci', 'deploy', 'code', 'programming', 'development', 'software',
                    'dependabot', 'workflow', 'action', 'branch', 'intelliswarm', 'vuln',
                    'patcher', 'compass', 'pipeline'
                ],
                'priority': 9
            },
            'E-commerce & Shopping': {
                'keywords': [
                    'order', 'purchase', 'buy', 'cart', 'shipping', 'delivery', 'product', 
                    'sale', 'discount', 'deal', 'price', 'shop', 'checkout',
                    'payment', 'invoice', 'receipt', 'store', 'item'
                ],
                'priority': 5
            },
            'Entertainment & Media': {
                'keywords': [
                    'streaming', 'video', 'watch', 'movie', 'show', 'prime', 'netflix', 
                    'youtube', 'entertainment', 'music', 'podcast', 'content', 'episode',
                    'series', 'film', 'amazon', 'uber'
                ],
                'priority': 4
            },
            'Security & Authentication': {
                'keywords': [
                    'login', 'secure', 'access', 'password', 'verification', 'authenticate', 
                    'security', 'account', 'claude', 'signin', 'verify', 'confirm',
                    'authorization', 'token', 'link'
                ],
                'priority': 8
            },
            'Financial Services': {
                'keywords': [
                    'bank', 'banking', 'payment', 'transaction', 'invoice', 'billing', 
                    'credit', 'finance', 'money', 'paypal', 'stripe', 'financial',
                    'balance', 'statement'
                ],
                'priority': 7
            },
            'Social & Networking': {
                'keywords': [
                    'linkedin', 'facebook', 'twitter', 'instagram', 'social', 'network',
                    'follow', 'friend', 'connection', 'share', 'like', 'comment',
                    'community', 'group'
                ],
                'priority': 6
            },
            'News & Updates': {
                'keywords': [
                    'news', 'newsletter', 'update', 'announcement', 'information', 
                    'bulletin', 'article', 'blog', 'report', 'digest', 'briefing'
                ],
                'priority': 6
            },
            'Communication & Meetings': {
                'keywords': [
                    'meeting', 'zoom', 'slack', 'teams', 'call', 'conference', 
                    'appointment', 'calendar', 'schedule', 'invite', 'reminder'
                ],
                'priority': 8
            },
            'Travel & Booking': {
                'keywords': [
                    'travel', 'booking', 'hotel', 'flight', 'trip', 'reservation', 
                    'vacation', 'airline', 'airport', 'itinerary', 'relais', 'torre'
                ],
                'priority': 7
            }
        }
        
        # Create feature text for analysis
        features_text = ' '.join(top_features[:15]).lower()
        
        # Score each category with priority weighting
        category_scores = {}
        for category, config in semantic_patterns.items():
            keywords = config['keywords']
            priority = config['priority']
            
            # Count keyword matches
            keyword_matches = sum(1 for keyword in keywords if keyword in features_text)
            
            if keyword_matches > 0:
                # Apply priority weighting and match multiplier
                base_score = keyword_matches * priority
                
                # Boost score if multiple related keywords found
                if keyword_matches > 1:
                    base_score *= 1.5
                
                category_scores[category] = base_score
        
        # Return best matching category with minimum threshold
        if category_scores:
            best_category, best_score = max(category_scores.items(), key=lambda x: x[1])
            cluster_size = len(cluster_emails)
            
            # Require a minimum score to avoid weak matches
            min_threshold = len(cluster_emails) * 0.1  # At least 10% of emails should match keywords
            if best_score >= min_threshold:
                return f"{best_category} ({cluster_size} emails)"
        
        return None
    
    def _analyze_cluster_domains(self, cluster_emails: List[Dict], cluster_id: int) -> str:
        """Enhanced domain-based analysis"""
        domains = []
        for email in cluster_emails:
            sender = email.get('sender', '')
            if '@' in sender:
                domain = sender.split('@')[1].lower()
                domains.append(domain)
        
        if not domains:
            return None
        
        domain_counts = Counter(domains)
        most_common_domain = domain_counts.most_common(1)[0][0]
        
        # Enhanced domain categorization
        domain_categories = {
            'github.com': 'GitHub Development',
            'noreply.github.com': 'GitHub Development',
            'linkedin.com': 'LinkedIn Professional',
            'amazon.com': 'Amazon Services',
            'amazon.co.uk': 'Amazon Services',
            'netflix.com': 'Netflix Entertainment',
            'spotify.com': 'Spotify Music',
            'youtube.com': 'YouTube Content',
            'facebook.com': 'Facebook Social',
            'twitter.com': 'Twitter Social',
            'instagram.com': 'Instagram Social',
            'paypal.com': 'PayPal Financial',
            'stripe.com': 'Stripe Payments',
            'google.com': 'Google Services',
            'gmail.com': 'Gmail Communications',
            'microsoft.com': 'Microsoft Services',
            'apple.com': 'Apple Services',
            'slack.com': 'Slack Communication',
            'zoom.us': 'Zoom Meetings',
            'anthropic.com': 'Anthropic AI',
            'claude.ai': 'Claude AI'
        }
        
        cluster_size = len(cluster_emails)
        
        # Exact domain match
        if most_common_domain in domain_categories:
            return f"{domain_categories[most_common_domain]} ({cluster_size} emails)"
        
        # Partial domain matching
        for known_domain, category in domain_categories.items():
            if known_domain in most_common_domain or most_common_domain in known_domain:
                return f"{category} ({cluster_size} emails)"
        
        # Generic domain-based naming - fix truncation issues
        if most_common_domain.count('.') == 1:  # Simple domain
            domain_name = most_common_domain.replace('.com', '').replace('.org', '').replace('.net', '')
            domain_name = domain_name.replace('.co.uk', '').replace('.io', '')
            
            # Clean up domain name properly
            if len(domain_name) > 15:  # Long domain names
                domain_name = domain_name[:12] + "..."
            
            return f"{domain_name.title()} Communications ({cluster_size} emails)"
        
        return None
    
    def _analyze_cluster_keywords(self, cluster_texts: List[str], cluster_id: int) -> str:
        """Enhanced keyword-based analysis"""
        all_text = ' '.join(cluster_texts).lower()
        words = re.findall(r'\b[a-z]{3,}\b', all_text)
        
        if not words:
            return f"Email Group {cluster_id}"
        
        word_counts = Counter(words)
        
        # Enhanced stopwords
        stopwords_extended = {
            'email', 'message', 'mail', 'sent', 'received', 'please', 'thank', 
            'thanks', 'regards', 'best', 'sincerely', 'hello', 'dear', 'the',
            'and', 'for', 'you', 'your', 'this', 'that', 'with', 'from',
            'will', 'can', 'have', 'are', 'our', 'all', 'new', 'get'
        }
        
        meaningful_words = [
            (word, count) for word, count in word_counts.most_common(10) 
            if word not in stopwords_extended and len(word) > 3
        ]
        
        if meaningful_words:
            top_word = meaningful_words[0][0].title()
            return f"{top_word} Related ({len(cluster_texts)} emails)"
        
        return f"Email Group {cluster_id} ({len(cluster_texts)} emails)"
    
    def _group_emails_by_category(self, emails: List[Dict], cluster_assignments: np.ndarray, 
                                category_names: Dict[int, str]) -> Dict[str, List[Dict]]:
        """Group emails by their assigned categories"""
        categorized_emails = {}
        
        for email, cluster_id in zip(emails, cluster_assignments):
            category_name = category_names.get(cluster_id, f"Cluster {cluster_id}")
            
            if category_name not in categorized_emails:
                categorized_emails[category_name] = []
            
            # Add metadata
            email_with_metadata = email.copy()
            email_with_metadata['cluster_id'] = int(cluster_id)
            email_with_metadata['category'] = category_name
            email_with_metadata['is_outlier'] = cluster_id == -1
            
            categorized_emails[category_name].append(email_with_metadata)
        
        return categorized_emails
    
    def _print_categorization_summary(self, categorized_emails: Dict[str, List[Dict]]):
        """Print enhanced summary of categorization results"""
        print(f"\n📊 Enhanced Email Categorization Results:")
        print(f"   🎯 Total Categories: {len(categorized_emails)}")
        
        # Sort by size
        sorted_categories = sorted(categorized_emails.items(), 
                                 key=lambda x: len(x[1]), reverse=True)
        
        for category, emails in sorted_categories:
            print(f"   📂 {category}: {len(emails)} emails")
            
            # Show sample subjects
            for email in emails[:2]:
                subject = email.get('subject', 'No Subject')
                if len(subject) > 60:
                    subject = subject[:57] + "..."
                print(f"      - {subject}")
            
            if len(emails) > 2:
                print(f"      ... and {len(emails) - 2} more")
    
    def get_categorization_insights(self, categorized_emails: Dict[str, List[Dict]]) -> Dict:
        """Get detailed insights about the categorization"""
        insights = {
            'total_categories': len(categorized_emails),
            'total_emails': sum(len(emails) for emails in categorized_emails.values()),
            'category_distribution': {},
            'outlier_ratio': 0,
            'avg_cluster_size': 0,
            'largest_category': None,
            'smallest_category': None
        }
        
        category_sizes = []
        outlier_count = 0
        
        for category, emails in categorized_emails.items():
            size = len(emails)
            category_sizes.append(size)
            insights['category_distribution'][category] = size
            
            if 'Miscellaneous' in category or any(email.get('is_outlier', False) for email in emails):
                outlier_count += size
        
        if category_sizes:
            insights['avg_cluster_size'] = np.mean(category_sizes)
            insights['outlier_ratio'] = outlier_count / insights['total_emails']
            
            # Find largest and smallest categories
            sorted_cats = sorted(categorized_emails.items(), key=lambda x: len(x[1]))
            insights['smallest_category'] = sorted_cats[0][0]
            insights['largest_category'] = sorted_cats[-1][0]
        
        return insights
    
    def _post_process_categories(self, categorized_emails: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Post-process categories to merge similar ones and add uncategorized"""
        processed_categories = {}
        used_emails = set()  # Track which emails have been processed to avoid duplicates
        
        # Merge similar categories WITHOUT duplicating emails
        merge_patterns = {
            'GitHub Development': ['GitHub & Development', 'GitHub Development'],
            'Professional Development': ['LinkedIn Professional', 'Glassdoor Communications', 'Jobleads Communications'],
            'Entertainment & Media': ['Amazon Services', 'Netflix Entertainment']
        }
        
        # First pass: merge categories
        for target_category, source_patterns in merge_patterns.items():
            merged_emails = []
            
            for category_name, emails in categorized_emails.items():
                # Check if this category should be merged
                should_merge = False
                for pattern in source_patterns:
                    if pattern in category_name:
                        should_merge = True
                        break
                
                if should_merge:
                    # Add emails that haven't been used yet
                    for email in emails:
                        email_id = email.get('id', f"{email.get('sender', '')}_{email.get('subject', '')}")
                        if email_id not in used_emails:
                            merged_emails.append(email)
                            used_emails.add(email_id)
            
            if merged_emails:
                processed_categories[f"{target_category} ({len(merged_emails)} emails)"] = merged_emails
        
        # Second pass: add remaining categories that weren't merged
        for category_name, emails in categorized_emails.items():
            # Check if this category was merged
            was_merged = False
            for source_patterns in merge_patterns.values():
                if any(pattern in category_name for pattern in source_patterns):
                    was_merged = True
                    break
            
            if not was_merged:
                # Add emails that haven't been used yet
                remaining_emails = []
                for email in emails:
                    email_id = email.get('id', f"{email.get('sender', '')}_{email.get('subject', '')}")
                    if email_id not in used_emails:
                        remaining_emails.append(email)
                        used_emails.add(email_id)
                
                if remaining_emails:
                    processed_categories[category_name] = remaining_emails
        
        return processed_categories
    
    def _add_uncategorized_category(self, categorized_emails: Dict[str, List[Dict]], all_emails: List[Dict]) -> Dict[str, List[Dict]]:
        """Add uncategorized category for emails that don't fit well in any category"""
        # Get all categorized email IDs
        categorized_ids = set()
        for emails in categorized_emails.values():
            for email in emails:
                email_id = email.get('id', f"{email.get('sender', '')}_{email.get('subject', '')}")
                categorized_ids.add(email_id)
        
        # Find uncategorized emails
        uncategorized_emails = []
        for email in all_emails:
            email_id = email.get('id', f"{email.get('sender', '')}_{email.get('subject', '')}")
            if email_id not in categorized_ids:
                email_copy = email.copy()
                email_copy['category'] = 'Uncategorized'
                email_copy['is_outlier'] = True
                uncategorized_emails.append(email_copy)
        
        # Add uncategorized category if there are any
        if uncategorized_emails:
            categorized_emails[f"Uncategorized ({len(uncategorized_emails)} emails)"] = uncategorized_emails
        
        return categorized_emails
    
    def _print_categorization_diagnostics(self, categorized_emails: Dict[str, List[Dict]], all_emails: List[Dict]):
        """Print detailed diagnostics about categorization quality"""
        print(f"\n🔍 Categorization Diagnostics:")
        
        # Count unique emails (no duplicates)
        unique_email_ids = set()
        total_categorized = 0
        
        for emails in categorized_emails.values():
            for email in emails:
                email_id = email.get('id', f"{email.get('sender', '')}_{email.get('subject', '')}")
                if email_id not in unique_email_ids:
                    unique_email_ids.add(email_id)
                    total_categorized += 1
        
        coverage = (total_categorized / len(all_emails)) * 100
        print(f"   📊 Coverage: {total_categorized}/{len(all_emails)} emails ({coverage:.1f}%)")
        
        # Check for uncategorized emails
        uncategorized_count = len(all_emails) - total_categorized
        if uncategorized_count > 0:
            print(f"   📋 Uncategorized: {uncategorized_count} emails")
        
        # Analyze category quality
        high_priority_categories = ['Professional Development', 'GitHub Development', 'Security & Authentication']
        
        priority_email_count = 0
        for category_name, emails in categorized_emails.items():
            if any(priority in category_name for priority in high_priority_categories):
                priority_email_count += len(emails)
                print(f"   🎯 High Priority: {category_name}")
        
        print(f"   ⚡ Total High Priority Emails: {priority_email_count}")
        
        # Check for potential issues
        if categorized_emails:
            largest_category = max(categorized_emails.items(), key=lambda x: len(x[1]))
            largest_size = len(largest_category[1])
            largest_percentage = (largest_size / len(all_emails)) * 100
            
            if largest_percentage > 40:
                print(f"   ⚠️  WARNING: Largest category '{largest_category[0]}' contains {largest_size} emails ({largest_percentage:.1f}%)")
                print(f"        This might indicate poor clustering - some emails may be miscategorized")
                
                # Sample some emails from the largest category for inspection
                print(f"   🔍 Sample subjects from largest category:")
                for i, email in enumerate(largest_category[1][:5]):
                    print(f"      {i+1}. {email.get('subject', 'No Subject')[:80]}...")
            
            # Category distribution analysis
            sizes = [len(emails) for emails in categorized_emails.values()]
            avg_size = np.mean(sizes)
            print(f"   📈 Average category size: {avg_size:.1f} emails")
            print(f"   📏 Size range: {min(sizes)} - {max(sizes)} emails")