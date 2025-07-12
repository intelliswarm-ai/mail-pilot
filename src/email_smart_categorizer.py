import logging
import re
from typing import Dict, List, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from sklearn.metrics import silhouette_score

class EmailSmartCategorizer:
    """
    State-of-the-art email categorizer using BERT embeddings + DBSCAN clustering
    with dynamic category discovery and meaningful category naming.
    """
    
    def __init__(self, min_cluster_size: int = 3, eps: float = 0.5):
        """
        Initialize the smart email categorizer
        
        Args:
            min_cluster_size: Minimum emails required to form a cluster
            eps: DBSCAN eps parameter for neighborhood distance
        """
        self.min_cluster_size = min_cluster_size
        self.eps = eps
        self.model = None
        self.embeddings = None
        self.clusterer = None
        self.reducer = None
        self.cluster_labels = {}
        
        # Load sentence transformer model
        print("🤖 Loading BERT model for email embeddings...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ BERT model loaded successfully")
    
    def categorize_emails(self, emails: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categorize emails using BERT embeddings and HDBSCAN clustering
        
        Returns: Dictionary with category names as keys and email lists as values
        """
        if len(emails) < self.min_cluster_size:
            logging.info(f"Too few emails ({len(emails)}) for clustering")
            return {"General": emails}
        
        print(f"\n🧠 Starting smart email categorization for {len(emails)} emails...")
        
        # Step 1: Preprocess emails and create text representations
        processed_texts = self._create_text_representations(emails)
        
        # Step 2: Generate BERT embeddings
        print("📊 Generating BERT embeddings...")
        self.embeddings = self.model.encode(processed_texts, show_progress_bar=True)
        print(f"✅ Created {self.embeddings.shape[0]}x{self.embeddings.shape[1]} embedding matrix")
        
        # Step 3: Reduce dimensionality with PCA
        print("🔄 Reducing dimensionality with PCA...")
        n_components = min(50, len(emails) - 1, self.embeddings.shape[1])
        self.reducer = PCA(n_components=n_components, random_state=42)
        reduced_embeddings = self.reducer.fit_transform(self.embeddings)
        print(f"✅ Reduced to {reduced_embeddings.shape[1]} dimensions")
        
        # Step 4: Determine optimal clustering method and parameters
        print("🎯 Discovering email clusters with adaptive clustering...")
        cluster_assignments = self._adaptive_clustering(reduced_embeddings, emails)
        n_clusters = len(set(cluster_assignments)) - (1 if -1 in cluster_assignments else 0)
        n_noise = list(cluster_assignments).count(-1)
        
        print(f"✅ Discovered {n_clusters} meaningful categories ({n_noise} outliers)")
        
        # Step 5: Generate meaningful category names
        category_names = self._generate_meaningful_category_names(
            emails, processed_texts, cluster_assignments
        )
        
        # Step 6: Group emails by categories
        categorized_emails = self._group_emails_by_category(
            emails, cluster_assignments, category_names
        )
        
        # Step 7: Print results
        self._print_categorization_summary(categorized_emails)
        
        return categorized_emails
    
    def _create_text_representations(self, emails: List[Dict]) -> List[str]:
        """Create rich text representations for embedding"""
        processed_texts = []
        
        print("🔄 Creating text representations...")
        for email in emails:
            # Combine multiple fields with weights
            subject = self._clean_text(email.get('subject', ''))
            body = self._clean_text(email.get('body', ''))
            sender = self._extract_sender_info(email.get('sender', ''))
            
            # Create weighted representation (subject gets more weight)
            text_repr = f"{subject} {subject} {body} {sender}"
            processed_texts.append(text_repr)
        
        return processed_texts
    
    def _adaptive_clustering(self, embeddings: np.ndarray, emails: List[Dict]) -> np.ndarray:
        """
        Adaptive clustering that chooses the best method and parameters based on data characteristics
        """
        n_samples = len(emails)
        
        # For small datasets, use agglomerative clustering
        if n_samples < 20:
            print("📊 Using Agglomerative Clustering for small dataset")
            n_clusters = min(max(2, n_samples // self.min_cluster_size), 6)
            clusterer = AgglomerativeClustering(
                n_clusters=n_clusters,
                metric='cosine',
                linkage='average'
            )
            cluster_assignments = clusterer.fit_predict(embeddings)
            return cluster_assignments
        
        # For larger datasets, try multiple approaches and pick the best
        best_assignments = None
        best_score = -1
        best_method = None
        
        # Try DBSCAN with different eps values
        eps_values = [0.3, 0.5, 0.7, 0.9]
        for eps in eps_values:
            try:
                clusterer = DBSCAN(eps=eps, min_samples=self.min_cluster_size, metric='cosine')
                assignments = clusterer.fit_predict(embeddings)
                
                n_clusters = len(set(assignments)) - (1 if -1 in assignments else 0)
                n_noise = list(assignments).count(-1)
                
                # Skip if too few clusters or too much noise
                if n_clusters < 2 or n_noise > len(emails) * 0.5:
                    continue
                
                # Calculate silhouette score (excluding noise points)
                if n_clusters > 1:
                    non_noise_mask = assignments != -1
                    if np.sum(non_noise_mask) > 1:
                        score = silhouette_score(embeddings[non_noise_mask], assignments[non_noise_mask])
                        
                        if score > best_score:
                            best_score = score
                            best_assignments = assignments
                            best_method = f"DBSCAN(eps={eps})"
            except:
                continue
        
        # Try Agglomerative clustering with different number of clusters
        for n_clusters in range(2, min(8, n_samples // self.min_cluster_size + 1)):
            try:
                clusterer = AgglomerativeClustering(
                    n_clusters=n_clusters,
                    metric='cosine',
                    linkage='average'
                )
                assignments = clusterer.fit_predict(embeddings)
                
                score = silhouette_score(embeddings, assignments)
                
                if score > best_score:
                    best_score = score
                    best_assignments = assignments
                    best_method = f"Agglomerative(n_clusters={n_clusters})"
            except:
                continue
        
        if best_assignments is not None:
            print(f"✅ Selected {best_method} with silhouette score: {best_score:.3f}")
            return best_assignments
        
        # Fallback: simple agglomerative clustering
        print("⚠️  Using fallback clustering method")
        n_clusters = min(4, max(2, n_samples // self.min_cluster_size))
        clusterer = AgglomerativeClustering(n_clusters=n_clusters)
        return clusterer.fit_predict(embeddings)
    
    def _clean_text(self, text: str) -> str:
        """Advanced text cleaning for better embeddings"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove HTML and email artifacts
        text = re.sub(r'<[^>]+>', ' ', text)  # HTML tags
        text = re.sub(r'&[a-z]+;', ' ', text)  # HTML entities
        text = re.sub(r'http[s]?://\S+', ' ', text)  # URLs
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', ' ', text)  # Emails
        
        # Remove technical noise
        noise_patterns = [
            r'\bzwnj\b', r'\bnull\b', r'\bwidth\b', r'\bheight\b', r'\bpx\b',
            r'\brgb\b', r'\bhex\b', r'\bstyle\b', r'\bfont\b', r'\bcolor\b',
            r'\bunsubscribe\b', r'\bview\s+browser\b', r'\bprivacy\s+policy\b'
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # Keep only alphabetic characters and spaces
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_sender_info(self, sender: str) -> str:
        """Extract meaningful information from sender"""
        if not sender or '@' not in sender:
            return ""
        
        try:
            # Extract domain and create meaningful tokens
            domain = sender.split('@')[1].lower()
            
            # Remove common TLDs and extract meaningful parts
            domain_parts = domain.replace('.com', '').replace('.org', '').replace('.net', '')
            domain_parts = domain_parts.replace('.co.uk', '').replace('.io', '')
            
            # Convert domain to meaningful terms
            domain_tokens = re.split(r'[.-]', domain_parts)
            meaningful_tokens = [token for token in domain_tokens if len(token) > 2]
            
            return ' '.join(meaningful_tokens)
        except:
            return ""
    
    def _generate_meaningful_category_names(self, emails: List[Dict], texts: List[str], 
                                          cluster_assignments: np.ndarray) -> Dict[int, str]:
        """Generate meaningful category names using multiple strategies"""
        category_names = {}
        unique_clusters = set(cluster_assignments)
        
        for cluster_id in unique_clusters:
            if cluster_id == -1:  # Noise cluster
                category_names[cluster_id] = "Miscellaneous"
                continue
            
            # Get emails in this cluster
            cluster_mask = cluster_assignments == cluster_id
            cluster_emails = [emails[i] for i in range(len(emails)) if cluster_mask[i]]
            cluster_texts = [texts[i] for i in range(len(texts)) if cluster_mask[i]]
            
            # Strategy 1: Semantic analysis using embeddings
            category_name = self._analyze_cluster_semantics(cluster_emails, cluster_texts, cluster_id)
            
            # Strategy 2: Domain-based analysis as fallback
            if not category_name or category_name.startswith("Cluster"):
                category_name = self._analyze_cluster_domains(cluster_emails, cluster_id)
            
            # Strategy 3: Keyword frequency as final fallback
            if not category_name or category_name.startswith("Cluster"):
                category_name = self._analyze_cluster_keywords(cluster_texts, cluster_id)
            
            category_names[cluster_id] = category_name
        
        return category_names
    
    def _analyze_cluster_semantics(self, cluster_emails: List[Dict], 
                                 cluster_texts: List[str], cluster_id: int) -> str:
        """Analyze cluster using semantic similarity to predefined categories"""
        
        # Predefined semantic categories with rich descriptions
        semantic_categories = {
            'Professional Development': [
                'job opportunities career development professional growth hiring recruitment',
                'linkedin work employment position application interview',
                'resume cv skills experience qualifications professional network'
            ],
            'Development & Technology': [
                'github repository code programming development software',
                'pull request commit merge build deployment ci cd',
                'bug fix update version release technical documentation'
            ],
            'E-commerce & Shopping': [
                'order purchase buy shopping cart checkout payment',
                'product price discount sale offer deal promotion',
                'shipping delivery return refund customer service'
            ],
            'Entertainment & Media': [
                'streaming video movie show series entertainment',
                'netflix amazon prime youtube music podcast',
                'watch listen subscribe content recommendation'
            ],
            'Security & Authentication': [
                'login security password authentication verification account',
                'secure access two factor verification email confirmation',
                'suspicious activity security alert password reset'
            ],
            'Financial Services': [
                'bank banking payment transaction invoice billing',
                'credit card account balance statement finance',
                'insurance loan mortgage investment financial services'
            ],
            'News & Information': [
                'news newsletter update announcement information bulletin',
                'article blog post research report industry insights',
                'weekly digest daily briefing market trends'
            ],
            'Social & Networking': [
                'social media facebook twitter linkedin instagram',
                'friend connection follow like share comment',
                'community group event networking social update'
            ],
            'Support & Service': [
                'support help assistance customer service ticket',
                'problem issue troubleshooting technical support',
                'contact support team help desk service request'
            ],
            'Travel & Lifestyle': [
                'travel booking hotel flight vacation trip',
                'reservation confirmation itinerary travel plans',
                'airline airport booking confirmation travel insurance'
            ]
        }
        
        # Combine all cluster texts
        cluster_text = ' '.join(cluster_texts)
        
        if not cluster_text.strip():
            return f"Cluster {cluster_id}"
        
        # Calculate similarity with each category
        cluster_embedding = self.model.encode([cluster_text])
        best_category = None
        best_score = 0
        
        for category, descriptions in semantic_categories.items():
            category_text = ' '.join(descriptions)
            category_embedding = self.model.encode([category_text])
            
            similarity = cosine_similarity(cluster_embedding, category_embedding)[0][0]
            
            if similarity > best_score and similarity > 0.3:  # Minimum threshold
                best_score = similarity
                best_category = category
        
        if best_category:
            cluster_size = len(cluster_emails)
            return f"{best_category} ({cluster_size} emails)"
        
        return None
    
    def _analyze_cluster_domains(self, cluster_emails: List[Dict], cluster_id: int) -> str:
        """Analyze cluster based on sender domains"""
        domains = []
        for email in cluster_emails:
            sender = email.get('sender', '')
            if '@' in sender:
                domain = sender.split('@')[1].lower()
                domains.append(domain)
        
        if not domains:
            return None
        
        # Count domain frequencies
        domain_counts = Counter(domains)
        most_common_domain = domain_counts.most_common(1)[0][0]
        
        # Domain-based categorization
        domain_categories = {
            'github.com': 'GitHub Notifications',
            'linkedin.com': 'LinkedIn Professional',
            'amazon.com': 'Amazon Services',
            'netflix.com': 'Netflix Entertainment',
            'spotify.com': 'Spotify Music',
            'youtube.com': 'YouTube Content',
            'facebook.com': 'Facebook Social',
            'twitter.com': 'Twitter Social',
            'instagram.com': 'Instagram Social',
            'paypal.com': 'PayPal Financial',
            'stripe.com': 'Stripe Payments',
            'google.com': 'Google Services',
            'microsoft.com': 'Microsoft Services',
            'apple.com': 'Apple Services',
            'dropbox.com': 'Dropbox Storage',
            'slack.com': 'Slack Communication',
            'zoom.us': 'Zoom Meetings',
            'notion.so': 'Notion Workspace'
        }
        
        cluster_size = len(cluster_emails)
        
        # Check for exact domain matches
        if most_common_domain in domain_categories:
            return f"{domain_categories[most_common_domain]} ({cluster_size} emails)"
        
        # Check for partial domain matches
        for known_domain, category in domain_categories.items():
            if known_domain in most_common_domain or most_common_domain in known_domain:
                return f"{category} ({cluster_size} emails)"
        
        # Generic domain-based naming
        domain_name = most_common_domain.replace('.com', '').replace('.org', '').replace('.net', '')
        return f"{domain_name.title()} Communications ({cluster_size} emails)"
    
    def _analyze_cluster_keywords(self, cluster_texts: List[str], cluster_id: int) -> str:
        """Fallback keyword-based analysis"""
        # Combine all texts and extract frequent meaningful words
        all_text = ' '.join(cluster_texts).lower()
        words = re.findall(r'\b[a-z]{4,}\b', all_text)  # Words with 4+ characters
        
        if not words:
            return f"Email Group {cluster_id}"
        
        # Count word frequencies
        word_counts = Counter(words)
        
        # Filter out common stopwords
        stopwords = {'email', 'message', 'mail', 'sent', 'received', 'please', 'thank', 
                    'thanks', 'regards', 'best', 'sincerely', 'hello', 'dear'}
        
        meaningful_words = [(word, count) for word, count in word_counts.most_common(10) 
                           if word not in stopwords and len(word) > 3]
        
        if meaningful_words:
            top_word = meaningful_words[0][0].title()
            return f"{top_word} Related"
        
        return f"Email Group {cluster_id}"
    
    def _group_emails_by_category(self, emails: List[Dict], cluster_assignments: np.ndarray, 
                                category_names: Dict[int, str]) -> Dict[str, List[Dict]]:
        """Group emails by their assigned categories"""
        categorized_emails = {}
        
        for email, cluster_id in zip(emails, cluster_assignments):
            category_name = category_names.get(cluster_id, f"Cluster {cluster_id}")
            
            if category_name not in categorized_emails:
                categorized_emails[category_name] = []
            
            # Add metadata to email
            email_with_metadata = email.copy()
            email_with_metadata['cluster_id'] = int(cluster_id)
            email_with_metadata['category'] = category_name
            email_with_metadata['is_outlier'] = cluster_id == -1
            
            categorized_emails[category_name].append(email_with_metadata)
        
        return categorized_emails
    
    def _print_categorization_summary(self, categorized_emails: Dict[str, List[Dict]]):
        """Print detailed summary of categorization results"""
        print(f"\n📊 Smart Email Categorization Results:")
        print(f"   🎯 Total Categories: {len(categorized_emails)}")
        
        # Sort categories by size (largest first)
        sorted_categories = sorted(categorized_emails.items(), 
                                 key=lambda x: len(x[1]), reverse=True)
        
        for category, emails in sorted_categories:
            print(f"   📂 {category}: {len(emails)} emails")
            
            # Show sample subjects with better formatting
            sample_subjects = []
            for email in emails[:2]:
                subject = email.get('subject', 'No Subject')
                if len(subject) > 60:
                    subject = subject[:57] + "..."
                sample_subjects.append(subject)
            
            for subject in sample_subjects:
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
            'avg_cluster_size': 0
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
        
        return insights