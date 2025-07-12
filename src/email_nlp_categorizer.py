import logging
import re
from typing import Dict, List, Tuple, Set
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

class EmailNLPCategorizer:
    def __init__(self, min_cluster_size: int = 2, max_clusters: int = 8):
        """
        Initialize NLP-based email categorizer with clustering
        
        Args:
            min_cluster_size: Minimum emails required to form a cluster
            max_clusters: Maximum number of clusters to create
        """
        self.min_cluster_size = min_cluster_size
        self.max_clusters = max_clusters
        self.vectorizer = None
        self.kmeans = None
        self.cluster_labels = {}
        self.lemmatizer = WordNetLemmatizer()
        
        # Download required NLTK data
        self._ensure_nltk_data()
        
        # Common email patterns for preprocessing
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # URLs
            r'\b(?:unsubscribe|click here|view online|privacy policy)\b',  # Common email boilerplate
        ]
    
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
        Categorize emails using NLP clustering
        
        Returns: Dictionary with cluster names as keys and email lists as values
        """
        if len(emails) < self.min_cluster_size:
            logging.info(f"Too few emails ({len(emails)}) for clustering, treating as single category")
            return {"General": emails}
        
        print(f"\n🤖 Starting NLP-based email clustering for {len(emails)} emails...")
        
        # Preprocess and extract features
        processed_texts = self._preprocess_emails(emails)
        
        # Create TF-IDF vectors
        print("📊 Creating TF-IDF feature vectors...")
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.8
        )
        
        try:
            tfidf_matrix = self.vectorizer.fit_transform(processed_texts)
            print(f"✅ Created {tfidf_matrix.shape[0]}x{tfidf_matrix.shape[1]} TF-IDF matrix")
        except Exception as e:
            logging.error(f"Failed to create TF-IDF matrix: {e}")
            return {"General": emails}
        
        # Determine optimal number of clusters
        n_clusters = self._determine_optimal_clusters(tfidf_matrix, len(emails))
        print(f"🎯 Using {n_clusters} clusters for email categorization")
        
        # Perform clustering
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_assignments = self.kmeans.fit_predict(tfidf_matrix)
        
        # Generate cluster labels
        cluster_labels = self._generate_cluster_labels(tfidf_matrix, cluster_assignments, n_clusters)
        
        # Debug: Show top features for troubleshooting
        self._debug_cluster_features(tfidf_matrix, cluster_assignments, n_clusters)
        
        # Group emails by cluster
        clustered_emails = self._group_emails_by_cluster(emails, cluster_assignments, cluster_labels)
        
        # Print clustering results
        self._print_clustering_summary(clustered_emails)
        
        return clustered_emails
    
    def _preprocess_emails(self, emails: List[Dict]) -> List[str]:
        """Preprocess email content for clustering"""
        processed_texts = []
        
        print("🔄 Preprocessing email content...")
        for email in emails:
            # Combine subject and body
            text = f"{email['subject']} {email['body']}"
            
            # Clean and preprocess
            processed_text = self._clean_text(text)
            processed_texts.append(processed_text)
        
        return processed_texts
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove HTML tags and entities
        text = re.sub(r'<[^>]+>', ' ', text)  # Remove HTML tags
        text = re.sub(r'&[a-z]+;', ' ', text)  # Remove HTML entities like &nbsp;
        text = re.sub(r'&[#x][0-9a-f]+;', ' ', text)  # Remove numeric HTML entities
        
        # Remove email patterns
        for pattern in self.email_patterns:
            text = re.sub(pattern, '', text)
        
        # Remove common email artifacts and technical noise
        noise_patterns = [
            r'\bzwnj\b', r'\bnull\b', r'\bwidth\b', r'\bheight\b', r'\bpx\b',
            r'\brgb\b', r'\bhex\b', r'\bhtml\b', r'\bcss\b', r'\bstyle\b',
            r'\bfont\b', r'\bcolor\b', r'\bborder\b', r'\bpadding\b',
            r'\bmargin\b', r'\bdiv\b', r'\bspan\b', r'\btable\b', r'\btr\b', r'\btd\b',
            r'\bimg\b', r'\bsrc\b', r'\balt\b', r'\bhref\b', r'\blink\b',
            r'\bunsubscribe\b', r'\bview\s+browser\b', r'\bprivacy\s+policy\b'
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # Remove special characters and numbers, but keep spaces
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Tokenize and lemmatize
        try:
            tokens = word_tokenize(text)
            stop_words = set(stopwords.words('english'))
            
            # Extended stop words for email context
            email_stop_words = {
                'email', 'message', 'mail', 'sent', 'received', 'inbox', 'subject',
                'dear', 'hello', 'hi', 'regards', 'sincerely', 'thanks', 'thank',
                'please', 'best', 'kind', 'click', 'here', 'now', 'today',
                'get', 'see', 'know', 'want', 'need', 'make', 'take', 'use',
                'would', 'could', 'should', 'may', 'might', 'will', 'can'
            }
            
            all_stop_words = stop_words.union(email_stop_words)
            
            # Filter tokens more aggressively
            tokens = [
                self.lemmatizer.lemmatize(token) 
                for token in tokens 
                if (token not in all_stop_words and 
                    len(token) > 3 and  # Increased minimum length
                    token.isalpha() and  # Only alphabetic tokens
                    not token.startswith(('http', 'www', 'com', 'org')))
            ]
            
            return ' '.join(tokens)
        except Exception as e:
            logging.warning(f"Text preprocessing failed: {e}")
            return text
    
    def _determine_optimal_clusters(self, tfidf_matrix, n_emails: int) -> int:
        """Determine optimal number of clusters using elbow method"""
        max_possible_clusters = min(self.max_clusters, n_emails // self.min_cluster_size)
        
        if max_possible_clusters < 2:
            return 1
        
        # Try different numbers of clusters
        inertias = []
        cluster_range = range(2, max_possible_clusters + 1)
        
        for k in cluster_range:
            try:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                kmeans.fit(tfidf_matrix)
                inertias.append(kmeans.inertia_)
            except:
                break
        
        if not inertias:
            return 2
        
        # Simple elbow detection (choose point where improvement slows down)
        if len(inertias) >= 2:
            improvements = [inertias[i-1] - inertias[i] for i in range(1, len(inertias))]
            if improvements:
                # Find point where improvement drops significantly
                avg_improvement = sum(improvements) / len(improvements)
                for i, improvement in enumerate(improvements):
                    if improvement < avg_improvement * 0.5:
                        return min(i + 3, max_possible_clusters)  # +3 because we start from k=2
        
        # Default to middle value
        return min(4, max_possible_clusters)
    
    def _generate_cluster_labels(self, tfidf_matrix, cluster_assignments: np.ndarray, n_clusters: int) -> Dict[int, str]:
        """Generate meaningful labels for clusters based on top keywords"""
        cluster_labels = {}
        feature_names = self.vectorizer.get_feature_names_out()
        
        for cluster_id in range(n_clusters):
            # Get emails in this cluster
            cluster_mask = cluster_assignments == cluster_id
            cluster_size = np.sum(cluster_mask)
            
            if cluster_size == 0:
                cluster_labels[cluster_id] = f"Empty Cluster {cluster_id}"
                continue
            
            # Get centroid for this cluster
            cluster_center = self.kmeans.cluster_centers_[cluster_id]
            
            # Get top features for this cluster
            top_indices = cluster_center.argsort()[-10:][::-1]  # Top 10 features
            top_features = [feature_names[i] for i in top_indices if cluster_center[i] > 0]
            
            # Generate descriptive label
            label = self._create_cluster_label(top_features, cluster_size)
            cluster_labels[cluster_id] = label
        
        return cluster_labels
    
    def _create_cluster_label(self, top_features: List[str], cluster_size: int) -> str:
        """Create a descriptive label from top features"""
        if not top_features:
            return f"General ({cluster_size} emails)"
        
        # Enhanced patterns for automatic labeling with more comprehensive keywords
        label_patterns = {
            'Job Notifications': ['job', 'jobs', 'apply', 'position', 'career', 'hiring', 'candidate', 'developer', 'engineer', 'work', 'employment'],
            'GitHub/Development': ['github', 'dependabot', 'repository', 'commit', 'pull', 'merge', 'build', 'failed', 'ci', 'deploy'],
            'Shopping/E-commerce': ['price', 'order', 'buy', 'purchase', 'cart', 'shipping', 'delivery', 'product', 'sale', 'discount', 'deal'],
            'Streaming/Entertainment': ['streaming', 'video', 'watch', 'movie', 'show', 'prime', 'netflix', 'youtube', 'entertainment'],
            'Authentication/Security': ['login', 'secure', 'access', 'password', 'verification', 'authenticate', 'security', 'account', 'claude'],
            'Marketing/Promotions': ['offer', 'promo', 'marketing', 'campaign', 'newsletter', 'unsubscribe', 'special'],
            'Social Media': ['follow', 'like', 'share', 'friend', 'social', 'linkedin', 'facebook', 'twitter', 'instagram'],
            'Finance/Banking': ['bank', 'payment', 'invoice', 'billing', 'credit', 'finance', 'money', 'transaction'],
            'Support/Help': ['support', 'help', 'ticket', 'issue', 'problem', 'assistance', 'contact'],
            'News/Updates': ['news', 'update', 'announcement', 'release', 'new', 'latest', 'information'],
            'Education/Learning': ['course', 'learn', 'training', 'education', 'tutorial', 'lesson', 'study'],
            'Travel/Booking': ['travel', 'booking', 'hotel', 'flight', 'trip', 'reservation', 'vacation']
        }
        
        # Convert top features to lowercase for matching
        features_text = ' '.join(top_features[:10]).lower()
        
        # Check for pattern matches with scoring
        category_scores = {}
        for category, keywords in label_patterns.items():
            score = sum(1 for keyword in keywords if keyword in features_text)
            if score > 0:
                category_scores[category] = score
        
        # Return the category with highest score
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])[0]
            return f"{best_category} ({cluster_size} emails)"
        
        # Fallback: Try to create meaningful labels from clean features
        # Filter out technical junk and short words
        meaningful_words = []
        for word in top_features[:5]:
            word_clean = word.lower()
            # Skip very short words, technical artifacts, and common stopwords
            if (len(word_clean) >= 4 and 
                not any(char in word_clean for char in ['&', 'zwnj', 'null', '_', '|', '@']) and
                word_clean not in ['important', 'width', 'annotation', 'price', 'nbsp', 'html', 'body', 'email', 'message']):
                meaningful_words.append(word_clean.title())
        
        if meaningful_words:
            if len(meaningful_words) == 1:
                return f"{meaningful_words[0]} Related ({cluster_size} emails)"
            else:
                return f"{meaningful_words[0]} & {meaningful_words[1]} ({cluster_size} emails)"
        
        # Last resort: Use cluster number
        return f"Email Group {cluster_size} ({cluster_size} emails)"
    
    def _group_emails_by_cluster(self, emails: List[Dict], cluster_assignments: np.ndarray, cluster_labels: Dict[int, str]) -> Dict[str, List[Dict]]:
        """Group emails by their cluster assignments"""
        clustered_emails = {}
        
        for email, cluster_id in zip(emails, cluster_assignments):
            cluster_label = cluster_labels.get(cluster_id, f"Cluster {cluster_id}")
            
            if cluster_label not in clustered_emails:
                clustered_emails[cluster_label] = []
            
            # Add cluster info to email
            email_with_cluster = email.copy()
            email_with_cluster['cluster_id'] = int(cluster_id)
            email_with_cluster['cluster_label'] = cluster_label
            
            clustered_emails[cluster_label].append(email_with_cluster)
        
        return clustered_emails
    
    def _debug_cluster_features(self, tfidf_matrix, cluster_assignments: np.ndarray, n_clusters: int):
        """Debug method to show top features per cluster"""
        if not hasattr(self, 'vectorizer') or self.vectorizer is None:
            return
            
        feature_names = self.vectorizer.get_feature_names_out()
        
        print(f"\n🔍 Debug: Top features per cluster:")
        for cluster_id in range(n_clusters):
            cluster_center = self.kmeans.cluster_centers_[cluster_id]
            top_indices = cluster_center.argsort()[-10:][::-1]
            top_features = [f"{feature_names[i]}({cluster_center[i]:.3f})" for i in top_indices if cluster_center[i] > 0]
            
            cluster_size = np.sum(cluster_assignments == cluster_id)
            print(f"   Cluster {cluster_id} ({cluster_size} emails): {', '.join(top_features[:5])}")
    
    def _print_clustering_summary(self, clustered_emails: Dict[str, List[Dict]]):
        """Print summary of clustering results"""
        print(f"\n📊 Email Clustering Results:")
        print(f"   🎯 Total Categories: {len(clustered_emails)}")
        
        for category, emails in clustered_emails.items():
            print(f"   📂 {category}: {len(emails)} emails")
            
            # Show sample subjects
            sample_subjects = [email['subject'][:50] + "..." if len(email['subject']) > 50 else email['subject'] 
                             for email in emails[:2]]
            for subject in sample_subjects:
                print(f"      - {subject}")
            if len(emails) > 2:
                print(f"      ... and {len(emails) - 2} more")
    
    def get_cluster_statistics(self, clustered_emails: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """Get detailed statistics for each cluster"""
        stats = {}
        
        for category, emails in clustered_emails.items():
            # Calculate priority distribution
            priorities = [email.get('priority', 'Medium') for email in emails]
            priority_counts = Counter(priorities)
            
            # Calculate sender distribution
            senders = [email['sender'].split('@')[1] if '@' in email['sender'] else email['sender'] 
                      for email in emails]
            sender_domains = Counter(senders)
            
            stats[category] = {
                'email_count': len(emails),
                'priority_distribution': dict(priority_counts),
                'top_sender_domains': dict(sender_domains.most_common(5)),
                'avg_subject_length': np.mean([len(email['subject']) for email in emails]),
                'avg_body_length': np.mean([len(email['body']) for email in emails])
            }
        
        return stats