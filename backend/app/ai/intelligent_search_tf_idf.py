"""
Intelligent Data Search (NLP-Based) for MEDIBORA
Uses TF-IDF vectorization and cosine similarity for semantic search
"""

import re
import math
from typing import List, Dict, Any, Tuple
from collections import Counter
from dataclasses import dataclass
import json

@dataclass
class SearchResult:
    """Represents a search result"""
    id: int
    type: str
    title: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any]

class TFIDFSearchEngine:
    """
    TF-IDF based Intelligent Search Engine
    Processes clinical notes using TF-IDF vectorization and cosine similarity
    """
    
    def __init__(self):
        self.documents = []
        self.document_vectors = []
        self.vocabulary = {}
        self.idf = {}
        self.stop_words = self._get_stop_words()
    
    def _get_stop_words(self) -> set:
        """Get English stop words for filtering"""
        return {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'the', 'this', 'but', 'they', 'have',
            'had', 'what', 'said', 'each', 'which', 'she', 'do', 'how', 'their',
            'if', 'up', 'out', 'many', 'then', 'them', 'these', 'so', 'some',
            'her', 'would', 'make', 'like', 'into', 'him', 'time', 'two', 'more',
            'go', 'no', 'way', 'could', 'my', 'than', 'first', 'been', 'call',
            'who', 'its', 'now', 'find', 'long', 'down', 'day', 'did', 'get',
            'come', 'made', 'may', 'part', 'patient', 'history', 'notes'
        }
    
    def _preprocess_text(self, text: str) -> List[str]:
        """
        Preprocess text: lowercase, tokenize, remove stop words
        """
        if not text:
            return []
        
        # Convert to lowercase and remove special characters
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        
        # Tokenize
        tokens = text.split()
        
        # Remove stop words and short tokens
        tokens = [t for t in tokens if t not in self.stop_words and len(t) > 2]
        
        return tokens
    
    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Compute term frequency"""
        if not tokens:
            return {}
        
        token_counts = Counter(tokens)
        total_tokens = len(tokens)
        
        return {term: count / total_tokens for term, count in token_counts.items()}
    
    def _compute_idf(self, documents: List[List[str]]) -> Dict[str, float]:
        """Compute inverse document frequency"""
        n_docs = len(documents)
        idf = {}
        
        # Count document frequency for each term
        for doc in documents:
            unique_terms = set(doc)
            for term in unique_terms:
                idf[term] = idf.get(term, 0) + 1
        
        # Compute IDF
        for term in idf:
            idf[term] = math.log(n_docs / (idf[term] + 1)) + 1
        
        return idf
    
    def _compute_tfidf_vector(self, tf: Dict[str, float], idf: Dict[str, float]) -> Dict[str, float]:
        """Compute TF-IDF vector"""
        return {term: tf[term] * idf.get(term, 0) for term in tf}
    
    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Compute cosine similarity between two vectors"""
        # Get all unique terms
        all_terms = set(vec1.keys()) | set(vec2.keys())
        
        # Compute dot product
        dot_product = sum(vec1.get(term, 0) * vec2.get(term, 0) for term in all_terms)
        
        # Compute magnitudes
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Index documents for search
        Each document should have: id, type, title, content, metadata
        """
        self.documents = documents
        
        # Preprocess all documents
        processed_docs = []
        for doc in documents:
            # Combine title and content for indexing
            full_text = f"{doc.get('title', '')} {doc.get('content', '')}"
            tokens = self._preprocess_text(full_text)
            processed_docs.append(tokens)
        
        # Compute IDF
        self.idf = self._compute_idf(processed_docs)
        
        # Compute TF-IDF vectors for all documents
        self.document_vectors = []
        for tokens in processed_docs:
            tf = self._compute_tf(tokens)
            tfidf = self._compute_tfidf_vector(tf, self.idf)
            self.document_vectors.append(tfidf)
    
    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        Search documents using TF-IDF and cosine similarity
        Returns top_k most relevant results
        """
        if not self.documents or not query:
            return []
        
        # Preprocess query
        query_tokens = self._preprocess_text(query)
        
        # Compute query TF-IDF vector
        query_tf = self._compute_tf(query_tokens)
        query_vector = self._compute_tfidf_vector(query_tf, self.idf)
        
        # Compute similarity with all documents
        results = []
        for i, doc_vector in enumerate(self.document_vectors):
            similarity = self._cosine_similarity(query_vector, doc_vector)
            
            if similarity > 0:  # Only include relevant results
                doc = self.documents[i]
                results.append(SearchResult(
                    id=doc.get('id', i),
                    type=doc.get('type', 'unknown'),
                    title=doc.get('title', ''),
                    content=doc.get('content', '')[:200] + '...' if len(doc.get('content', '')) > 200 else doc.get('content', ''),
                    similarity_score=round(similarity, 4),
                    metadata=doc.get('metadata', {})
                ))
        
        # Sort by similarity score (descending)
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return results[:top_k]
    
    def search_by_patient(self, query: str, patient_id: int, top_k: int = 5) -> List[SearchResult]:
        """Search within a specific patient's records"""
        # Filter documents by patient_id
        patient_docs = [doc for doc in self.documents if doc.get('metadata', {}).get('patient_id') == patient_id]
        
        if not patient_docs:
            return []
        
        # Create temporary index for patient documents
        temp_engine = TFIDFSearchEngine()
        temp_engine.index_documents(patient_docs)
        
        return temp_engine.search(query, top_k)
    
    def suggest_similar_terms(self, query: str) -> List[str]:
        """Suggest similar terms based on indexed vocabulary"""
        query_tokens = self._preprocess_text(query)
        suggestions = []
        
        for token in query_tokens:
            # Find similar terms in vocabulary
            for vocab_term in self.idf.keys():
                if vocab_term != token and self._levenshtein_distance(token, vocab_term) <= 2:
                    suggestions.append(vocab_term)
        
        return list(set(suggestions))[:5]
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Compute Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

# Medical synonym mapping for enhanced search
MEDICAL_SYNONYMS = {
    'bp': ['blood pressure', 'hypertension', 'hypotension'],
    'hr': ['heart rate', 'pulse', 'tachycardia', 'bradycardia'],
    'temp': ['temperature', 'fever', 'pyrexia', 'hypothermia'],
    'rr': ['respiratory rate', 'breathing', 'respiration'],
    'spo2': ['oxygen saturation', 'oximetry', 'hypoxemia'],
    'dm': ['diabetes', 'diabetes mellitus', 'hyperglycemia'],
    'htn': ['hypertension', 'high blood pressure'],
    'copd': ['chronic obstructive pulmonary disease', 'emphysema'],
    'chest pain': ['angina', 'myocardial infarction', 'mi'],
    'fever': ['pyrexia', 'hyperthermia', 'febrile'],
    'cough': ['tussis', 'productive cough', 'dry cough'],
    'headache': ['migraine', 'cephalalgia'],
    'rash': ['dermatitis', 'exanthem', 'eruption'],
    'shortness of breath': ['dyspnea', 'sob', 'breathlessness'],
}

def expand_medical_query(query: str) -> str:
    """Expand medical query with synonyms"""
    query_lower = query.lower()
    expanded_terms = [query]
    
    for term, synonyms in MEDICAL_SYNONYMS.items():
        if term in query_lower:
            expanded_terms.extend(synonyms)
    
    return ' '.join(expanded_terms)

# Singleton instance
_search_engine = None

def get_search_engine() -> TFIDFSearchEngine:
    """Get or create the search engine singleton"""
    global _search_engine
    if _search_engine is None:
        _search_engine = TFIDFSearchEngine()
    return _search_engine
