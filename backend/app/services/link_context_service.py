"""Link Context Extraction Service.

Extracts deep linguistic, structural, and semantic context surrounding hyperlinks
in documents. Computes sentence boundaries, salient domain keywords, and URL tokens.
"""

import re
from typing import List, Dict, Any, Optional
from backend.app.utils.url_utils import extract_url_tokens

# Standard English stopwords to filter out when extracting domain keywords
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "arent", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "cant", "cannot", "could", "couldnt", "did", "didnt", "do", "does", "doesnt",
    "doing", "dont", "down", "during", "each", "few", "for", "from", "further", "had", "hadnt",
    "has", "hasnt", "have", "havent", "having", "he", "hed", "hell", "hes", "her", "here", "heres",
    "hers", "herself", "him", "himself", "his", "how", "hows", "i", "id", "ill", "im", "ive", "if",
    "in", "into", "is", "isnt", "it", "its", "itself", "lets", "me", "more", "most", "mustnt", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shant", "she", "shed", "shell", "shes",
    "should", "shouldnt", "so", "some", "such", "than", "that", "thats", "the", "their", "theirs",
    "them", "themselves", "then", "there", "theres", "these", "they", "theyd", "theyll", "theyre",
    "theyve", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasnt", "we", "wed", "well", "were", "weve", "werent", "what", "whats", "when", "whens",
    "where", "wheres", "which", "while", "who", "whos", "whom", "why", "whys", "with", "wont",
    "would", "wouldnt", "you", "youd", "youll", "youre", "youve", "your", "yours", "yourself",
    "yourselves", "click", "here", "link", "url", "http", "https", "www", "com", "org", "net"
}


class LinkContextService:
    @staticmethod
    def extract_sentence(text: str, anchor: str) -> str:
        """Extract the exact sentence containing the anchor text or URL."""
        if not text:
            return ""
        if not anchor:
            return text[:200].strip()

        # Split on sentence boundaries (. ! ?)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for s in sentences:
            if anchor.lower() in s.lower():
                return s.strip()

        # Fallback: slice 100 chars around the anchor
        idx = text.lower().find(anchor.lower())
        if idx != -1:
            start = max(0, idx - 80)
            end = min(len(text), idx + len(anchor) + 80)
            return text[start:end].strip()

        return text[:250].strip()

    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """Extract salient domain keywords from text using frequency and stopword filtering."""
        if not text:
            return []

        # Find words (minimum 3 characters, alphanumeric)
        words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]{2,}\b", text.lower())
        meaningful_words = [w for w in words if w not in STOPWORDS and not w.isdigit()]

        # Frequency count
        freq: Dict[str, int] = {}
        for w in meaningful_words:
            freq[w] = freq.get(w, 0) + 1

        # Sort by frequency
        sorted_keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [k for k, _ in sorted_keywords[:max_keywords]]

    @classmethod
    def build_structured_context(
        cls,
        url: str,
        anchor_text: Optional[str],
        paragraph_text: Optional[str],
        section_heading: Optional[str],
        document_title: Optional[str],
    ) -> Dict[str, Any]:
        """Build the complete research-grade context structure."""
        anchor = (anchor_text or "").strip()
        paragraph = (paragraph_text or "").strip()
        heading = (section_heading or "").strip()
        title = (document_title or "").strip()

        surrounding_text = cls.extract_sentence(paragraph, anchor or url)

        # Keyword pool combines title, heading, anchor, and surrounding sentence
        keyword_source = f"{title} {heading} {anchor} {surrounding_text}"
        keywords = cls.extract_keywords(keyword_source, max_keywords=10)

        # URL tokens (domain, path, filename, query terms)
        url_tokens = extract_url_tokens(url)

        return {
            "anchor_text": anchor or url_tokens.get("filename") or url,
            "surrounding_text": surrounding_text or paragraph[:200],
            "paragraph_text": paragraph,
            "section_heading": heading or "General Document Body",
            "document_title": title or "Untitled Document",
            "url_tokens": url_tokens,
            "keywords": keywords,
        }
